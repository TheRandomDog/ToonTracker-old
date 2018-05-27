from .module import *

class CustomCommandsModule(Module):
    def __init__(self, client):
        Module.__init__(self, client)

        commands = Config.getModuleSetting('custom_commands', 'commands')
        for command in commands:
            if not command.get('name', None):
                print('A command in the custom commands config does not have a name.')
            elif not command.get('response', None):
                print('The {} commad in the custom commands config does not have a response'.format(command['name']))

            class CustomCommand(Command):
                """~{}
                    
                    A custom created command.
                    {}
                """.format(command['name'], command.get('description', ''))
                NAME = str(command['name'])
                RANK = assertType(command.get('rank', 0), int, otherwise=0)
                DELETE_PRIOR_MESSAGE = assertType(command.get('delete_prior_message', False), bool, otherwise=False)
                RESPOND_IN_DM = assertType(command.get('respond_in_dm', False), bool, otherwise=False)

                @classmethod
                async def execute(cls, client, module, message, *args):
                    if cls.RESPOND_IN_DM:
                        await message.author.send(str(command['response']))
                    else:
                        await message.channel.send(str(command['response']))

