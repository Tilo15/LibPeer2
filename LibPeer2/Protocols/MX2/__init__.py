from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference
from LibPeer2.Protocols.MX2.Instance import Instance
from LibPeer2.Protocols.MX2.Frame import Frame
from LibPeer2.Protocols.MX2.Packet import Packet
from LibPeer2.Protocols.MX2.Inquiry import Inquiry
from LibPeer2.Protocols.MX2.PathInfo import PathInfo
from LibPeer2.Protocols.MX2.PathStrategy import PathStrategy
from LibPeer2.Networks.Receiption import Receiption
from LibPeer2.Networks.PeerInfo import PeerInfo
from LibPeer2.Networks import Network
from LibPeer2.Debug import Log

from io import BytesIO
from cachetools import TTLCache
from typing import Dict
from typing import Tuple
from typing import List
from typing import Set
from typing import Callable
from threading import Timer
from rx.subject import Subject
from threading import Thread

import uuid
import time

"""MuXer 2"""
class MX2:

    PACKET_INQUIRE = b"\x05"
    PACKET_GREET = b"\x06"
    PACKET_PAYLOAD = b"\x16"

    def __init__(self):
        self.__networks: Dict[bytes, Set[Network]] = {}
        self.__instances: Dict[InstanceReference, Instance] = {}
        self.__remote_instance_mapping: Dict[InstanceReference, Tuple[Network, PeerInfo, PathInfo]] = {}
        self.__inquiries = TTLCache(512, 120)
        self.__pings: Dict[InstanceReference, float] = {}


    """Register a network on the MX2 instance, allowing it to use the network to find and talk to instances"""
    def register_network(self, network: Network):
        # Do we have a set for this network type yet?
        if(network.NETWORK_IDENTIFIER not in self.__networks):
            # No, add one
            self.__networks[network.NETWORK_IDENTIFIER] = set()

        # Get the network set
        network_set = self.__networks[network.NETWORK_IDENTIFIER]

        # Do we have this network yet?
        if(network in network_set):
            # Yes, nothing to do
            return

        # Add the network to the set
        network_set.add(network)
        network.incoming_receiption.subscribe(self.__handle_receiption)

    """Create a new instance for use by an application"""
    def create_instance(self, application_namespace):
        # Create the instance
        instance = Instance(application_namespace)

        # Save the instance to the dictionary
        self.__instances[instance.reference] = instance

        # Return the instance
        return instance


    """Given a destination instance. Send inquire packets as instance to every PeerInfo peer in the peers list"""
    def inquire(self, instance: Instance, destination: InstanceReference, peers: List[PeerInfo]):
        # Create an inquiry
        inquiry = Inquiry(destination)
        self.__inquiries[inquiry.id] = inquiry

        if(len(peers) == 0):
            raise Exception("why")

        packets = 0

        # Loop over each peer to try
        for peer in peers:
            # Do we have the network associated with the peer info?
            if(peer.NETWORK_TYPE not in self.__networks):
                Log.debug("Connection method skipped as there are no networks of type '{}' registered".format(peer.NETWORK_TYPE.decode("utf-8")))
                # We don't have this peer's network
                continue

            # Loop over the networks that match the type
            for network in self.__networks[peer.NETWORK_TYPE]:
                # Create a frame containing an inquire packet
                frame = Frame(destination, instance.reference, PathInfo.empty(), BytesIO(MX2.PACKET_INQUIRE + inquiry.id + instance.application_namespace.encode("utf-8")))

                # Send using the network and peer info
                Thread(name="MX2 Inquiry", target=self.__tolerant_inquire, args=(network, frame, peer, instance)).start()
                packets += 1

        Log.debug("Sent inquiry, resulting in {} packet/s".format(packets))
        return inquiry.complete


    # TODO next: Add Inquire via paths:
    # takes a list of an object containing a possible path to an instance and the
    # peer info of the first hop

    def inquire_via_paths(self, instance: Instance, destination: InstanceReference, strategies: List[PathStrategy]):
        # Create an inquiry
        inquiry = Inquiry(destination)
        self.__inquiries[inquiry.id] = inquiry

        packets = 0

        # Loop over each path to try
        for strategy in strategies:
            # Do we have the network associated with the peer info?
            if(strategy.first_hop.NETWORK_TYPE not in self.__networks):
                # We don't have this repeater's network
                continue

            # Loop over the networks that match the type
            for network in self.__networks[strategy.first_hop.NETWORK_TYPE]:
                # Create a frame containing an inquire packet
                frame = Frame(destination, instance.reference, strategy.path, BytesIO(MX2.PACKET_INQUIRE + inquiry.id + instance.application_namespace.encode("utf-8")))

                # Send using the network and peer info
                Thread(name="MX2 Inquiry", target=self.__tolerant_inquire, args=(network, frame, strategy.first_hop, instance)).start()
                packets += 1

        Log.debug("Sent inquiry via path, resulting in {} packet/s".format(packets))
        return inquiry.complete

    """Returns peer info on the specified instance"""
    def get_peer_info(self, instance: InstanceReference) -> PeerInfo:
        return self.__remote_instance_mapping[instance][1]

    """Returns the network that the specified instance is connected via"""
    def get_peer_network(self, instance: InstanceReference) -> Network:
        return self.__remote_instance_mapping[instance][0]


    """Send data to the specified destination"""
    def send(self, instance: Instance, destination: InstanceReference, data):
        # Send payload
        self.__send_packet(instance, destination, BytesIO(MX2.PACKET_PAYLOAD + data))

    """Get a suggested timeout time in seconds for replies from this peer"""
    def suggested_timeout(self, target: InstanceReference):
        # Do we have a ping for the peer?
        if(target in self.__pings):
            return self.__pings[target] * 2.0

        return 120.0


    def __tolerant_inquire(self, network: Network, frame: Frame, peer: PeerInfo, instance: Instance):
        for i in range(24):
            network.send(frame.serialise(instance.signing_key), peer)
            time.sleep(5)
            # Stop inquiring if we have received a reply
            if(frame.destination in self.__remote_instance_mapping):
                return


    def __send_packet(self, instance: Instance, destination: InstanceReference, payload):
        # Do we know how to reach the destination instance?
        if(destination not in self.__remote_instance_mapping):
            # Throw an error
            raise IOError("No known way to reach the specified instance")

        # Get network, peer, and path info
        network, peer_info, path_info = self.__remote_instance_mapping[destination]

        # Create a frame
        frame = Frame(destination, instance.reference, path_info, payload)

        # Send frame over network
        network.send(frame.serialise(instance.signing_key), peer_info)


    def __handle_receiption(self, receiption: Receiption):
        # Read frame within receiption
        try:
            frame, instance = Frame.deserialise(receiption.stream, self.__instances)
        except Exception as e:
            Log.error(str(e))
            return

        # Read packet type
        packet_type = frame.payload.read(1)

        # Determine what to do
        if(packet_type == MX2.PACKET_INQUIRE):
            Log.debug("Received Inquire Packet")
            # First 16 bytes of packet is inquiry id
            inquiry_id = frame.payload.read(16)

            # Rest of packet indicates desired application name
            application_namespace = frame.payload.read().decode("utf-8")

            # Does the application namespace match the instance's?
            if(instance.application_namespace == application_namespace):
                # Yes! Save this instance's information locally for use later
                self.__remote_instance_mapping[frame.origin] = (receiption.network, receiption.peer_info, frame.via.return_path())

                # Reply with a greeting and the inquiry id
                self.__send_packet(instance, frame.origin, BytesIO(MX2.PACKET_GREET + inquiry_id))

        elif(packet_type == MX2.PACKET_GREET):
            Log.debug("Received Greet Packet")
            # We received a greeting!
            # Have we received one from this instance before?
            if(frame.origin not in self.__remote_instance_mapping):
                # No, this is the first (therefore, least latent) method of talking to this instance
                self.__remote_instance_mapping[frame.origin] = (receiption.network, receiption.peer_info, frame.via.return_path())

                # Read inquiry id
                inquiry_id = frame.payload.read(16)

                # Get ping
                ping = 120.0
                if(inquiry_id in self.__inquiries):
                    ping = self.__inquiries[inquiry_id].response_received()

                # Save ping
                self.__pings[frame.origin] = ping

            # Does the instance know that this is now a reachable peer?
            if(frame.origin not in instance.reachable_peers):
                # No, notify it
                instance.reachable_peers.add(frame.origin)
                instance.incoming_greeting.on_next(frame.origin)

        elif(packet_type == MX2.PACKET_PAYLOAD):
            # This is a payload for the next layer to handle, pass it up.
            instance.incoming_payload.on_next(Packet(frame))
                


        



