import discord
import time
import re
from io import BytesIO
from datetime import datetime
from extra.commands import Command
from modules.module import Module
from utils import Config, assertType, assertClass, getTimeFromSeconds

class Lobby:
    def __init__(self):
        self.id = None                              # The channel category's lobby ID, it's consistent and easy to restore.
        self.category = None                        # The channel category object.
        self.textChannel = None                     # The text channel object.
        self.voiceChannel = None                    # The voice channel object.
        self.role = None                            # The member role object.
        self.ownerRole = None                       # The owner role object.
        self.modRole = None                         # The lobby mod role object.
        self.created = time.mktime(time.gmtime())   # The time when the lobby was created, in UTC.
        self.customName = ""                        # The name of the lobby.
        self.invited = []                           # The members that have been invited to the lobby. It is not persistent.
        self.lastVisited = None                     # The time when the last message was sent or when a voice channel was joined.
        self.expiryWarning = None                   # The time when a warning was given that the lobby would soon expire.
        self.filter = True                          # The status of the bad word filter... "True" if it's applied to the lobby.
        self.filterVotes = []                       # A list of members who have voted to toggle the bad word filter.
        self.filterVotesNeeded = 0                  # The total amount of votes needed to toggle the filter.
        self.filterWarning = False                  # "True" if a notification has been given that the bad word filter can be toggled.

LOBBY_FAILURE_GUILD = 'Sorry, but you need to be in the Toontown Rewritten Discord to use lobbies.'
LOBBY_FAILURE_MISSING_LOBBY = "You're not currently in a lobby."

CREATION_FAILURE_OWNER = "You own a lobby right now. You'll have to `~disbandLobby` to create a new one."
CREATION_FAILURE_MEMBER = "You are in a lobby right now. You'll have to `~leaveLobby` to create a new one."
CREATION_FAILURE_NAME_LENGTH = 'Your lobby name must be 30 characters or less.'
CREATION_FAILURE_NAME_MISSING = 'Give your lobby a name!'
CREATION_FAILURE_NAME_GENERIC = 'Please choose a different name.'
CREATION_SUCCESS = 'Your lobby has been created!'

INVITATION_FAILURE_MISSING_LOBBY = "You're not in a lobby yourself -- create a lobby before you invite users."
INVITATION_FAILURE_MISSING_MENTION = 'I need a mention of the user you want to invite to your lobby.'
INVITATION_FAILURE_NARCISSISTIC = 'No need to invite yourself to the lobby!'
INVITATION_FAILURE_PARTIAL = 'Some of the invites could not be sent out:'
INVITATION_FAILURE_FULL = 'None of the invites could be sent out:'
INVITATION_FAILURE_MESSAGE = '{author} Could not send out messages to {failedCount} {personGrammar} *({failedList})*... the channel is still open for them if they use `~acceptLobbyInvite {lobbyID}`. {alreadyPending}But otherwise, invites sent!'
INVITATION_FAILURE_MESSAGE = 'Could not send messages out to these users: '
INVITATION_FAILURE_BOT = 'Can not send invites to bots: '
INVITATION_FAILURE_PENDING = 'An invite is already pending for these users: '
INVITATION_FAILURE_JOINED = 'These users are already in the lobby: '
INVITATION_MESSAGE_1 = "Hey there, {invitee}! {author} has invited you to join their private lobby on the Toontown Rewritten Discord. {filterStatus}" \
                        "\n\nIf you're not interested, you can ignore this message. To accept, {inLobbyInstructions}copy & paste the following:"
INVITATION_MESSAGE_2 = '~acceptLobbyInvite {}'
INVITATION_MESSAGE_FILTER = 'Note that the bad word filter in this lobby is **disabled**, and you should not accept this invite if you are of a younger age. Anything 18+ will still be moderated.'
INVITATION_MESSAGE_LEAVE_LOBBY = 'first leave your current lobby with `~leaveLobby` *(or `~disbandLobby` if you created the lobby)* and then '
INVITATION_SUCCESS = 'Invite{plural} sent!'
INVITATION_SUCCESS_PARTIAL = 'But otherwise, invites sent!'

UNINVITE_FAILURE_MEMBER = "You must be the owner of the lobby to uninvite another user."
UNINVITE_FAILURE_SELF = "You can't uninvite yourself to a lobby, please use `~leaveLobby` *(or `~disbandLobby` if you created the lobby)* to leave."
UNINVITE_FAILURE_NOT_INVITED = 'Could not uninvite any of the mentioned users, because either none of them were invited to start with or they already accepted.'
UNINVITE_FAILURE_NOT_INVITED_OTHERS = "Could not uninvite some users because they weren't invited to begin with or had already accepted. Otherwise, all other mentioned invites have been voided."
UNINVITE_FAILURE_MISSING_MENTION = 'I need a mention of the user you want to uninvite from your lobby.'
UNINVITE_SUCCESS = 'The mentioned user{plural} taken off the invitation list.'

KICK_FAILURE_MEMBER = "You must be the owner of the lobby to kick users from it."
KICK_FAILURE_SELF = 'No need to kick yourself from the lobby, that would be anarchy! You can use `~leaveLobby` *(or `~disbandLobby` if you created the lobby)* to leave.'
KICK_FAILURE_NONMEMBER = 'Could not kick any of the mentioned users, because none of them were currently in the lobby.'
KICK_FAILURE_NONMEMBER_OTHERS = 'Could not kick some users because they were not in the lobby. But otherwise, kicks have been issued!'
KICK_FAILURE_MISSING_MENTION = 'I need a mention of the user you want to kick from your lobby.'
KICK_MESSAGE = "You've been kicked from the **{lobbyName}** lobby."
KICK_SUCCESS = 'The mentioned user{plural} successfully kicked.'

