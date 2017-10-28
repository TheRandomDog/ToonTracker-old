import sys
import time
import praw
import threading
from discord import Color
from modules.module import Module, Announcer
from traceback import format_exception, format_exc
from utils import Config, assertTypeOrOtherwise

class NotifyMeModule(Module):
    NOT_SPECIFIED = ""
    MANUAL = "manual "
    AUTOMATIC = "automatic "

    class NotifyMeCMD(Command):
        """~notifyMe <role>

            This will give you the specified <role> allowing you to receive notifications for only what you want to hear.
        """
        NAME = 'notifyMe'

        @staticmethod
        async def execute(client, module, message, *args):
            role = None
            for possibleRole in self.availableRoles:
                if args[0].lower() == possibleRole.lower():
                    role = self.avilableRoles[possibleRole]

            if not role:
                return "I don't know of a role named `{}`. You may have typo'd it or it may have been removed.".format(args[0])

            await message.author.add_roles(role[0], reason='Added via ~notifyMe')
            return "Got it, you've been signed up for {}notifications for `{}`".format(role[1], args[0])

    class StopNotifyingMeCMD(Command):
        """~stopNotifyingMe <role>

            This removes the specified <role> and you will not receive any more notifications about it.
        """
        NAME = 'stopNotifyingMe'

        @staticmethod
        async def execute(client, module, message, *args):
            role = None
            for possibleRole in self.availableRoles:
                if args[0].lower() == possibleRole.lower():
                    role = self.avilableRoles[possibleRole]

            if not role:
                return "I don't know of a role named `{}`. You may have typo'd it or it may have been removed.".format(args[0])
            elif role[0] not in message.author.roles:
                return "You don't have the role `{}`. You may have typo'd it or it may have been removed.".format(args[0])

            await message.author.remove_roles(role[0], reason='Removed via ~stopNotifyingMe')
            return "Got it, you won't receive any more notifications for `{}`".format(args[0])

    class NotificationCreationCMD(Command):
        """~makeNotificationRole [notification type (automatic | manual)] <role name>

            Makes a role that can be self-assigned by users. If a role with the same name exists, it will be used instead.
            You can clarify to users whether the notifications will be automatic (by a bot) or manual (done by moderators, whenever). Events will generally be manual.
        """
        NAME = 'makeNotificationRole'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            if args[0] in ['automatic', 'manual']:
                notificationType = args[0]
                roleName = ' '.join(args[1:])
            else:
                notificationType = None
                roleName = ' '.join(args)

            role = None
            madeRole = True
            for possibleRole in client.rTTR.roles:
                if roleName.lower() == possibleRole.lower():
                    role = possibleRole
                    madeRole = False

            configRoles = Config.getModuleSetting('notifyMe', 'roles')
            if not role:
                role = await client.rTTR.create_role(name=roleName, mentionable=True)
            configRoles[roleName] = [role.id, notificationType]
            Config.setModuleSetting('notifyMe', 'roles', configRoles)
            self.refreshAvailableRoles()

            if madeRole:
                return 'Created the new `{}` role!{}'.format(roleName, (" It's notification type is " + notificationType) if notificationType else '')
            return 'Made the pre-existing `{}` role self-assignable by users.'.format(role.name)

    class NotificationStopCMD(Command):
        """~removeNotificationRole <role name>

            Makes a role no longer self-assignable by users, but does not delete the role from the server nor clears the role already assigned to users.
        """
        NAME = 'stopNotificationRole'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            roleName = ' '.join(args)

            role = None
            for possibleRole in client.rTTR.roles:
                if roleName.lower() == possibleRole.lower():
                    role = possibleRole
                    configRoles = Config.getModuleSetting('notifyMe', 'roles')
                    if role.name not in configRoles:
                        return 'The `{}` role was already not self-assignable.'.format(role.name)
                    del configRoles[roleName]
                    Config.setModuleSetting('notifyMe', 'roles', configRoles)
                    self.refreshAvailableRoles()
                    return 'Made the `{}` role no longer self-assignable by users.'.format(role.name)

            # No matching role
            return "I don't know of a role named `{}`. You may have typo'd it or it may have been removed.".format(roleName)

    class NotificationRemovalCMD(Command):
        """~removeNotificationRole <role name>

            Makes a role no longer self-assignable by users and removes it from users who currently have it, but does not delete the role from the server.
        """
        NAME = 'removeNotificationRole'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            roleName = ' '.join(args)

            role = None
            for possibleRole in client.rTTR.roles:
                if roleName.lower() == possibleRole.lower():
                    role = possibleRole
                    for member in client.rTTR.members:
                        if role in member.roles:
                            await member.remove_roles(role, reason='Removed by moderator via ~removeNotificationRole')

                    configRoles = Config.getModuleSetting('notifyMe', 'roles')
                    if role.name not in configRoles:
                        return 'The `{}` role was already not self-assignable. It was cleared from users who had it.'.format(role.name)
                    del configRoles[roleName]
                    Config.setModuleSetting('notifyMe', 'roles', configRoles)
                    self.refreshAvailableRoles()
                    return 'Made the `{}` role no longer self-assignable by users, and cleared it from users who had it.'.format(role.name)

            # No matching role
            return "I don't know of a role named `{}`. You may have typo'd it or it may have been removed.".format(roleName)

    class NotificationDeletionCMD(Command):
        """~deleteNotificationRole <role name>

            Makes a role no longer self-assignable by users and deletes the role from the server.
        """
        NAME = 'deleteNotificationRole'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            roleName = ' '.join(args)

            role = None
            for possibleRole in client.rTTR.roles:
                if roleName.lower() == possibleRole.lower():
                    role = possibleRole
                    await role.delete(reason='Deleted by moderator via ~deleteNotificationRole')

                    configRoles = Config.getModuleSetting('notifyMe', 'roles')
                    if role.name not in configRoles:
                        return 'The `{}` role was already not self-assignable. It was deleted from the server.'.format(role.name)
                    del configRoles[roleName]
                    Config.setModuleSetting('notifyMe', 'roles', configRoles)
                    self.refreshAvailableRoles()
                    return 'Made the `{}` role no longer self-assignable by users and deleted it.'.format(role.name)

            # No matching role
            return "I don't know of a role named `{}`. You may have typo'd it or it may have been removed.".format(roleName)


    def __init__(self, client):
        Module.__init__(self, client)

        self.availableRoles = {}
        self.refreshAvailableRoles()

    def refreshAvailableRoles(self):
        self.availableRoles = assertTypeOrOtherwise(Config.getModuleSetting('notifyMe', 'roles'), dict, {})
        for role, data in self.availableRoles.items():
            if not assertTypeOrOtherwise(data.get('id', None), int, None):
                del self.availableRoles[role]

            roleObject = discord.utils.get(self.client.rTTR.roles, id=data['id'])
            if not roleObject:
                del self.availableRoles[role]

            self.availableRoles[role] = (roleObject, data.get('notificationType', None))

module = NotifyMeModule