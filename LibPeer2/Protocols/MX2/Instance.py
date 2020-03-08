from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference
from nacl.public import PrivateKey
from nacl.signing import SigningKey

from typing import Set

import rx

class Instance:

    def __init__(self, application_namespace):
        # Save the application namespace
        self.application_namespace = application_namespace

        # Generate a private key
        self.private_key = PrivateKey.generate()

        # Generate a signing key
        self.signing_key = SigningKey.generate()

        # Create subject for incoming payloads
        self.incoming_payload = rx.subjects.Subject()

        # Create a set of reachable instances
        self.reachable_peers: Set[InstanceReference] = set()

        # Create subject for newly reachable instances
        self.incoming_greeting = rx.subjects.Subject()
    
    @property
    def reference(self) -> InstanceReference:
        return InstanceReference(self.signing_key.verify_key, self.private_key.public_key)

