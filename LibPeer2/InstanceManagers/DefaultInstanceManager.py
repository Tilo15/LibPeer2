from LibPeer2.InstanceManagers import InstanceManager
from LibPeer2.Protocols.MX2 import MX2
from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference
from LibPeer2.Protocols.AIP import AIP
from LibPeer2.Protocols.AIP.ApplicationInformation import ApplicationInformation
from LibPeer2.Protocols.AIP.InstanceInformation import InstanceInformation
from LibPeer2.Protocols.STP import STP
from LibPeer2.Networks.IPv4 import IPv4


from typing import Set
from typing import Dict
from rx.subjects import ReplaySubject
from rx.subjects import Subject


class DefaultInstanceManager(InstanceManager):

    def __init__(self, namespace: str, try_routes = True, networks = []):
        super().__init__(namespace)

        self.try_routes = try_routes

        self.__reachable_peers: Set[InstanceReference] = set()
        self.__resource_subjects: Dict[bytes, ReplaySubject] = {}
        self.__peer_subjects: Dict[InstanceReference, ReplaySubject] = {}
        self.__networks = networks

        if(len(self.__networks) == 0):
            port = 5156
            while True:
                try:
                    network = IPv4("0.0.0.0", port)
                    self.__networks.append(network)
                    break
                except Exception as e:
                    if(port >= 9000):
                        raise e

                    port += 1

        self.__muxer = MX2()

        for network in self.__networks:
            network.bring_up()
            self.__muxer.register_network(network)

        self.__discoverer = AIP(self.__muxer)
        self.__instance = self.__muxer.create_instance(self.namespace)
        self.__transport = STP(self.__muxer, self.__instance)

        self.__discoverer.ready.subscribe(self.__aip_ready)
        self.__instance.incoming_greeting.subscribe(self.__received_greeting)
        self.__transport.incoming_stream.subscribe(self.__new_stream)

        for network in self.__networks:
            self.__discoverer.add_network(network)

        self.__info = ApplicationInformation.from_instance(self.__instance)


    def establish_stream(self, peer: InstanceReference, *, in_reply_to = None) -> Subject:
        # Settle on a reply
        reply = in_reply_to or b"\x00"*16

        # Ask the transport to establish a stream
        return self.__transport.initialise_stream(peer, in_reply_to=reply)


    def find_resource_peers(self, resource: bytes) -> Subject:
        # Do we already have a subject for this query?
        if(resource not in self.__resource_subjects):
            # Create one
            self.__resource_subjects[resource] = ReplaySubject()

        # Create a query for the resource
        query = self.__discoverer.find_application_resource(self.__info, resource)

        # Subscribe to the queries answer
        query.answer.subscribe(lambda x: self.__found_resource_instance(x, resource))

        # Return the resource subject
        return self.__resource_subjects[resource]


    @property
    def resources(self) -> Set[bytes]:
        return self.__info.resources


    def __aip_ready(self, state):
        # Add the application to the discoverer
        self.__discoverer.add_application(self.__info).subscribe(self.__new_aip_app_peer)

    
    def __new_aip_app_peer(self, instance):
        # Query for application instances
        self.__discoverer.find_application_instance(self.__info).subscribe(self.__found_instance)

    
    def __found_instance(self, instance_info: InstanceInformation):
        # Is this peer already reachable?
        if(instance_info.instance_reference in self.__reachable_peers):
            # Don't harras it
            return

        # Inquire about the peer
        subject = self.__muxer.inquire(self.__instance, instance_info.instance_reference, instance_info.connection_methods)

        # Handle timeouts
        subject.subscribe(on_error=lambda x: self.__greeting_timeout(instance_info.instance_reference, instance_info.aip_instance))



    def __found_resource_instance(self, instance_info: InstanceInformation, resource: bytes):
        # Get the resource subject
        resource_subject = self.__resource_subjects[resource]

        # Get the instance subject
        instance_subject = self.__get_instance_subject(instance_info.instance_reference)

        # Notify resource subject when instance subject is reachable
        instance_subject.subscribe(resource_subject.on_next)

        # Handle new instance
        self.__found_instance(instance_info)
        

    
    def __received_greeting(self, instance: InstanceReference):
        # Have we already marked this instance as reachable
        if(instance in self.__reachable_peers):
            # Don't notify app again
            return

        # Add to reachable peers
        self.__reachable_peers.add(instance)

        # Notify instance subject
        self.__get_instance_subject(instance).on_next(instance)

        # Notify the app
        self.new_peer.on_next(instance)


    def __new_stream(self, stream):
        # Notify app of new stream
        self.new_stream.on_next(stream)


    def __get_instance_subject(self, ref: InstanceReference) -> Subject:
        # Do we have it?
        if(ref in self.__peer_subjects):
            # Yes
            return self.__peer_subjects[ref]

        # No, create it
        subject = ReplaySubject()
        self.__peer_subjects[ref] = subject
        return subject


    def __greeting_timeout(self, target: InstanceReference, router: InstanceReference):
        # Have we already found this peer?
        if(target in self.__instance.reachable_peers or not self.try_routes):
            return

        # Did not receive greeting from instance, ask for routes
        query = self.__discoverer.find_route(router, target)

        def handle_route(next_router: InstanceInformation):
            # Have we already found this peer?
            if(target in self.__instance.reachable_peers):
                return

            # An AIP peer said that it is connected to the peer and is willing to route, inquire via the router
            inquire_subject = self.__muxer.inquire(self.__instance, target, next_router.connection_methods)

            # Handle timeout
            inquire_subject.subscribe(on_error=lambda x: self.__greeting_timeout(target, next_router.aip_instance))

        # Subscribe to answers
        query.answer.subscribe(handle_route)
