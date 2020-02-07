from LibPeer2.Protocols.STP.Stream.Features import Feature
from LibPeer2.Protocols.STP.Stream.EgressStream import EgressStream
from LibPeer2.Protocols.STP.Stream.IngressStream import IngressStream
from LibPeer2.Protocols.STP.Stream.Segments import Segment
from LibPeer2.Protocols.STP.Stream.Segments.Payload import Payload
from LibPeer2.Protocols.STP.Stream.Segments.Acknowledgement import Acknowledgement
from LibPeer2.Protocols.STP.Stream.Segments.Control import Control
from LibPeer2.Protocols.STP.Stream.SegmentTracker import SegmentTracker

from threading import Lock
from io import BytesIO
from typing import List
import rx
import time
import queue
import math


SEGMENT_PAYLOAD_SIZE = 2048
METRIC_WINDOW_SIZE = 2

class Session:

    def __init__(self, features, identifier: bytes, ping: float, reference: bytes = b"\x00"*16, ingress = False):
        # Instansiate class members
        self.ingress = ingress
        self.features: List[Feature] = [x() for x in features]
        self.identifier = identifier
        self.reference = reference
        self.open = True

        self.outgoing_segment_queue = queue.Queue()

        self.best_ping = ping
        self.window_size = METRIC_WINDOW_SIZE
        self.adjustment_delta = 0

        self.segment_number = 0
        self.segment_lock = Lock()
        self.segment_queue = queue.Queue()
        self.in_flight = {}
        self.segment_trips = set()
        self.segment_subjects = {}
        
        self.reconstruction = {}
        self.next_expected_sequence_number = 0
        self.incoming_app_data = rx.subjects.Subject()

        if(ingress):
            close_subject = rx.subjects.Subject()
            close_subject.subscribe(None, None, self.__handle_app_close)
            self.stream = IngressStream(self.incoming_app_data, close_subject)
        else:
            self.stream = EgressStream(self.__handle_app_data, self.__handle_app_close)


    def has_pending_segment(self):
        # Do we need to queue some stuff?
        self.__enqueue_segments()

        # Do we have stuff queued?
        return self.outgoing_segment_queue.qsize() > 0


    def get_pending_segment(self, stream):
        segment: Segment = self.outgoing_segment_queue.get_nowait()
        segment.serialise(stream)


    def process_segment(self, stream):
        # We have received a segment from the muxer
        segment = Segment.deserialise(stream)

        # Figure out the segment type
        if(isinstance(segment, Acknowledgement)):
            # We have an acknowledgement segment, remove payload segment from in-flight
            del self.in_flight[segment.sequence_number]

            # What was the time difference?
            round_trip = time.time() - segment.timing

            # Are we currently at metric window size?
            if(self.window_size == METRIC_WINDOW_SIZE):
                # Add round trip time to the set
                self.segment_trips.add(round_trip)

                # Do we have a sample?
                if(len(self.segment_trips) >= METRIC_WINDOW_SIZE):
                    # Update the ping based on the average of the metric segments
                    self.best_ping = round(sum(self.segment_trips) / len(self.segment_trips))
                    
                    # Update the window size now we have our baseline
                    self.__adjust_window_size(round_trip)

            else:
                # No, adjust the window size normally
                self.__adjust_window_size(round_trip)

        elif(isinstance(segment, Payload)):
            # We have a payload segment, run it through the enabled features
            for i in range(len(self.features), 0, -1):
                segment.data = self.features[i - 1].unwrap(segment.data)

            # Is this the next expected segment?
            if(self.next_expected_sequence_number == segment.sequence_number):
                # Is there anything on the reconstruction dictionary?
                if(len(self.reconstruction) > 0):
                    # Add to reconstruction dict
                    self.reconstruction[segment.sequence_number] = segment

                    # Reconstruct and send to application
                    self.incoming_app_data.on_next(self.__complete_reconstruction())

                else:
                    # Just send to the app
                    self.incoming_app_data.on_next(BytesIO(segment.data))

            elif(self.next_expected_sequence_number < segment.sequence_number):
                # We obviously missed a segment, get this one ready for reconstruction
                self.reconstruction[segment.sequence_number] = segment

            # Acknowledge the segment
            acknowledgement = Acknowledgement(segment.sequence_number, segment.timing)
            self.outgoing_segment_queue.put(acknowledgement)

        elif(isinstance(segment, Control)):
            # We have a control segment, what is it telling us?
            if(segment.command = Control.CMD_ABORT):
                pass
            # TODO

                            
    def __complete_reconstruction(self):
        # Create a buffer
        buffer = BytesIO(b"")

        # Start a counter
        sequence = self.next_expected_sequence_number

        # Loop until we don't have anything to reconstruct
        while (sequence in self.reconstruction):
            # Get the segment from the reconstruction dictionary
            segment = self.reconstruction[sequence]

            # Remove segment from dictionary
            del self.reconstruction[sequence]
            
            # Write the segment data to the buffer
            buffer.write(segment.data)

            # Increment the sequence number
            sequence += 1

        # Sequence is now the next expected sequence number
        self.next_expected_sequence_number = sequence

        # Rewind the buffer for reading
        buffer.seek(0, 0)

        # Return the buffer
        return buffer

            
    def __adjust_window_size(self, last_trip):
        # Has the trip time gotten longer?
        if(last_trip > self.best_ping):
            # Yes, were we previously increasing the window size?
            if(self.adjustment_delta > 0):
                # Yes, stop increasing it
                self.adjustment_delta = 0

            # Were we keeping the window size consistant?
            elif(self.adjustment_delta == 0):
                # Yes, start decreasing it
                self.adjustment_delta = -1

            # Were we previously decreasing it?
            elif(self.adjustment_delta < 0):
                # Yes, decrease it some more
                self.adjustment_delta *= 2

        # Did the trip get shorter?
        elif(last_trip < self.best_ping):
            # Yes, were we previously increasing the window size?
            if(self.adjustment_delta > 0):
                # Yes, increase it some more
                self.adjustment_delta *= 2

            # Were we previously decreasing it or keeping it the same?
            elif(self.adjustment_delta <= 0):
                # Yes, stop
                self.adjustment_delta = 0

            # Since this is now the best round trip time, update best ping
            self.best_ping = last_trip

        # Apply the delta
        self.window_size += self.adjustment_delta 

        # Is the window size now less than the metric size?
        if(self.window_size < METRIC_WINDOW_SIZE):
            # Yes, reset it to the metric size
            self.window_size = METRIC_WINDOW_SIZE
            
            # Update the delta so when we have our baseline we start slowly increasing again
            self.adjustment_delta = 1

            # Clear out our trip metrics
            self.segment_trips.clear()


    def __enqueue_segments(self):
        # If we have segments to queue, and room in our window, queue them
        while self.segment_queue.qsize() > 0 and len(self.in_flight) < self.window_size:
            self.outgoing_segment_queue.put(self.segment_queue.get())

        # Calculate a maximum time value for segments eligable to be resent
        maxtime = time.time() - (self.best_ping * 1.5)

        # Do we have any in-flight packets to resend?
        for segment in self.in_flight.values():
            # Is the segment timing value less than the max time?
            if(segment.timing < maxtime):
                # Resend it
                self.outgoing_segment_queue.put(segment)


    def __handle_app_data(self, stream):
        # Figure out what sequence number we need to watch for
        sequence_number = -1    

        # Count the number of segments we create
        segment_count = 0    

        # Get the segment lock
        with self.segment_lock:
            # Create the segments
            for segment in self.__create_payload_segments(stream):
                # Add to the segment queue
                self.segment_queue.put(segment)
                sequence_number = segment.sequence_number
                segment_count += 1

        # Did we make any segments?
        if(sequence_number == -1):
            raise OSError("No data to send.")

        # Create a subject
        subject = rx.subjects.Subject()

        # Add it to our tracker (TODO: This could be a race condition) ALSO, TODO implement good tracking this model won't actually work
        self.segment_subjects[sequence_number] = (subject, segment_count)

        # Return the subject
        return subject


    def __handle_app_close(self):
        raise NotImplementedError()


    def __create_payload_segments(self, stream):
        # Generator for creating segments from a stream
        while True:
            # Read data from stream
            data = stream.read(SEGMENT_PAYLOAD_SIZE)

            # Did we read any data?
            if(len(data) == 0):
                break

            # Run the data through the features
            processed_data = data
            for feature in self.features:
                processed_data = feature.wrap(processed_data)

            # Create the segment
            segment = Payload(self.segment_number, processed_data)

            # Increment segment number
            self.segment_number += 1

            # Return the segment
            yield segment