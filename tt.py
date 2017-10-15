import discord
import asyncio
import time
import sys
from extra.commands import Command, CommandResponse
from importlib import import_module, reload
from traceback import format_exc
from utils import *

this = sys.modules[__name__]
loop = asyncio.get_event_loop()
restarted = False

# Sends Discord events to modules.
def delegateEvent(func):
    async def inner(self, *args):
        if not self.ready:
            pass

        for module in self.modules:
            if hasattr(module, func.__name__):
                await getattr(module, func.__name__)(*args)

        return await func(self, *args)
    return inner

class ToonTracker(discord.Client):
    # Evaluate Pythonic code.
    class EvalCMD(Command):
        NAME = 'eval'
        RANK = 500

        @staticmethod
        async def execute(client, module, message, *args):
            try:
                result = eval(' '.join(args))
            except BaseException as e:
                result = '```{}```'.format(format_exc())
            return str(result) if result != None else 'Evaluated successfully.'

    # Execute Pythonic code.
    class ExecCMD(Command):
        NAME = 'exec'
        RANK = 500

        @staticmethod
        async def execute(client, module, message, *args):
            try:
                exec(' '.join(args))
                return 'Excecuted successfully.'
            except BaseException as e:
                return '```{}```'.format(format_exc())

    # Logs out and closes client.
    class QuitCMD(Command):
        NAME = 'quit'
        RANK = 500

        @staticmethod
        async def execute(client, module, message, *args):
            await client.logout()
            await client.close()

    # Reloads config and modules.
    class ReloadCMD(Command):
        NAME = 'reload'
        RANK = 400

        @staticmethod
        async def execute(client, module, message, *args):
            for module in client.modules:
                module.stopTracking()

            client.modules.clear()
            client.toLoad = Config.getSetting('load_modules')
            await client.load_config(term='reload', channel=message.channel)

    def __init__(self):
        super().__init__()

        self.toLoad = Config.getSetting('load_modules')
        self.modules = []

        self.commands = [self.QuitCMD, self.ReloadCMD, self.EvalCMD, self.ExecCMD]
        self.commandPrefix = Config.getSetting('command_prefix', '!')

        self.ready = False
        self.readyToClose = False
        self.restart = False

        self.prevUpdateTime = time.time()
        self.updateDelay = assertTypeOrOtherwise(Config.getSetting('update_delay'), int, float, otherwise=10)

    async def connect(self):
        try:
            await super().connect()
        except Exception as e:
            print('[!!!] A connection issue occured with Discord. Restarting ToonTracker.')
            self.readyToClose = True
            self.restart = True
            global restarted
            restarted = True
            await self.close()

    async def close(self):
        self.readyToClose = True
        await super().close()

    async def on_message(self, message):
        if not self.ready or message.author == self.rTTR.me:
            return

        for command in self.commands:
            if message.content.startswith(self.commandPrefix + command.NAME) and \
                    (Config.getRankOfUser(message.author.id) >= command.RANK or any([Config.getRankOfRole(role.id) >= command.RANK for role in message.author.roles])):
                try:
                    response = await command.execute(self, None, message, *message.content.split(' ')[1:])
                    if type(response) == CommandResponse:
                        await self.send_command_response(response)
                    elif response:
                        await self.send_message(message.channel, response)
                except Exception:
                    await self.send_message(message.channel, '```\n{}```'.format(format_exc()))

        for module in self.modules:
            try:
                response = await module._handleMsg(message)
                if type(response) == CommandResponse:
                    await self.send_command_response(response)
                elif response:
                    print(response)
                    await self.send_message(message.channel, response)
            except Exception:
                await self.send_message(message.channel, '```\n{}```'.format(format_exc()))

    async def send_command_response(self, response):
        await self.send_message(response.target, response.message, response.deleteIn, response.priorMessage, **response.kwargs)

    async def send_message(self, target, message, deleteIn=0, priorMessage=None, **kwargs):
        # Recurses for a list of messages.
        if type(message) == list:
            for msg in message:
                await self.send_message(target, msg, deleteIn, priorMessage, **kwargs)
            return

        # Recurses for a list of targets.
        if type(target) == list:
            for tgt in target:
                await self.send_message(tgt, message, deleteIn, priorMessage, **kwargs)
            return
        # Gets a channel object from a string (channel ID).
        elif type(target) == int:
            target = self.get_channel(target)
            if not target:
                return
        # No target? Rip.
        elif type(target) == None:
            return

        # Deliver message
        if message.__class__ == discord.Embed:
            msgObj = await target.send(content=None, embed=message)
        else:
            msgObj = await target.send(message)

        # Delete message (and optional trigger message)
        if deleteIn:
            self.loop.create_task(self.delete_message(msgObj, deleteIn))
            if priorMessage:
                self.loop.create_task(self.delete_message(priorMessage, deleteIn))

        return msgObj

    async def delete_message(self, message, delay=0):
        await asyncio.sleep(delay)
        await message.delete()

    async def announceUpdates(self):
        self.prevUpdateTime = time.time()

        for module in self.modules:
            for announcement in module.pendingAnnouncements:
                # announcement[0] = Target
                # announcement[1] = Message
                # announcement[2] = Keyword Arguments: (module)
                try:
                    await self.send_message(announcement[0], announcement[1])
                except Exception as e:
                    print('{} tried to send an announcement to channel ID {}, but an exception was raised.\nAnnouncement: {}\n\n{}'.format(
                        announcement[2]['module'].__class__.__name__ if announcement[2].get('module', None) else 'Unknown Module', 
                        announcement[0],
                        announcement[1],
                        format_exc()
                    ))
                    await self.send_message(botspam, '**{}** tried to send an announcement to {}, but an exception was raised.\n```\n{}```'.format(
                        announcement[2]['module'].__class__.__name__ if announcement[2].get('module', None) else 'Unknown Module',
                        discord.get_channel(announcement[0]).mention,
                        format_exc()
                    ))

            # A permanent message is only available as an embed.
            for update in module.pendingUpdates:
                # update[0] = Target (only one target)
                # update[1] = The embed's title, used to find and edit message.
                # update[2] = Embed (Message)
                # update[3] = Keyword Arguments: (module)
                messageSent = False
                channel = self.get_channel(update[0])
                async for message in self.logs_from(channel, limit=10):
                    for embed in message.embeds:
                        # Find the message that has a matching title / author to replace with the new message.
                        if embed.get('fields', [{}])[0].get('name', '') == update[1] or embed.get('author', {}).get('name', '') == update[1]:
                            await self.edit_message(message, embed=update[2])
                            messageSent = True
                if not messageSent:
                    await self.send_message(channel, update[2])

            # All pending messages sent, clear out the list.
            module.pendingAnnouncements = []
            module.pendingUpdates = []

    def ttLoop(self):
        while not self.readyToClose:
            loop.stop()
            loop.run_forever()

            if time.time() - self.prevUpdateTime > 10:
                loop.create_task(self.announceUpdates())
                self.prevUpdateTime = time.time()

    @delegateEvent
    async def on_channel_create(self, channel): pass
    @delegateEvent
    async def on_channel_delete(self, channel): pass
    @delegateEvent
    async def on_channel_update(self, before, after): pass
    @delegateEvent
    async def on_member_ban(self, guild, user): pass
    @delegateEvent
    async def on_member_join(self, member): pass
    @delegateEvent
    async def on_member_remove(self, member): pass
    @delegateEvent
    async def on_member_update(self, before, after): pass
    @delegateEvent
    async def on_message_delete(self, message): pass
    @delegateEvent
    async def on_message_edit(self, before, after): pass
    @delegateEvent
    async def on_reaction_add(self, reaction, user): pass
    @delegateEvent
    async def on_reaction_clear(self, message, reactions): pass
    @delegateEvent
    async def on_reaction_remove(self, reaction, user): pass
    @delegateEvent
    async def on_guild_available(self, guild): pass
    @delegateEvent
    async def on_guild_emojis_update(self, guild, before, after): pass
    @delegateEvent
    async def on_guild_join(self, guild): pass
    @delegateEvent
    async def on_guild_remove(self, guild): pass
    @delegateEvent
    async def on_guild_role_create(self, role): pass
    @delegateEvent
    async def on_guild_role_delete(self, role): pass
    @delegateEvent
    async def on_guild_unavailable(self, guild): pass
    @delegateEvent
    async def on_guild_role_update(self, before, after): pass
    @delegateEvent
    async def on_guild_update(self, before, after): pass
    @delegateEvent
    async def on_voice_state_update(self, member, before, after): pass

    async def load_config(self, term='start', channel=None):
        if not channel:
            channel = Config.getSetting('botspam')

        warnings = []
        errors = []

        rTTR = Config.getSetting('rTTR')
        if not rTTR:
            e = 'No guild ID was designated as rTTR in config.'
            errors.append(e)
            print('[!!!] ' + e)
        self.rTTR = self.get_guild(rTTR)
        if not self.rTTR:
            e = 'No known guild was designated as rTTR in config.'
            errors.append(e)
            print('[!!!] ' + e)

        if errors:
            full = 'ToonTracker failed to {} with **{}** error(s).\n\n'.format(term, len(errors))
            print(full)
            full += '\n'.join([':exclamation: ' + e for e in errors])
            await self.send_message(channel, full)
            await self.logout()
            await self.close()

        # LOADING MODULES

        if self.toLoad == None:
            w = '"load_modules" option not found in config'
            warnings.append(w)
            print(w)
            self.toLoad = []
        for module in self.toLoad:
            assertType(module, str)

            try:
                modsmod = import_module('modules.' + module)
            except ImportError:
                w = 'Could not find Python module of ToonTracker module "{}" (may be misspelled in config).'.format(module)
                warnings.append(w)
                print(w)
                continue
            if not hasattr(modsmod, 'module'):
                w = 'Could not locate module subclass for "{}"'.format(module)
                warnings.append(w)
                print(w)
                continue
            try:
                m = modsmod.module(self)
            except Exception as e:
                w = 'Could not load module subclass for "{}"'.format(module)
                warnings.append(w)
                print(w + '\n\n{}'.format(format_exc()))
                continue

            self.modules.append(m)
            if hasattr(m, 'restoreSession'):
                await m.restoreSession()
            m.startTracking()

        full = 'ToonTracker {}ed with {} warning(s).'.format(term, 'no' if len(warnings) == 0 else '**' + str(len(warnings)) + '**')
        print(full)
        if warnings:
            full += '\n\n'
            full += '\n'.join([':warning: ' + w for w in warnings])
        await self.send_message(channel, full)

    async def on_ready(self):
        if self.ready:
            return

        await self.load_config(term='start' if not restarted else 'restart')
        self.ready = True


token = Config.getSetting('token')
if not token:
    print('ToonTracker failed to start. No Discord token was found in the config.')
    sys.exit()

while True:
    try:
        TT = ToonTracker()
    except Exception as e:
        print('ToonTracker failed to start.\n\n{}'.format(format_exc()))
        sys.exit()

    try:
        loop.run_until_complete(TT.login(token))
    except Exception as e:
        print('ToonTracker failed to login. {}'.format(e))
        sys.exit()

    botspam = Config.getSetting('botspam')
    if not botspam:
        print('No bot spam channel specified in the config. You may miss important messages.')

    connLoop = loop.create_task(TT.connect())
    loop.run_until_complete(TT.wait_until_ready())

    TT.ttLoop()

    for module in TT.modules:
        module.stopTracking()

    if TT.restart:
        del TT
    else:
        break