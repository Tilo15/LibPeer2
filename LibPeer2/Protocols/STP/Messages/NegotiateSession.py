from LibPeer2.Protocols.STP import Messages
import struct
import time

class NegotiateSession(Messages.Message):

    MESSAGE_TYPE = Messages.MESSAGE_NEGOTIATE_SESSION

    def __init__(self, session_id, feature_codes, reply_timing, timing = None):
        self.session_id = session_id
        self.feature_codes = feature_codes
        self.reply_timing = reply_timing
        self.timing = timing


    def _build(stream):
        # Read the session ID
        session_id = stream.read(16)

        # Read feature count
        feature_count = struct.unpack("!B", stream.read(1))[0]

        # Read features
        feature_codes = list(stream.read(feature_count))

        # Read timing values
        reply_timing, timing = struct.unpack("!dd", stream.read(16))

        # Return the object
        return NegotiateSession(session_id, feature_codes, reply_timing, timing)

    def _serialise(self, stream):
        # Write the session ID
        stream.write(self.session_id)

        # Write the feature count
        stream.write(struct.pack("!B", len(self.feature_codes)))

        # Write the feature codes
        stream.write(bytes(self.feature_codes))

        # Write the timing values
        stream.write(struct.pack("!dd", self.reply_timing, time.time()))
