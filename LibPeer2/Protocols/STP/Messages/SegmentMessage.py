from LibPeer2.Protocols.STP import Messages
from LibPeer2.Protocols.STP.Stream.Segments import Segment
import struct

class SegmentMessage(Messages.Message):

    MESSAGE_TYPE = Messages.MESSAGE_SEGMENT

    def __init__(self, session_id, segment: Segment):
        self.session_id = session_id
        self.segment = segment

    def _build(self, stream):
        # Read the session ID
        session_id = stream.read(16)

        # Return the object
        return SegmentMessage(session_id, Segment.deserialise(stream))

    def _serialise(self, stream):
        # Write the session ID
        stream.write(self.session_id)

        # Write the segment
        self.segment.serialise(stream)


