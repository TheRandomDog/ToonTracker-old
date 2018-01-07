import discord
from modules.module import Module
from extra.commands import Command
from utils import Config

class SuggestModule(Module):
    class SuggestCMD(Command):
        NAME = 'suggest'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.id == module.interactionChannel:
                for emoji in module.emojis:
                    if not emoji:
                        pass
                    try:
                        await message.add_reaction(emoji)
                    except discord.HTTPException:
                        print("An emoji couldn't be added to a message as a reaction. Ensure that they are correctly inputted in config and the \"add reactions\" role is assigned to the bot.")

    def __init__(self, client):
        Module.__init__(self, client)

        discordEmojis = Config.getModuleSetting('suggest', 'discord_emojis', otherwise=[])
        customEmojis = [discord.utils.get(client.rTTR.emojis, name=e) for e in Config.getModuleSetting('suggest', 'custom_emojis', otherwise=[])]
        self.emojis = discordEmojis + customEmojis
        if self.emojis.count(None):
            print('{} custom emoji(s) used for suggestions could not be found on the server.').format(self.emojis.count(None))
        self.interactionChannel = Config.getModuleSetting('suggest', 'interaction')

module = SuggestModule