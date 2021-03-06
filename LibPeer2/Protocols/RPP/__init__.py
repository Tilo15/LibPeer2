from LibPeer2.Networks import Network
from LibPeer2.Networks.PeerInfo import PeerInfo
from LibPeer2.Protocols.MX2 import MX2
from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference
from LibPeer2.Protocols.MX2.PathInfo import PathInfo
from LibPeer2.Protocols.MX2.PathStrategy import PathStrategy
from LibPeer2.Protocols.AIP import AIP
from LibPeer2.Protocols.AIP.ApplicationInformation import ApplicationInformation
from LibPeer2.Protocols.AIP.InstanceInformation import InstanceInformation
from LibPeer2.Protocols.STP import STP
from LibPeer2.Protocols.STP.Stream.IngressStream import IngressStream
from LibPeer2.Protocols.STP.Stream.EgressStream import EgressStream
from LibPeer2.Protocols.RPP.Announcement import Announcement
from LibPeer2.Protocols.RPP.PathQuery import PathQuery
from LibPeer2.Protocols.RPP.PathResponse import PathResponse
from LibPeer2.Protocols.RPP import PathNode
from LibPeer2.Debug import Log

from rx.subject import Subject
from rx import operators
from typing import Set
from typing import Dict

import struct

RPP_NAMESPACE = "RPP"
REPEATER_RESOURCE = b"INTERCONNECTED-NETWORK-REPEATERS"

COMMAND_ANNOUNCE = b"\x01"
COMMAND_JOIN = b"\x02"
COMMAND_FIND_PATH = b"\x03"

# Repeater Path Protocol

