from .module import *
from extra.tunetracker import TuneTracker

class MusicManager(Module):
	class SummonBotCMD(Command):
		NAME = 'summonBot'

		@classmethod
		async def execute(cls, client, module, message, *args):
			try:
				token = module.available.pop()
				config = Config.getModuleSetting('music', 'bots')[token]
			except IndexError:
				return 'No available TuneTrackers.'

			bot = TuneTracker()
			client.loop.create_task(bot.start(token))

	def __init__(self, client):
		Module.__init__(self, client)

		self.available = list(Config.getModuleSetting('music', 'bots', {}).keys())
		self.runningBots = {}

module = MusicManager