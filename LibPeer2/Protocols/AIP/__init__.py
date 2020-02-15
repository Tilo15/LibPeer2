from LibPeer2.Protocols.MX2 import MX2
from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference
from LibPeer2.Protocols.STP import STP
from LibPeer2.Protocols.STP.Stream.IngressStream import IngressStream
from LibPeer2.Protocols.STP.Stream.EgressStream import EgressStream
from LibPeer2.Protocols.AIP.QueryGroup import QueryGroup
from LibPeer2.Protocols.AIP.Query import Query
from LibPeer2.Protocols.AIP.Answer import Answer
from LibPeer2.Protocols.AIP.ApplicationInformation import ApplicationInformation
from LibPeer2.Protocols.AIP.InstanceInformation import InstanceInformation
from LibPeer2.Networks import Network
from LibPeer2.Networks.PeerInfo import PeerInfo
from LibPeer2.Networks.Advertisement import Advertisement

from typing import Dict
from typing import Set
from typing import List
from cachetools import TTLCache

import struct
import random
import rx

DATA_FOLLOWING_REQUEST = "R"
DATA_FOLLOWING_QUERY = b"Q"
DATA_FOLLOWING_ANSWER = b"A"

REQUEST_CAPABILITIES = b"C"
REQUEST_ADDRESS = b"A"
REQUEST_PEERS = b"P"

QUERY_GROUP = b"G"
QUERY_APPLICATION = b"A"
QUERY_APPLICATION_RESOURCE = b"R"

CAPABILITY_ADDRESS_INFO = b"A"
CAPABILITY_FIND_PEERS = b"P"
CAPABILITY_QUERY_ANSWER = b"Q"

MAX_QUERY_HOPS = 16


