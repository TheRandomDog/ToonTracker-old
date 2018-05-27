import discord
from modules.module import Module
from extra.commands import Command
from utils import Config

class SuggestModule(Module):
    class SuggestCMD(Command):
        NAME = 'suggest'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.id == module.interaction_channel:
                for emoji in module.emojis:
                    if not emoji:
                        pass
                    try:
                        await message.add_reaction(emoji)
                    except discord.HTTPException:
                        print("An emoji couldn't be added to a message as a reaction. Ensure that they are correctly inputted in config and the \"add reactions\" role is assigned to the bot.")

    def __init__(self, client):
        Module.__init__(self, client)

        discord_emojis = Config.get_module_setting('suggest', 'discord_emojis', otherwise=[])
        custom_emojis = [discord.utils.get(client.focused_guild.emojis, name=e) for e in Config.get_module_setting('suggest', 'custom_emojis', otherwise=[])]
        self.emojis = discord_emojis + custom_emojis
        if self.emojis.count(None):
            print('{} custom emoji(s) used for suggestions could not be found on the server.').format(self.emojis.count(None))
        self.interaction_channel = Config.get_module_setting('suggest', 'interaction')

module = SuggestModule