from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference
from typing import List

import rx

class StreamNegotiation:

    STATE_REQUESTED = 0
    STATE_NEGOTIATED = 1
    STATE_ACCEPTED = 2

    def __init__(self, identifer: bytes, in_reply_to: bytes, feature_codes: List[int], state, instance_reference: InstanceReference, ingress):
        self.session_id = identifer
        self.in_reply_to = in_reply_to
        self.feature_codes = feature_codes
        self.state = state
        self.remote_instance = instance_reference
        self.ping = 120
        self.ingress = ingress
        self.notify = rx.subject.Subject()