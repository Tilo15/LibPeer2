from LibPeer2.Networks.Advertisement import Advertisement
from LibPeer2.Networks.Receiption import Receiption
from LibPeer2.Networks.Simulation import Conduit
from LibPeer2.Protocols.MX2 import MX2
from LibPeer2.Protocols.MX2.Packet import Packet
from LibPeer2.Protocols.STP import STP

import struct
import uuid
import os

class GiveFile:

    def __init__(self, conduit, file_path):
        self.muxer = MX2()
        self.network = conduit.get_interface(False, 0.0, 0.001, 0.05)
        self.network.bring_up()
        self.muxer.register_network(self.network)
        self.instance = self.muxer.create_instance("GiveFile")
        self.transport = STP(self.muxer, self.instance)
        self.path = file_path
        self.peers = set()

        self.instance.incoming_greeting.subscribe(self.rx_greeting)
        self.network.incoming_advertisment.subscribe(self.rx_advertisement)
        self.transport.incoming_stream.subscribe(self.incoming)

        self.network.advertise(self.instance.reference)


    def rx_advertisement(self, adv: Advertisement):
        if(adv.instance_reference not in self.peers):
            self.muxer.inquire(self.instance, adv.instance_reference, [adv.peer_info])


    def rx_greeting(self, origin):
        self.peers.add(origin)
        self.transport.initialise_stream(origin).subscribe(self.make_request)

    
    def make_request(self, stream):
        stream.reply.subscribe(self.reply)
        print("Asking peer to gib file...")
        stream.write(b"Gib file")


    def reply(self, stream):
        print("Peer gibs file...")
        # Get file size
        size = struct.unpack("!L", stream.read(4))[0]

        # Save file
        file = open(str(uuid.uuid4()), 'wb')
        file.write(stream.read(size))
        print("Done")


    def incoming(self, stream):
        print("I have a new stream")
        if(stream.read(8) != b"Gib file"):
            print("Peer did not ask me to gib file")
            return
        
        self.transport.initialise_stream(stream.origin, in_reply_to=stream.id).subscribe(self.send_file)


    def send_file(self, stream):
        print("Sending my file")
        stream.write(struct.pack("!L", os.path.getsize(self.path)))
        f = open(self.path, 'rb')
        stream.write(f.read())
        f.close()
        


if __name__ == "__main__":
    
    conduit = Conduit()

    p1 = GiveFile(conduit, "/home/bbarrow/Music/Anders Enger Jensen - The Last Goddess OST/Anders Enger Jensen - The Last Goddess OST - 01 The Last Goddess Theme.flac")
    p2 = GiveFile(conduit, "/home/bbarrow/Music/Snail Mail - Lush/Snail Mail - Lush - 08 Full Control.flac")

    #p1 = GiveFile(conduit, "/home/bbarrow/Pictures/Lame Party Music.png")
    #p2 = GiveFile(conduit, "/home/bbarrow/Pictures/Lame Party Music.jpg")