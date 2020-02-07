

class SegmentTracker:

    def __init__(self, notify_subject):
        self.remaining = set()
        self.notify_subject = notify_subject

    def add_segment(self, segment):
        self.remaining.add(segment.sequence_number)

    def complete(self, sequence_number):
        self.remaining.remove(sequence_number)
        if(len(self.remaining) == 0):
            self.notify_subject.on_complete()
