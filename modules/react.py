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
                if emote == None:
                    continue
                await message.add_reaction(emote)
        elif message.channel.id == self.interact and not message.attachments and (Config.getRankOfUser(message.author.id) < 200 or Config.getRankOfRole(message.author.top_role.id) < 200):
          await message.delete()

module = ReactModule