from LibPeer2.Networks import Network


from typing import List

class RouterConfiguration:

    def __init__(self, networks: List[Network]):
        self.networks = networks

        