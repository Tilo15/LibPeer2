from LibPeer2.Networks import Network
from LibPeer2.Networks.Receiption import Receiption
from LibPeer2.Networks.Advertisement import Advertisement
from LibPeer2.Networks.IPv4.IPv4PeerInfo import IPv4PeerInfo
from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference

from io import BytesIO

import rx
import socket
import struct
import threading


class IPv4(Network):

    NETWORK_IDENTIFIER = b"IPv4"

    def __init__(self, address, port):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__mcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.__mcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__address = address
        self.__port = port
        super().__init__()


    def bring_up(self):
        # Bind the main socket
        self.__socket.bind((self.__address, self.__port))

        # Setup the multicast socket
        self.__mcast_socket.bind(("224.0.0.3", 1199))
        mreq = struct.pack("=4sl", socket.inet_aton("224.0.0.3"), socket.INADDR_ANY)
        self.__mcast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        threading.Thread(name="LibPeer IPv4 Listener", target=self.__listen).start()
        threading.Thread(name="LibPeer IPv4 Local Discovery", target=self.__mcast_listen).start()




    def bring_down(self):
        raise NotImplementedError


    def advertise(self, instance_reference: InstanceReference):
        # Prepare a message
        message = b"LibPeer2-IPv4:"

        # Write our port number
        message += struct.pack("!H", self.__port)

        # Write the instance reference
        message += instance_reference.serialise().read()

        # Send the message
        self.__mcast_socket.sendto(message, ("224.0.0.3", 1199))


    def send(self, buffer, peer_info):
        # Send the data
        self.__socket.sendto(buffer.read(), (peer_info.address, peer_info.port))


    def __listen(self):
        while True:
            try:
                # Receive the next datagram
                datagram, sender = self.__socket.recvfrom(65536)

                # Create peer info
                info = IPv4PeerInfo(sender[0], sender[1])
                
                # Create a new receiption
                receiption = Receiption(BytesIO(datagram), info, self)

                # Pass up
                self.incoming_receiption.on_next(receiption)

            except Exception as e:
                print("Exception on incoming packet: {}".format(e))


    def __mcast_listen(self):
        while True:
            # Receive the next discovery datagram
            datagram, sender = self.__mcast_socket.recvfrom(InstanceReference.SERIALISED_SIZE + 16)

            if(datagram[:14] != b"LibPeer2-IPv4:"):
                continue

            # Get advertised port number
            port = struct.unpack("!H", datagram[14:16])[0]

            # Create peer info
            info = IPv4PeerInfo(sender[0], port)

            # Create the instance reference
            instance_reference = InstanceReference.deserialise(BytesIO(datagram[16:]))

            # Create the advertisement
            advertisement = Advertisement(instance_reference, info)

            # Send to the application
            self.incoming_advertisment.on_next(advertisement)