"""Application Information Protocol"""
class AIP:
    

    def __init__(self, muxer: MX2, capabilities = set(CAPABILITY_ADDRESS_INFO, CAPABILITY_FIND_PEERS, CAPABILITY_QUERY_ANSWER)):

        self.__application_information: List[ApplicationInformation] = []

        self.__capabilities = capabilities

        self.__muxer = muxer
        self.__instance = muxer.create_instance("AIP")
        self.__transport = STP(self.__muxer, self.__instance)
    
        self.__discovered_peers: Set[InstanceReference] = set()
        self.__peer_connection_methods: Dict[InstanceReference, Set[PeerInfo]] = {}
        self.__instance_capabilities: Dict[InstanceReference, Set[int]] = {}
        self.__default_group = QueryGroup(20)
        self.__query_groups: Dict[bytes, QueryGroup] = {}

        self.__instance.incoming_greeting.subscribe(self.__rx_greeting)
        self.__transport.incoming_stream.subscribe(self.__rx_stream)

        self.__queries = TTLCache(64, 120)
        self.__query_response_count = TTLCache(65536, 120)
        self.__handled_query_ids: Set[bytes] = set()
        self.__peer_info: Set[PeerInfo] = set()


    def add_network(self, network: Network):
        network.incoming_advertisment.subscribe(self.__rx_advertisement)
        self.__muxer.register_network(network)


    def add_application(self, application_information: ApplicationInformation):
        # Save reference to the application
        self.__application_information.append(application_information)

        # Join group for this application
        self.__join_query_group(application_information.namespace_bytes)


    def find_application_instance(self, app: ApplicationInformation):
        # Are we in a query group for this application yet?
        if(app.namespace_bytes not in self.__query_groups):
            raise Exception("Not in query group for specified application namespace")

        # Create the query
        query = Query(QUERY_APPLICATION + app.namespace_bytes)

        # Send the query
        self.__initiate_query(query, self.__query_groups[app.namespace_bytes])

        # Return the query
        return query


    def find_application_resource(self, app: ApplicationInformation, resource_identifier: bytes):
        # Are we in a query group for this application yet?
        if(app.namespace_bytes not in self.__query_groups):
            raise Exception("Not in query group for specified application namespace")

        # Is the resource identifier valid?
        if(len(resource_identifier) != 32):
            raise Exception("Resource identifier not 32 bytes.")

        # Create the query
        query = Query(QUERY_APPLICATION_RESOURCE + resource_identifier + app.namespace_bytes)

        # Send the query
        self.__initiate_query(query, self.__query_groups[app.namespace_bytes])

        # Return the query
        return query



    def __initiate_query(self, query: Query, group: QueryGroup):
        # Save a reference to the query
        self.__queries[query.identifier] = query
        self.__handled_query_ids.add(query.identifier)

        # Send the query
        self.__send_query(query, group)

    
    def __send_query(self, query: Query, group: QueryGroup):
        # Does the query have any hops left?
        if(query.hops > MAX_QUERY_HOPS):
            return

        # Function to handle new streams for this query
        def on_stream_open(stream: EgressStream):
            # Tell the instance that the data that follows is a query
            stream.write(DATA_FOLLOWING_QUERY)

            # Write the query
            query.serialise(stream)

            # Close the stream
            stream.close()

        # Loop over each instance in the query group
        for instance in group.instances:
            # Open a stream with the instance
            self.__transport.initialise_stream(instance).subscribe(on_stream_open)


    def __send_answer(self, answer: Answer):
        # Get (and remove) the last item from the path list
        send_to = answer.path.pop()

        # Don't send answers to queries we havent received
        if(answer.in_reply_to not in self.__query_response_count):
            return

        # Don't send answers to queries that have exceed there maximum replies
        if(self.__query_response_count[answer.in_reply_to] <= 0):
            return

        # Decrement response counter (stops at 0)
        self.__query_response_count[answer.in_reply_to] -= 1

        # Function to handle new stream for this answer
        def on_stream_open(stream: EgressStream):
            # Tell the instance that the data that follows is an answer
            stream.write(DATA_FOLLOWING_ANSWER)

            # Write the query
            answer.serialise(stream)

            # Close the stream
            stream.close()

        # Open a stream with the instance
        self.__transport.initialise_stream(send_to).subscribe(on_stream_open)


    def __join_query_group(self, group: bytes):
        # Create the query group
        self.__query_groups[group] = QueryGroup()

        # Construct a query asking for peers in the group
        query = Query(QUERY_GROUP + group)

        # Create handler for query answers
        def on_query_answer(answer: InstanceInformation):
            # Inquire
            self.__muxer.inquire(self.__instance, answer.instance_reference, answer.connection_methods)

        # Send the query
        self.__initiate_query(query, self.__default_group)


    def __rx_advertisement(self, advertisement: Advertisement):
        # Send an inquiry
        self.__muxer.inquire(self.__instance, advertisement.instance_reference, [advertisement.peer_info])


    def __rx_greeting(self, greeting: InstanceReference):
        # Add to known peers
        self.__discovered_peers.add(greeting)

        # Request capabilities from the instance
        self.__request_capabilities(greeting).subscribe(lambda x: self.__rx_capabilities(x, greeting))


    def __rx_capabilities(self, capabilities: List[bytes], instance: InstanceReference):
        # Save the capabilities
        self.__capabilities[instance] = capabilities

        # Can we ask the peer for our address?
        if(CAPABILITY_ADDRESS_INFO in capabilities):
            # Yes, do it
            self.__request_address(instance).subscribe(self.__rx_address)

        # Can we ask the peer for other peers?
        if(CAPABILITY_FIND_PEERS in capabilities):
            # Yes, do it
            self.__request_peers(instance).subscribe(self.__rx_peers)

        # Can we send queries and answers to this peer?
        if(CAPABILITY_QUERY_ANSWER in capabilities):
            # Yes, add to default group
            self.__default_group.add_peer(instance)


    def __rx_address(self, info: PeerInfo):
        # We received peer info, add to our set
        self.__peer_info.add(info)


    def __rx_peers(self, peers: List[InstanceInformation]):
        # We received a list of peers running AIP, do we want more peers?
        if(not self.__default_group.actively_connect):
            # Don't worry bout it
            return

        # Send out inquries to the peers
        for peer in peers:
            self.__muxer.inquire(self.__instance, peer.instance_reference, peer.connection_methods)


    def __rx_stream(self, stream: IngressStream):
        # Figure out what data follows
        following = stream.read(1)

        if(following == DATA_FOLLOWING_ANSWER and CAPABILITY_QUERY_ANSWER in self.__capabilities):
            self.__handle_answer(stream)

        elif(following == DATA_FOLLOWING_QUERY and CAPABILITY_QUERY_ANSWER in self.__capabilities):
            self.__handle_query(stream)

        elif(following == DATA_FOLLOWING_REQUEST):
            self.__handle_request(stream)

        else:
            stream.close()


    def __handle_answer(self, stream: IngressStream):
        # Deserialise the answer
        answer = Answer.deserialise(stream)

        # Is this an answer to one of our queries?
        if(answer.in_reply_to in self.__queries):
            # Yes, get the query
            query = self.__queries[answer.in_reply_to]

            # Get instance information from the answer
            info = InstanceInformation.deserialise(answer.data)

            # Notify the query's subject listeners
            query.answer.on_next(info)

            # Complete!
            return

        # Does this have somwhere to forward to?
        if(len(answer.path) > 0):
            # Put it back on its path
            self.__send_answer(answer)


    def __handle_query(self, stream: IngressStream):
        # Deserialise the query
        query = Query.deserialise(stream)

        # Have we come across this query before?
        if(query.identifier in self.__handled_query_ids):
            # Don't forward
            return

        # Mark as handled
        self.__handled_query_ids.add(query.identifier)

        # Create a replies counter
        self.__query_response_count[query.identifier] = query.max_replies

        # Append the originator of the stream to the query reply path
        query.return_path.append(stream.origin)

        # Increment the query hops
        query.hops += 1

        # Find query type
        query_type = query.data[:1]

        if(query_type == QUERY_GROUP):
            # Get the group identifier
            group = query.data[1:]

            # Are we in this group?
            if(group in self.__query_groups):
                # Yes, create some instance information
                instance = InstanceInformation(self.__instance.reference, self.__peer_info)

                # Send the instance information in the answer
                answer = Answer(instance.serialise())

                # Send the answer
                self.__send_answer(answer)

            # This is a query for a group, forward on to default group
            self.__send_query(query, self.__default_group)


        elif(query_type == QUERY_APPLICATION):
            # Get the application namespace
            namespace = query.data[1:]

            # Are we in the group for this namespace?
            if(namespace in self.__query_groups):
                # Yes, find relevent ApplicationInformation
                for app in self.__application_information:
                    # Is this app relevent? TODO: Use a dictionary
                    if(app.namespace_bytes == namespace):
                        # Yes, create instance information
                        instance = InstanceInformation(app.instance, self.__peer_info)

                        # Send the instance information in the answer
                        self.__send_answer(Answer(instance.serialise()))

                # Forward on to the group
                self.__send_query(query, self.__query_groups[namespace])


        elif(query_type == QUERY_APPLICATION_RESOURCE):
            # Read the label
            label = query.data[1:33]

            # Read the application namespace
            namespace = query.data[33:]

            # Are we in the group for this namespace?
            if(namespace in self.__query_groups):
                # Yes, find relevent ApplicationInformation
                for app in self.__application_information:
                    # Is this app relevent? TODO: Use a dictionary
                    if(app.namespace_bytes == namespace and label in app.resources):
                        # Yes, create instance information
                        instance = InstanceInformation(app.instance, self.__peer_info)

                        # Send the instance information in the answer
                        self.__send_answer(Answer(instance.serialise()))

                # Forward on to the group
                self.__send_query(query, self.__query_groups[namespace])



    def __handle_request(self, stream: IngressStream):
        # Get the request type
        request_type = stream.read(1)

        # Is the request one of our capabilities?
        if(request_type not in self.__capabilities):
            # Ignore
            return

        # Handler to reply to the request
        def handle_stream(es: EgressStream):
            if(request_type == REQUEST_CAPABILITIES):
                capabilities = struct.pack("!B", len(self.__capabilities))
                capabilities += b"".join(self.__capabilities)
                es.write(capabilities)
                es.close()

            elif(request_type == REQUEST_ADDRESS):
                address = self.__muxer.get_peer_info(es.target)
                es.write(address.serialise())
                es.close()

            elif(request_type == REQUEST_PEERS):
                # Select up to 5 peers to reply with
                peers = [x for x in random.sample(self.__default_group.instances, min(5, len(s))) if x in self.__peer_connection_methods]

                # Send the count
                es.write(struct.pack("!B", len(peers)))
                
                for peer in peers:
                    # Get the peer's connection methods
                    methods = self.__peer_connection_methods[peer]

                    # Create an instance information object
                    info = InstanceInformation(peer, methods)

                    # Write the object to the stream
                    es.write(info.serialise())

        # Get a reply stream
        self.__transport.initialise_stream(stream.origin, stream.id).subscribe(handle_stream)

        # Have we encountered this peer before?
        if(instance not in self.__discovered_peers):
            # No, add it
            self.__discovered_peers.add(instance)

            # Ask for capabilities
            self.__request_capabilities(instance).subscribe(lambda x: self.__rx_capabilities(x, instance))


    def __send_request(self, request, instance: InstanceReference):
        # Create the reply subject
        reply = rx.subjects.Subject()

        # Create a handler
        def on_stream_open(stream: EgressStream):
            # Subscribe to stream reply
            stream.reply.subscribe(reply.on_next, reply.on_error, reply.on_completed)

            # Send the request
            stream.write(DATA_FOLLOWING_REQUEST + request)
            stream.close()

        # Open a stream with the peer
        self.__transport.initialise_stream(instance).subscribe(on_stream_open)

        return reply


    def __request_capabilities(self, instance: InstanceReference):
        # Create the subject
        reply = rx.subjects.Subject()

        # Handler for the reply
        def on_reply(stream: IngressStream):
            # Read number of capabilities
            capability_count = struct.unpack("!B", stream.read(1))[0]

            # Read the capabilities
            capabilities = [bytes([x]) for x in list(stream.read(capability_count))]

            # Notify subscriber
            reply.on_next(capabilities)
            reply.on_completed()

        # Make the request
        self.__send_request(REQUEST_CAPABILITIES, instance).subscribe(on_reply)
        return reply
        

    def __request_address(self, instance: InstanceReference):
        # Create the subject
        reply = rx.subjects.Subject()

        # Handler for the reply
        def on_reply(stream: IngressStream):
            # Read the address (peer info)
            address = PeerInfo.deserialise(stream)

            # Notify subscriber
            reply.on_next(address)
            reply.on_completed()

        # Make the request
        self.__send_request(REQUEST_ADDRESS, instance).subscribe(on_reply)
        return reply
        

    def __request_peers(self, instance: InstanceReference):
        # Create the subject
        reply = rx.subjects.Subject()

        # Handler for the reply
        def on_reply(stream: IngressStream):
            # Read number of peers
            peer_count = struct.unpack("!B", stream.read(1))[0]

            # List to hold info
            info = []

            # Read the peers (instance info)
            for i in range(peer_count):
                info.append(InstanceInformation.deserialise(stream))

            # Notify subscriber
            reply.on_next(info)
            reply.on_completed()

        # Make the request
        self.__send_request(REQUEST_PEERS, instance).subscribe(on_reply)
        return reply
 





