import discord
import time
from extra.commands import Command
from modules.module import Module
from utils import Config, assertTypeOrOtherwise, getTimeFromSeconds

class Lobby:
    def __init__(self):
        self.id = None
        self.category = None
        self.textChannel = None
        self.voiceChannel = None
        self.role = None
        self.ownerRole = None
        self.created = time.mktime(time.gmtime())
        self.customName = ""
        self.invited = []
        self.visited = None
        self.expiryWarning = None

async def createLobby(client, module, message, *args, textChannelOnly=False, voiceChannelOnly=False):
    if message.channel.id != module.channelID:
        return

    lobby = getUsersLobby(module, message.author)
    ownsLobby = lobby.ownerRole in message.author.roles
    auditLogReason = 'Lobby created by {}'.format(str(message.author))

    if ownsLobby:
        return '{} You own a lobby right now. You\'ll have to `~disbandLobby` to create a new one.'.format(message.author.mention)
    elif lobby:
        return '{} You are in a lobby right now. You\'ll have to `~leaveLobby` to create a new one.'.format(message.author.mention)

    moderation = client.requestModule('moderation')

    name = ' '.join(args)
    if moderation:
        try:
            filterActivated = await moderation.filterBadWords(message)
            if filterActivated:
                return
        except discord.errors.NotFound:
            # If a Not Found error returned, that means that it tried to remove something
            # that contained a bad word, meaning we're safe to stop making the lobby.
            return
    elif len(name) > 30:
        return '{} Your lobby name must be 30 characters or less.'.format(message.author.mention)
    elif not name:
        return '{} Give your lobby a name!'.format(message.author.mention)

    category = await client.rTTR.create_category(name='Lobby [{}]'.format(name), reason=auditLogReason)

    lobby = Lobby()
    lobby.category = category
    lobby.customName = name
    lobby.id = category.id
    module.activeLobbies[lobby.id] = lobby

    lobby.ownerRole = await client.rTTR.create_role(
        name='lobby-{}-owner'.format(lobby.id),
        reason=auditLogReason
    )
    lobby.role = await client.rTTR.create_role(
        name='lobby-{}'.format(lobby.id),
        reason=auditLogReason
    )
    await message.author.add_roles(lobby.ownerRole, reason=auditLogReason)

    discordModRole = discord.utils.get(client.rTTR.roles, name='Discord Mods')
    await category.set_permissions(client.rTTR.default_role, read_messages=False)
    await category.set_permissions(lobby.ownerRole, read_messages=True)
    await category.set_permissions(lobby.role, read_messages=True)
    await category.set_permissions(discordModRole, read_messages=True, send_messages=False)

    if not voiceChannelOnly:
        lobby.textChannel = await client.rTTR.create_text_channel(
            name="text-lobby",
            category=lobby.category,
            reason=auditLogReason
        )
    if not textChannelOnly:
        lobby.voiceChannel = await client.rTTR.create_voice_channel(
            name='Voice Lobby',
            category=lobby.category,
            reason=auditLogReason
        )

    return '{} Your lobby has been created!'.format(message.author.mention)

def getLobbyByID(module, id):
    for lobby in module.activeLobbies.values():
        if lobby.id == id:
            return lobby

def getUsersLobby(module, member):
    assert member.__class__ == discord.Member
    lobbyRole = discord.utils.find(lambda r: 'lobby-' in r.name, member.roles)
    for lobby in module.activeLobbies.values():
        if lobbyRole in (lobby.role, lobby.ownerRole):
            return lobby

def getOwnersLobby(module, member):
    assert member.__class__ == discord.Member
    lobbyRole = discord.utils.find(lambda r: 'lobby-' in r.name, member.roles)
    for lobby in module.activeLobbies.values():
        if lobbyRole == lobby.ownerRole:
            return lobby

