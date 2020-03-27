from LibPeer2.Router.Configuration import RouterConfiguration
from LibPeer2.Router.MX2Router import MX2Router
from LibPeer2.Router.Route import Route
from LibPeer2.Networks import Network
from LibPeer2.Protocols.AIP import AIP
from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference


class BasicRouter:

    def __init__(self, configuration: RouterConfiguration):
        self.frame_router = MX2Router()
        self.configuration = configuration

        for network in self.configuration.networks:
            self.frame_router.register_network(network)

        for network in self.configuration.networks:
            network.bring_up()

        self.aip = AIP(self.frame_router.muxer)
        self.aip._aip_instance_touch.subscribe(self.__new_aip)
        self.aip._aip_instance_association.subscribe(self.__new_association)

        self.frame_router.local_destinations.add(self.aip.instance_reference)
        self.aip.can_route = True
        self.aip.will_route = self.frame_router.will_route
        
        for network in self.configuration.networks:
            self.aip.add_network(network)


    def __new_aip(self, instance: InstanceReference):
        info = self.frame_router.muxer.get_peer_info(instance)
        network = self.frame_router.muxer.get_peer_network(instance)
        route = Route(instance, info, network)
        self.frame_router.add_route(route)


    def __new_association(self, instances):
        original = self.frame_router.routes[instances[0]]
        route = Route(instances[1], original.peer, original.network)
        self.frame_router.add_route(route)
