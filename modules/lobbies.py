import discord
import time
from io import BytesIO
from datetime import datetime
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
        self.filter = True
        self.filterVotes = []
        self.filterVotesNeeded = 0
        self.filterWarning = False

async def createLobby(client, module, message, *args, textChannelOnly=False, voiceChannelOnly=False):
    if message.channel.id != module.channelID:
        return

    lobby = getUsersLobby(module, message.author)
    ownsLobby = lobby and lobby.ownerRole in message.author.roles
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
    if discordModRole:
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

async def getChatLog(client, lobby, savingMessage=None):
    chatlog = ""
    participants = []
    creator = discord.utils.find(lambda m: lobby.ownerRole in m.roles, client.rTTR.members)
    async for m in lobby.textChannel.history(limit=10000, reverse=True):
        if savingMessage and m.content == savingMessage:
            continue
        participant =  m.author.name + '#' + m.author.discriminator + (' [BOT]' if m.author.bot else '')
        if participant not in participants:
            participants.append(participant)
        messageHeader = '== {name}{bot} - {time}{edited}{attachments}{embeds} =='.format(
            name=m.author.name,
            bot=' [BOT]' if m.author.bot else '',
            time=m.created_at.strftime('%m/%d/%Y @ %I:%M%p'),
            edited=(' (edited on ' + m.edited_at.strftime('%m/%d/%Y @ %I:%M%p') + ')') if m.edited_at else '',
            attachments=' *' if m.attachments else '',
            embeds=' **' if m.embeds else '',
        )
        chatlog += '\r\n\r\n{messageHeader}\r\n{content}'.format(
            messageHeader=messageHeader,
            content=m.clean_content.replace('\n', '\r\n')
        )
    chatlog = '{} Lobby\r\nCreated by {}\r\nCreated on {}\r\nAll Lobby Participants:\r\n\t{}\r\n\r\n' \
        '* = This message included an attachment.\r\n** = This message included an embed.\r\n\r\n============= BEGIN CHAT LOG ============='.format(
        lobby.customName,
        creator.name + '#' + creator.discriminator + (' [BOT]' if creator.bot else ''),
        datetime.fromtimestamp(lobby.created).strftime('%m/%d/%Y @ %I:%M%p'),
        '\r\n\t'.join(participants)
    ) + chatlog
    return chatlog

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
            if module.channel.id != module.channelID and \
                (message.channel.__class__ == discord.DMChannel or not message.channel.category or not message.channel.category.name.startswith('Lobby')):
                return

            lobby = getUsersLobby(module, message.author)

            if not lobby:
                return '{} You\'re not in a lobby yourself -- create a lobby before you invite users.'.format(message.author.mention)
            elif not message.mentions:
                return '{} I need a mention of the user you want to invite to your lobby.'.format(message.author.mention)
            elif len(message.mentions) == 1 and message.mentions[0] == message.author:
                return '{} No need to invite yourself to the lobby!'.format(message.author.mention)
            elif message.author in message.mentions:
                message.mentions.remove(message.author)

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
                    await user.send("Hey there, {}! {} has invited you to join their private lobby on the Toontown Rewritten Discord. {}" \
                        "\n\nIf you're not interested, you can ignore this message. To accept, {}copy & paste the following:".format(
                            user.mention,
                            message.author.mention,
                            'Note that the bad word filter in this lobby is **disabled**, and you should not accept this invite if you are of a younger age. Anything 18+ will still be moderated.' \
                            if not lobby.filter else '',
                            'first leave your current lobby with `~leaveLobby` *(or `~disbandLobby` if you created the lobby)* and then ' \
                            if getUsersLobby(module, user) else ''
                        )
                    )
                    await user.send("`~acceptLobbyInvite {}`".format(lobby.id))
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
        """~acceptLobbyInvite <lobby id>

            This allows you to accept an invite to a lobby from another user.
            Once you accept, you'll be able to see and chat within their lobby.
        """
        NAME = 'acceptLobbyInvite'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.__class__ != discord.DMChannel and message.channel.__class__ == discord.DMChannel and \
                not message.channel.category and not message.channel.category.name.startswith('Lobby'):
                return

            try:
                lobby = int(args[0])
            except ValueError:
                lobby = args[0]
            if lobby not in module.activeLobbies:
                return "{} Sorry, but I didn't recognize that Lobby ID. The Lobby may have been disbanded or the invite may have expired.".format(message.author.mention)

            message.author = client.rTTR.get_member(message.author.id)
            if not message.author:
                return 'Sorry, but you need to be in the Toontown Rewritten Discord to use lobbies.'
            invited = module.activeLobbies[lobby].invited
            inLobby = discord.utils.find(lambda r: 'lobby-' in r.name, client.rTTR.get_member(message.author.id).roles)
            ownsLobby = 'owner' in inLobby.name if inLobby else False

            if message.author.id not in invited:
                return '{} Sorry, but you weren\'t invited to that lobby.'.format(message.author.mention)
            elif ownsLobby:
                return '{} Sorry, but you cannot join another lobby until you have left your own lobby. You can do this by typing `~disbandLobby`.'.format(message.author.mention)
            elif inLobby:
                return '{} Sorry, but you cannot join another lobby until you have left your own lobby. You can do this by typing `~leaveLobby`.'.format(message.author.mention)

            module.activeLobbies[lobby].invited.remove(message.author.id)
            await message.author.add_roles(module.activeLobbies[lobby].role, reason='Accepted invite to lobby')

            return "{} You're now in the **{}** lobby! Have fun!".format(message.author.mention, module.activeLobbies[lobby].customName)
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
            if message.channel.__class__ != discord.DMChannel and message.channel.id != module.channelID and \
                (message.channel.__class__ != discord.TextChannel or not message.channel.category or not message.channel.category.name.startswith('Lobby')):
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
            if message.channel.__class__ != discord.DMChannel and message.channel.id != module.channelID and \
                (message.channel.__class__ != discord.TextChannel or not message.channel.category or not message.channel.category.name.startswith('Lobby')):
                return
            message.author = client.rTTR.get_member(message.author.id)
            if not message.author:
                return 'Sorry, but you need to be in the Toontown Rewritten Discord to use lobbies.'

            lobby = getUsersLobby(module, message.author)

            if not lobby:
                return '{} You\'re not currently in a lobby.'.format(message.author.mention)
            elif not lobby.ownerRole in message.author.roles:
                return '{} You don\'t own the **{}** lobby, meaning you need to use `~leaveLobby` to part with the group.'.format(message.author.mention, lobby.customName)
            
            savingMessage = "Alrighty, will do! I'm just saving you a copy of your chat logs in case you want them in the future, hang on a second..."
            await client.send_message(message.channel, savingMessage)
            async with message.channel.typing():
                chatlog = await getChatLog(client, lobby, savingMessage)

            auditLogReason = 'User disbanded lobby via ~disbandLobby'
            await lobby.role.delete(reason=auditLogReason)
            await lobby.ownerRole.delete(reason=auditLogReason)
            category = discord.utils.get(client.rTTR.categories, id=lobby.id)
            for channel in category.channels:
                await channel.delete(reason=auditLogReason)
            await category.delete(reason=auditLogReason)
            await client.send_message(message.channel if message.channel.__class__ == discord.DMChannel else module.channelID, 
                '{} You\'ve disbanded your lobby, everyone\'s free now!'.format(message.author.mention))
            del module.activeLobbies[lobby.id]

            confirmationMessage = await client.send_message(message.author, 'Here\'s that chat log for you...')
            async with message.author.typing():
                file = discord.File(BytesIO(bytes(chatlog, 'utf-8')), filename='lobby-chatlog-{}.txt'.format(int(lobby.created)))
                await client.send_message(message.author, file)
            await confirmationMessage.edit(content='Here\'s that chat log for you:')
    class LobbyDisbandCMD_Variant1(LobbyDisbandCMD): NAME = 'disbandlobby'

    class LobbyFilterEnableCMD(Command):
        """~enableFilter

            This re-enables the bad word filter for the lobby.
            Half of the users in the lobby must also use the command to re-enable the bad word filter, to ensure that a majority consents to it.
        """
        NAME = 'enableFilter'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.__class__ == discord.DMChannel or not message.channel.category or not message.channel.category.name.startswith('Lobby'):
                return

            lobby = getUsersLobby(module, message.author)

            if not lobby:
                return '{} You\'re not currently in a lobby.'.format(message.author.mention)
                # Ironic, since it shouldn't get here.
            moderation = client.requestModule('moderation')
            if not moderation:
                return '{} The lobby filter cannot be enabled because the `moderation` module has not been loaded.'.format(message.author.mention)
            elif lobby.filter:
                return '{} The lobby filter is already enabled.'.format(message.author.mention)
            elif message.author.id in lobby.filterVotes:
                return '{} You\'ve already voted!'.format(message.author.mention)

            lobby.filterVotesNeeded = int(len([m for m in filter(lambda m: lobby.role in m.roles, client.rTTR.members)]) / 2) + 1  # (+ 1) == owner
            lobby.filterVotes.append(message.author.id)

            if len(lobby.filterVotes) >= lobby.filterVotesNeeded:
                lobby.filterVotesNeeded = 0
                lobby.filterVotes = []
                lobby.filter = True
                return 'The bad word filter has been re-enabled.'
            else:
                return '{} Your vote to re-enabled the bad word filter has been submitted; **{} more vote{} required.'.format(
                    message.author.mention, lobby.filterVotesNeeded - lobby.filterVotes, '** is' if lobby.filterVotesNeeded - lobby.filterVotes == 1 else 's** are')
    class LobbyFilterEnableCMD_Variant1(LobbyFilterEnableCMD): NAME = 'enablefilter'

    class LobbyFilterDisableCMD(Command):
        """~disableFilter

            This disables the bad word filter for the lobby.
            Please note that anything that breaks Discord's Terms of Service or Community Guidelines is still prohibited, including any messages or content that's 18+ (as the lobby channel is not a properly labeled NSFW channel, and is not intended to be).
            All of the users in the lobby must also use the command to disable the bad world filter, to ensure that everyone consents to it.
        """
        NAME = 'disableFilter'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.__class__ == discord.DMChannel or not message.channel.category or not message.channel.category.name.startswith('Lobby'):
                return

            lobby = getUsersLobby(module, message.author)

            if not lobby:
                return '{} You\'re not currently in a lobby.'.format(message.author.mention)
                # Ironic, since it shouldn't get here.
            if not lobby.filter:
                return '{} The lobby filter is already disabled.'.format(message.author.mention)
            elif message.author.id in lobby.filterVotes:
                return '{} You\'ve already voted!'.format(message.author.mention)

            lobby.filterVotesNeeded = len([m for m in filter(lambda m: lobby.role in m.roles, client.rTTR.members)]) + 1  # (+ 1) == owner
            lobby.filterVotes.append(message.author.id)

            if len(lobby.filterVotes) >= lobby.filterVotesNeeded:
                lobby.filterVotesNeeded = 0
                lobby.filterVotes = []
                lobby.filter = False
                return 'The bad word filter has been disabled. To re-enable it, use `~enableFilter`.'
            else:
                return '{} Your vote to disable the bad word filter has been submitted; **{} more vote{} required.'.format(
                    message.author.mention, lobby.filterVotesNeeded - lobby.filterVotes, '** is' if lobby.filterVotesNeeded - lobby.filterVotes == 1 else 's** are')
    class LobbyFilterDisableCMD_Variant1(LobbyFilterDisableCMD): NAME = 'disablefilter'

    class LobbyChatLogCMD(Command):
        """~chatlog

            Generates a chat log in a downloadable .txt format, and outputs it to the channel. This may take a few seconds depending on the history size of your lobby.
            If you're about to disband your lobby, there's no need to run this command, a chatlog is generated for you upon disband automatically.
            Only the first 10,000 messages are generaetd.
        """
        NAME = 'getChatLog'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.__class__ == discord.DMChannel or not message.channel.category or not message.channel.category.name.startswith('Lobby'):
                return

            lobby = getUsersLobby(module, message.author)

            if not lobby:
                return '{} You\'re not currently in a lobby.'.format(message.author.mention)

            savingMessage = "Alrighty, I'm fetching that chat log for you, hang on a second..."
            await client.send_message(message.channel, savingMessage)
            async with message.channel.typing():
                chatlog = await getChatLog(client, lobby, savingMessage)

            confirmationMessage = await client.send_message(message.channel, 'Here\'s that chat log for you...')
            async with message.author.typing():
                file = discord.File(BytesIO(bytes(chatlog, 'utf-8')), filename='lobby-chatlog-{}.txt'.format(int(message.created_at.timestamp())))
                await client.send_message(message.channel, file)
            await confirmationMessage.edit(content='Here\'s that chat log for you:')
    class LobbyChatLogCMD_Variant1(LobbyChatLogCMD): NAME = 'getchatlog'
    class LobbyChatLogCMD_Variant2(LobbyChatLogCMD): NAME = 'chatlog'

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
        if message.channel.__class__ == discord.TextChannel and message.channel.category and message.channel.category.name.startswith('Lobby'):
            lobby = getLobbyByID(self, message.channel.category.id)
            lobby.visited = time.mktime(time.gmtime())
            lobby.expiryWarning = None

            moderation = self.client.requestModule('moderation')
            if lobby.filter and moderation:
                filterActivated = await moderation.filterBadWords(message, silentFilter=True)
                if filterActivated and not lobby.filterWarning:
                    lobby.filterWarning = True
                    await self.client.send_message(
                        message.channel, 
                        "{} Your message was removed because it contained a bad word. " \
                        "This is a reminder that, if everyone in the lobby agrees they're okay with it, you can disable the bad word filter " \
                        "by using `~disableFilter`.\n\nNote that **anything that breaks Discord's Terms of Service or Community Guidelines is " \
                        "still prohibited.** This includes any messages or content that's 18+, as the lobby channel is " \
                        "labeled NSFW channel, and is not intended to be.".format(message.author.mention)
                    )

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
            # If the lobby has not been visited...
            if not lobby.visited and not lobby.expiryWarning and time.mktime(time.gmtime()) - lobby.created >= self.unvisitedExpiryWarningTime:
                lobby.expiryWarning = time.mktime(time.gmtime())
                target = discord.utils.find(lambda m: lobby.ownerRole in m.roles, self.client.rTTR.members) if not lobby.textChannel else lobby.textChannel
                await self.client.send_message(target, 'Just a heads up, to prevent lobby spam, your lobby will be disbanded if not used within the next {}.'.format(
                    getTimeFromSeconds(self.unvisitedExpiryTime))
                )
            # If the lobby was last visited...
            elif lobby.visited and not lobby.expiryWarning and time.mktime(time.gmtime()) - lobby.visited >= self.visitedExpiryWarningTime:
                lobby.expiryWarning = time.mktime(time.gmtime())
                target = discord.utils.find(lambda m: lobby.ownerRole in m.roles, self.client.rTTR.members) if not lobby.textChannel else lobby.textChannel
                await self.client.send_message(target, "Just a heads up -- your lobby hasn't been used in a while, and will expire in {} if left unused.".format(
                    getTimeFromSeconds(self.visitedExpiryTime))
                )
            # If the lobby was visited and an expiry warning was sent...
            # OR
            # If the lobby was not visited and an expiry warning was sent...
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