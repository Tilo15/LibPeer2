from LibPeer2.InstanceManagers.DefaultInstanceManager import DefaultInstanceManager

def InstanceManager(namespace: str, networks = []):
    return DefaultInstanceManager(namespace, networks=networks)