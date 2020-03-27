from LibPeer2.Networks import Network
from LibPeer2.Networks.Receiption import Receiption
from LibPeer2.Router.Route import Route
from LibPeer2.Protocols.MX2 import MX2
from LibPeer2.Protocols.MX2 import InstanceReference
from LibPeer2.Protocols.MX2.Frame import Frame

from typing import Dict
from typing import Set
from typing import Callable


class MX2Router:

    def __init__(self):
        self.routes: Dict[InstanceReference, Route] = {}
        self.will_route: Callable[[InstanceReference, InstanceReference], bool] = lambda x, y: True
        self.local_destinations: Set[InstanceReference] = set()
        self.muxer = MX2()
        self.muxer._interceptor = self.__handle_receiption

    def register_network(self, network: Network):
        self.muxer.register_network(network)

    
    def add_route(self, route: Route):
        self.routes[route.instance] = route


    def __will_route(self, origin, destination):
        print(origin, destination)
        return destination in self.routes


    def __handle_receiption(self, receiption: Receiption):
        # Is this a MX2 frame?
        if(receiption.stream.read(len(Frame.MAGIC_NUMBER)) != Frame.MAGIC_NUMBER):
            # No, drop
            return None

        # Read the destination
        destination = InstanceReference.deserialise(receiption.stream)

        # Is this a local destination?
        if(destination in self.local_destinations):
            # Yes, let the muxer handle it
            # TODO XXX we should not assume this is a seekable stream
            receiption.stream.seek(0, 0)
            return receiption
            
        # Is the destination a known route?
        if(destination not in self.routes):
            # No, drop
            return None

        # Read the origin
        origin = InstanceReference.deserialise(receiption.stream)

        # Will we route this?
        if(not self.will_route(origin, destination)):
            # No, drop
            return None

        # Do we have the origin saved as a route?
        if(origin not in self.routes):
            # No, add it
            self.routes[origin] = Route(origin, receiption.peer_info, receiption.network)

        # Get the route to the destination
        route = self.routes[destination]

        # TODO XXX we should not assume this is a seekable stream
        receiption.stream.seek(0, 0)
        route.network.send(receiption.stream, route.peer)

        # Muxer should ignore this frame
        return None



    
