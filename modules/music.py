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

    class PlayCMD(Command):
        NAME = 'play'

        @classmethod
        async def execute(cls, client, module, message, *args):
            if not message.author.voice:
                return module.createDiscordEmbed(subtitle=':music: Please join a voice channel and I\'ll send a TuneTracker your way!')

            if message.author.voice.channel.id not in module.running_bots:
                await message.channel.send('Spinning up your TuneTracker, it\'ll just be a jif...')
                bot = await module.spawn_bot(message.author.voice.channel)
                await bot.get_channel(message.author.voice.channel.id).connect()

    def __init__(self, client):
        Module.__init__(self, client)

        self.available = list(Config.getModuleSetting('music', 'bots', {}).keys())
        self.running_bots = {}

    async def spawn_bot(self, channel):
        token = self.available.pop()
        config = Config.getModuleSetting('music', 'bots')[token]

        bot = TuneTracker()
        self.client.loop.create_task(bot.start(token))
        await bot.wait_until_ready()
        self.running_bots[channel.id] = bot
        return bot

module = MusicManager