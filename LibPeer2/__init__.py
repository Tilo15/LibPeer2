from LibPeer2.InstanceManagers.DefaultInstanceManager import DefaultInstanceManager
from LibPeer2.Protocols.STP.Stream.IngressStream import IngressStream
from LibPeer2.Protocols.STP.Stream.EgressStream import EgressStream

def InstanceManager(namespace: str, use_repeaters = True, networks = []):
    return DefaultInstanceManager(namespace, use_repeaters, networks) 