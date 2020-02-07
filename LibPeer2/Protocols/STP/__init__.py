from LibPeer2.Protocols.MX2 import MX2
from LibPeer2.Protocols.MX2.Instance import Instance
from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference

from cachetools import TTLCache

"""Stream Transmission Protocol"""
class STP:
    
    def __init__(self, muxer: MX2, instance: Instance):
        self.__muxer = muxer
        self.__instance = instance

        self.__open_streams = {}
        self.__pending_streams = TTLCache(65536, 120)

    
