from LibPeer2.Protocols.STP import Messages

import struct
import time

class RequestSession(Messages.Message):

    MESSAGE_TYPE = Messages.MESSAGE_REQUEST_SESSION

    def __init__(self, session_id, in_reply_to, feature_codes, timing = None):
        self.session_id = session_id
        self.in_reply_to = in_reply_to
        self.feature_codes = feature_codes
        self.timing = timing


    def _build(stream):
        # Read the session ID
        session_id = stream.read(16)

        # Read the in-reply-to field
        in_reply_to = stream.read(16)

        # Read feature count
        feature_count = struct.unpack("!B", stream.read(1))[0]

        # Read features
        feature_codes = list(stream.read(feature_count))

        # Read timing
        timing = struct.unpack("!d", stream.read(8))[0]

        # Return the object
        return RequestSession(session_id, in_reply_to, feature_codes, timing)

    def _serialise(self, stream):
        # Write the session ID
        stream.write(self.session_id)

        # Write the in-reply-to field
        stream.write(self.in_reply_to)

        # Write the feature count
        stream.write(struct.pack("!B", len(self.feature_codes)))

        # Write the feature codes
        stream.write(bytes(self.feature_codes))

        # Write the timing value
        stream.write(struct.pack("!d", time.time()))