RSVP_FAILURE_MISSING_ID = 'Please reference the Lobby ID provided to you like this: `~acceptLobbyInvite lobbyid`'
RSVP_FAILURE_ID = "Sorry, but I didn't recognize that Lobby ID. The Lobby may have been disbanded or the invite may have expired."
RSVP_FAILURE_OWNER = 'Sorry, but you cannot join another lobby until you have left your own lobby. You can do this by typing `~disbandLobby`.'
RSVP_FAILURE_MEMBER = 'Sorry, but you cannot join another lobby until you have left your own lobby. You can do this by typing `~leaveLobby`.'
RSVP_FAILURE_UNINVITED = "Sorry, but you weren't invited to that lobby or the invite was rescinded."
RSVP_SUCCESS = "You're now in the **{name}** lobby! Have fun!"

LEAVE_FAILURE_OWNER = 'You own the **{name}** lobby, meaning you need to use `~disbandLobby` to ensure you actually want to disband the lobby.'

DISBAND_FAILURE_MEMBER = "You don't own the **{}** lobby, meaning you need to use `~leaveLobby` to part with the group."
DISBAND_SUCCESS = "You've disbanded your lobby, everyone's free now!"
DISBAND_SUCCESS_MEMBER = 'The **{}** lobby you were in was disbanded.'
DISBAND_LOG_SAVE = "Alrighty, will do! I'm just saving you a copy of your chat logs in case you want them in the future, hang on a second..."

FORCE_FAILURE_MISSING_NAME = "Please specify the name of the lobby you wish to disband forcefully. Be sure to use correct spelling."
FORCE_FAILURE_MISSING_LOBBY = "I don't know any lobbies by the name **{name}**. Be sure to use correct spelling."
FORCE_SUCCESS = 'The **{}** lobby was forcefully disbanded.'
FORCE_SUCCESS_OWNER = 'Your **{}** was forcefully disbanded by a moderator. Please make sure your lobby follows all the server and Discord rules.'

FILTER_ENABLE_FAILURE_MODULE = 'The lobby filter cannot be enabled because the `moderation` module has not been loaded.'
FILTER_ENABLE_FAILURE_ENABLED = 'The lobby filter is already enabled.'
FILTER_ENABLE_VOTED = 'Your vote to re-enabled the bad word filter has been submitted; **{count} more vote{plural} required.'
FILTER_ENABLE_SUCCESS = 'The bad word filter has been re-enabled.'
FILTER_DISABLE_FAILURE_DISABLED = 'The lobby filter is already disabled.'
FILTER_DISABLE_SUCCESS = 'The bad word filter has been disabled. To re-enable it, use `~enableFilter`.'
FILTER_DISABLE_VOTED = 'Your vote to disable the bad word filter has been submitted; **{count} more vote{plural} required.'
FILTER_FAILURE_VOTED = "You've already voted!"
FILTER_WARNING = "Your message was removed because it contained a bad word. " \
                "This is a reminder that, if everyone in the lobby agrees they're okay with it, you can disable the bad word " \
                "filter by using `~disableFilter`.\n\nNote that **anything that breaks Discord's Terms of Service or Community " \
                "Guidelines is still prohibited.** This includes any messages or content that's 18+, as the lobby channel is not " \
                "labeled as a NSFW channel, and is not intended to be."

LOG_CONFIRM_1 = "Alrighty, I'm fetching that chat log for you, hang on a second..."
LOG_CONFIRM_2 = "Here's that chat log for you..."
LOG_CONFIRM_3 = "Here's that chat log for you:"
LOG_CONFIRM_4 = "We're generating a chat log for you in case you needed to save anything..."
LOG_CONFIRM_5 = "Here's the chat log for your lobby, in case you needed to save anything..."
LOG_CONFIRM_6 = "Here's the chat log for your lobby, in case you needed to save anything:"
LOG_CONFIRM_MOD = "The **{}** lobby disbanded, here's a chat log from the channel:"
LOG_NO_TEXT = 'No chatlog was generated because the lobby does not have a text channel.'

CORRUPTED_CHANNELS = 'Just a heads up -- your lobby (somehow) ended up with no channels associated with it, ' \
                    'so both a new text channel and voice channel have been assigned to it. Apologies for any inconvenience.'
CORRUPTED_ROLE_MEMBER = 'Just a heads up -- your lobby (somehow) ended up with no role assigned to it that allows other users to join. ' \
                        "That's been fixed up for you, but we're not sure who, if anybody, was in your lobby with you. You may have to " \
                        're-invite members with `~invite`. Apologies for any inconvenience.'

