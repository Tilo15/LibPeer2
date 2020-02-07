from io import BytesIO

class EgressStream:

    def __init__(self, send_callback, close_callback):
        self.__send_callback = send_callback
        self.__close_callback = close_callback
        self.closed = False
        
    
    def write(self, data: bytes):
        if(self.closed):
            raise OSError("Stream is closed")

        return self.__send_callback(BytesIO(data))


    def close(self):
        self.closed = True
        self.__close_callback()
