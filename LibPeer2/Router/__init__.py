from LibPeer2.Router.Configuration import RouterConfiguration
from LibPeer2.Router.MX2Router import MX2Router
from LibPeer2.Networks import Network
from LibPeer2.Protocols.AIP import AIP


class BasicRouter:

    def __init__(self, configuration: RouterConfiguration):
        self.frame_router = MX2Router()
        self.configuration = configuration

        for network in self.configuration.networks:
            self.frame_router.register_network(network)

        for network in self.configuration.networks:
            network.bring_up()

        self.aip = AIP(self.frame_router.muxer)

        self.frame_router.local_destinations.add(self.aip.instance_reference)
        self.aip.can_route = True
        self.aip.will_route = self.frame_router.will_route
        
        for network in self.configuration.networks:
            self.aip.add_network(network)
