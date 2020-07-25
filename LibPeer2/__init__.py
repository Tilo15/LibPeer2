from LibPeer2.InstanceManagers.DefaultInstanceManager import DefaultInstanceManager

def InstanceManager(namespace: str, use_repeaters = True, networks = []):
    return DefaultInstanceManager(namespace, use_repeaters, networks) 