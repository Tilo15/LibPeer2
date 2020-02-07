from LibPeer2.Protocols.STP.Stream.Segments import Segment

import struct
import time

class Payload(Segment):

    IDENTIFIER = b"\x0E"

    def __init__(self, sequence_number, data, timing = None):
        self.sequence_number = sequence_number
        self.data = data
        self.timing = timing

    def _serialise(self, stream):
        self.timing = time.time()
        stream.write(struct.pack("!QdL", self.sequence_number, self.timing, len(self.data)))
        stream.write(self.data)

    @staticmethod
    def _build(stream):
        seq, timing, size = struct.unpack("!QdL", stream.read(20))
        data = stream.read(size)

        if(len(data) != size):
            raise IOError("Data from packet does not match expected size")

        return Payload(seq, data, timing)
