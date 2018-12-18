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

        self.contest_name = 'House Contest'
        self.uploads = database.create_section(self, 'deccontest2018', {
            'user': [database.INT, database.PRIMARY_KEY],
            'uploads': database.INT,
            'reaction_end_time': database.INT,
            'reaction_message_id': database.INT
        })
        self.channel = Config.get_module_setting('contest', 'channel')
        self.scheduled_reactions = []
        self.p1 = discord.utils.get(client.focused_guild.emojis, name='moo')
        #self.m1 = discord.utils.get(client.focused_guild.emojis, name='m1')

    async def on_message(self, message):
        if message.channel.id != self.channel:
            return
        if message.content:
            message.nonce = 'silent'
            await message.delete()
            response = "Hello there! This channel is for the {}, and text is not allowed. If you're trying to submit photos, please upload them as an attachment.".format(self.contestName)
            try:
                await message.author.send(response)
            except:
                await message.channel.send(message.author.mention + " " + response)
            return

        attachments = len(message.attachments)
        query = self.uploads.select(where=['user=?', message.author.id], limit=1)
        if query == None:
            self.uploads.insert(user=message.author.id, uploads=0, reaction_end_time=0, reaction_message_id=0)
            uploads = 0
        else:
            uploads, reaction_message_id = query['uploads'], query['reaction_message_id']

        if uploads + attachments <= 4:
            if reaction_message_id:
                try:
                    message = await self.client.get_channel(self.channel).get_message(reaction_message_id)
                except discord.errors.NotFound:
                    message = None
                if message and message.reactions:
                    await message.clear_reactions()
            updatedArguments = {'uploads': uploads + attachments}
            if message.id in self.scheduled_reactions:
                self.scheduled_reactions.remove(message.id)
            updatedArguments['reaction_end_time'] = time.time() + (0 if uploads + attachments == 4 else 10)
            updatedArguments['reaction_message_id'] = message.id
            self.uploads.update(where=['user=?', message.author.id], **updatedArguments)
        else:
            message.nonce = 'silent'
            await message.delete()
            try:
                response = "Hello there! You're only allowed 4 photo uploads per entry for this contest. "
                if attachments >= 4:
                    suggestion = 'Please resubmit with only 4 photos.'
                else:
                    suggestion = 'Please delete a recent picture to upload a new one.'
                await message.author.send(response + suggestion)
            except:
                await message.channel.send(message.author.mention + " " + response + suggestion)
        self.schedule_reactions()

    async def on_message_delete(self, message):
        if message.channel.id != self.channel or message.content or not message.attachments or message.nonce == 'silent':
            return

        attachments = len(message.attachments)
        query = self.uploads.select(where=['user=?', message.author.id], limit=1)
        uploads, reaction_message_id = query['uploads'], query['reaction_message_id']
        if uploads == None:
            # Only a sanity check.
            self.uploads.insert(user=message.author.id, uploads=0)
            uploads = 0
        else:
            uploads = uploads['uploads']
            self.uploads.update(where=['user=?', message.author.id], uploads=max(0, uploads - attachments))

        if message.id == reaction_message_id:
            self.schedule_reactions.remove(message.id)

        self.schedule_reactions()

    def schedule_reactions(self):
        allUploads = self.uploads.select()
        for uploads in allUploads:
            if uploads['reaction_message_id'] in self.scheduled_reactions or 0 < uploads['reaction_end_time'] <= time.time():
                continue
            self.scheduled_reactions.append(uploads['reaction_message_id'])
            self.client.loop.create_task(
                self.add_reaction(
                    uploads['user'],
                    uploads['reaction_message_id'],
                    uploads['reaction_end_time']
                )
            )

    async def add_reaction(self, user_id, message_id, end_time=None):
        print (user_id)
        print (message_id)
        print (end_time)
        if not self.channel:
            return  # Our channel is gone, no need to do anything.
        if end_time:
            print('end_time - time.time() {}'.format(end_time - time.time()))
            await asyncio.sleep(end_time - time.time())
        try:
            message = await self.client.get_channel(self.channel).get_message(message_id)
        except discord.errors.NotFound:
            message = None
        if not message:
            print (message, message_id)
            return  # Our message is gone, no need to do anything.
        if message_id not in self.scheduled_reactions:
            print (message_id, self.scheduled_reactions)
            return  # If it was removed externally, we basically cancel it.
        try:
            print ('reactions')
            await message.add_reaction(self.p1)
            #await message.add_reaction(self.m1)
        except Exception as e:
            print('Failed to add reactions to a contest post!!!\n{}'.format(format_exc()))
        self.scheduled_reactions.remove(message_id)

module = ContestModule