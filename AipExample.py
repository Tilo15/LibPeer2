from LibPeer2.Networks import Network
from LibPeer2.Protocols.MX2 import MX2
from LibPeer2.Protocols.AIP import AIP
from LibPeer2.Protocols.AIP.ApplicationInformation import ApplicationInformation
from LibPeer2.Protocols.AIP.InstanceInformation import InstanceInformation
from LibPeer2.Protocols.STP import STP

import time
import struct

class AipExample:

    def __init__(self, network: Network):
        print("init")
        self.network = network
        self.muxer = MX2()
        self.muxer.register_network(network)
        self.discoverer = AIP(self.muxer)
        self.discoverer.add_network(self.network)
        self.discoverer.ready.subscribe(self.aip_ready)
        self.instance = self.muxer.create_instance("AipExample")
        self.info = ApplicationInformation.from_instance(self.instance)
        self.transport = STP(self.muxer, self.instance)
        self.start = time.time()

        self.instance.incoming_greeting.subscribe(self.on_greet)
        self.transport.incoming_stream.subscribe(self.on_stream)

    def aip_ready(self, state):
        print("aip ready")

        self.discoverer.add_application(self.info).subscribe(self.new_aip_peer)

    def new_aip_peer(self, instance):
        print("new aip peer")

        self.discoverer.find_application_instance(self.info).subscribe(self.new_app_peer)

    
    def new_app_peer(self, info: InstanceInformation):
        print("new app peer")

        self.muxer.inquire(self.instance, info.instance_reference, info.connection_methods)

    def on_greet(self, instance):
        print("on greet")

        def on_stream_established(stream):
            print("on stream established")

            stream.write(struct.pack("!H", int(time.time() - self.start)))
            stream.close()


        self.transport.initialise_stream(instance).subscribe(on_stream_established)


    def on_stream(self, stream):
        print("on stream")

        value = struct.unpack("!H", stream.read(2))[0]

        print("I was discovered in {} second(s)".format(value))


from LibPeer2.Networks.Simulation import Conduit
from LibPeer2.Networks.Simulation.NetSim import NetSim
from LibPeer2.Networks.IPv4 import IPv4

import sys

if __name__ == "__main__":

    network = sys.argv[1]
    
    if(network.lower() == "ipv4"):
        net = IPv4("0.0.0.0", 8091)
        net.bring_up()
        AipExample(net)

    else:
        conduit = Conduit(False)

        for i in range(2):
            net = conduit.get_interface(False, 0, 0)
            net.bring_up()
            AipExample(net)