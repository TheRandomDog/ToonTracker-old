import discord
import asyncio
import sys
import os
from extra.commands import Command
from utils import *
from importlib import import_module, reload
from modules import invasion, status, news, release, lobbies, reddit, moderation
from traceback import format_exc
import threading
import time

this = sys.modules[__name__]
loop = asyncio.get_event_loop()
restarted = False

def delegateEvent(func):
    async def inner(self, *args):
        if not self.ttReady:
            pass

        for module in self.modules:
            if hasattr(module, func.__name__):
                await getattr(module, func.__name__)(*args)

        return await func(self, *args)
    return inner

class ToonTracker(discord.Client):
    class EvalCMD(Command):
        NAME = 'eval'
        RANK = 500

        @staticmethod
        async def execute(client, module, message, *args):
            try:
                result = eval(' '.join(args))
            except BaseException as e:
                result = '```{}```'.format(format_exc())
            #await client.send_message(message.channel, str(result) if result != None else 'Evaluated successfully.')
            return str(result) if result != None else 'Evaluated successfully.'

    class ExecCMD(Command):
        NAME = 'exec'
        RANK = 500

        @staticmethod
        async def execute(client, module, message, *args):
            try:
                exec(' '.join(args))
                #await client.send_message(message.channel, 'Executed successfully.')
                return 'Excecuted successfully.'
            except BaseException as e:
                #await client.send_message(message.channel, '```{}```'.format(format_exc()))
                return '```{}```'.format(format_exc())

    class QuitCMD(Command):
        NAME = 'quit'
        RANK = 500

        @staticmethod
        async def execute(client, module, message, *args):
            await client.logout()
            await client.close()

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

        self.ttReady = False
        self.readyToClose = False
        self.restart = False

        self.lastGot = time.time()

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
        if not self.ttReady or message.author == self.rTTR.me:
            return

        for command in self.commands:
            if message.content.startswith(self.commandPrefix + command.NAME) and \
                    (Config.getRankOfUser(message.author.id) >= command.RANK or any([Config.getRankOfRole(role.id) >= command.RANK for role in message.author.roles])):
                response = await command.execute(self, None, message, *message.content.split(' ')[1:])
                if response:
                    await self.send_message(message.channel, response)

        for module in self.modules:
            response = await module._handleMsg(message)
            if response:
                await self.send_message(message.channel, response)

    async def send_message(self, target, message, deleteIn=30, priorMessage=None, **kwargs):
        if type(message) == list:
            for msg in message:
                await self.send_message(target, msg, deleteIn, priorMessage, **kwargs)
            return

        if type(target) == list:
            for tgt in target:
                await self.send_message(tgt, message, deleteIn, priorMessage, **kwargs)
            return
        elif type(target) == str:
            target = self.get_channel(target)
            if not target:
                return
        elif type(target) == None:
            return

        if message.__class__ == discord.Embed:
            msgObj = await super().send_message(target, content=None, embed=message)
        else:
            msgObj = await super().send_message(target, message)
            #if deleteIn:
            #    self.loop.call_later(deleteIn, self.deleteMessage, deleteIn, msgObj)
            #    if priorMessage:
            #        self.loop.call_later(deleteIn, self.deleteMessage, deleteIn, priorMessage.originalObject)

        return msgObj

    async def announceUpdates(self):
        self.lastGot = time.time()

        for module in self.modules:
            for announcement in module.pendingAnnouncements:
                try:
                    await self.send_message(announcement[0], announcement[1])
                except Exception as e:
                    print('{} tried to send an announcement to channel ID {}, but an exception was raised.\nAnnouncement: {}\n\n{}'.format(
                        announcement[2]['module'].__class__.__name__ if announcement[2].get('module', None) else 'Unknown Module', announcement[0], announcement[1], format_exc()))
                    await self.send_message(botspam, '**{}** tried to send an announcement to channel ID {}, but an exception was raised.\n```\n{}```'.format(
                        announcement[2]['module'].__class__.__name__ if announcement[2].get('module', None) else 'Unknown Module', announcement[0], format_exc()))

            for update in module.pendingUpdates:
                messageSent = False
                channel = self.get_channel(update[0])
                async for message in self.logs_from(channel, limit=10):
                    for embed in message.embeds:
                        #print(embed.get('fields', [{}])[0].get('name', ''), update[1].fields[0].name)
                        #print(embed, update[2])
                        if embed.get('fields', [{}])[0].get('name', '') == update[1] or embed.get('author', {}).get('name', '') == update[1]:
                            await self.edit_message(message, embed=update[2])
                            messageSent = True
                if not messageSent:
                    await self.send_message(channel, update[2])

            module.pendingAnnouncements = []
            module.pendingUpdates = []

    def ttLoop(self):
        while not self.readyToClose:
            loop.stop()
            loop.run_forever()

            if time.time() - self.lastGot > 10:
                loop.create_task(self.announceUpdates())
                self.lastGot = time.time()

    @delegateEvent
    async def on_channel_create(self, channel): pass
    @delegateEvent
    async def on_channel_delete(self, channel): pass
    @delegateEvent
    async def on_channel_update(self, before, after): pass
    @delegateEvent
    async def on_member_ban(self, member): pass
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
    async def on_server_available(self, server): pass
    @delegateEvent
    async def on_server_emojis_update(self, before, after): pass
    @delegateEvent
    async def on_server_join(self, server): pass
    @delegateEvent
    async def on_server_remove(self, server): pass
    @delegateEvent
    async def on_server_role_create(self, role): pass
    @delegateEvent
    async def on_server_role_delete(self, role): pass
    @delegateEvent
    async def on_server_unavailable(self, server): pass
    @delegateEvent
    async def on_server_role_update(self, before, after): pass
    @delegateEvent
    async def on_server_update(self, before, after): pass
    @delegateEvent
    async def on_voice_state_update(self, before, after): pass

    async def load_config(self, term='start', channel=botspam):
        warnings = []
        errors = []

        rTTR = Config.getSetting('rTTR')
        if not rTTR:
            e = 'No server ID was designated as rTTR in config.'
            errors.append(e)
            print('[!!!] ' + e)
        self.rTTR = self.get_server(rTTR)
        if not self.rTTR:
            e = 'No known server was designated as rTTR in config.'
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
            continue
        for module in self.toLoad:
            assertType('module', module, str)

            if not hasattr(this, module):
                w = 'Could not find Pythonic module of ToonTracker module "{}" (may be misspelled in config).'.format(module)
                warnings.append(w)
                print(w)
                continue
            modsmod = getattr(this, module)
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
        if self.ttReady:
            return

        await self.load_config(term='start' if not restarted else 'restart')
        self.ttReady = True


token = Config.getSetting('token')
if not token:
    print('ToonTracker failed to start. No Discord token was found in the config.')
    sys.exit()

while True:
    try:
        T = ToonTracker()
    except Exception as e:
        print('ToonTracker failed to start.\n\n{}'.format(format_exc()))
        sys.exit()

    try:
        loop.run_until_complete(T.login(token))
    except Exception as e:
        print('ToonTracker failed to login. {}'.format(e))
        sys.exit()

    botspam = Config.getSetting('botspam')
    if not botspam:
        print('No bot spam channel specified in the config. You may miss important messages.')

    connLoop = loop.create_task(T.connect())
    loop.run_until_complete(T.wait_until_ready())

    T.ttLoop()

    for module in T.modules:
        module.stopTracking()

    if T.restart:
        del T
    else:
        break