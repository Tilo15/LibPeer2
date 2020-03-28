from LibPeer2.Networks import Network
from LibPeer2.Networks.Receiption import Receiption
from LibPeer2.Router.Route import Route
from LibPeer2.Protocols.MX2 import MX2
from LibPeer2.Protocols.MX2 import InstanceReference
from LibPeer2.Protocols.MX2.Frame import Frame

from typing import Dict
from typing import Set
from typing import Callable

import sys


class MX2Router:

    def __init__(self):
        self.routes: Dict[InstanceReference, Route] = {}
        self.will_route: Callable[[InstanceReference, InstanceReference], bool] = self.__will_route
        self.local_destinations: Set[InstanceReference] = set()
        self.muxer = MX2()
        self.muxer._interceptor = self.__handle_receiption

    def register_network(self, network: Network):
        self.muxer.register_network(network)

    
    def add_route(self, route: Route):
        print("Route to {} added".format(str(route.instance).split('"')[1][:6]))
        self.routes[route.instance] = route


    def __will_route(self, origin, destination, message = True):
        if(message):
            print("Will route query: {}\t->\t{}".format(str(origin).split('"')[1][:6], str(destination).split('"')[1][:6]))
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
            #print("{}\t->\tROUTER\t\t\t(delivered)".format(str(InstanceReference.deserialise(receiption.stream)).split('"')[1][:6]))
            receiption.stream.seek(0, 0)
            return receiption

        # Read the origin
        origin = InstanceReference.deserialise(receiption.stream)

        # Is the destination a known route?
        if(destination not in self.routes):
            sys.stdout.write("{}\t->\tROUTER\t->\t{}\t".format(str(origin).split('"')[1][:6], str(destination).split('"')[1][:6]))
            print("(no route)")
            # No, drop
            return None

        # Will we route this?
        if(not self.will_route(origin, destination, False)):
            sys.stdout.write("{}\t->\tROUTER\t->\t{}\t".format(str(origin).split('"')[1][:6], str(destination).split('"')[1][:6]))
            print("(refused)")
            # No, drop
            return None

        # Do we have the origin saved as a route?
        if(origin not in self.routes):
            # No, add it
            self.routes[origin] = Route(origin, receiption.peer_info, receiption.network)

        # Get the route to the destination
        route = self.routes[destination]

        #sys.stdout.write("{}\t->\tROUTER\t->\t{}\t".format(str(origin).split('"')[1][:6], str(destination).split('"')[1][:6]))
        #print("(forwarded)")

        # TODO XXX we should not assume this is a seekable stream
        receiption.stream.seek(0, 0)
        route.network.send(receiption.stream, route.peer)

        # Muxer should ignore this frame
        return None



    
