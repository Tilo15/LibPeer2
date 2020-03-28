from LibPeer2.Networks import Network
from LibPeer2.Networks.Receiption import Receiption
from LibPeer2.Networks.Advertisement import Advertisement
from LibPeer2.Networks.IPv4.IPv4PeerInfo import IPv4PeerInfo
from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference

from io import BytesIO
from dns import resolver

import rx
import socket
import struct
import threading
import base64

LIBPEER_DNS_SEEDS = ["libpeer.localresolver", "libpeer.pcthingz.com", "libpeer.unitatem.net", "libpeer.mooo.com"]
DGRAM_DATA = b"\x00"
DGRAM_INQUIRE = b"\x01"
DGRAM_INSTANCE = b"\x02"


class IPv4(Network):

    NETWORK_IDENTIFIER = b"IPv4"

    def __init__(self, address, port):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__mcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.__mcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__address = address
        self.__port = port
        self.__advertised_instances = set()
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
        threading.Thread(name="LibPeer IPv4 DNS Discovery", target=self.__discover_dns_seeds).start()


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

        # Save the advertised instance
        self.__advertised_instances.add(instance_reference)


    def send(self, buffer, peer_info):
        # Send the data
        self.__socket.sendto(DGRAM_DATA + buffer.read(), (peer_info.address, peer_info.port))


    def __listen(self):
        while True:
            try:
                # Receive the next datagram
                datagram, sender = self.__socket.recvfrom(65536)

                # Put the datagram into a buffer
                buffer = BytesIO(datagram[1:])

                # Create peer info
                info = IPv4PeerInfo(sender[0], sender[1])

                # Read the datagram type
                dgram_type = datagram[:1]

                # Regular data packet
                if(dgram_type == DGRAM_DATA):                    
                    # Create a new receiption
                    receiption = Receiption(buffer, info, self)

                    # Pass up
                    self.incoming_receiption.on_next(receiption)

                elif(dgram_type == DGRAM_INQUIRE):
                    # Respond with instance information
                    for instance in self.__advertised_instances:
                        # Send the instance information as a single datagram
                        self.__socket.sendto(DGRAM_INSTANCE + instance.serialise().read(), sender)

                elif(dgram_type == DGRAM_INSTANCE):
                    # Create the instance reference
                    instance_reference = InstanceReference.deserialise(buffer)

                    # Is the instance one we advertise?
                    if(instance_reference in self.__advertised_instances):
                        # Yes, skip
                        continue

                    # Create the advertisement
                    advertisement = Advertisement(instance_reference, info)

                    # Send to the application
                    self.incoming_advertisment.on_next(advertisement)

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

            # Is the instance one we advertise?
            if(instance_reference in self.__advertised_instances):
                # Yes, skip
                continue

            # Create the advertisement
            advertisement = Advertisement(instance_reference, info)

            # Send to the application
            self.incoming_advertisment.on_next(advertisement)

    
    def __discover_dns_seeds(self):
        # Loop over each DNS seed
        for seed in LIBPEER_DNS_SEEDS:
            # Try and query
            try:
                # Query for TXT records
                answers = resolver.query(seed, "TXT")

                # Loop over answers
                for answer in answers:
                    # Loop over strings
                    for string in answer.strings:
                        # Split on '/' delimiter
                        data = string.split(b'/')

                        # Is it a LibPeer2 entry?
                        if(not data[0].startswith(b"P2")):
                            # No, skip
                            continue

                        if(data[0] == b"P2M"):
                            # Seed message
                            print("DNS Seed: {}".format(data[1].decode('utf-8')))

                        elif(data[0] == b"P2D" or data[0] == b"P2A"):
                            # Domain pointer or IP Address
                            self.__handle_dns_discovery(data[1], data[2])
            
            except:
                pass

        print("DNS Seed Search Complete")


    def __handle_dns_discovery(self, host, port):

        try:
            # Resolve the host
            resolved = socket.gethostbyname(host)

            # Inquire about the peer
            self.__socket.sendto(DGRAM_INQUIRE, (resolved, int(port)))
        except:
            pass

        


