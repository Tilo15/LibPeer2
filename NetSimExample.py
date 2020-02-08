from LibPeer2.Networks.Advertisement import Advertisement
from LibPeer2.Networks.Receiption import Receiption
from LibPeer2.Networks.Simulation import Conduit
from LibPeer2.Protocols.MX2 import MX2
from LibPeer2.Protocols.MX2.Packet import Packet

from io import BytesIO
import time

class ExponentialPinger:

    def __init__(self, conduit: Conduit):
        self.muxer = MX2()
        self.network = conduit.get_interface(True, 0.2, 0.0, 0.5)
        self.network.bring_up()
        self.muxer.register_network(self.network)
        self.instance = self.muxer.create_instance("ExponentialPinger")
        self.peers = set()

        self.instance.incoming_greeting.subscribe(self.rx_greeting)
        self.instance.incoming_payload.subscribe(self.rx_data)
        self.network.incoming_advertisment.subscribe(self.rx_advertisement)

        self.network.advertise(self.instance.reference)

    def rx_advertisement(self, adv: Advertisement):
        if(adv.instance_reference not in self.peers):
            self.muxer.inquire(self.instance, adv.instance_reference, [adv.peer_info])

    def rx_greeting(self, origin):
        self.peers.add(origin)
        self.muxer.send(self.instance, origin, b"Hello World!")

    def rx_data(self, packet: Packet):
        self.peers.add(packet.origin)
        self.network.advertise(self.instance.reference)
        #print("RX DATA, I have {} peers".format(len(self.peers)))
        data = packet.stream.read()
        # Ping out to everyone
        for peer in self.peers:
            self.muxer.send(self.instance, peer, data)


if __name__ == "__main__":
    conduit = Conduit()
    for i in range(10):
        ExponentialPinger(conduit)
