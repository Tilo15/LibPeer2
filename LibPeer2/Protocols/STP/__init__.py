from LibPeer2.Protocols.MX2 import MX2
from LibPeer2.Protocols.MX2.Instance import Instance
from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference
from LibPeer2.Protocols.MX2.Packet import Packet
from LibPeer2.Protocols.STP.StreamNegotiation import StreamNegotiation
from LibPeer2.Protocols.STP.Stream.Features import Feature
from LibPeer2.Protocols.STP.Messages import Message
from LibPeer2.Protocols.STP.Messages.RequestSession import RequestSession
from LibPeer2.Protocols.STP.Messages.NegotiateSession import NegotiateSession
from LibPeer2.Protocols.STP.Messages.BeginSession import BeginSession
from LibPeer2.Protocols.STP.Messages.SegmentMessage import SegmentMessage
from LibPeer2.Protocols.STP.Stream.Session import Session
from LibPeer2.Protocols.STP.Stream.EgressStream import EgressStream
from LibPeer2.Protocols.STP.Stream.IngressStream import IngressStream
from LibPeer2.Protocols.STP.Repeater import Repeater

from cachetools import TTLCache
from io import BytesIO

import struct
import time
import uuid
import rx
import threading
import queue
import traceback


"""Stream Transmission Protocol"""
class STP:
    
    def __init__(self, muxer: MX2, instance: Instance):
        self.__muxer = muxer
        self.__instance = instance

        self.__open_sessions = {}
        self.__negotiations = TTLCache(65536, 120)
        self.__reply_subjects = {}
        self.__instance.incoming_payload.subscribe(self.__handle_packet)
        self.__notification_queue = queue.Queue()

        self.incoming_stream = rx.subject.Subject()

        threading.Thread(name="Stream Transmittion Protocol network thread for instance: {}".format(self.__instance.reference), target=self.__run).start()
        threading.Thread(name="Stream Transmittion Protocol notification thread for instance: {}".format(self.__instance.reference), target=self.__notify).start()


    
    def initialise_stream(self, target: InstanceReference, features = [], in_reply_to: bytes = b"\x00"*16):
        # Initiate a stream with another peer
        session_id = uuid.uuid4().bytes

        # Start the negotiation
        negotiation = StreamNegotiation(session_id, in_reply_to, features, StreamNegotiation.STATE_REQUESTED, target, False)
        self.__negotiations[negotiation.session_id] = negotiation

        # Create the session request
        session_request = RequestSession(negotiation.session_id, in_reply_to, features)

        # Send the request in a repeater
        repeater = Repeater(10, 12, lambda: self.__send_packet(target, session_request.serialise()), "STP Stream Request")

        # Save agains the negotiation
        negotiation.request_repeater = repeater

        # Return the negotiation subject
        return negotiation.notify


    def __run(self):
        while True:
            # Get all sessions
            sessions = list(self.__open_sessions.values())

            # Order by the session that sent data longest ago
            sessions.sort(key = lambda x: x.last_send)

            # Loop over each session
            for session in sessions:
                # Does this session have something to send?
                if(session.has_pending_segment()):
                    # Get the segment
                    segment = session.get_pending_segment()

                    # Create a segment message
                    message = SegmentMessage(session.identifier, segment)

                    # Send the segment message
                    self.__send_packet(session.target, message.serialise())


    def __notify(self):
        while True:
            try:
                self.__notification_queue.get()()
            except Exception as e:
                print(traceback.format_exc())
                print("Exception executing task in STP notification queue: {}".format(e))



    def __send_packet(self, destination, stream):
        # Send the packet to the destination
        self.__muxer.send(self.__instance, destination, stream.read())


    def __handle_packet(self, packet: Packet):
        # We have a packet from the muxer, deserialise it
        message = Message.deserialise(packet.stream)

        # What type of message do we have?
        if(isinstance(message, RequestSession)):
            # Skip if we have already handled this request
            if(message.session_id in self.__negotiations):
                return

            # A peer wants to initiate a session with us
            # Create a negotiation object (consider it negotiated as we are about to send back our negotiation)
            negotiation = StreamNegotiation(message.session_id, message.in_reply_to, message.feature_codes, StreamNegotiation.STATE_NEGOTIATED, packet.origin, True)

            # Add to negotiations
            self.__negotiations[message.session_id] = negotiation
            
            # Figure out which features we can apply
            features = Feature.get_features(message.feature_codes)

            # Get our feature codes
            feature_codes = [x.IDENTIFIER for x in features]

            # Construct a reply
            reply = NegotiateSession(negotiation.session_id, feature_codes, message.timing)

            # Repeatedly send the negotiation
            repeater = Repeater(10, 12, lambda: self.__send_packet(negotiation.remote_instance, reply.serialise()), "STP Stream Negotiation")

            # Save the repeater against the negotiation
            negotiation.negotiate_repeater = repeater
            

        elif(isinstance(message, NegotiateSession)):
            # We are getting a negotiation reply from a peer
            # Do we have a negotiation open with this peer?
            if(message.session_id not in self.__negotiations):
                # TODO send cleanup
                return

            # Get the negotiation
            negotiation: StreamNegotiation = self.__negotiations[message.session_id]

            # Cancel the request repeater
            if(negotiation.request_repeater != None):
                negotiation.request_repeater.cancel()

            # Set the ping value
            negotiation.ping = time.time() - message.reply_timing

            # Make sure we have all the features they negotiated upon
            features = Feature.get_features(message.feature_codes)

            if(len(features) != len(message.feature_codes)):
                # TODO send cleanup
                return
                
            # Update the features list
            negotiation.feature_codes = message.feature_codes

            # Reply with a begin session message
            reply = BeginSession(negotiation.session_id, message.timing)

            # Send the reply
            self.__send_packet(negotiation.remote_instance, reply.serialise())

            # Make sure the negotiation is in the right state
            if(negotiation.state != StreamNegotiation.STATE_REQUESTED):
                return

            # Update the negotiaiton state
            negotiation.state = StreamNegotiation.STATE_ACCEPTED

            # Setup the session
            self.__setup_session(negotiation)


        elif(isinstance(message, BeginSession)):
            # We are getting a negotiation reply from a peer
            # Do we have a negotiation open with this peer?
            if(message.session_id not in self.__negotiations):
                # TODO send cleanup
                return

            # Get the negotiation
            negotiation: StreamNegotiation = self.__negotiations[message.session_id]
            
            # Cancel the negotiate repeater
            if(negotiation.negotiate_repeater != None):
                negotiation.negotiate_repeater.cancel()

            # Make sure the negotiation is in the right state
            if(negotiation.state != StreamNegotiation.STATE_NEGOTIATED):
                # TODO send cleanup
                return

            # Update the negotiation state
            negotiation.state = StreamNegotiation.STATE_ACCEPTED

            # Set the ping value
            negotiation.ping = time.time() - message.reply_timing

            # Setup the session
            self.__setup_session(negotiation)

            # Cleanup the negotiation
            del self.__negotiations[message.session_id]

        elif(isinstance(message, SegmentMessage)):
            # Do we have a session open?
            if(message.session_id not in self.__open_sessions):
                # Skip
                return

            # Is there a valid negotiation still open?
            if(message.session_id in self.__negotiations):
                # Cleanup the negotiation
                del self.__negotiations[message.session_id]

            # Get the session
            session: Session = self.__open_sessions[message.session_id]

            # Give the session the segment
            session.process_segment(message.segment)


    def __setup_session(self, negotiation: StreamNegotiation):
        # Get a list of feature instances
        features = [x() for x in Feature.get_features(negotiation.feature_codes)]

        # Create the session object
        session = Session(negotiation.remote_instance, features, negotiation.session_id, negotiation.ping, negotiation.ingress)

        # Save the session
        self.__open_sessions[session.identifier] = session

        # Is this an egress session?
        if(not negotiation.ingress):
            # Save the reply subject
            self.__reply_subjects[session.identifier] = session.reply_subject

            # Notify the application that the stream is ready
            self.__notification_queue.put(lambda: negotiation.notify.on_next(session.stream))
            

        else:
            # Do we have a reply subject to inform?
            if(negotiation.in_reply_to in self.__reply_subjects):
                # Notify the application via the previous stream
                self.__notification_queue.put(lambda: self.__reply_subjects[negotiation.in_reply_to].on_next(session.stream))

            else:
                # Otherwise notify the application normally
                self.__notification_queue.put(lambda: self.incoming_stream.on_next(session.stream))

                





