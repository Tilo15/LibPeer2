from LibPeer2.Networks.PeerInfo import PeerInfo
from LibPeer2.Protocols.MX2 import MX2
from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference
from LibPeer2.Protocols.AIP import AIP
from LibPeer2.Protocols.AIP.ApplicationInformation import ApplicationInformation
from LibPeer2.Protocols.AIP.InstanceInformation import InstanceInformation
from LibPeer2.Protocols.STP import STP
from LibPeer2.Protocols.STP.Stream.IngressStream import IngressStream
from LibPeer2.Protocols.STP.Stream.EgressStream import EgressStream
from LibPeer2.Protocols.NGP.Announcement import Announcement

from rx.subject import Subject
from typing import Set
from typing import Dict

import struct

NGP_NAMESPACE = b"NGP"
REPEATER_RESOURCE = b"REPEATER" + b"\x00"*24

COMMAND_ANNOUNCE = b"\x01"
COMMAND_JOIN = b"\x02"
QUERY_PATH = b"\x03"


class NGP:

    def __init__(self, muxer: MX2, discoverer: AIP, is_repeater: bool = False):
        self.__muxer = muxer
        self.__discoverer = discoverer
        self.__transport = STP(self.__muxer, self.__instance)

        self.is_repeater = is_repeater
        self.instance_info: Dict[InstanceReference, PeerInfo] = {}
        self.__announced_instances = Set[InstanceReference]()

        # Create instance 
        self.__instance = self.__muxer.create_instance(NGP_NAMESPACE)

        # Create application information
        self.__info = ApplicationInformation.from_instance(self.__instance)

        # Subscribe to muxer and discoverer events
        self.__discoverer.ready.subscribe(self.__aip_ready)
        self.__instance.incoming_greeting.subscribe(self.__received_greeting)
        self.__transport.incoming_stream.subscribe(self.__new_stream)

        # Keep a set of reachable NGP repeater peers
        self.__repeaters = Set[InstanceReference] = set()


    def __aip_ready(self, state):       
        # Are we a repeater?
        if(self.is_repeater):
            # Yes, tag ourself with that resource
            self.__info.resources.add(REPEATER_RESOURCE)

        # Add the application to the discoverer
        self.__discoverer.add_application(self.__info).subscribe(self.__new_aip_app_peer)


    def __new_aip_app_peer(self, instance):
        # Query for NGP repeater instances
        self.__discoverer.find_application_resource(self.__info, REPEATER_RESOURCE).subscribe(self.__found_instance)


    def __found_instance(self, instance_info: InstanceInformation):
        # Is this peer already reachable?
        if(instance_info.instance_reference in self.__reachable_peers):
            # Don't harras it
            return

        # Inquire about the peer
        self.__muxer.inquire(self.__instance, instance_info.instance_reference, instance_info.connection_methods)
    

    def __received_greeting(self, instance: InstanceReference):
        # Do we already know about this peer?
        if(instance in self.__reachable_peers):
            # Nothing to do
            return

        # No, announce our instances
        self.__send_command_to(COMMAND_ANNOUNCE, Announcement(self.__announced_instances), instance)


    def add_instance(self, instance: InstanceReference):
        # Add to our set
        self.__announced_instances.add(instance)

        # Announce to connected repeaters
        self.__send_command(COMMAND_ANNOUNCE, Announcement([instance]))

    
    def __send_command(self, command_type: bytes, data: bytes, expect_reply: bool) -> Subject:
        # If we expect replies to this command, create a subject
        reply_subject = None
        if(expect_reply):
            reply_subject = Subject()

        # Loop over each repeater
        for repeater in self.__repeaters:
            # Send command
            subject = self.__send_command_to(command_type, data, repeater, expect_reply)

            # Do we expect a reply?
            if(expect_reply):
                # Yes, connect to subject
                subject.subscribe(reply_subject.on_next)

        # Return reply subject
        return reply_subject


    def __send_command_to(self, command_type: bytes, data: bytes, instance: InstanceReference, expect_reply: bool) -> Subject:
        # Returns when the command has been sent, or with the reply if expctant
        subject = Subject()
            
        # Handler for eventual opening of stream
        def on_connected(stream: EgressStream):
            # Do we expect a reply?
            if(expect_reply):
                # Subscribe to reply
                stream.reply.subsribe(subject.on_next)

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
        

    
        
    
        