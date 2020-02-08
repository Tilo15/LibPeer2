

class SegmentTracker:

    def __init__(self, notify_subject):
        self.segment_count = 0
        self.remaining = set()
        self.notify_subject = notify_subject

    def add_segment(self, segment):
        self.segment_count += 1
        self.remaining.add(segment.sequence_number)

    def complete(self, sequence_number):
        self.remaining.remove(sequence_number)
        self.notify_subject.on_next((len(self.remaining) / float(self.segment_count) - 1) * -1)

        if(len(self.remaining) == 0):
            self.notify_subject.on_complete()
