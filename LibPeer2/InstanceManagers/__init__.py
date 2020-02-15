from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference

from typing import Set

import rx

class InstanceManager:
    
    def __init__(self, application_namespace: str):
        self.namespace = application_namespace
        self.new_peer = rx.subjects.Subject()
        self.new_stream = rx.subjects.Subject()

    def establish_stream(self, peer: InstanceReference, *, in_reply_to = None) -> rx.subjects.Subject:
        raise NotImplementedError()

    def find_resource_peers(self, resource: bytes) -> rx.subjects.Subject:
        raise NotImplementedError()

    @property
    def resources(self) -> Set[bytes]:
        raise NotImplementedError()

