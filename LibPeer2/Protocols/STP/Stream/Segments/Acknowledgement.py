from LibPeer2.Protocols.STP.Stream.Segments import Segment

import struct

class Acknowledgement(Segment):

    IDENTIFIER = b"\x06"

    def __init__(self, sequence_number, timing):
        self.sequence_number = sequence_number
        self.timing = timing

    def _serialise(self, stream):
        stream.write(struct.pack("!Qd", self.sequence_number, self.timing))

    @staticmethod
    def _build(stream):
        seq, timing = struct.unpack("!Qd", stream.read(16))
        return Acknowledgement(seq, timing)
