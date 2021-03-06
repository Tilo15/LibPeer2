from LibPeer2.Networks import Network
from LibPeer2.Networks.Simulation.NetSimPeerInfo import NetSimPeerInfo
from LibPeer2.Networks.Receiption import Receiption
from LibPeer2.Networks.Advertisement import Advertisement
from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference
from LibPeer2.Debug import Log

from io import BytesIO

import threading
import queue
import time
import random
import traceback

class NetSim(Network):

    NETWORK_IDENTIFIER = b"NetSim"

    def __init__(self, conduit, identifier, count, delay = 0.001, latency=0.01, loss_probability=0.0):
        self.conduit = conduit
        self.count = count
        self.identifier = identifier
        self.delay = delay
        self.latency = latency
        self.loss_probability = loss_probability

        self.queue = queue.Queue()
        self.up = False

        super().__init__()

    def bring_up(self):
        self.up = True
        threading.Thread(target=self.__loop).start()

    def bring_down(self):
        self.up = False

    def advertise(self, instance_reference: InstanceReference):
        advetrisement = Advertisement(instance_reference, NetSimPeerInfo(self.identifier))
        self.conduit.advertise(self.identifier, advetrisement)

    def send(self, buffer, peer_info: NetSimPeerInfo):
        data = buffer.read()
        threading.Thread(name="Packet latency timer", target=self.__send, args=(BytesIO(data), peer_info)).start()

    def __send(self, buffer, peer_info: NetSimPeerInfo):
        time.sleep(self.latency)
        self.conduit.send_packet(self.identifier, peer_info.identifier, buffer)

    def _receive_packet(self, origin, buffer):
        peer_info = NetSimPeerInfo(origin)
        receiption = Receiption(buffer, peer_info, self)
        self.queue.put(receiption)

    def __loop(self):
        while(self.up):
            receiption = self.queue.get()
            time.sleep(self.delay)

            ran_num = random.randint(1, 100)
            lost = ran_num <= self.loss_probability * 100

            if(not lost):
                try:
                    self.incoming_receiption.on_next(receiption)
                except Exception as e:
                    print(traceback.format_exc())
                    Log.error("Exception on incoming packet: {}".format(e))

            else:
                Log.info("NetSim dropped a packet ({} <= {})".format(ran_num, self.loss_probability * 100))

