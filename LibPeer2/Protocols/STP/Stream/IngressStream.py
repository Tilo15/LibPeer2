from io import BytesIO
import queue

class IngressStream:

    def __init__(self, incoming_buffer, closed_subject):
        incoming_buffer.subscribe(self.__add_buffer, None, lambda: self.closed = True)
        self.closed = False
        self.__queue = queue.Queue()
        self.__current_buffer: BytesIO = None
        self.__closed_subject = closed_subject


    def __add_buffer(self, buffer):
        self.__queue.put(buffer)

    
    def __next_buffer(self):
        if(self.closed and self.__queue.qsize() == 0):
            raise OSError("Stream is closed")

        self.__current_buffer = self.__queue.get()


    def read(self, size):
        data = b""

        while len(data) != size:
            read_data = self.__current_buffer.read(size - len(data))

            if(len(read_data) == 0):
                self.__next_buffer()
                continue
                
            data += read_data

        return data


    def close(self):
        self.closed = True
        self.__closed_subject.on_next(None)

            