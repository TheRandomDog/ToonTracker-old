import logging

__author__ = 'TheRandomDog'
__version__ = 'ToonTracker-bot/4.0-test'

try:
	from logging import NullHandler
except ImportError:
	class NullHandler(logging.Handler):
		def emit(self, record):
			pass

logging.getLogger('ToonTracker').addHandler(NullHandler())