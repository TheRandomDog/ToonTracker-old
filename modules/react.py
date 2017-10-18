import discord
import asyncio
from modules.module import Module
from extra.commands import Command
from utils import Config

class ReactModule(Module):

    def __init__(self, client):
        Module.__init__(self, client)
       # self.commands = [
       #     self.ReactCMD
       # ]
        self.emotes = [discord.utils.get(client.rTTR.emojis, id = emote) for emote in Config.getModuleSetting('react', 'emotes')]
        self.interact = Config.getModuleSetting('react', 'interaction')

    async def handleMsg(self, message):
        if message.channel.id == self.interact and message.attachments:
            for emote in self.emotes:
                print (emote)
                if emote == None:
                    continue
                await message.add_reaction(emote)

module = ReactModule