BUMP_WARNING_UNVISITED = 'Just a heads up, to prevent lobby spam, your lobby will be disbanded if not used within the next {time}.'
BUMP_WARNING_VISITED = "Just a heads up -- your lobby hasn't been used in a while, and will expire in {time} if left unused."
BUMP_OWNER = 'The lobby you created was disbanded because it was left inactive for an extended period of time.'
BUMP_MEMBER = 'The lobby you were in was disbanded because it was left inactive for an extended period of time.'

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
        async def execute(client, module, message, *args, textChannelOnly=False, voiceChannelOnly=False):
            if message.channel.id != module.lobbyChannel and not module.channelIsDM(message.channel) and not module.channelInLobby(message.channel):
                return

            lobby = module.getLobby(member=message.author)
            owner = lobby and lobby.ownerRole in message.author.roles
            auditLogReason = 'Lobby created by {}'.format(str(message.author))

            if owner:
                return message.author.mention + ' ' + CREATION_FAILURE_OWNER
            elif lobby:
                return message.author.mention + ' ' + CREATION_FAILURE_MEMBER

            moderation = client.requestModule('moderation')
            name = ' '.join(args)
            print(moderation)
            if moderation:
                try:
                    filterActivated = await moderation.filterBadWords(message)
                    if filterActivated:
                        return
                except discord.errors.NotFound:
                    # If a Not Found error returned, that means that it tried to remove something
                    # that contained a bad word, meaning we're safe to stop making the lobby.
                    return
            if len(name) > 25:
                return message.author.mention + ' ' + CREATION_FAILURE_NAME_LENGTH
            elif not name:
                return message.author.mention + ' ' + CREATION_FAILURE_NAME_MISSING
            elif module.getLobby(name=name):
                return message.author.mention + ' ' + CREATION_FAILURE_NAME_GENERIC

            category = await client.rTTR.create_category(name='Lobby [{}]'.format(name), reason=auditLogReason)

            discordModRole = discord.utils.get(client.rTTR.roles, name='Discord Mods')
            dmrPos = discordModRole.position

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
            lobby.modRole = await client.rTTR.create_role(
                name='lobby-{}-mod'.format(lobby.id),
                reason=auditLogReason
            )
            await message.author.add_roles(lobby.ownerRole, reason=auditLogReason)

            discordModRole = discord.utils.get(client.rTTR.roles, name='Discord Mods')
            await category.set_permissions(client.rTTR.default_role, read_messages=False)
            await category.set_permissions(lobby.ownerRole, read_messages=True, embed_links=True)
            await category.set_permissions(lobby.role, read_messages=True, embed_links=True)
            await category.set_permissions(lobby.modRole, send_messages=True, add_reactions=True, speak=True)
            if discordModRole:
                await category.set_permissions(
                    discordModRole,
                    read_messages=True,
                    send_messages=False,
                    manage_messages=True,
                    manage_roles=False,
                    manage_channels=False,
                    add_reactions=False,
                    connect=True,
                    speak=False
                )
                print('trying to move to position {}'.format(dmrPos + 3))
                await lobby.modRole.edit(position=dmrPos + 3)
                if discordModRole in message.author.roles:
                    await message.author.add_roles(lobby.modRole, reason=auditLogReason)

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

            return message.author.mention + ' ' + CREATION_SUCCESS
    class CreateLobbyCMD_Variant1(CreateLobbyCMD): NAME = 'createlobby'

    class CreateTextLobbyCMD(Command):
        NAME = 'createTextLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            return await module.CreateLobbyCMD.execute(client, module, message, *args, textChannelOnly=True)
    class CreateTextLobbyCMD_Variant1(CreateTextLobbyCMD): NAME = 'createtextlobby'

    class CreateVoiceLobbyCMD(Command):
        NAME = 'createVoiceLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            return await module.CreateLobbyCMD.execute(client, module, message, *args, voiceChannelOnly=True)
    class CreateVoiceLobbyCMD_Variant1(CreateVoiceLobbyCMD): NAME = 'createvoicelobby'

    class LobbyInviteCMD(Command):
        """~invite <mention> [mentions]

            This will send a DM to another user(s) asking them to join your lobby.
            If they accept, they'll be able to see and chat within your lobby.
        """
        NAME = 'invite'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.id != module.lobbyChannel and not module.channelIsDM(message.channel) and not module.channelInLobby(message.channel):
                return

            lobby = module.getLobby(member=message.author)
            if not lobby:
                return message.author.mention + ' ' + INVITATION_FAILURE_MISSING_LOBBY
            elif not message.mentions:
                return message.author.mention + ' ' + INVITATION_FAILURE_MISSING_MENTION
            elif len(message.mentions) == 1 and message.mentions[0] == message.author:
                return message.author.mention + ' ' + INVITATION_FAILURE_NARCISSISTIC
            elif message.author in message.mentions:
                message.mentions.remove(message.author)

            failedMessages = []
            failedBot = []
            failedPendingInvite = []
            failedJoined = []
            for user in message.mentions:
                if user.bot:
                    failedBot.append(user.mention)
                    continue

                if user.id in lobby.invited:
                    failedPendingInvite.append(user.mention)
                    continue

                if module.getLobby(member=user) == lobby:
                    failedJoined.append(user.mention)
                    continue

                try:
                    lobby.invited.append(user.id)
                    await user.send(INVITATION_MESSAGE_1.format(
                            invitee=user.mention,
                            author=message.author.mention,
                            filterStatus=INVITATION_MESSAGE_FILTER if not lobby.filter else '',
                            inLobbyInstructions=INVITATION_MESSAGE_LEAVE_LOBBY if module.getLobby(member=user) else ''
                        )
                    )
                    await user.send(INVITATION_MESSAGE_2.format(lobby.id))
                except discord.HTTPException as e:
                    failedMessages.append(user.mention)
            response = INVITATION_FAILURE_PARTIAL
            if failedMessages:
                response += '\n\t' + INVITATION_FAILURE_MESSAGE + ' '.join(failedMessages)
            if failedBot:
                response += '\n\t' + INVITATION_FAILURE_BOT + ' '.join(failedBot)
            if failedPendingInvite:
                response += '\n\t' + INVITATION_FAILURE_PENDING + ' '.join(failedPendingInvite)
            if failedJoined:
                response += '\n\t' + INVITATION_FAILURE_JOINED + ' '.join(failedJoined)
            if len(failedMessages + failedBot + failedPendingInvite + failedJoined) == len(message.mentions):
                response = response.replace(INVITATION_FAILURE_PARTIAL, INVITATION_FAILURE_FULL)
            elif response == INVITATION_FAILURE_PARTIAL:
                response = INVITATION_SUCCESS.format(plural='s' if len(message.mentions) > 1 else '')
            else:
                response += '\n' + INVITATION_SUCCESS_PARTIAL
            return message.author.mention + ' ' + response

    class LobbyUninviteCMD(Command):
        """~uninvite <mention> [mentions]

            This will void an invite to your lobby that was sent to a user.
        """
        NAME = 'uninvite'

        @staticmethod
        async def execute(client, module, message, *args):
            if not module.channelInLobby(message.channel):
                return
            message.author = client.rTTR.get_member(message.author.id)
            if not message.author:
                return LOBBY_FAILURE_GUILD

            lobby = module.getLobby(owner=message.author)
            if not lobby:
                return message.author.mention + ' ' + LOBBY_FAILURE_MISSING_LOBBY
            elif not lobby.ownerRole in message.author.roles:
                return message.author.mention + ' ' + UNINVITE_FAILURE_MEMBER
            elif not message.mentions:
                return message.author.mention + ' ' + UNINVITE_FAILURE_MISSING_MENTION
            elif len(message.mentions) == 1 and message.mentions[0] == message.author:
                return message.author.mention + ' ' + UNINVITE_FAILURE_SELF
            elif message.author in message.mentions:
                message.mentions.remove(message.author)

            failedNotInvited = []
            for user in message.mentions:
                if user.id not in lobby.invited:
                    failedNotInvited.append(user.mention)
                    continue
                lobby.invited.remove(user.id)
            if len(failedNotInvited) == len(message.mentions):
                return message.author.mention + ' ' + UNINVITE_FAILURE_NOT_INVITED
            elif failedNotInvited:
                return message.author.mention + ' ' + UNINVITE_FAILURE_NOT_INVITED_OTHERS
            else:
                return message.author.mention + ' ' + UNINVITE_SUCCESS.format(plural='s were' if len(message.mentions) > 1 else ' was')

    class LobbyInviteAcceptCMD(Command):
        """~acceptLobbyInvite <lobby id>

            This allows you to accept an invite to a lobby from another user.
            Once you accept, you'll be able to see and chat within their lobby.
        """
        NAME = 'acceptLobbyInvite'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.id != module.lobbyChannel and not module.channelIsDM(message.channel) and not module.channelInLobby(message.channel):
                return

            if not args:
                return message.author.mention + ' ' + RSVP_FAILURE_MISSING_ID

            try:
                lobby = int(args[0])
            except ValueError:
                lobby = args[0]
            if lobby not in module.activeLobbies:
                return message.author.mention + ' ' + RSVP_FAILURE_ID
            else:
                lobby = module.activeLobbies[lobby]

            message.author = client.rTTR.get_member(message.author.id)
            if not message.author:
                return LOBBY_FAILURE_GUILD
            userInLobby = module.getLobby(member=message.author)
            userOwnsLobby = userInLobby and userInLobby.ownerRole in message.author.roles

            if userOwnsLobby:
                return message.author.mention + ' ' + RSVP_FAILURE_OWNER
            elif userInLobby:
                return message.author.mention + ' ' + RSVP_FAILURE_MEMBER
            elif message.author.id not in lobby.invited:
                return message.author.mention + ' ' + RSVP_FAILURE_UNINVITED

            lobby.invited.remove(message.author.id)
            discordModRole = discord.utils.get(client.rTTR.roles, name='Discord Mods')
            if discordModRole and discordModRole in message.author.roles:
                await message.author.add_roles(lobby.modRole, reason='Accepted invite to lobby')
            else:
                await message.author.add_roles(lobby.role, reason='Accepted invite to lobby')
            if lobby.textChannel:
                await lobby.textChannel.send('{} has joined the lobby!'.format(message.author.mention))

            return message.author.mention + ' ' + RSVP_SUCCESS.format(name=lobby.customName)
    class LobbyInviteAcceptCMD_Variant1(LobbyInviteAcceptCMD): NAME = 'acceptlobbyinvite'

    class LobbyKickCMD(Command):
        """~kickFromLobby <mention>

            This allows you to remove a user from your lobby, you must be the owner to do this.
            The user must receive another invite to re-join the lobby.
        """
        NAME = 'kickFromLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            if not module.channelInLobby(message.channel):
                return
            message.author = client.rTTR.get_member(message.author.id)
            if not message.author:
                return LOBBY_FAILURE_GUILD

            lobby = module.getLobby(owner=message.author)
            if not lobby:
                return message.author.mention + ' ' + LOBBY_FAILURE_MISSING_LOBBY
            elif not lobby.ownerRole in message.author.roles:
                return message.author.mention + ' ' + KICK_FAILURE_MEMBER
            elif not message.mentions:
                return message.author.mention + ' ' + KICK_FAILURE_MISSING_MENTION
            elif len(message.mentions) == 1 and message.mentions[0] == message.author:
                return message.author.mention + ' ' + KICK_FAILURE_SELF
            elif message.author in message.mentions:
                message.mentions.remove(message.author)

            failedNotMember = []
            for user in message.mentions:
                if module.getLobby(member=user) != lobby:
                    failedNotMember.append(user.mention)
                    continue

                role = lobby.modRole if lobby.modRole in user.roles else lobby.role
                await user.remove_roles(role, reason='Kicked by lobby owner')
                if lobby.textChannel:
                    await lobby.textChannel.send('{} has left the lobby.'.format(user.mention))
                try:
                    await user.send(KICK_MESSAGE.format(lobbyName=lobby.customName))
                except discord.HTTPException as e:
                    pass
            if len(failedNotMember) == len(message.mentions):
                return message.author.mention + ' ' + KICK_FAILURE_NONMEMBER
            elif failedNotMember:
                return message.author.mention + ' ' + KICK_FAILURE_NONMEMBER_OTHERS
            else:
                return message.author.mention + ' ' + KICK_SUCCESS.format(plural='s were' if len(message.mentions) > 1 else ' was')
    class LobbyKickCMD_Variant1(LobbyKickCMD): NAME = 'kickfromlobby'

    class LobbyLeaveCMD(Command):
        """~leaveLobby

            This will leave the lobby you are currently in.
            You will no longer be able to see and chat within the lobby and you'll need to ask for another invite to rejoin.
            If you own the lobby, use `~disbandLobby` instead.
        """
        NAME = 'leaveLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.id != module.lobbyChannel and not module.channelIsDM(message.channel) and not module.channelInLobby(message.channel):
                return
            message.author = client.rTTR.get_member(message.author.id)
            if not message.author:
                return LOBBY_FAILURE_GUILD

            lobby = module.getLobby(member=message.author)
            if lobby and lobby.ownerRole in message.author.roles:
                return message.author.mention + ' ' + LEAVE_FAILURE_OWNER.format(name=lobby.customName)
            elif not lobby:
                return message.author.mention + ' ' + LOBBY_FAILURE_MISSING_LOBBY

            role = lobby.modRole if lobby.modRole in message.author.roles else lobby.role
            await message.author.remove_roles(role, reason='User left lobby via ~leaveLobby')
            if lobby.textChannel:
                await lobby.textChannel.send('{} has left the lobby.'.format(message.author.mention))
    class LobbyLeaveCMD_Variant1(LobbyLeaveCMD): NAME = 'leavelobby'

    class LobbyDisbandCMD(Command):
        """~disbandLobby

            This will disband your lobby if you are the lobby's owner.
        """
        NAME = 'disbandLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.id != module.lobbyChannel and not module.channelIsDM(message.channel) and not module.channelInLobby(message.channel):
                return
            message.author = client.rTTR.get_member(message.author.id)
            if not message.author:
                return LOBBY_FAILURE_GUILD

            lobby = module.getLobby(member=message.author)
            if not lobby:
                return message.author.mention + ' ' + LOBBY_FAILURE_MISSING_LOBBY
            elif not lobby.ownerRole in message.author.roles:
                return message.author.mention + ' ' + DISBAND_FAILURE_MEMBER.format(lobby.customName)
            
            if lobby.textChannel:
                savingMessage = DISBAND_LOG_SAVE
                savingMsgObj = await client.send_message(message.channel, savingMessage)
                async with message.channel.typing():
                    chatlog = await module.getChatLog(lobby, savingMessage)

            members = module.getLobbyMembers(lobby, withOwner=False)

            auditLogReason = 'User disbanded lobby via ~disbandLobby'
            await lobby.role.delete(reason=auditLogReason)
            await lobby.ownerRole.delete(reason=auditLogReason)
            await lobby.modRole.delete(reason=auditLogReason)
            for channel in lobby.category.channels:
                await channel.delete(reason=auditLogReason)
            await lobby.category.delete(reason=auditLogReason)
            for member in members:
                await client.send_message(member, DISBAND_SUCCESS_MEMBER.format(lobby.customName))
            await client.send_message(module.lobbyChannel if message.channel.id == module.lobbyChannel else message.author, 
                message.author.mention + ' ' + DISBAND_SUCCESS)
            del module.activeLobbies[lobby.id]

            if lobby.textChannel:
                try:
                    # This really only matters if the command was not sent in a lobby.
                    await savingMsgObj.delete()
                except discord.errors.NotFound:
                    pass
                confirmationMessage = await client.send_message(message.author, LOG_CONFIRM_2)
                async with message.author.typing():
                    file = discord.File(BytesIO(bytes(chatlog, 'utf-8')), filename='lobby-chatlog-{}.txt'.format(int(lobby.created)))
                    await client.send_message(message.author, file)
                await confirmationMessage.edit(content=LOG_CONFIRM_3)
                if module.logChannel:
                    await client.send_message(module.logChannel, LOG_CONFIRM_MOD.format(lobby.customName))
                    async with module.logChannel.typing():
                        file = discord.File(BytesIO(bytes(chatlog, 'utf-8')), filename='lobby-chatlog-{}.txt'.format(int(lobby.created)))
                        await client.send_message(module.logChannel, file)
    class LobbyDisbandCMD_Variant1(LobbyDisbandCMD): NAME = 'disbandlobby'
    class LobbyDisbandCMD_Variant2(LobbyDisbandCMD): NAME = 'disband'

    class LobbyForceDisbandCMD(Command):
        """~forceDisband <lobby name>

            This will disband a user's lobby forcefully.
        """
        NAME = 'forceDisband'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            name = ' '.join(args)
            lobby = module.getLobby(name=name)
            if not name:
                return message.author.mention + ' ' + FORCE_FAILURE_MISSING_NAME
            elif not lobby:
                return message.author.mention + ' ' + FORCE_FAILURE_MISSING_LOBBY.format(name=name)
            
            if lobby.textChannel:
                #savingMessage = DISBAND_LOG_SAVE
                #savingMsgObj = await client.send_message(message.channel, savingMessage)
                async with message.channel.typing():
                    chatlog = await module.getChatLog(lobby)

            members = module.getLobbyMembers(lobby, withOwner=False)
            owner = module.getLobbyOwner(lobby)

            auditLogReason = 'Mod disbanded lobby via ~forceDisband'
            await lobby.role.delete(reason=auditLogReason)
            await lobby.ownerRole.delete(reason=auditLogReason)
            await lobby.modRole.delete(reason=auditLogReason)
            for channel in lobby.category.channels:
                await channel.delete(reason=auditLogReason)
            await lobby.category.delete(reason=auditLogReason)
            for member in members:
                await client.send_message(member, DISBAND_SUCCESS_MEMBER.format(lobby.customName))
            await client.send_message(owner, FORCE_SUCCESS_OWNER.format(name))
            await client.send_message(message.channel, message.author.mention + ' ' + FORCE_SUCCESS.format(name))
            del module.activeLobbies[lobby.id]

            if lobby.textChannel:
                confirmationMessage = await client.send_message(owner, LOG_CONFIRM_5)
                async with message.author.typing():
                    file = discord.File(BytesIO(bytes(chatlog, 'utf-8')), filename='lobby-chatlog-{}.txt'.format(int(lobby.created)))
                    await client.send_message(message.author, file)
                await confirmationMessage.edit(content=LOG_CONFIRM_6)
                if module.logChannel:
                    await client.send_message(module.logChannel, LOG_CONFIRM_MOD.format(lobby.customName))
                    async with module.logChannel.typing():
                        file = discord.File(BytesIO(bytes(chatlog, 'utf-8')), filename='lobby-chatlog-{}.txt'.format(int(lobby.created)))
                        await client.send_message(module.logChannel, file)
    class LobbyForceDisbandCMD_Variant1(LobbyForceDisbandCMD): NAME = 'forcedisband'

    class LobbyFilterEnableCMD(Command):
        """~enableFilter

            This re-enables the bad word filter for the lobby.
            Half of the users in the lobby must also use the command to re-enable the bad word filter, to ensure that a majority consents to it.
        """
        NAME = 'enableFilter'

        @staticmethod
        async def execute(client, module, message, *args):
            if not module.channelInLobby(message.channel):
                return

            lobby = module.getLobby(member=message.author)
            if not lobby:
                return message.author.mention + ' ' + LOBBY_FAILURE_MISSING_LOBBY
                # Ironic, since it shouldn't get here.

            # The number of filter votes needed is the number of users
            lobby.filterVotesNeeded = int(len(module.getLobbyMembers(lobby)) / 2)

            moderation = client.requestModule('moderation')
            if not moderation:
                return message.author.mention + ' ' + FILTER_ENABLE_FAILURE_MODULE
            elif lobby.filter:
                return message.author.mention + ' ' + FILTER_ENABLE_FAILURE_ENABLED
            if len(lobby.filterVotes) >= lobby.filterVotesNeeded:
                # Just in case users leave the server or lobby, and their votes were the last ones required.
                pass
            elif message.author in lobby.filterVotes:
                return message.author.mention + ' ' + FILTER_FAILURE_VOTED

            lobby.filterVotes.append(message.author)

            if len(lobby.filterVotes) >= lobby.filterVotesNeeded:
                lobby.filterVotesNeeded = 0
                lobby.filterVotes = []
                lobby.filter = True
                return FILTER_ENABLE_SUCCESS
            else:
                return message.author.mention + ' ' + FILTER_ENABLE_VOTED.format(
                    count=lobby.filterVotesNeeded - len(lobby.filterVotes),
                    plural='** is' if lobby.filterVotesNeeded - len(lobby.filterVotes) == 1 else 's** are'
                )
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
            if not module.channelInLobby(message.channel):
                return

            lobby = module.getLobby(member=message.author)
            if not lobby:
                return message.author.mention + ' ' + LOBBY_FAILURE_MISSING_LOBBY
                # Ironic, since it shouldn't get here.

            # The number of filter votes needed is the number of users
            lobby.filterVotesNeeded = len(module.getLobbyMembers(lobby))

            if not lobby.filter:
                return message.author.mention + ' ' + FILTER_DISABLE_FAILURE_DISABLED
            if len(lobby.filterVotes) >= lobby.filterVotesNeeded:
                # Just in case users leave the server or lobby, and their votes were the last ones required.
                pass
            elif message.author in lobby.filterVotes:
                return message.author.mention + ' ' + FILTER_FAILURE_VOTED

            lobby.filterVotesNeeded = len(module.getLobbyMembers(lobby))
            lobby.filterVotes.append(message.author)

            if len(lobby.filterVotes) >= lobby.filterVotesNeeded:
                lobby.filterVotesNeeded = 0
                lobby.filterVotes = []
                lobby.filter = False
                return FILTER_DISABLE_SUCCESS
            else:
                return message.author.mention + ' ' + FILTER_DISABLE_VOTED.format(
                    count=lobby.filterVotesNeeded - len(lobby.filterVotes),
                    plural='** is' if lobby.filterVotesNeeded - len(lobby.filterVotes) == 1 else 's** are'
                )
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
            if not module.channelInLobby(message.channel):
                return

            lobby = module.getLobby(member=message.author)
            if not lobby:
                return message.author.mention + ' ' + LOBBY_FAILURE_MISSING_LOBBY
            elif not lobby.textChannel:
                return message.author.mention + ' ' + LOG_NO_TEXT

            confirmationMessage = LOG_CONFIRM_1
            confMsgObj = await client.send_message(message.channel, confirmationMessage)
            async with message.channel.typing():
                chatlog = await module.getChatLog(lobby, confirmationMessage)

            await confMsgObj.edit(content=LOG_CONFIRM_2)
            async with message.author.typing():
                file = discord.File(BytesIO(bytes(chatlog, 'utf-8')), filename='lobby-chatlog-{}.txt'.format(int(message.created_at.timestamp())))
                await client.send_message(message.channel, file)
            await confMsgObj.edit(content=LOG_CONFIRM_3)
    class LobbyChatLogCMD_Variant1(LobbyChatLogCMD): NAME = 'getchatlog'
    class LobbyChatLogCMD_Variant2(LobbyChatLogCMD): NAME = 'chatlog'

    def __init__(self, client):
        Module.__init__(self, client)
        
        self.activeLobbies = {}
        self.lobbyChannel = Config.getModuleSetting('lobbies', 'interaction')
        self.logChannel = client.get_channel(Config.getModuleSetting('lobbies', 'log_channel'))
        self.unvisitedExpiryWarningTime = assertType(Config.getModuleSetting('lobbies', 'unvisited_expiry_warning_time'), int, otherwise=600)
        self.unvisitedExpiryTime = assertType(Config.getModuleSetting('lobbies', 'unvisited_expiry_time'), int, otherwise=300)
        self.visitedExpiryWarningTime = assertType(Config.getModuleSetting('lobbies', 'visited_expiry_warning_time'), int, otherwise=518400)
        self.visitedExpiryTime = assertType(Config.getModuleSetting('lobbies', 'visited_expiry_time'), int, otherwise=86400)

    def loopIteration(self):
        self.client.loop.create_task(self.bumpInactiveLobbies())

    def channelInLobby(self, channel):
        if not self.channelIsDM(channel):
            return channel.category and channel.category.name.startswith('Lobby')
        return False

    def channelIsDM(self, channel):
        return assertClass(channel, discord.DMChannel, otherwise=False)

    def getLobby(self, **kwargs):
        if kwargs.get('id', None):
            for lobby in self.activeLobbies.values():
                if lobby.id == kwargs['id']:
                    return lobby
        elif kwargs.get('role', None):
            for lobby in self.activeLobbies.values():
                if kwargs['role'] in (lobby.role, lobby.ownerRole, lobby.modRole):
                    return lobby
        elif kwargs.get('name', None):
            for lobby in self.activeLobbies.values():
                if lobby.customName.lower() == kwargs['name'].lower():
                    return lobby
        user = kwargs.get('member', None) or kwargs.get('owner', None)
        if user:
            role = discord.utils.find(lambda r: 'lobby-' in r.name, user.roles)
            return self.getLobby(role=role)

    def getLobbyOwner(self, lobby):
        return discord.utils.find(lambda m: lobby.ownerRole in m.roles, self.client.rTTR.members)

    def getLobbyMembers(self, lobby, withOwner=True):
        members = [member for member in filter(
            lambda m: (lobby.role in m.roles or lobby.modRole in m.roles) and not lobby.ownerRole in m.roles, 
            self.client.rTTR.members
        )]
        if withOwner:
            members += [self.getLobbyOwner(lobby)]
        return members

    async def on_message(self, message):
        if self.channelInLobby(message.channel):
            lobby = self.getLobby(id=message.channel.category.id)
            lobby.lastVisited = time.mktime(time.gmtime())
            lobby.expiryWarning = None

            moderation = self.client.requestModule('moderation')
            if lobby.filter and moderation:
                filterActivated = await moderation.filterBadWords(message, silentFilter=True)
                if filterActivated and not lobby.filterWarning:
                    lobby.filterWarning = True
                    await self.client.send_message(
                        message.channel, 
                        message.author.mention + ' ' + FILTER_WARNING
                    )

    async def on_message_edit(self, before, after):
        message = after
        if self.channelInLobby(message.channel):
            lobby = self.getLobby(id=message.channel.category.id)
            lobby.lastVisited = time.mktime(time.gmtime())
            lobby.expiryWarning = None

            moderation = self.client.requestModule('moderation')
            if lobby.filter and moderation:
                filterActivated = await moderation.filterBadWords(message, edited=' edited ', silentFilter=True)
                if filterActivated and not lobby.filterWarning:
                    lobby.filterWarning = True
                    await self.client.send_message(
                        message.channel, 
                        message.author.mention + ' ' + FILTER_WARNING
                    )

    async def on_voice_state_update(self, member, before, after):
        if after.channel and self.channelInLobby(after.channel):
            lobby = self.getLobby(id=after.channel.category.id)
            lobby.lastVisited = time.mktime(time.gmtime())
            lobby.expiryWarning = None

    async def restoreSession(self):
        discordModRole = discord.utils.get(self.client.rTTR.roles, name='Discord Mods')
        dmrPos = discordModRole.position
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
                lobby.modRole = discord.utils.get(self.client.rTTR.roles, name='lobby-{}-mod'.format(category.id))
                lobby.created = category.created_at.timestamp()
                match = re.match(r'Lobby \[(.+)\]', category.name)
                if match:
                    lobby.customName = match.group(1)

                if lobby.textChannel:
                    # Get the last three messages sent in the text channel.
                    # There's only three things we want that might show up at once:
                    #
                    #   User: badword           The last visited message from a user.
                    #   Bot:  FILTER_WARNING    The bot's filter warning.
                    #     [time passes]
                    #   Bot:  BUMP_WARNING      The bot's lobby expiry warning.
                    lastMessages = await category.channels[0].history(limit=3).flatten()
                    for message in lastMessages:
                        if message.author == self.client.rTTR.me:
                            if FILTER_WARNING in message.content:
                                lobby.filterWarning = True
                            elif BUMP_WARNING_UNVISITED[:45] in message.content or BUMP_WARNING_VISITED[:45] in message.content:
                                lobby.expiryWarning = message.created_at.timestamp()
                        else:
                            lobby.lastVisited = message.created_at.timestamp()
                            break  # We already found the last visited message; this is the most recent time.

                # Make sure that we're not missing anything the lobby uses.
                # If we are, we can try and restore it.
                if not lobby.ownerRole or not self.getLobbyOwner(lobby):
                    # There's not much that can be done here. We don't know who the owner is.
                    if lobby.ownerRole:
                        print('Lobby {} has no user assigned to its owner role. The lobby will be disbanded.'.format(lobby.id))
                        auditLogReason = 'Lobby had no user assigned to its owner role, so it could not be restored.'
                    else:
                        print('Lobby {} has no owner role assigned to it. The lobby will be disbanded.'.format(lobby.id))
                        auditLogReason = 'Lobby had no owner role, so it could not be restored.'
                    await lobby.category.delete(reason=auditLogReason)
                    if lobby.textChannel: await lobby.textChannel.delete(reason=auditLogReason)
                    if lobby.voiceChannel: await lobby.voiceChannel.delete(reason=auditLogReason)
                    if lobby.role: await lobby.role.delete(reason=auditLogReason)
                    if lobby.modRole: await lobby.modRole.delete(reason=auditLogReason)
                    continue
                if not lobby.textChannel and not lobby.voiceChannel:
                    print('Lobby {} has no channels assigned to it. Assigning both a text channel and a voice channel...'.format(lobby.id))
                    lobby.textChannel = await self.client.rTTR.create_text_channel(
                        name="text-lobby",
                        category=lobby.category,
                        reason='Lobby had no channels, so a restore was performed.'
                    )
                    lobby.voiceChannel = await self.client.rTTR.create_voice_channel(
                        name='Voice Lobby',
                        category=lobby.category,
                        reason='Lobby had no channels, so a restore was performed.'
                    )
                    await self.client.send_message(self.getLobbyOwner(lobby), CORRUPTED_CHANNELS)
                if not lobby.role:
                    print('Lobby {} has no member role assigned to it. One is being created...'.format(lobby.id))
                    lobby.role = await self.client.rTTR.create_role(
                        name='lobby-{}'.format(lobby.id),
                        reason='Lobby had no member role, so a restore was performed.'
                    )
                    await self.client.send_message(self.getLobbyOwner(lobby), CORRUPTED_ROLE_MEMBER)
                    await lobby.category.set_permissions(lobby.role, read_messages=True, embed_links=True)
                    dmrPos += 1
                if not lobby.modRole:
                    print('Lobby {} has no mod role assigned to it. One is being created...'.format(lobby.id))
                    lobby.modRole = await self.client.rTTR.create_role(
                        name='lobby-{}-mod'.format(lobby.id),
                        reason='Lobby had no mod role, so a restore was performed.'
                    )
                    await lobby.category.set_permissions(lobby.modRole, send_messages=True, add_reactions=True, speak=True)
                    if discordModRole:
                        await lobby.modRole.edit(position=dmrPos + 1)

                self.activeLobbies[lobby.id] = lobby
        await self.bumpInactiveLobbies()

    async def bumpInactiveLobbies(self):
        inactiveLobbies = []
        for lobby in self.activeLobbies.values():
            # If the lobby has not been visited...
            if not lobby.lastVisited and not lobby.expiryWarning and time.mktime(time.gmtime()) - lobby.created >= self.unvisitedExpiryWarningTime:
                lobby.expiryWarning = time.mktime(time.gmtime())
                target = discord.utils.find(lambda m: lobby.ownerRole in m.roles, self.client.rTTR.members) if not lobby.textChannel else lobby.textChannel
                await self.client.send_message(target, BUMP_WARNING_UNVISITED.format(time=getTimeFromSeconds(self.unvisitedExpiryTime, oneUnitLimit=True))
                )
            # If the lobby was last visited...
            elif lobby.lastVisited and not lobby.expiryWarning and time.mktime(time.gmtime()) - lobby.lastVisited >= self.visitedExpiryWarningTime:
                lobby.expiryWarning = time.mktime(time.gmtime())
                target = discord.utils.find(lambda m: lobby.ownerRole in m.roles, self.client.rTTR.members) if not lobby.textChannel else lobby.textChannel
                await self.client.send_message(target, BUMP_WARNING_VISITED.format(time=getTimeFromSeconds(self.visitedExpiryTime, oneUnitLimit=True))
                )
            # If the lobby was visited and an expiry warning was sent...
            # OR
            # If the lobby was not visited and an expiry warning was sent...
            elif lobby.expiryWarning and time.mktime(time.gmtime()) - lobby.expiryWarning >= (self.visitedExpiryTime if lobby.lastVisited else self.unvisitedExpiryTime):
                for member in filter(lambda m: lobby.role in m.roles, self.client.rTTR.members):
                    await self.client.send_message(member, BUMP_MEMBER)
                owner = discord.utils.find(lambda m: lobby.ownerRole in m.roles, self.client.rTTR.members)
                await self.client.send_message(owner, BUMP_OWNER)
                
                if lobby.textChannel:
                    savingMessage = LOG_CONFIRM_4
                    savingMsgObj = await self.client.send_message(owner, savingMessage)
                    async with owner.typing():
                        chatlog = await self.getChatLog(lobby, savingMessage)

                auditLogReason = 'Lobby hit expiration date of {}'.format(
                    getTimeFromSeconds(self.visitedExpiryTime if lobby.lastVisited else self.unvisitedExpiryTime, oneUnitLimit=True))
                if lobby.textChannel: await lobby.textChannel.delete(reason=auditLogReason)
                if lobby.voiceChannel: await lobby.voiceChannel.delete(reason=auditLogReason)
                await lobby.category.delete(reason=auditLogReason)
                await lobby.role.delete(reason=auditLogReason)
                await lobby.modRole.delete(reason=auditLogReason)
                await lobby.ownerRole.delete(reason=auditLogReason)
                inactiveLobbies.append(lobby)

                if lobby.textChannel:
                    await savingMsgObj.delete()
                    confirmationMessage = await self.client.send_message(owner, LOG_CONFIRM_5)
                    async with owner.typing():
                        file = discord.File(BytesIO(bytes(chatlog, 'utf-8')), filename='lobby-chatlog-{}.txt'.format(int(lobby.created)))
                        await self.client.send_message(owner, file)
                    await confirmationMessage.edit(content=LOG_CONFIRM_6)

        for inactiveLobby in inactiveLobbies:
            del self.activeLobbies[inactiveLobby.id]

    async def getChatLog(self, lobby, savingMessage=None):
        if not lobby.textChannel:
            return LOG_NO_TEXT

        chatlog = ""
        participants = []
        creator = self.getLobbyOwner(lobby)
        messages = await lobby.textChannel.history(limit=None).flatten()
        messages.reverse()
        for m in messages:
            if savingMessage and m.content == savingMessage:
                continue
            participant = m.author.name + '#' + m.author.discriminator + (' [BOT]' if m.author.bot else '')
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


module = LobbyManagement