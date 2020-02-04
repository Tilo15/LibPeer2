
class Segment:

    IDENTIFIER = b""

    def serialise(self, stream):
        stream.write(self.IDENTIFIER)
        self._serialise(stream)

    def _serialise(self, stream):
        raise NotImplementedError()

    @staticmethod
    def _build(self, stream):
        raise NotImplementedError()

    @staticmethod
    def deserialise(stream):
        # Get the type
        type_byte = stream.read(1)
        subclass = next(x for x in Segment.__subclasses__() if x.IDENTIFIER == type_byte)

        return subclass._build(stream)