class LobbyManagement(Module):
    class CreateLobbyCMD(Command):
        """~createLobby <lobby name>

            This will create you a lobby with a text channel and a voice channel.
            You can also choose to have a lobby with only one of those two by doing:
                `~createTextLobby`
                `~createVoiceLobby`
        """
        NAME = 'createLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            return await createLobby(client, module, message, *args)
    class CreateLobbyCMD_Variant1(CreateLobbyCMD): NAME = 'createlobby'

    class CreateTextLobbyCMD(Command):
        NAME = 'createTextLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            return await createLobby(client, module, message, *args, textChannelOnly=True)
    class CreateTextLobbyCMD_Variant1(CreateTextLobbyCMD): NAME = 'createtextlobby'

    class CreateVoiceLobbyCMD(Command):
        NAME = 'createVoiceLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            return await createLobby(client, module, message, *args, voiceChannelOnly=True)
    class CreateVoiceLobbyCMD_Variant1(CreateVoiceLobbyCMD): NAME = 'createvoicelobby'

    class LobbyInviteCMD(Command):
        """~inviteToLobby <mention>

            This will send a DM to another user asking them to join your lobby.
            If they accept, they'll be able to see and chat within your lobby.
        """
        NAME = 'inviteToLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            if not message.channel.category or not message.channel.category.name.startswith('Lobby'):
                return

            lobby = getUsersLobby(module, message.author)

            if not lobby:
                return '{} You\'re not in a lobby yourself -- create a lobby before you invite users.'.format(message.author.mention)
            elif not message.mentions:
                return '{} I need a mention of the user you want to invite to your lobby.'.format(message.author.mention)

            failedMessages = []
            failedBot = []
            failedPendingInvite = []
            for user in message.mentions:
                if user.bot:
                    failedBot.append(user.mention)
                    continue

                if user.id in lobby.invited:
                    failedPendingInvite.append(user.mention)
                    continue

                try:
                    lobby.invited.append(user.id)
                    await user.send("Hey there, {}! {} has invited you to join their private lobby on the Toontown Rewritten Discord. " \
                        "\n\nTo accept, {}copy & paste `~acceptLobbyInvite {}`. If you're not interested, you can ignore this message.".format(
                            user.mention,
                            message.author.mention,
                            'first leave your current lobby with `~leaveLobby` *(or `~disbandLobby` if you created the lobby)* and then ' \
                            if getUsersLobby(module, user) else '',
                            lobby.id
                        )
                    )
                except discord.HTTPException as e:
                    failedMessages.append(user.mention)
            if failedMessages:
                return '{} Could not send out messages to {} {} *({})*... the channel is still open for them if they use `~acceptLobbyInvite {}`. {}But otherwise, invites sent!'.format(
                    message.author.mention,
                    len(failedMessages + failedBot),
                    'person' if len(failedMessages + failedBot) == 1 else 'people',
                    ', '.join(failedMessages) + (' and [uninvitable] bots' if failedBot else ''),
                    lobby.id,
                    'Also, you\'ve already sent an invite that\'s pending to {} of the mentioned users. '.format(len(failedPendingInvite)) if failedPendingInvite else ''
                )
            elif len(failedBot) == len(message.mentions):
                return '{} Could not invite any mentioned users, because all mentioned users were bots.'.format(message.author.mention)
            elif failedBot:
                return '{} Could not invite some users because they were bots. {}But otherwise, invites sent!'.format(
                    message.author.mention,
                    'Also, you\'ve already sent an invite that\'s pending to {} of the mentioned users. '.format(len(failedPendingInvite)) if failedPendingInvite else ''
                )
            elif len(failedPendingInvite) == len(message.mentions):
                return '{} You\'ve already sent pending invites to the mentioned users.'.format(message.author.mention)
            elif failedPendingInvite:
                return '{} You\'ve already sent an invite that\'s pending to {} of the mentioned users. But otherwise, invites sent!'.format(
                    message.author.mention,
                    len(failedPendingInvite)
                )
            else:
                return '{} Invite{} sent!'.format(message.author.mention, 's' if len(message.mentions) > 1 else '')
    class LobbyInviteCMD_Variant1(LobbyInviteCMD): NAME = 'invitetolobby'

    class LobbyInviteAcceptCMD(Command):
        """~acceptLobbyInvite

            This allows you to accept an invite to a lobby from another user.
            Once you accept, you'll be able to see and chat within their lobby.
        """
        NAME = 'acceptLobbyInvite'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.__class__ != discord.DMChannel and message.channel.id != module.channelID:
                return

            if args[0] not in module.activeLobbies:
                return "{} Sorry, but I didn't recognize that Lobby ID. The Lobby may have been disbanded or the invite may have expired.".format(message.author.mention)

            message.author = client.rTTR.get_member(message.author.id)
            if not message.author:
                return 'Sorry, but you need to be in the Toontown Rewritten Discord to use lobbies.'
            invited = module.activeLobbies[args[0]].invited
            inLobby = discord.utils.find(lambda r: 'lobby-' in r.name, client.rTTR.get_member(message.author.id).roles)
            ownsLobby = 'owner' in inLobby.name if inLobby else False

            if message.author.id not in invited:
                return '{} Sorry, but you weren\'t invited to that lobby.'.format(message.author.mention)
            elif ownsLobby:
                return '{} Sorry, but you cannot join another lobby until you have left your own lobby. You can do this by typing `~disbandLobby`.'.format(message.author.mention)
            elif inLobby:
                return '{} Sorry, but you cannot join another lobby until you have left your own lobby. You can do this by typing `~leaveLobby`.'.format(message.author.mention)

            module.activeLobbies[args[0]].invited.remove(message.author.id)
            await message.author.add_roles(module.activeLobbies[args[0]].role, reason='Accepted invite to lobby')

            return "{} You're now in the **{}** lobby! Have fun!".format(message.author.mention, module.activeLobbies[args[0]].customName)
    class LobbyInviteAcceptCMD_Variant1(LobbyInviteAcceptCMD): NAME = 'acceptlobbyinvite'

    class LobbyLeaveCMD(Command):
        """~leaveLobby

            This will leave the lobby you are currently in.
            You will no longer be able to see and chat within the lobby and you'll need to ask for another invite to rejoin.
            If you own the lobby, use `~disbandLobby` instead.
        """
        NAME = 'leaveLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.__class__ != discord.DMChannel and message.channel.id != module.channelID:
                return
            message.author = client.rTTR.get_member(message.author.id)
            if not message.author:
                return 'Sorry, but you need to be in the Toontown Rewritten Discord to use lobbies.'

            lobby = getUsersLobby(module, message.author)
            if lobby.ownerRole in message.author.roles:
                return '{} You own the **{}** lobby, meaning you need to use `~disbandLobby` to ensure you actually want to disband the lobby.'.format(message.author.mention, lobby.customName)
            elif not lobby:
                return '{} You\'re not currently in a lobby.'.format(message.author.mention)

            await message.author.remove_roles(lobby.role, reason='User left lobby via ~leaveLobby')
    class LobbyLeaveCMD_Variant1(LobbyLeaveCMD): NAME = 'leavelobby'

    class LobbyDisbandCMD(Command):
        """~disbandLobby

            This will disband your lobby if you are the lobby's owner.
        """
        NAME = 'disbandLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.__class__ != discord.DMChannel and message.channel.id != module.channelID:
                return
            message.author = client.rTTR.get_member(message.author.id)
            if not message.author:
                return 'Sorry, but you need to be in the Toontown Rewritten Discord to use lobbies.'

            lobby = getUsersLobby(module, message.author)

            if not lobby:
                return '{} You\'re not currently in a lobby.'.format(message.author.mention)
            elif not lobby.ownerRole in message.author.roles:
                return '{} You don\'t own the **{}** lobby, meaning you need to use `~leaveLobby` to part with the group.'.format(message.author.mention, lobby.customName)
            
            auditLogReason = 'User disbanded lobby via ~disbandLobby'
            await lobby.role.delete(reason=auditLogReason)
            await lobby.ownerRole.delete(reason=auditLogReason)
            category = discord.utils.get(client.rTTR.categories, id=lobby.id)
            for channel in category.channels:
                await channel.delete(reason=auditLogReason)
            await category.delete(reason=auditLogReason)
            await client.send_message(message.channel if message.channel.__class__ == discord.DMChannel else module.channelID, 
                '{} You\'ve disbanded your lobby, everyone\'s free now!'.format(message.author.mention))
    class LobbyDisbandCMD_Variant1(LobbyDisbandCMD): NAME = 'disbandLobby'

    def __init__(self, client):
        Module.__init__(self, client)
        
        self.activeLobbies = {}
        self.channelID = Config.getModuleSetting("lobbies", "interaction")
        self.unvisitedExpiryWarningTime = assertTypeOrOtherwise(Config.getModuleSetting('lobbies', 'unvisited_expiry_warning_time'), int, otherwise=600)
        self.unvisitedExpiryTime = assertTypeOrOtherwise(Config.getModuleSetting('lobbies', 'unvisited_expiry_time'), int, otherwise=300)
        self.visitedExpiryWarningTime = assertTypeOrOtherwise(Config.getModuleSetting('lobbies', 'visited_expiry_warning_time'), int, otherwise=518400)
        self.visitedExpiryTime = assertTypeOrOtherwise(Config.getModuleSetting('lobbies', 'visited_expiry_time'), int, otherwise=86400)

    def loopIteration(self):
        self.client.loop.create_task(self.bumpInactiveLobbies())

    async def handleMsg(self, message):
        if message.channel.category and message.channel.category.name.startswith('Lobby'):
            lobby = getLobbyByID(self, message.channel.category.id)
            lobby.visited = time.mktime(time.gmtime())
            lobby.expiryWarning = None

    async def on_voice_state_update(self, member, before, after):
        if after.channel and after.channel.category and after.channel.category.name.startswith('Lobby'):
            lobby = getLobbyByID(self, after.channel.category.id)
            lobby.visited = time.mktime(time.gmtime())
            lobby.expiryWarning = None

    async def restoreSession(self):
        for category in self.client.rTTR.categories:
            if category.name.startswith('Lobby'):
                lobby = Lobby()
                lobby.id = category.id
                lobby.category = category
                for channel in category.channels:
                    if channel.__class__ == discord.TextChannel:
                        lobby.textChannel = channel
                    elif channel.__class__ == discord.VoiceChannel:
                        lobby.voiceChannel = channel
                lobby.role = discord.utils.get(self.client.rTTR.roles, name='lobby-{}'.format(category.id))
                lobby.ownerRole = discord.utils.get(self.client.rTTR.roles, name='lobby-{}-owner'.format(category.id))
                lobby.created = category.created_at.timestamp()
                lobby.customName = category.name.replace('Lobby [', '').replace(']', '')
                lastMessages = await category.channels[0].history(limit=2).flatten()
                if len(lastMessages) > 0 and lastMessages[0].author == self.client.rTTR.me:
                    lobby.expiryWarning = lastMessages[0].created_at.timestamp()
                    if len(lastMessages) > 1:
                        lobby.visited = lastMessages[1].created_at.timestamp()
                elif lastMessages[0]:
                    lobby.visited = lastMessages[0].created_at.timestamp()
                self.activeLobbies[lobby.id] = lobby
        await self.bumpInactiveLobbies()

    async def bumpInactiveLobbies(self):
        inactiveLobbies = []
        for lobby in self.activeLobbies.values():
            # If the lobby has not been visited for 10 minutes...
            if not lobby.visited and not lobby.expiryWarning and lobby.created >= self.unvisitedExpiryWarningTime:
                lobby.expiryWarning = time.mktime(time.gmtime())
                target = discord.utils.find(lambda m: lobby.ownerRole in m.roles, self.client.rTTR.members) if not lobby.textChannel else lobby.textChannel
                await self.client.send_message(target, 'Just a heads up, to prevent lobby spam, your lobby will be disbanded if not used within the next {}.'.format(
                    getTimeFromSeconds(self.unvisitedExpiryTime))
                )
            # If the lobby was last visited 6 days ago...
            elif lobby.visited and not lobby.expiryWarning and lobby.visited >= self.visitedExpiryWarningTime:
                lobby.expiryWarning = time.mktime(time.gmtime())
                target = discord.utils.find(lambda m: lobby.ownerRole in m.roles, self.client.rTTR.members) if not lobby.textChannel else lobby.textChannel
                await self.client.send_message(target, "Just a heads up -- your lobby hasn't been used in a while, and will expire in {} if left unused.".format(
                    getTimeFromSeconds(self.visitedExpiryTime))
                )
            # If the lobby was visited and an expiry warning was sent 24 hours ago...
            # OR
            # If the lobby was not visited and an expiry warning was sent 5 minutes ago...
            elif lobby.expiryWarning and time.mktime(time.gmtime()) - lobby.expiryWarning >= (self.visitedExpiryTime if lobby.visited else self.unvisitedExpiryTime):
                for member in filter(lambda m: lobby.role in m.roles, self.client.rTTR.members):
                    await self.client.send_message(member, "The lobby you were in was disbanded because it was left inactive for an extended period of time.")
                owner = discord.utils.find(lambda m: lobby.ownerRole in m.roles, self.client.rTTR.members)
                await self.client.send_message(owner, "The lobby you created was disbanded because it was left inactive for an extended period of time.")
                
                if lobby.textChannel: await lobby.textChannel.delete()
                if lobby.voiceChannel: await lobby.voiceChannel.delete()
                await lobby.category.delete()
                await lobby.role.delete()
                await lobby.ownerRole.delete()
                inactiveLobbies.append(lobby)

        for inactiveLobby in inactiveLobbies:
            del self.activeLobbies[inactiveLobby.id]

module = LobbyManagement