
class Feature:

    IDENTIFIER = 0

    def wrap(self, data: bytes):
        raise NotImplementedError()

    def unwrap(self, data: bytes):
        raise NotImplementedError()