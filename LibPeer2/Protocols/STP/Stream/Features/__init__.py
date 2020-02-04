
class Feature:

    IDENTIFIER = 0

    def wrap(self, stream):
        raise NotImplementedError()

    def unwrap(self, stream):
        raise NotImplementedError()