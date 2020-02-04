from LibPeer2.Protocols.STP.Stream.Segments import Segment

import struct

class Payload(Segment):

    IDENTIFIER = b"\x0E"

    def __init__(self, sequence_number, timing, data):
        self.sequence_number = sequence_number
        self.timing = timing
        self.data = data

    def _serialise(self, stream):
        stream.write(struct.pack("!QdL", self.sequence_number, self.timing, len(self.data)))
        stream.write(self.data)

    @staticmethod
    def _build(stream):
        seq, timing, size = struct.unpack("!QdL", stream.read(20))
        data = stream.read(size)

        if(len(data) != size):
            raise IOError("Data from packet does not match expected size")

        return Payload(seq, timing, data)
