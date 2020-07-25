COLOUR_BLACK = 0
COLOUR_RED = 1
COLOUR_GREEN = 2
COLOUR_YELLOW = 3
COLOUR_BLUE = 4
COLOUR_MAGENTA = 5
COLOUR_CYAN = 6
COLOUR_WHITE = 7

class Formatter:
	def __init__(self, string):
		self.string = "%s\x1b[0m" % string

	def gfxcode(self, code):
		self.string = "\x1b[%dm%s" % (code, self.string)
		return self

	def bold(self):
		return self.gfxcode(1)

	def underline(self):
		return self.gfxcode(4)

	def blink(self):
		return self.gfxcode(5)

	def colour(self, colour):
		return self.gfxcode(colour+30)

	def highlight(self, colour):
		return self.gfxcode(colour+40)