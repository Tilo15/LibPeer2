from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference

from typing import Set

import rx

class ApplicationInformation:

    def __init__(self, instance: InstanceReference, namespace: str, resources: Set[bytes]):
        self.instance = instance
        self.namespace = namespace
        self.resources = resources

        self.discovery = rx.subjects.Subject()

    @property
    def namespace_bytes(self):
        return self.namespace.encode("utf-8")