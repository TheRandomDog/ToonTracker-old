from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from pubnub.callbacks import SubscribeCallback

from .module import *
from discord import Embed, Color
from utils import Config, getVersion
uaHeader = Config.getSetting('ua_header', getVersion())

digits = str.maketrans({
    '0': ':zero:',
    '1': ':one:',
    '2': ':two:',
    '3': ':three:',
    '4': ':four:',
    '5': ':five:',
    '6': ':six:',
    '7': ':seven:',
    '8': ':eight:',
    '9': ':nine:'
})

class SilliModule(Module, SubscribeCallback):
    CHANNEL_ID = Config.getModuleSetting('silli', 'perma')

    class AdvanceCMD(Command):
        # No peeking.
        NAME = 'advanceStory'
        RANK = 500

        @staticmethod
        async def execute(client, module, message, *args):
            module.advance = True

    def __init__(self, client):
        Module.__init__(self, client)

        pnconfig = PNConfiguration()
        pnconfig.subscribe_key = assertType(Config.getModuleSetting('silli', 'subkey'), str)
        pnconfig.ssl = True
        self.pubnub = PubNub(pnconfig)

        self.advance = None
        self.advMsg = assertType(Config.getModuleSetting('silli', 'adv_msg'), str)
        self.particles = {'remaining': None, 'count': None}

    def startTracking(self):
        self.pubnub.subscribe().channels('sillyparticles').execute()
        self.pubnub.add_listener(self)

    def stopTracking(self):
        self.pubnub.unsubscribe().channels('sillyparticles').execute()
        self.pubnub.remove_listener(self)

    def message(self, pubnub, message):
        if message.message != self.particles:
            if self.advance == None:
                if message.message['count'] <= 0:
                    self.advance = True
                else:
                    self.advance = False

            self.particles = message.message
            self.updatePermaMsg(SilliPermaMsg)


class SilliPermaMsg(PermaMsg):
    TITLE = 'Silly Particles'

    def update(module):
        title = 'Silly Particles'

        r, c = str(module.particles['remaining']), str(module.particles['count'])
        particlesRemaining, particleCount = r.translate(digits), c.translate(digits)
        return module.createDiscordEmbed(
            subtitle=title,
            info=self.advMsg if module.advance else None,
            fields=[
                {'name': 'Count', 'value': particleCount},
                {'name': 'Remaining', 'value': particlesRemaining, 'inline': False}
            ],
            thumbnail='https://cdn.discordapp.com/attachments/309043960943214592/429175538079236096/loonylabs.png',
            color=Color.orange()
        )


module = SilliModule