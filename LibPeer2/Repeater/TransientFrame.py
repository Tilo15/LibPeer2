from LibPeer2.Protocols.MX2 import Frame
from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference
from LibPeer2.Protocols.MX2.PathInfo import PathInfo
from io import BytesIO

class TransientFrame:
    
    def __init__(self, raw_frame: bytes):
        self.__raw_frame = raw_frame

        # Read stream copy to get information
        stream = self.to_stream()

        # Check magic number
        if(stream.read(len(Frame.MAGIC_NUMBER)) != Frame.MAGIC_NUMBER):
            raise Exception("Provided raw frame does not start with magic number")

        # Get frame destination
        self.target = InstanceReference.deserialise(stream)

        # Get frame origin
        self.origin = InstanceReference.deserialise(stream)

        # Get path info
        self.via = PathInfo.deserialise(stream)


    def to_stream(self):
        return BytesIO(self.__raw_frame)


    def next_hop(self, after: InstanceReference):
        # Get index of current potision in path
        position = self.via.repeaters.index(after)

        # Is there a next element?
        if(len(self.via.repeaters) <= position + 1):
            # No, next hop is destination
            return self.target

        # Return it
        return self.via.repeaters[position + 1]


    def has_next_hop(self, after: InstanceReference):
        return (self.origin == after) or (after in self.via.repeaters)

    
    def previous_hop(self, before: InstanceReference):
        # Is the current hop the destination?
        if(before == self.target):
            # Did this come through any repeaters?
            if(len(self.via.repeaters) > 0):
                # Return the last repeater
                return self.via.repeaters[-1]

            # No, return the source
            return self.origin

        # Get index of current potision in path
        position = self.via.repeaters.index(before)

        # Is there a previous element?
        if(lposition - 1 < 0):
            # No, next hop is source
            return self.target

        # Return it
        return self.via.repeaters[position - 1]