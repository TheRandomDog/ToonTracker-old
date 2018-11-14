import discord
from modules.module import Module
from extra.commands import Command
from utils import Config, assert_type

class NotifyMeModule(Module):
    NAME = 'Notify Me'
    
    class NotifyMeCMD(Command):
        """~notifyMe <role name>

            This will give you the specified role allowing you to receive notifications for only what you want to hear.
        """
        NAME = 'notifyMe'

        @staticmethod
        async def execute(client, module, message, *args):
            if not type(message.channel) == discord.DMChannel and message.channel.id != module.interaction:
                return
            message.author = client.focused_guild.get_member(message.author.id)
            if not message.author:
                return "You cannot use these commands because you're not in the Toontown Rewritten Discord server."

            if not args:
                return 'You need to give me a role name to notify you for.'

            role = None
            for possible_role in module.available_roles:
                if args[0].lower() == possible_role.lower():
                    role = module.available_roles[possible_role]

            if not role:
                return "I don't know of a role named `{}`. You may have typo'd it or it may have been removed.".format(args[0])
            elif role[0] in message.author.roles:
                return "You've already got the `{}` role, you're good to go!".format(role[0].name)

            await message.author.add_roles(role[0], reason='Added by user via ~notifyMe')
            return "Got it, you've been signed up for {}notifications for `{}`! :thumbsup:".format((role[1] + ' ') if role[1] else '', role[0].name)

    class StopNotifyingMeCMD(Command):
        """~stopNotifyingMe <role name>

            This removes the specified role and you will not receive any more notifications about it.
        """
        NAME = 'stopNotifyingMe'

        @staticmethod
        async def execute(client, module, message, *args):
            if not type(message.channel) == discord.DMChannel and message.channel.id != module.interaction:
                return
            message.author = client.focused_guild.get_member(message.author.id)
            if not message.author:
                return "You cannot use these commands because you're not in the Toontown Rewritten Discord server."

            if not args:
                return "You need to give me the role name of the notifications you'd like to cancel."

            role = None
            for possible_role in module.available_roles:
                if args[0].lower() == possible_role.lower():
                    role = module.available_roles[possible_role]

            if not role:
                return "I don't know of a role named `{}`. You may have typo'd it or it may have been removed.".format(args[0])
            elif role[0] not in message.author.roles:
                return "You don't have the role `{}`, you're all good.".format(role[0].name)

            await message.author.remove_roles(role[0], reason='Removed by user via ~stopNotifyingMe')
            return "Got it, you won't receive any more notifications for `{}`.".format(role[0].name)

    class NotificationCreationCMD(Command):
        """~createNotificationRole [notification type (automatic | manual)] <role name>

            Makes a role that can be self-assigned by users. If a role with the same name exists, it will be used instead.
            You can clarify to users whether the notifications will be automatic (by a bot) or manual (done by moderators, whenever). Events will generally be manual.
        """
        NAME = 'createNotificationRole'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            if not args:
                return 'You need to give me a role name that I can use to create/modify for notification purposes.'

            if args[0] in ['automatic', 'manual']:
                notification_type = args[0]
                role_name = ' '.join(args[1:])
            else:
                notification_type = None
                role_name = ' '.join(args)

            role = None
            made_role = True
            for possible_role in client.focused_guild.roles:
                if role_name.lower() == possible_role.name.lower():
                    role = possible_role
                    made_role = False

            config_roles = Config.get_module_setting('notifyMe', 'roles')
            if not role:
                role = await client.focused_guild.create_role(reason='Created by moderator via ~makeNotificationRole', name=role_name, mentionable=True,)
            config_roles[role.name] = [role.id, notification_type]
            Config.set_module_setting('notifyMe', 'roles', config_roles)
            module.refresh_available_roles()

            response_supplement = (" It's notification type is " + notification_type + ".") if notification_type else ''
            if made_role:
                return 'Created the new `{}` role!{}'.format(role_name, response_supplement)
            return 'Made the pre-existing `{}` role self-assignable by users.{}'.format(role.name, response_supplement)

    class NotificationStopCMD(Command):
        """~stopNotificationRole <role name>

            Makes a role no longer self-assignable by users, but does not delete the role from the server nor clears the role already assigned to users.
        """
        NAME = 'stopNotificationRole'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            if not args:
                return 'You need to give me a role name that I can make no longer self-assignable.'
            role_name = ' '.join(args)

            role = None
            for possible_role in client.focused_guild.roles:
                if role_name.lower() == possible_role.name.lower():
                    role = possible_role
                    config_roles = Config.get_module_setting('notifyMe', 'roles')
                    if role.name not in config_roles:
                        return 'The `{}` role was already not self-assignable.'.format(role.name)
                    del config_roles[role.name]
                    Config.set_module_setting('notifyMe', 'roles', config_roles)
                    module.refresh_available_roles()
                    return 'Made the `{}` role no longer self-assignable by users.'.format(role.name)

            # No matching role
            return "I don't know of a role named `{}`. You may have typo'd it or it may have been removed.".format(role_name)

    class NotificationRemovalCMD(Command):
        """~removeNotificationRole <role name>

            Makes a role no longer self-assignable by users and removes it from users who currently have it, but does not delete the role from the server.
        """
        NAME = 'removeNotificationRole'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            if not args:
                return 'You need to give me a role name so that I can make no longer self-assignable and remove from users.'
            role_name = ' '.join(args)

            role = None
            for possible_role in client.focused_guild.roles:
                if role_name.lower() == possible_role.name.lower():
                    role = possible_role
                    async with message.channel.typing():
                        for member in client.focused_guild.members:
                            if role in member.roles:
                                await member.remove_roles(role, reason='Removed by moderator via ~removeNotificationRole')

                    config_roles = Config.get_module_setting('notifyMe', 'roles')
                    if role.name not in config_roles:
                        return 'The `{}` role was already not self-assignable. It was cleared from users who had it.'.format(role.name)
                    del config_roles[role.name]
                    Config.set_module_setting('notifyMe', 'roles', config_roles)
                    module.refresh_available_roles()
                    return 'Made the `{}` role no longer self-assignable by users, and cleared it from users who had it.'.format(role.name)

            # No matching role
            return "I don't know of a role named `{}`. You may have typo'd it or it may have been removed.".format(role_name)

    class NotificationDeletionCMD(Command):
        """~deleteNotificationRole <role name>

            Makes a role no longer self-assignable by users and deletes the role from the server.
        """
        NAME = 'deleteNotificationRole'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            if not args:
                return 'You need to give me a role name so that I can delete the role from the server.'
            role_name = ' '.join(args)

            role = None
            for possible_role in client.focused_guild.roles:
                if role_name.lower() == possible_role.name.lower():
                    role = possible_role
                    await role.delete(reason='Deleted by moderator via ~deleteNotificationRole')

                    config_roles = Config.get_module_setting('notifyMe', 'roles')
                    if role.name not in config_roles:
                        return 'The `{}` role was already not self-assignable. It was deleted from the server.'.format(role.name)
                    del config_roles[role.name]
                    Config.set_module_setting('notifyMe', 'roles', config_roles)
                    module.refresh_available_roles()
                    return 'Made the `{}` role no longer self-assignable by users and deleted it.'.format(role.name)

            # No matching role
            return "I don't know of a role named `{}`. You may have typo'd it or it may have been removed.".format(role_name)


    def __init__(self, client):
        Module.__init__(self, client)

        self.interaction = Config.get_module_setting('notifyMe', 'interaction')

        self.available_roles = {}
        self.refresh_available_roles()

    def refresh_available_roles(self):
        self.available_roles = assert_type(Config.get_module_setting('notifyMe', 'roles'), dict, otherwise={})
        for role, data in self.available_roles.items():
            if not assert_type(data[0], int, otherwise=None):
                del self.available_roles[role]

            role_object = discord.utils.get(self.client.focused_guild.roles, id=data[0])
            if not role_object:
                del self.available_roles[role]

            self.available_roles[role] = (role_object, data[1])

module = NotifyMeModule