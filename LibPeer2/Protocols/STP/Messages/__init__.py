from io import BytesIO

MESSAGE_REQUEST_SESSION = b"\x05"
MESSAGE_NEGOTIATE_SESSION = b"\x01"
MESSAGE_BEGIN_SESSION = b"\x06"
MESSAGE_SEGMENT = b"\x02"
MESSAGE_CLEANUP = b"\x1B"

class Message:

    MESSAGE_TYPE = b""

    def serialise(self):
        stream = BytesIO(b"")
        stream.write(self.MESSAGE_TYPE)
        self._serialise(stream)
        stream.seek(0, 0)
        return stream
         

    def _serialise(self, stream):
        raise NotImplementedError()

    @staticmethod
    def _build(self, stream):
        raise NotImplementedError()

    @staticmethod
    def deserialise(stream):
        # Get the type
        type_byte = stream.read(1)
        subclass = next(x for x in Message.__subclasses__() if x.MESSAGE_TYPE == type_byte)

        return subclass._build(stream)
