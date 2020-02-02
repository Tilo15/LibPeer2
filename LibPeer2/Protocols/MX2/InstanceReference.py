from nacl import signing
from nacl import public
from io import BytesIO

class InstanceReference:

    SERIALISED_SIZE = 64

    def __init__(self, verification_key: signing.VerifyKey, public_key: public.PublicKey):
        self.verification_key = verification_key
        self.public_key = public_key

    def serialise(self):
        # Create buffer
        buffer = BytesIO()

        # Write verification key
        buffer.write(self.verification_key.encode())

        # Add public key to buffer
        buffer.write(self.public_key.encode())

        # Rewind and return buffer
        buffer.seek(0, 0)
        return buffer

    @staticmethod
    def deserialise(stream):
        # Read verification key
        bytes_vkey = stream.read(32)
        verification_key = signing.VerifyKey(bytes_vkey)
        
        # Read public key
        bytes_pkey = stream.read(32)
        public_key = public.PublicKey(bytes_pkey)

        # Return a new instance
        return Instance(verification_key, public_key)

    def __hash__(self):
        hash((self.verification_key.encode(), self.public_key.encode()))

    def __eq__(self, other):
        return self.verification_key.encode() == other.verification_key.encode() and self.public_key.encode() == other.public_key.encode()