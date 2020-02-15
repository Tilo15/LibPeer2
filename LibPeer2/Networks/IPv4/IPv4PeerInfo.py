from LibPeer2.Networks.PeerInfo import PeerInfo

import struct

class IPv4PeerInfo(PeerInfo):

    NETWORK_TYPE = b"IPv4"

    def __init__(self, address, port):
        self.address = address
        self.port = port


    def _serialise(self):
        address_parts = [int(x) for x in self.address.split(".")]
        ip_address = struct.pack("!BBBB", *address_parts)
        port = struct.pack("!H", self.port)

        return ip_address + port
        

    @staticmethod
    def _build(stream):
        ip_address = stream.read(4)
        port = stream.read(2)

        address = ".".join(str(int(x)) for x in ip_address)
        port_no = struct.unpack("!H", port)[0]
        return IPv4PeerInfo(address, port_no)

    def __eq__(self, other):
        # Do the addresses match?
        if(self.address != other.address):
            return False

        # Do the ports match?
        if(self.port != other.port):
            return False

        # They match
        return True

    
    def __hash__(self):
        return hash(self.port, self.address)