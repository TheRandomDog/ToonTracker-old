import discord
import asyncio
import aiohttp
import time
import sys
from extra.commands import Command, CommandResponse
from extra.startmessages import Info, Warning, Error
from importlib import import_module, reload
from traceback import format_exc
from inspect import isclass
from utils import *

this = sys.modules[__name__]
loop = asyncio.get_event_loop()
restarted = False

# Sends Discord events to modules.
def delegateEvent(func):
    async def inner(self, *args):
        if not self.ready:
            pass

        for module in self.modules.values():
            if hasattr(module, func.__name__):
                await getattr(module, func.__name__)(*args)

        return await func(self, *args)
    return inner

class ToonTracker(discord.Client):
    # Evaluate Pythonic code.
    class EvalCMD(Command):
        """~eval <python>

            Evaluates Python code and returns the output. You shouldn't use this unless you know what you're doing.
            To get to the client instance, use `TT`.
        """
        NAME = 'eval'
        RANK = 450

        @staticmethod
        async def execute(client, module, message, *args):
            try:
                result = eval(' '.join(args))
            except BaseException as e:
                result = '```{}```'.format(format_exc())
            return str(result) if result != None else 'Evaluated successfully.'

    # Execute Pythonic code.
    class ExecCMD(Command):
        """~exec <python>

            Executes Python code (doesn't return an output). You shouldn't use this unless you know what you're doing.
            To get to the client instance, use `TT`.
        """
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
        """~quit

            Logs out of the bot account, closes the client, and exits the program.
        """

        @staticmethod
        async def execute(client, module, message, *args):
            await client.logout()
            await client.close()

    # Reloads config and modules.
    class ReloadCMD(Command):
        NAME = 'reload'
        RANK = 400
        """~reload

            Reloads all modules and the configuration file.
        """

        @staticmethod
        async def execute(client, module, message, *args):
            for module in client.modules.values():
                module.stopTracking()

            client.modules.clear()
            client.toLoad = Config.getSetting('load_modules')
            await client.load_config(term='reload', channel=message.channel)

    # Helps.
    class HelpCMD(Command):
        NAME = 'help'

        @staticmethod
        async def execute(client, module, message, *args):
            rank = max([Config.getRankOfUser(message.author.id), Config.getRankOfRole(message.author.top_role.id)])

            msg = "Here's a list of available commands I can help with. To get more info, use `~help command`."
            for command in sorted(client.commands, key=lambda c: c.NAME):
                if command.RANK <= rank and command.__doc__:
                    if args and args[0].lower() == command.NAME.lower():
                        doc = command.__doc__.split('\n')
                        doc[0] = '`' + doc[0] + '`'
                        doc = '\n'.join([line.strip() for line in doc])
                        return doc
                    msg += '\n\t' + client.commandPrefix + command.NAME
            for module in client.modules.values():
                for command in sorted(module.commands, key=lambda c: c.NAME):
                    if command.RANK <= rank and command.__doc__:
                        if args and args[0].lower() == command.NAME.lower():
                            doc = command.__doc__.split('\n')
                            doc[0] = '`' + doc[0] + '`'
                            doc = '\n'.join([line.strip() for line in doc])
                            return doc
                        msg += '\n\t' + client.commandPrefix + command.NAME
            return msg


    def __init__(self):
        super().__init__()

        self.toLoad = Config.getSetting('load_modules')
        self.modules = {}

        self.commands = [attr for attr in self.__class__.__dict__.values() if isclass(attr) and issubclass(attr, Command)]
        self.commandPrefix = Config.getSetting('command_prefix', '!')

        self.ready = False
        self.readyToClose = False
        self.restart = False

        self.updateInterval = assertType(Config.getSetting('update_interval'), int, float, otherwise=10)

    def isModuleAvailable(self, module):
        if module in self.modules and self.modules[module].publicModule:
            return True

    def requestModule(self, module):
        if self.isModuleAvailable(module):
            return self.modules[module]

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
            if message.content and message.content.split(' ')[0] == self.commandPrefix + command.NAME and \
                    (Config.getRankOfUser(message.author.id) >= command.RANK or any([Config.getRankOfRole(role.id) >= command.RANK for role in message.author.roles])):
                try:
                    response = await command.execute(self, None, message, *message.content.split(' ')[1:])
                    if type(response) == CommandResponse:
                        await self.send_command_response(response)
                    elif response:
                        await self.send_message(message.channel, response)
                except discord.errors.HTTPException as e:
                    msg = '{} tried to send a response to a message ({}), but Discord threw an HTTPException: {}'.format(command.__class__.__name__, message.id, str(e))
                    print(msg)
                    await self.send_message(botspam, msg)
                except aiohttp.client_exceptions.ClientError as e:
                    msg = '{} tried to send a response to a message ({}), but aiohttp threw an exception: {}'.format(command.__class__.__name__, message.id, str(e))
                    print(msg)
                    await self.send_message(botspam, msg)
                except Exception:
                    await self.send_message(message.channel, '```\n{}```'.format(format_exc()))

        for module in self.modules.values():
            try:
                response = await module._handleMsg(message)
                if type(response) == CommandResponse:
                    await self.send_command_response(response)
                elif response:
                    await self.send_message(message.channel, response)
            except discord.errors.HTTPException as e:
                msg = '{} tried to send a response to a message ({}), but Discord threw an HTTPException: {}'.format(module.__class__.__name__, message.id, str(e))
                print(msg)
                await self.send_message(botspam, msg)
            except aiohttp.client_exceptions.ClientError as e:
                msg = '{} tried to send a response to a message ({}), but Discord threw an HTTPException: {}'.format(module.__class__.__name__, message.id, str(e))
                print(msg)
                await self.send_message(botspam, msg)
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
            target = self.get_channel(target) or self.get_user(target)
            if not target:
                return
        # No target? Rip.
        elif type(target) == None:
            raise TypeError('target type not recognized')

        # Deliver message
        if message.__class__ == discord.File:
            msgObj = await target.send(content='', file=message)
        elif message.__class__ == discord.Embed:
            msgObj = await target.send(content=None, embed=message)
        else:
            msgObj = await target.send(message)

        # Delete message (and optional trigger message)
        if deleteIn:
            msgObj.nonce = 'silent'  # Mainly unused Message attribute that we can use, discord.Message implements __slots__
            self.loop.create_task(self.delete_message(msgObj, deleteIn))
            if priorMessage:
                priorMessage.nonce = 'silent'
                self.loop.create_task(self.delete_message(priorMessage, deleteIn))

        return msgObj

    async def delete_message(self, message, delay=0):
        await asyncio.sleep(delay)
        await message.delete()

    @delegateEvent
    async def on_private_channel_create(self, channel): pass
    @delegateEvent
    async def on_private_channel_delete(self, channel): pass
    @delegateEvent
    async def on_private_channel_update(self, before, after): pass
    @delegateEvent
    async def on_private_channel_pins_update(self, channel, lastPin): pass
    @delegateEvent
    async def on_guild_channel_create(self, channel): pass
    @delegateEvent
    async def on_guild_channel_delete(self, channel): pass
    @delegateEvent
    async def on_guild_channel_update(self, before, after): pass
    @delegateEvent
    async def on_guild_channel_pins_update(self, channel, lastPin): pass
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
            try:
                if type(channel) == list:
                    channel = [int(c) for c in channel]
                else:
                    channel = int(channel)
            except ValueError:
                channel = None

        info = []
        warnings = []
        errors = []

        rTTR = Config.getSetting('guild')
        if not rTTR:
            e = 'No guild ID was designated for participating in in config, or it was malformed.'
            errors.append(e)
            print('[!!!] ' + e)
        self.rTTR = self.get_guild(rTTR)
        if not self.rTTR:
            e = 'No known guild was designated for participating in in config, or it was malformed.'
            errors.append(e)
            print('[!!!] ' + e)
        if not channel:
            e = 'No known channel was designated as the bot output in the config, or it was malformed.'
            errors.append(e)
            print('[!!!] ' + e)

        if errors:
            full = 'ToonTracker failed to {} with **{}** error(s).\n\n'.format(term, len(errors))
            print(full)
            full += '\n'.join([':exclamation: ' + e for e in errors])
            if channel:
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
            except ImportError as e:
                w = 'Could not **import** Python module of ToonTracker module "{}"'.format(module)
                warnings.append(w)
                print(w + '\n\n{}'.format(format_exc()))
                continue
            except Exception as e:
                w = 'Could not **load** Python module of ToonTracker module "{}"'.format(module)
                warnings.append(w)
                print(w + '\n\n{}'.format(format_exc()))
                continue
            if not hasattr(modsmod, 'module'):
                w = 'Could not locate module subclass for "{}"'.format(module)
                warnings.append(w)
                print(w)
                continue
            if hasattr(modsmod, 'messages'):
                for message in modsmod.messages:
                    if message.__class__ == Info:
                        info.append('**{} module:**'.format(module) + str(message))
                    else:
                        warnings.append('**{} module:** '.format(module) + str(message))
            try:
                m = modsmod.module(self)
            except Exception as e:
                w = 'Could not load module subclass for "{}"'.format(module)
                warnings.append(w)
                print(w + '\n\n{}'.format(format_exc()))
                continue

            self.modules[module] = m
            if hasattr(m, 'restoreSession'):
                try:
                    await m.restoreSession()
                except Exception as e:
                    w = 'The **{}** modules encountered an exception while trying to restore its session.'.format(module)
                    warnings.append(w)
                    print(w + '\n\n{}'.format(format_exc()))
                    if not m.runWithoutRestoredSession:
                        continue
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
    TT.botspam = botspam

    loop.run_until_complete(TT.connect())

    for module in TT.modules.values():
        module.stopTracking()

    if TT.restart:
        del TT
    else:
        break