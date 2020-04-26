from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference
from LibPeer2.Protocols.MX2.Instance import Instance
from nacl.public import SealedBox
from nacl.public import PrivateKey
from nacl.signing import SigningKey
from io import BytesIO
from typing import Dict

class Frame:

    MAGIC_NUMBER = b"MX2"

    def __init__(self, destination: InstanceReference, origin: InstanceReference, payload):
        # Save all properties
        self.destination = destination
        self.origin = origin
        self.payload = payload

    def serialise(self, signing_key: SigningKey):
        # Create buffer
        buffer = BytesIO()

        # Write magic number
        buffer.write(Frame.MAGIC_NUMBER)

        # Write the destination key
        buffer.write(self.destination.serialise().read())

        # Write the origin key
        buffer.write(self.origin.serialise().read())

        # Sign the payload
        signed = signing_key.sign(self.payload.read())

        # Create a box to send the signed data in
        box = SealedBox(self.destination.public_key)

        # Encrypt and write the data to the buffer
        buffer.write(box.encrypt(signed))

        # Rewind the buffer
        buffer.seek(0, 0)

        # Return the buffer
        return buffer


    @staticmethod
    def deserialise(stream, instances: Dict[InstanceReference, Instance]):
        # Does the stream start with the magic number?
        number = stream.read(len(Frame.MAGIC_NUMBER))
        if(number != Frame.MAGIC_NUMBER):
            # Raise an error
            raise IOError("Stream did not start with frame magic number.")

        # Read the destination
        destination = InstanceReference.deserialise(stream)

        # Read the origin
        origin = InstanceReference.deserialise(stream)

        # Do we have an instance matching the destination of this packet?
        if(destination not in instances):
            # Raise an error
            raise IOError("Received frame does not belong to any current instances")

        # The remainder of the stream is the encrypted payload
        encrypted = stream.read()

        # Create a sealed box for decryption
        box = SealedBox(instances[destination].private_key)

        # Decrypt the message
        signed = box.decrypt(encrypted)

        # Read the payload into a buffer
        payload = BytesIO(origin.verification_key.verify(signed))

        # Create the object
        return Frame(destination, origin, payload), instances[destination]







    
