
class PairStats:

    def __init__(self, num1, num2):
        self.count = 0
        self.size = 0
        self.num1 = num1
        self.num2 = num2

    def send(self, size):
        self.count += 1
        self.size += size

    @property
    def between(self):
        return "{}->{}".format(self.num1, self.num2)