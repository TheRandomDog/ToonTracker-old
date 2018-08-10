from .module import *
from discord import Embed, Color

class CustomCommandsModule(Module):
    class AddCMD(Command):
        """~addCommand <commandName> [response]
        
        Adds an empty command to the custom command list.
        If a response is specified, it'll be added as a "reply" action.
        """
        NAME = 'addCommand'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            if not args:
                return module.createDiscordEmbed(subtitle='Please reference the command name.', color=Color.red())
            command_name = args[0]
            command_reply = ' '.join(args[1:])
            for command in module.commands:
                if command['name'] == command_name:
                    return module.createDiscordEmbed(subtitle='The command **{}** already exists.'.format(command_name), color=Color.red())

            command = {'name': command_name}
            if command_reply:
                command['actions'] = [
                    {
                        'action': 'Reply',
                        'content': command_reply
                    }
                ]
            else:
                command['actions'] = []
            module.commands.append(command)
            Config.setModuleSetting('custom_commands', 'commands', module.commands)
            module.load_command(command)
            return module.createDiscordEmbed(subtitle='Created the **{}** command.'.format(command_name), footer='Available Commands: ~removeCommand | ~viewCommand | ~editCommand', color=Color.green())

    class RemoveCMD(Command):
        """~removeCommand <commandName>

        Removes a command from the custom command list.
        """
        NAME = 'removeCommand'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            if not args:
                return module.createDiscordEmbed(subtitle='Please reference the command name.', color=Color.red())
            command_name = args[0]
            for command in module.commands:
                if command['name'] == command_name:
                    module.commands.remove(command)
                    Config.setModuleSetting('custom_commands', 'commands', module.commands)
                    return module.createDiscordEmbed(subtitle='Removed the **{}** command.'.format(command_name), color=Color.green())
            return module.createDiscordEmbed(subtitle='The command **{}** does not exist.'.format(command_name), color=Color.red())

    class ViewCMD(Command):
        """~viewCommand <commandName>

        Views the documentation and actions of a command.
        """
        NAME = 'viewCommand'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            if not args:
                return module.createDiscordEmbed(subtitle='Please reference the command name.', color=Color.red())
            command_name = args[0]
            command_index = None
            for c in module.commands:
                if c['name'] == command_name:
                    command_index = module.commands.index(c)
            if command_index is None:
                return module.createDiscordEmbed(subtitle='The command **{}** does not exist.'.format(command_name), color=Color.red())
            return module.visualize_command(module.commands[command_index])

    class ListCMDs(Command):
        """~listCommands

        Lists all the custom commands and their documentation.
        """
        NAME = 'listCommands'

        @classmethod
        async def execute(cls, client, module, message, *args):
            return Embed(
                title='Custom Commands',
                description='\n'.join(['**{}**{}{}'.format('~' + command['name'] + '\n', command.get('description', ''), '\n' if command.get('description', '') else '') for command in module.commands]),
                color=Color.from_rgb(114, 198, 255)
            ).set_footer(text='Available Commands: ~addCommand | ~removeCommand | ~viewCommand | ~editCommand')

    class EditCMD(Command):
        """~editCommand <commandName> <part> [...]

        Edits a command. Here are some examples:
        `~editCommand ping name pong` - Changes a command name from `ping` to `pong`
        `~editCommand ping description Send pong.` - Changes a command descripton to `Send pong.`
        `~editCommand ping action add reply` - Adds a command action to ~ping that replies to the user.
        `~editCommand ping action add send #channel` - Adds a command action to ~ping that sends a message to #channel.
        `~editCommand ping action 1 dm true` - Tells the first action (a reply action) to send the reply to a DM.
        `~editCommand ping action 2 channel #channeltwo` - Tells the second action (a send action) to go to #channeltwo instead.
        `~editCommand ping action 1 content Pong!` - Changes the reply of the first action to `Pong!`.
        `~editCommand ping action 2 delete` - Deletes the second action.
        """
        NAME = 'editCommand'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            if not args:
                return module.createDiscordEmbed(subtitle='Please reference the command name.', color=Color.red())
            command_name = args[0]
            command_index = None
            for c in module.commands:
                if c['name'] == command_name:
                    command_index = module.commands.index(c)
            if command_index is None:
                return module.createDiscordEmbed(subtitle='The command **{}** does not exist.'.format(command_name), color=Color.red())

            if len(args) < 2:
                return module.createDiscordEmbed(subtitle='Please reference the part of the command to edit.', footer='Available Parts: name | description | action', color=Color.red())
            part = args[1]
            if part == 'name':
                if len(args) < 3:
                    return module.createDiscordEmbed(subtitle='Please provide the new name for the command.', color=Color.red())
                new_name = args[2]
                for c in module.commands:
                    if c['name'] == new_name:
                        return module.createDiscordEmbed(subtitle='The command **{}** already exists.'.format(new_name), color=Color.red())
                module.commands[command_index]['name'] = new_name
            elif part == 'description':
                desc = ' '.join(args[2:])
                module.commands[command_index]['description'] = desc
            elif part == 'action':
                if len(args) < 3:
                    return module.createDiscordEmbed(subtitle='Please edit an action by referring to its number or using `add`.', color=Color.red())
                action_context = args[2]
                if action_context.isdigit():
                    action_context = int(action_context)
                    if not (0 < action_context <= len(module.commands[command_index]['actions'])):
                        return module.createDiscordEmbed(subtitle='Please choose a number that represents an action.', color=Color.red())
                    if len(args) < 4:
                        return module.createDiscordEmbed(subtitle='Please refer what part you\'d like to modify of this action.', footer='Available Parts: dm | channel | content | delete', color=Color.red())
                    action_part = args[3]
                    if action_part == 'delete':
                        module.commands[command_index]['actions'].pop(action_context - 1)
                    elif action_part == 'content':
                        module.commands[command_index]['actions'][action_context - 1]['content'] = ' '.join(args[4:])
                    elif module.commands[command_index]['actions'][action_context - 1]['action'] == 'Reply' and action_part == 'dm':
                        if len(args) < 5:
                            return module.createDiscordEmbed(subtitle='Please use **true** / **false** if you\'d like the response to this command to be sent in a DM.', color=Color.red())
                        elif args[4].lower() in ['yes', 'true', '1']:
                            module.commands[command_index]['actions'][action_context - 1]['dm'] = True
                        elif args[4].lower() in ['no', 'false', '0']:
                            module.commands[command_index]['actions'][action_context - 1]['dm'] = False
                        else:
                            return module.createDiscordEmbed(subtitle='Please use **true** / **false** if you\'d like the response to this command to be sent in a DM.', color=Color.red())
                    elif module.commands[command_index]['actions'][action_context - 1]['action'] == 'Send' and action_part == 'channel':
                        if not message.channel_mentions:
                            return module.createDiscordEmbed(subtitle='Please use a channel mention to refer to a channel.', color=Color.red())
                        else:
                            module.commands[command_index]['actions'][action_context - 1]['channel'] = message.channel_mentions[0].id
                    else:
                        return module.createDiscordEmbed(subtitle='Unknown action part: **{}**'.format(action_part), footer='Available Parts: dm | channel | content | delete', color=Color.red())
                elif action_context == 'add':
                    if len(args) < 4:
                        return module.createDiscordEmbed(subtitle='Please mention what type of action you\'d like to add.', footer='Available Actions: Reply | Send', color=Color.red())
                    action_type = args[3]
                    if action_type.lower() == 'reply':
                        module.commands[command_index]['actions'].append({'action': 'Reply', 'content': ' '.join(args[4:])})
                    elif action_type.lower() == 'send':
                        if not message.channel_mentions:
                            return module.createDiscordEmbed(subtitle='Please use a channel mention to refer to the channel this action should be sent to.', color=Color.red())
                        else:
                            module.commands[command_index]['actions'].append({'action': 'Send', 'channel': message.channel_mentions[0].id, 'content': ' '.join(args[5:])})
                    else:
                        return module.createDiscordEmbed(subtitle='Unknown action: **{}**'.format(action_type), footer='Available Actions: reply | send', color=Color.red())
                else:
                    return module.createDiscordEmbed(subtitle='Please edit an action by referring to its number or using `add`.', color=Color.red())
            else:
                return module.createDiscordEmbed(subtitle='Invalid part: **{}**'.format(part), footer='Available Parts: name | description | action', color=Color.red())
            Config.setModuleSetting('custom_commands', 'commands', module.commands)
            module.__init__(module.client)
            return module.visualize_command(module.commands[command_index])

    def __init__(self, client):
        Module.__init__(self, client)

        self.commands = Config.getModuleSetting('custom_commands', 'commands')
        for command in self.commands:
            if not command.get('name', None):
                print('A command in the custom commands config does not have a name.')
            elif not command.get('actions', []):
                print('The {} commad in the custom commands config does not have any associated actions.'.format(command['name']))
            else:
                self.load_command(command)

    def load_command(self, command):
        class CustomCommand(Command):
            NAME = str(command['name'])
            RANK = assertType(command.get('rank', 0), int, otherwise=0)

            @classmethod
            async def execute(cls, client, module, message, *args):
                for action in command['actions']:
                    if action['action'] == 'Reply':
                        if action.get('dm', False):
                            await message.author.send(action['content'])
                        else:
                            await message.channel.send(action['content'])
                    elif action['action'] == 'Send':
                        await client.get_channel(action['channel']).send(action['content'])
        CustomCommand.__doc__ = """~{}
            
            A custom created command.
            {}
        """.format(command['name'], command.get('description', ''))

        # Hack it in!
        self._commands.append(CustomCommand)

    def visualize_command(self, command):
        embed = Embed(title=self.client.commandPrefix + command['name'], description=command.get('description', Embed.Empty), color=Color.from_rgb(114, 198, 255))
        actions = 0
        for action in command['actions']:
            actions += 1
            embed.add_field(
                name='Action {} - {}'.format(actions, action['action']),
                value='{}\n{}'.format(
                    '**[Channel: {}]**'.format(self.client.get_channel(action['channel']).mention) if action['action'] == 'Send' else '**[Send to DMs: {}]**'.format(action.get('dm', False)),
                    action['content']
                )
            )
        return embed

module = CustomCommandsModule