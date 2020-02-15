from io import BytesIO
import queue


class IngressStream:

    def __init__(self, identifier, origin, incoming_buffer, closed_subject):
        self.id = identifier
        self.origin = origin
        incoming_buffer.subscribe(self.__add_buffer, None, lambda: self.__close_stream)
        self.closed = False
        self.__queue = queue.Queue()
        self.__current_buffer: BytesIO = None
        self.__closed_subject = closed_subject


    def __close_stream(self):
        self.closed = True


    def __add_buffer(self, buffer):
        self.__queue.put(buffer)

    
    def __next_buffer(self):
        if(self.closed and self.__queue.qsize() == 0):
            raise OSError("Stream is closed")

        self.__current_buffer = self.__queue.get()


    def __get_buffer(self):
        if(self.__current_buffer == None):
            self.__next_buffer()

        return self.__current_buffer


    def read(self, size):
        data = b""

        while len(data) != size:
            read_data = self.__get_buffer().read(size - len(data))

            if(len(read_data) == 0):
                self.__next_buffer()
                continue
                
            data += read_data

        return data


    def close(self):
        self.closed = True
        self.__closed_subject.on_completed()


            