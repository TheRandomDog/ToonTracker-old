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

loop = asyncio.get_event_loop()
restarted = False

# Sends Discord events to modules.
def delegate_event(func):
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
        """~quit OR ~exit

            Logs out of the bot account, closes the client, and exits the program.
        """
        NAME = 'quit'
        RANK = 500

        @staticmethod
        async def execute(client, module, message, *args):
            await client.logout()
            await client.close()
    class ExitCMD(QuitCMD):
        NAME = 'exit'

    # Reloads config and modules.
    class ReloadCMD(Command):
        """~reload

            Reloads all modules and the configuration file.
        """
        NAME = 'reload'
        RANK = 300        

        @staticmethod
        async def execute(client, module, message, *args):
            for module in client.modules.values():
                module.stop_tracking()

            client.modules.clear()
            client.to_load = Config.get_setting('load_modules')
            await client.load_config(term='reload', channel=message.channel)

    # Helps.
    class HelpCMD(Command):
        NAME = 'help'

        @staticmethod
        async def execute(client, module, message, *args):
            message.author = client.focused_guild.get_member(message.author.id)
            if not message.author:
                return "You cannot use these commands because you're not in the Toontown Rewritten Discord server."
            rank = max([Config.get_rank_of_user(message.author.id), Config.get_rank_of_role(message.author.top_role.id)])

            embed = Embed(description="Here's a list of available commands I can help with.\nTo get more info, use `~help command`.", color=discord.Color.blurple())
            top_level_commands = []
            for command in sorted(client._commands, key=lambda c: c.NAME):
                if command.RANK <= rank and command.__doc__:
                    if args and args[0].lower() == command.NAME.lower():
                        doc = command.__doc__.split('\n')
                        doc[0] = '`' + doc[0] + '`'
                        doc = '\n'.join([line.strip() for line in doc])
                        return doc
                    top_level_commands.append(client.command_prefix + command.NAME)
            if top_level_commands:
                embed.add_field(name='ToonTracker', value='\n'.join(top_level_commands))

            for module in client.modules.values():
                commands = []
                for command in sorted(module._commands, key=lambda c: c.NAME):
                    if command.RANK <= rank and command.__doc__:
                        if args and args[0].lower() == command.NAME.lower():
                            doc = command.__doc__.split('\n')
                            doc[0] = '`' + doc[0] + '`'
                            doc = '\n'.join([line.strip() for line in doc])
                            return Embed(title=command.__doc__.split('\n')[0].split(' ')[0], description=doc, color=discord.Color.blurple())
                        commands.append(client.command_prefix + command.NAME)
                if commands:
                    embed.add_field(name=module.NAME if hasattr(module, 'NAME') else module.__class__.__name__, value='\n'.join(commands))

            return embed


    def __init__(self):
        super().__init__()

        self.to_load = Config.get_setting('load_modules')
        self.modules = {}

        self._commands = [attr for attr in self.__class__.__dict__.values() if isclass(attr) and issubclass(attr, Command)]
        self.command_prefix = Config.get_setting('command_prefix', '!')

        self.ready = False
        self.ready_to_close = False
        self.restart = False

    def is_module_available(self, module):
        if module in self.modules and self.modules[module].public_module:
            return True

    def request_module(self, module):
        if self.is_module_available(module):
            return self.modules[module]

    async def connect(self):
        try:
            await super().connect()
        except Exception as e:
            print('[!!!] A connection issue occured with Discord. Restarting ToonTracker.')
            self.ready_to_close = True
            self.restart = True
            global restarted
            restarted = True
            await self.close()

    async def close(self):
        self.ready_to_close = True
        await super().close()

    async def on_message(self, message):
        if not self.ready or message.author == self.focused_guild.me:
            return

        for command in self._commands:
            if message.content and message.content.split(' ')[0] == self.command_prefix + command.NAME and \
                    (Config.get_rank_of_user(message.author.id) >= command.RANK or any([Config.get_rank_of_role(role.id) >= command.RANK for role in message.author.roles])):
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
                response = await module._handle_message(message)
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
        await self.send_message(response.target, response.message, response.delete_in, response.prior_message, **response.kwargs)

    async def send_message(self, target, message, delete_in=0, prior_message=None, **kwargs):
        # Recurses for a list of messages.
        if type(message) == list:
            for msg in message:
                await self.send_message(target, msg, delete_in, prior_message, **kwargs)
            return

        # Recurses for a list of targets.
        if type(target) == list:
            for tgt in target:
                await self.send_message(tgt, message, delete_in, prior_message, **kwargs)
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
            msg_obj = await target.send(content='', file=message)
        elif message.__class__ == discord.Embed:
            msg_obj = await target.send(content=None, embed=message)
        else:
            msg_obj = await target.send(message)

        # Delete message (and optional trigger message)
        if delete_in:
            msg_obj.nonce = 'silent'  # Mainly unused Message attribute that we can use, discord.Message implements __slots__
            self.loop.create_task(self.delete_message(msg_obj, delete_in))
            if prior_message:
                prior_message.nonce = 'silent'
                self.loop.create_task(self.delete_message(prior_message, delete_in))

        return msg_obj

    async def delete_message(self, message, delay=0):
        await asyncio.sleep(delay)
        await message.delete()

    @delegate_event
    async def on_private_channel_create(self, channel): pass
    @delegate_event
    async def on_private_channel_delete(self, channel): pass
    @delegate_event
    async def on_private_channel_update(self, before, after): pass
    @delegate_event
    async def on_private_channel_pins_update(self, channel, last_pin): pass
    @delegate_event
    async def on_guild_channel_create(self, channel): pass
    @delegate_event
    async def on_guild_channel_delete(self, channel): pass
    @delegate_event
    async def on_guild_channel_update(self, before, after): pass
    @delegate_event
    async def on_guild_channel_pins_update(self, channel, last_pin): pass
    @delegate_event
    async def on_member_ban(self, guild, user): pass
    @delegate_event
    async def on_member_join(self, member): pass
    @delegate_event
    async def on_member_remove(self, member): pass
    @delegate_event
    async def on_member_update(self, before, after): pass
    @delegate_event
    async def on_message_delete(self, message): pass
    @delegate_event
    async def on_message_edit(self, before, after): pass
    @delegate_event
    async def on_reaction_add(self, reaction, user): pass
    @delegate_event
    async def on_reaction_clear(self, message, reactions): pass
    @delegate_event
    async def on_reaction_remove(self, reaction, user): pass
    @delegate_event
    async def on_guild_available(self, guild): pass
    @delegate_event
    async def on_guild_emojis_update(self, guild, before, after): pass
    @delegate_event
    async def on_guild_join(self, guild): pass
    @delegate_event
    async def on_guild_remove(self, guild): pass
    @delegate_event
    async def on_guild_role_create(self, role): pass
    @delegate_event
    async def on_guild_role_delete(self, role): pass
    @delegate_event
    async def on_guild_unavailable(self, guild): pass
    @delegate_event
    async def on_guild_role_update(self, before, after): pass
    @delegate_event
    async def on_guild_update(self, before, after): pass
    @delegate_event
    async def on_voice_state_update(self, member, before, after): pass

    async def load_config(self, term='start', channel=None):
        if not channel:
            channel = Config.get_setting('bot_output')
            try:
                if type(channel) == list:
                    channel = [int(c) for c in channel]
                else:
                    channel = int(channel)
            except TypeError:
                channel = None

        info = []
        warnings = []
        errors = []

        # Get the guild ID we're participating in.
        focused_guild = Config.get_setting('guild')
        if not focused_guild:
            e = 'No guild ID was designated for participating in in config, or it was malformed.'
            errors.append(e)
            print('[!!!] ' + e)

        # Get the guild object
        self.focused_guild = self.get_guild(focused_guild)
        if not self.focused_guild:
            e = 'No known guild was designated for participating in in config, or it was malformed.'
            errors.append(e)
            print('[!!!] ' + e)

        # Ensure we have marked a bot spam channel
        if not channel:
            e = 'No known channel was designated as the bot output in the config, or it was malformed.'
            errors.append(e)
            print('[!!!] ' + e)

        # If we have errors, output them and quit.
        if errors:
            full = 'ToonTracker failed to {} with **{}** error(s).\n\n'.format(term, len(errors))
            print(full)
            full += '\n'.join([':exclamation: ' + e for e in errors])
            if channel:
                await self.send_message(channel, full)
            await self.logout()
            await self.close()
            return

        # LOADING MODULES

        if self.to_load == None:
            w = '"load_modules" option not found in config'
            warnings.append(w)
            print(w)
            self.to_load = []
        for module in self.to_load:
            assert_type(module, str)

            # Try and load all modules marked in the config.
            # modsmods means "module's module", aka the Python module's ToonTracker module. Very transparent.
            try:
                modsmod = import_module('modules.' + module)
            except ImportError as e:
                # We couldn't import the Python file at all.
                w = 'Could not **import** Python module of ToonTracker module "{}"'.format(module)
                warnings.append(w)
                print(w + '\n\n{}'.format(format_exc()))
                continue
            except Exception as e:
                # There was an exception when loading the Python file.
                w = 'Could not **load** Python module of ToonTracker module "{}"'.format(module)
                warnings.append(w)
                print(w + '\n\n{}'.format(format_exc()))
                continue
            if not hasattr(modsmod, 'module'):
                # The actual module subclass (subclassed from Module) wasn't marked with the global variable `module`.
                w = 'Could not locate module subclass for "{}"'.format(module)
                warnings.append(w)
                print(w)
                continue
            if hasattr(modsmod, 'messages'):
                # Any information or warnings the modules had while starting up will be added here.
                for message in modsmod.messages:
                    if message.__class__ == Info:
                        info.append('**{} module:**'.format(module) + str(message))
                    elif message.__class__ == Warning:
                        warnings.append('**{} module:** '.format(module) + str(message))
            try:
                m = modsmod.module(self)
            except Exception as e:
                # An exception occurred when the module subclass was initialized.
                w = 'Could not load module subclass for "{}"'.format(module)
                warnings.append(w)
                print(w + '\n\n{}'.format(format_exc()))
                continue

            # Everything went okay... add it to our modules list!
            self.modules[module] = m
            # Some modules may want to restore their session, let 'em do it now.
            if hasattr(m, 'restore_session'):
                try:
                    await m.restore_session()
                except Exception as e:
                    w = 'The **{}** modules encountered an exception while trying to restore its session.'.format(module)
                    warnings.append(w)
                    print(w + '\n\n{}'.format(format_exc()))
                    if not m.run_without_restored_session:
                        continue
            # Start their loop iterations!
            m.start_tracking()

        # Final startup message. Will display warnings. Might display info soon.
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


token = Config.get_setting('token')
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

    botspam = Config.get_setting('bot_output')
    TT.botspam = botspam

    loop.run_until_complete(TT.connect())

    for module in TT.modules.values():
        module.stop_tracking()

    if TT.restart:
        del TT
    else:
        break