class RPP:

    def __init__(self, muxer: MX2, discoverer: AIP, is_repeater: bool = False):
        self.__muxer = muxer
        self.__discoverer = discoverer

        self.is_repeater = is_repeater
        self.instance_info: Dict[InstanceReference, PeerInfo] = {}
        self.instance_network: Dict[InstanceReference, Network] = {}
        self.__announced_instances: Set[InstanceReference] = set()

        # Create instance 
        self.__instance = self.__muxer.create_instance(RPP_NAMESPACE)

        # Create transport
        self.__transport = STP(self.__muxer, self.__instance)

        # Create application information
        self.__info = ApplicationInformation.from_instance(self.__instance)

        # Subscribe to muxer and discoverer events
        # self.__discoverer.ready.subscribe(self.__aip_ready)
        self.__instance.incoming_greeting.subscribe(self.__received_greeting)
        self.__transport.incoming_stream.subscribe(self.__new_stream)

        self.__ready = False
        self.ready = Subject()

        # Are we a repeater?
        if(self.is_repeater):
            # Yes, tag ourself with that resource
            self.__info.resources.add(REPEATER_RESOURCE)

        # Add the application to the discoverer
        self.__discoverer.add_application(self.__info).subscribe(self.__new_aip_app_peer)

        # Keep a set of reachable RPP repeater peers
        self.__repeaters: Set[InstanceReference] = set()

        self._ready = False
        self.ready = Subject()


    @property
    def instance_reference(self):
        return self.__instance.reference


    def add_instance(self, instance: InstanceReference):
        # Add to our set
        self.__announced_instances.add(instance)

        # Announce to connected repeaters
        self.__send_command(COMMAND_ANNOUNCE, Announcement([instance]).serialise().read())


    def find_path(self, instance: InstanceReference):
        # Construct a query
        query = PathQuery(instance, 15, [])

        # Create a Path Info from a stream
        def read_response(stream: IngressStream):
            response = PathResponse.deserialise(stream)
            stream.close()

            # Prepend hop to respondant repeater
            # TODO these flags may need to be looked at some more or the 
            # PathNode object redesigned
            # HACK we should probably just get some sort of full representation
            # from the RPP repeater we ask the path from, but can't at the moment as we require peer info
            response.nodes.insert(0, PathNode.PathNode(stream.origin, PathNode.FLAGS_NONE, self.__muxer.get_peer_info(stream.origin)))

            # TODO generate many possible strategies
            return [PathStrategy(PathInfo([x.instance for x in response.nodes]), response.nodes[0].peer_info),]

        # Send the query and map reply to PathResponse
        return self.__send_command(COMMAND_FIND_PATH, query.serialise().read(), True).pipe(operators.take(1), operators.map(read_response))


    def __new_aip_app_peer(self, instance):
        # Query for RPP repeater instances
        self.__discoverer.find_application_resource(self.__info, REPEATER_RESOURCE).answer.subscribe(self.__found_instance)


    def __found_instance(self, instance_info: InstanceInformation):
        # Is this peer already reachable?
        if(instance_info.instance_reference in self.__repeaters):
            # Don't harras it
            return

        # Inquire about the peer
        self.__muxer.inquire(self.__instance, instance_info.instance_reference, instance_info.connection_methods)
    

    def __received_greeting(self, instance: InstanceReference):
        # Do we already know about this peer?
        if(instance in self.__repeaters):
            # Nothing to do
            return

        # No, announce our instances
        self.__send_command_to(COMMAND_ANNOUNCE, Announcement(self.__announced_instances).serialise().read(), instance).subscribe(on_completed=self.__set_ready)

        # Save as repeater
        self.__repeaters.add(instance)

        # Are we a repeater?
        if(self.is_repeater):
            # Send join (empty)
            self.__send_command_to(COMMAND_JOIN, b"", instance)

            # Save instance info for flag lookups
            self.instance_info[instance] = self.__muxer.get_peer_info(instance)
            self.instance_network[instance] = self.__muxer.get_peer_network(instance)

    
    def __set_ready(self):
        if(self._ready):
            return

        self.ready.on_completed()

    
    def __send_command(self, command_type: bytes, data: bytes, expect_reply: bool = False, blacklist: Set[InstanceReference] = set()) -> Subject:
        # If we expect replies to this command, create a subject
        reply_subject = None
        if(expect_reply):
            reply_subject = Subject()

        count = 0

        # Loop over each repeater
        for repeater in self.__repeaters:
            # Is this a blacklisted repeater?
            if(repeater in blacklist):
                # Yes, skip
                continue

            # Send command
            subject = self.__send_command_to(command_type, data, repeater, expect_reply)

            count += 1

            # Do we expect a reply?
            if(expect_reply):
                # Yes, connect to subject
                subject.subscribe(reply_subject.on_next)

        Log.debug("Broadcasted a command to {} repeater/s".format(count))

        # Return reply subject
        return reply_subject


    def __send_command_to(self, command_type: bytes, data: bytes, instance: InstanceReference, expect_reply: bool = False) -> Subject:
        # Returns when the command has been sent, or with the reply if expctant
        subject = Subject()
            
        # Handler for eventual opening of stream
        def on_connected(stream: EgressStream):
            # Do we expect a reply?
            if(expect_reply):
                # Subscribe to reply
                stream.reply.subscribe(subject.on_next)

            # Send command type and command
            stream.write(command_type + data)

            # Close the stream
            stream.close()

            # Do we expect a reply?
            if(not expect_reply):
                # No, let caller know we are done
                subject.on_completed()

        # Open stream with the peer
        self.__transport.initialise_stream(instance).subscribe(on_connected)

        # Return the subject
        return subject
        

    def __new_stream(self, stream: IngressStream):
        # New command, what is it?
        command_type = stream.read(1)

        # Announce
        if(command_type == COMMAND_ANNOUNCE):
            # Read announcement
            announcement = Announcement.deserialise(stream)

            # Get peer info and network
            info = self.__muxer.get_peer_info(stream.origin)
            network = self.__muxer.get_peer_network(stream.origin)

            Log.debug("Peer announced itself with {} attached instance/s".format(len(announcement.instances)))

            # Update records
            for instance in announcement.instances:
                self.instance_info[instance] = info
                self.instance_network[instance] = network

            # Also add info for the RPP peer
            self.instance_info[stream.origin] = info
            self.instance_network[stream.origin] = network

        # Join
        elif(command_type == COMMAND_JOIN):
            Log.debug("Repeater peer joined")
            # Add as repeater peer
            self.__repeaters.add(stream.origin)

            # Save instance info for flag lookups
            self.instance_info[stream.origin] = self.__muxer.get_peer_info(stream.origin)
            self.instance_network[stream.origin] = self.__muxer.get_peer_network(stream.origin)

        # Find path
        elif(command_type == COMMAND_FIND_PATH):
            # Read the query
            query = PathQuery.deserialise(stream)

            # Is it an instance directly connected to us?
            if(query.target in self.instance_info):
                # Yes, get the flags
                flags = self.__get_instance_flags(stream.origin, query.target)

                Log.debug("Servicing query for path to an instance that is currently connected")

                self.__query_respond(stream.origin, stream.id, PathResponse([]))

            elif(query.ttl > 0):
                Log.debug("Forwarding query for path to instance")
                # Instance is not directly connected, forward query if still alive
                self.__forward_query(stream.origin, stream.id, query)


    def __forward_query(self, instance: InstanceReference, reply_to, query: PathQuery):
        # Add out own instance reference to the blacklist so it can't route through us again
        query.blacklist.append(self.__instance.reference)

        # Handle responses
        def on_responded(stream: IngressStream):
            # Read response
            response = PathResponse.deserialise(stream)

            # TODO: Save PeerInfo of other repeaters we may be able to communicate with
            # as the client asking for this path will try combinations

            # Get flags for respondant repeater
            flags = self.__get_instance_flags(instance, stream.origin)

            # Prepend hop to respondant repeater
            response.nodes.insert(0, PathNode.PathNode(stream.origin, flags, self.__muxer.get_peer_info(stream.origin)))

        # Forward the query to all my repeater friends
        self.__send_command(COMMAND_FIND_PATH, query.serialise().read(), True, set(query.blacklist)).pipe(operators.take(1)).subscribe(on_responded)


    def __get_instance_flags(self, origin: InstanceReference, target: InstanceReference):
        #set up flags
        flags = PathNode.FLAGS_NONE

        # Is it on the same network as the caller?
        # TODO this may need to use self.instance_network instead of the muxer lookup
        if(self.instance_network[origin] != self.instance_network[target]):
            # No, add bridge flag
            flags = flags | PathNode.FLAGS_BRIDGE

        return flags


    def __query_respond(self, instance: InstanceReference, reply_to, response: PathResponse):
        # Handler for stream setup
        def on_stream(stream: EgressStream):
            # Send the response
            stream.write(response.serialise().read())

            # Close
            stream.close()

        # Set up connection with instance
        self.__transport.initialise_stream(instance, in_reply_to=reply_to).subscribe(on_stream)