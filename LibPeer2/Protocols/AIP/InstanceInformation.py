from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference
from LibPeer2.Networks.PeerInfo import PeerInfo

from typing import List
from io import BytesIO

import struct

class InstanceInformation:

    def __init__(self, instance_reference: InstanceReference, connection_methods: List[PeerInfo], aip_instance: InstanceReference):
        self.instance_reference = instance_reference
        self.connection_methods = connection_methods
        self.aip_instance = aip_instance

    def serialise(self):
        # Create a buffer
        buffer = BytesIO(b"")

        # Write instance reference
        buffer.write(self.instance_reference.serialise().read())

        # Write number of connection methods
        buffer.write(struct.pack("!B", len(self.connection_methods)))

        # Write connection methods
        for method in self.connection_methods:
            buffer.write(method.serialise())

        # Return the serialised bytes
        buffer.seek(0, 0)
        return buffer.read()

    
    @staticmethod
    def deserialise(data):
        buffer = BytesIO(data)

        # Read the instance reference
        instance_reference = InstanceReference.deserialise(buffer)

        # Read the AIP instance reference
        aip_reference = InstanceReference.deserialise(buffer)

        # Read number of connection methods
        method_count = struct.unpack("!B", buffer.read(1))[0]

        # Read connection methods
        methods = []
        for i in range(method_count):
            methods.append(PeerInfo.deserialise(buffer))

        # Return new InstanceInformation object
        return InstanceInformation(instance_reference, methods, aip_instance)
