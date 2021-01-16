from LibPeer2.Debug import Formatter

import sys
import inspect
import subprocess


class Log:
	enabled = True
	level = 0
	output = sys.stdout
	levels = ["DEBUG", "MESSAGE", "INFO", "WARNING", "ERROR", "CRITICAL", "MELTDOWN"]
	
	level_formats = [
			(lambda f: f.colour(Formatter.COLOUR_WHITE)),                                          # DEBUG
			(lambda f: f.colour(Formatter.COLOUR_WHITE).bold()),                                   # MESSAGE
			(lambda f: f.colour(Formatter.COLOUR_CYAN).bold()),                                    # INFORMATION
			(lambda f: f.colour(Formatter.COLOUR_YELLOW).bold()),                                  # WARNING
			(lambda f: f.colour(Formatter.COLOUR_RED).bold()),                                     # ERROR
			(lambda f: f.colour(Formatter.COLOUR_WHITE).highlight(Formatter.COLOUR_RED).bold()),        # CRITICAL
			(lambda f: f.colour(Formatter.COLOUR_WHITE).highlight(Formatter.COLOUR_RED).bold().blink()) # MELTDOWN
			]
	

	@staticmethod
	def debug(message):
		identifier = Log.get_identifier(2)
		Log.log(0, identifier, message)

	@staticmethod
	def msg(message):
		identifier = Log.get_identifier(2)
		Log.log(1, identifier, message)

	@staticmethod
	def info(message):
		identifier = Log.get_identifier(2)
		Log.log(2, identifier, message)

	@staticmethod
	def warn(message):
		identifier = Log.get_identifier(2)
		Log.log(3, identifier, message)

	@staticmethod
	def error(message):
		identifier = Log.get_identifier(2)
		Log.log(4, identifier, message)

	@staticmethod
	def critical(message):
		identifier = Log.get_identifier(2)
		Log.log(5, identifier, message)

	@staticmethod
	def meltdown(message):
		identifier = Log.get_identifier(2)
		Log.log(6, identifier, message)


	@staticmethod
	def log(level, identifier, message):
		if(Log.enabled and level >= Log.level):
			# Find out the longest name in the levels
			space = 0
			for lvl in Log.levels:
				if(len(lvl) > space):
					space = len(lvl)

			# Padding is nice
			space += 2

			levelText = Log.levels[level]
			levelText = " "*(space - len(levelText)) + levelText

			logHeader = "%s  " % (Log.level_formats[level](Formatter.Formatter(levelText)).string)


			# Prepend the identifier to the message
			message = "[%s] %s" % (identifier, message)
			
			# Get terminal size
			rows, columns = subprocess.check_output(['stty', 'size']).decode().split()
			columns = int(columns)
			
			resetLevel = len(levelText) + 2

			messageLines = message

			if(len(message) + resetLevel > columns and columns > resetLevel):
				messageLines = message[:columns - resetLevel]
				message = message[columns - resetLevel:]

				while(message != ""):
					messageLines += "\n" + " "*(resetLevel) + message[:columns - resetLevel]
					message = message[columns - resetLevel:]
				

			Log.output.write("%s%s\n" % (logHeader, messageLines))

	@staticmethod
	def get_identifier(iterations=1):
		frame = inspect.currentframe()
		for i in range(iterations):
			frame = frame.f_back

		function_name = frame.f_code.co_name
		
		identifier = "@sm %s" % function_name

		if "self" in frame.f_locals:
			identifier = str(frame.f_locals["self"].__class__.__name__)

		return identifier

	@staticmethod
	def settings(enabled, level=1, output=sys.stdout):
		"""set settings on the logger, options are:
			settings(enabled, [level, [output]])
				enabled: a boolean turning on or off logging,
				level: an int from 0 to 6 to filter out messages of less important
					   6 being the most important, 0 being the least
				output: the output to write to
		"""
		Log.enabled = enabled
		Log.level = level
		Log.output = output