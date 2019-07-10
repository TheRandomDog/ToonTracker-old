import discord
import asyncio
import time
from traceback import format_exc
from modules.module import Module
from extra.commands import Command
from utils import Config, database

class ContestModule(Module):
    class NameCMD(Command):
        """~removeBadLink <url format>

        Removes a bad link format from the filter list. Be sure to use the format that was added exactly.
        """
        NAME = 'contestName'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            if args:
                self.contest_name = ' '.join(args)

    def __init__(self, client):
        Module.__init__(self, client)

        self.contest_name = 'Emoji Contest'
        self.uploads = database.create_section(self, 'julcontest2019', {
            'user': [database.INT, database.PRIMARY_KEY],
            'uploads': database.INT,
        })
        self.channel = Config.get_module_setting('contest', 'channel')
        self.channel_name = None
        self.p1 = discord.utils.get(client.focused_guild.emojis, name='p1')
        #self.m1 = discord.utils.get(client.focused_guild.emojis, name='m1')

    async def on_message(self, message):
        if message.channel.id != self.channel:
            return
        if message.content:
            message.nonce = 'silent'
            await message.delete()
            if not self.channel_name:
                self.channel_name = self.client.get_channel(self.channel).name
            response = "Hey! #{} is for the Discord's {}, and text is not allowed. If you're trying to submit entries, please upload them as an attachment.".format(self.channel_name, self.contest_name)
            try:
                await message.author.send(response)
            except:
                await message.channel.send(message.author.mention + " " + response)
            return

        attachments = len(message.attachments)
        query = self.uploads.select(where=['user=?', message.author.id], limit=1)
        if query == None:
            self.uploads.insert(user=message.author.id, uploads=0)
            uploads = 0
        else:
            uploads = query['uploads']

        if uploads + attachments <= 10:
            updatedArguments = {'uploads': uploads + attachments}
            self.uploads.update(where=['user=?', message.author.id], **updatedArguments)
            await message.add_reaction(self.p1)
        else:
            message.nonce = 'silent'
            await message.delete()
            try:
                response = "Hello there! You're only allowed 10 entries for this contest. "
                if attachments >= 10:
                    suggestion = 'Please resubmit with only 10 entries.'
                else:
                    suggestion = 'Please delete a recent entry to upload a new one.'
                await message.author.send(response + suggestion)
            except:
                await message.channel.send(message.author.mention + " " + response + suggestion)
        
    async def on_message_delete(self, message):
        if message.channel.id != self.channel or message.content or not message.attachments or message.nonce == 'silent':
            return

        attachments = len(message.attachments)
        query = self.uploads.select(where=['user=?', message.author.id], limit=1)
        uploads = query['uploads']
        if uploads == None:
            # Only a sanity check.
            self.uploads.insert(user=message.author.id, uploads=0)
            uploads = 0
        else:
            self.uploads.update(where=['user=?', message.author.id], uploads=max(0, uploads - attachments))

module = ContestModule