from LibPeer2.Networks import Network
from LibPeer2.Networks.PeerInfo import PeerInfo
from LibPeer2.Networks.Receiption import Receiption
from LibPeer2.Protocols.MX2 import MX2
from LibPeer2.Protocols.RPP import RPP
from LibPeer2.Protocols.AIP import AIP
from LibPeer2.Protocols.MX2.Instance import InstanceReference
from LibPeer2.Repeater.TransientFrame import TransientFrame


from typing import Tuple
from typing import Dict

class FrameRepeater(MX2):

    def __init__(self):
        # Call base constructor
        super().__init__()

        # Keep track of added networks
        self.__networks = set()

        # Store information about where we have received messages from instance references from
        self.__node_info: Dict[InstanceReference, Tuple[Network, PeerInfo]] = {}

        # Create discoverer
        self.__discoverer = AIP(self, join_all=True)

        # Create RPP instance
        self.__relay_path_protocol = RPP(self, self.__discoverer, True)


    # Override
    def register_network(self, network: Network):
        # Have we added this network before?
        if(network in self.__networks):
            # Yes, skip
            return

        # Add to set
        self.__networks.add(network)

        # Call base add
        super().register_network(network)

        # Add to discoverer
        self.__discoverer.add_network(network)


    # Override
    def _MX2__handle_receiption(self, receiption: Receiption):
        # Read as transient frame
        frame = TransientFrame(receiption.stream.read())

        # Is there a next hop?
        if(frame.has_next_hop(self.__relay_path_protocol.instance_reference)):
            # Yes, save node info 
            self.__node_info[frame.previous_hop(self.__relay_path_protocol.instance_reference)] = (receiption.network, receiption.peer_info)
            
            # find next instance to pass on to
            next_instance = frame.next_hop(self.__relay_path_protocol.instance_reference)

            # Get network and peer info of instance
            network = self.__relay_path_protocol.instance_network[next_instance]
            info = self.__relay_path_protocol.instance_info[next_instance]


            # TODO Remove Print
            #print("{}\t->\t{}\t->\t{}".format(self.__short_name(frame.previous_hop(self.__relay_path_protocol.instance_reference)), self.__short_name(self.__relay_path_protocol.instance_reference), self.__short_name(frame.next_hop(self.__relay_path_protocol.instance_reference))))

            # Send
            network.send(frame.to_stream(), info)

        else:
            # No, save node info (differently)
            self.__node_info[frame.previous_hop(frame.target)] = (receiption.network, receiption.peer_info)

            # TODO Remove Print
            #print("{} (ORIGIN)\t->\t{}".format(self.__short_name(frame.origin), self.__short_name(frame.target)))

            # Create new receiption and allow the base to handle
            new_receiption = Receiption(frame.to_stream(), receiption.peer_info, receiption.network)
            super()._MX2__handle_receiption(new_receiption)

    
    def __short_name(self, instance: InstanceReference):
        return repr(instance).split('"')[1][:6]
