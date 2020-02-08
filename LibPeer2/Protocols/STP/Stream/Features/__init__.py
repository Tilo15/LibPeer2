
class Feature:

    IDENTIFIER = 0

    def wrap(self, data: bytes):
        raise NotImplementedError()

    def unwrap(self, data: bytes):
        raise NotImplementedError()

    @staticmethod
    def get_features(feature_codes):
        features = {x.IDENTIFIER: x for x in Feature.__subclasses__()}
        return [features[x] for x in feature_codes if x in features]