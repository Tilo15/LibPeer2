from io import BytesIO

class EgressStream:

    def __init__(self, data_subject):
        self.__data_subject = data_subject
        self.closed = False
        
    
    def write(self, data: bytes):
        if(self.closed):
            raise OSError("Stream is closed")

        self.__data_subject.on_next(BytesIO(data))


    def close(self):
        self.__data_subject.on_complete()
