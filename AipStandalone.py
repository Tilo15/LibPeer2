from LibPeer2.Networks import Network
from LibPeer2.Networks.IPv4 import IPv4
from LibPeer2.Protocols.MX2 import MX2
from LibPeer2.Protocols import AIP
from LibPeer2.Protocols.AIP.ApplicationInformation import ApplicationInformation
from LibPeer2.Protocols.AIP.InstanceInformation import InstanceInformation


import sys

class AipStandalone:

    def __init__(self, port = 1999):

        self.muxer = MX2()

        features = set((
            AIP.CAPABILITY_ADDRESS_INFO,
            AIP.CAPABILITY_FIND_PEERS
        ))

        self.aip = AIP.AIP(self.muxer, capabilities = features)

        self.network = IPv4("0.0.0.0", port)
        self.network.bring_up()

        self.aip.add_network(self.network)

        print("Ready")

if __name__ == "__main__":
    if(len(sys.argv) >= 2):
        AipStandalone(int(sys.argv[1]))
    else:
        AipStandalone()
