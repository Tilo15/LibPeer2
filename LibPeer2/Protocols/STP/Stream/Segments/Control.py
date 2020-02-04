from LibPeer2.Protocols.STP.Stream.Segments import Segment

import struct

class Control(Segment):

    IDENTIFIER = b"\x10"

    CMD_COMPLETE = b"\x04"
    CMD_ABORT = b"\x18"
    CMD_NOT_CONFIGURED = b"\x15"

    def __init__(self, command):
        self.command = command

    def _serialise(self, stream):
        stream.write(self.command)

    @staticmethod
    def _build(stream):
        command = stream.read(1)
        return Control(command)
