from LibPeer2.Protocols.STP import Messages
import struct

class BeginSession(Messages.Message):

    MESSAGE_TYPE = Messages.MESSAGE_BEGIN_SESSION

    def __init__(self, session_id, reply_timing):
        self.session_id = session_id
        self.reply_timing = reply_timing

    def _build(self, stream):
        # Read the session ID
        session_id = stream.read(16)

        # Read reply timing
        reply_timing = struct.unpack("!d", stream.read(8))[0]

        # Return the object
        return BeginSession(session_id, feature_codes)

    def _serialise(self, stream):
        # Write the session ID
        stream.write(self.session_id)

        # Write the reply timing
        stream.write(struct.pack("!d", self.reply_timing)


