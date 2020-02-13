from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference

from typing import Set

class QueryGroup:

    def __init__(self, target = 15):
        # Keep a set of instances
        self.instances: Set[InstanceReference] = set()
        self.target = target

    def add_peer(self, instances: InstanceReference):
        self.instances.add(instance)

    @property
    def actively_connect(self):
        return len(self.instances) < self.target