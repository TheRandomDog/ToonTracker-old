# -*- coding: utf-8 -*-

import discord
import re

from modules.module import Module
from extra.commands import Command
from utils import Config

COMMAND_ADDED = "{} has been added as a custom command! 👍"
COMMAND_REMOVED = "{} has been removed! 👍"
COMMAND_UPDATED = "{} has been updated! 👍"
COMMAND_EXISTS = "🛑 That command already exists! 🛑"
COMMAND_DOESNT_EXIST = "🛑 That command doesn't exist! 🛑"
PREFIX_UPDATED = "Prefix updated! 👍"
CHANNEL_TOGGLED = "Custom Commands are now **{}** in this channel!"

class CustomCommandModule(Module):

    class AddCustomCommand(Command):
        NAME = 'addCustomCommand'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            if not args[0]:
                return
            command = args[0].lower()
            reply = re.sub("(?i)" + command + " ", "", ' '.join(args).strip())
            if not command or not reply:
                return
            commands = Config.getModuleSetting('customcommands', 'commands')
            if command in commands:
                return COMMAND_EXISTS
            commands[command] = reply
            Config.setModuleSetting('customcommands', 'commands', commands)
            return COMMAND_ADDED.format(command)

    class RemoveCustomCommand(Command):
        NAME = 'removeCustomCommand'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            if not args[0]:
                return
            command = args[0].lower()
            commands = Config.getModuleSetting('customcommands', 'commands')
            if not command in commands:
                return COMMAND_DOESNT_EXIST
            del commands[command]
            Config.setModuleSetting('customcommands', 'commands', commands)
            return COMMAND_REMOVED.format(command)

    class EditCustomCommand(Command):
        NAME = 'editCustomCommand'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            if not args[0]:
                return
            command = args[0].lower()
            reply = re.sub("(?i)" + command + " ", "", ' '.join(args).strip())
            if not command or not reply:
                return
            commands = Config.getModuleSetting('customcommands', 'commands')
            if not command in commands:
                return COMMAND_DOESNT_EXIST
            commands[command] = reply
            Config.setModuleSetting('customcommands', 'commands', commands)
            return COMMAND_UPDATED.format(command)

    class CustomCommandPrefix(Command):
        NAME = 'customCommandPrefix'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            if not args[0]:
                return
            Config.setModuleSetting('customcommands', 'prefix', args[0])
            return PREFIX_UPDATED

    class ToggleCustomCommands(Command):
        NAME = 'toggleCustomCommands'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            channels = Config.getModuleSetting('customcommands', 'channels')
            if not str(message.channel.id) in channels:
                channels.append(str(message.channel.id))
                Config.setModuleSetting('customcommands', 'channels', channels)
                return CHANNEL_TOGGLED.format("enabled")
            else:
                channels.remove(str(message.channel.id))
                Config.setModuleSetting('customcommands', 'channels', channels)
                return CHANNEL_TOGGLED.format("disabled")

    async def on_message(self, message):
        prefix = Config.getModuleSetting('customcommands', 'prefix')
        channels = Config.getModuleSetting('customcommands', 'channels')
        if not str(message.channel.id) in channels:
            return
        commands = Config.getModuleSetting('customcommands', 'commands')
        for command, reply in commands.items():
            if message.content.lower().startswith(prefix + command):
                return reply

module = CustomCommandModule
