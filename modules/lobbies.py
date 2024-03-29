import discord
import time
import re
from io import BytesIO
from datetime import datetime
from extra.commands import Command
from modules.module import Module
from utils import Config, assert_type, assert_class, get_time_from_seconds, database, make_count_of_string, make_list_from_string

LOBBY_FAILURE_GUILD = 'Sorry, but you need to be in the Toontown Rewritten Discord to use lobbies.'
LOBBY_FAILURE_MISSING_LOBBY = "You're not currently in a lobby."
LOBBY_FAILURE_MISSING_NAME = "I'm not sure which lobby you're referring to. Please make sure you've typed the lobby name correctly -- casing counts!"

CREATION_FAILURE_OWNER = "You own too many lobbies right now. You'll have to `~disbandLobby` to create a new one."
CREATION_FAILURE_NAME_LENGTH = 'Your lobby name must be 30 characters or less.'
CREATION_FAILURE_NAME_MISSING = 'Give your lobby a name!'
CREATION_FAILURE_NAME_GENERIC = 'Please choose a different name.'
CREATION_SUCCESS = 'Your lobby has been created!'

INVITATION_FAILURE_MISSING_LOBBY = "I'm not sure which lobby you're referring to. Please provide the lobby name first and then the users, or you can use the command in the lobby you're referring to."
INVITATION_FAILURE_MISSING_MENTION = 'I need a mention of the user you want to invite to your lobby.'
INVITATION_FAILURE_NARCISSISTIC = 'No need to invite yourself to the lobby!'
INVITATION_FAILURE_PARTIAL = 'Some of the invites could not be sent out:'
INVITATION_FAILURE_FULL = 'None of the invites could be sent out:'
INVITATION_FAILURE_MESSAGE = 'Could not send messages out to these users: '
INVITATION_FAILURE_BOT = 'Can not send invites to bots: '
INVITATION_FAILURE_PENDING = 'An invite is already pending for these users: '
INVITATION_FAILURE_JOINED = 'These users are already in the lobby: '
INVITATION_MESSAGE_1 = "Hey there, {invitee}! {author} has invited you to join their private lobby on the Toontown Rewritten Discord. {filter_status}" \
                        "\n\nIf you're not interested, you can ignore this message. To accept, copy & paste the following here or in #{lobby_channel}:"
INVITATION_MESSAGE_2 = '~acceptLobbyInvite {}'
INVITATION_MESSAGE_FILTER = 'Note that the bad word filter in this lobby is **disabled**, and you should not accept this invite if you are of a younger age. Anything 18+ will still be moderated.'
INVITATION_SUCCESS = 'Invite{plural} sent!'
INVITATION_SUCCESS_PARTIAL = 'But otherwise, invites sent!'

UNINVITE_FAILURE_MISSING_LOBBY = "I'm not sure which lobby you're referring to. Please provide the lobby name first and then the users, or you can use the command in the lobby you're referring to."
UNINVITE_FAILURE_MEMBER = "You must be the owner of the lobby to uninvite another user."
UNINVITE_FAILURE_SELF = "You can't uninvite yourself to a lobby, please use `~leaveLobby` *(or `~disbandLobby` if you created the lobby)* to leave."
UNINVITE_FAILURE_NOT_INVITED = 'Could not uninvite any of the mentioned users, because either none of them were invited to start with or they already accepted.'
UNINVITE_FAILURE_NOT_INVITED_OTHERS = "Could not uninvite some users because they weren't invited to begin with or had already accepted. Otherwise, all other mentioned invites have been voided."
UNINVITE_FAILURE_MISSING_MENTION = 'I need a mention of the user you want to uninvite from your lobby.'
UNINVITE_SUCCESS = 'The mentioned user{plural} taken off the invitation list.'

KICK_FAILURE_NO_NAME = "You own multiple lobbies right now. Please use the name of the lobby you wish to perform the kick in."
KICK_FAILURE_MEMBER = "You must be the owner of the lobby to kick users from it."
KICK_FAILURE_SELF = 'No need to kick yourself from the lobby, that would be anarchy! You can use `~leaveLobby` *(or `~disbandLobby` if you created the lobby)* to leave.'
KICK_FAILURE_NONMEMBER = 'Could not kick any of the mentioned users, because none of them were currently in the lobby.'
KICK_FAILURE_NONMEMBER_OTHERS = 'Could not kick some users because they were not in the lobby. But otherwise, kicks have been issued!'
KICK_FAILURE_MISSING_MENTION = 'I need a mention of the user you want to kick from your lobby.'
KICK_MESSAGE = "You've been kicked from the **{lobby_name}** lobby."
KICK_SUCCESS = 'The mentioned user{plural} successfully kicked.'

RSVP_FAILURE_MISSING_ID = 'Please reference the Lobby ID provided to you like this: `~acceptLobbyInvite lobbyid`'
RSVP_FAILURE_ID = "Sorry, but I didn't recognize that Lobby ID. The Lobby may have been disbanded or the invite may have expired."
RSVP_FAILURE_OWNER = 'Sorry, but you cannot join another lobby until you have left your own lobby. You can do this by typing `~disbandLobby`.'
RSVP_FAILURE_MEMBER = 'Sorry, but you cannot join another lobby until you have left your own lobby. You can do this by typing `~leaveLobby`.'
RSVP_FAILURE_UNINVITED = "Sorry, but you weren't invited to that lobby or the invite was rescinded."
RSVP_SUCCESS = "You're now in the **{name}** lobby! Have fun!"

LEAVE_FAILURE_NO_NAME = "You're participating in multiple lobbies right now. Please use the name of the lobby you wish to leave."
#LEAVE_FAILURE_OWNER = "You own all the lobbies you're participating in, meaning you need to use `~disbandLobby <lobby name>` to ensure you actually want to disband a lobby."
LEAVE_FAILURE_OWNER_SPECIFIC = 'You own the **{name}** lobby, meaning you need to use `~disbandLobby` to ensure you actually want to disband the lobby.'

DISBAND_FAILURE_NO_NAME = "You own multiple lobbies right now. Please use the name of the lobby you wish to disband."
DISBAND_FAILURE_MEMBER = "You don't own the **{}** lobby, meaning you need to use `~leaveLobby` to part with the group."
DISBAND_FAILURE_STRANGER = "You don't own the **{}** lobby."
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
    NAME = 'Lobbies'

    class CreateLobbyCMD(Command):
        """~createLobby <lobby name>

            This will create you a lobby with a text channel and a voice channel.
            You can also choose to have a lobby with only one of those two by doing:
                `~createTextLobby`
                `~createVoiceLobby`
        """
        NAME = 'createLobby'

        @staticmethod
        async def execute(client, module, message, *args, text_channel_only=False, voice_channel_only=False):
            if message.channel.id != module.lobby_channel and not module.channel_is_dm(message.channel) and not module.channel_in_lobby(message.channel):
                return

            lobbies_owned = len(module.get_owner_lobbies(message.author))
            audit_log_reason = 'Lobby created by {}'.format(str(message.author))

            if lobbies_owned >= module.max_lobby_owner:
                return message.author.mention + ' ' + CREATION_FAILURE_OWNER

            moderation = client.request_module('moderation')
            name = ' '.join(args)
            if moderation:
                try:
                    filter_activated = await moderation.filter_bad_words(message)
                    if filter_activated:
                        return
                except discord.errors.NotFound:
                    # If a Not Found error returned, that means that it tried to remove something
                    # that contained a bad word, meaning we're safe to stop making the lobby.
                    return
            if len(name) > module.max_name_length:
                return message.author.mention + ' ' + CREATION_FAILURE_NAME_LENGTH
            elif not name:
                return message.author.mention + ' ' + CREATION_FAILURE_NAME_MISSING
            elif module.active_lobbies.select(where=['name=?', name]):
                return message.author.mention + ' ' + CREATION_FAILURE_NAME_GENERIC

            category = await client.focused_guild.create_category(name='Lobby [{}]'.format(name), reason=audit_log_reason)
            mod_role = discord.utils.get(client.focused_guild.roles, name='Moderators')
            await category.set_permissions(client.focused_guild.default_role, read_messages=False)
            await category.set_permissions(message.author, read_messages=True, send_messages=True)
            await category.set_permissions(
                mod_role,
                read_messages=True,
                send_messages=False,
                manage_messages=True,
                manage_roles=False,
                manage_channels=False,
                add_reactions=False,
                connect=True,
                speak=False
            )

            if not voice_channel_only:
                text_channelID = await client.focused_guild.create_text_channel(
                    name="text-lobby",
                    category=category,
                    reason=audit_log_reason
                )
                text_channelID = text_channelID.id
            else:
                text_channelID = None
            if not text_channel_only:
                voice_channel_id = await client.focused_guild.create_voice_channel(
                    name='Voice Lobby',
                    category=category,
                    reason=audit_log_reason
                )
                voice_channel_id = voice_channel_id.id
            else:
                voice_channel_id = None

            module.active_lobbies.insert(
                category_id=category.id,
                text_channel_id=text_channelID,
                voice_channel_id=voice_channel_id,
                owner_id=message.author.id,
                created=time.time(),
                name=name
            )

            return message.author.mention + ' ' + CREATION_SUCCESS
    class CreateLobbyCMD_Variant1(CreateLobbyCMD): NAME = 'createlobby'

    class CreateTextLobbyCMD(Command):
        NAME = 'createTextLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            return await module.CreateLobbyCMD.execute(client, module, message, *args, text_channelOnly=True)
    class CreateTextLobbyCMD_Variant1(CreateTextLobbyCMD): NAME = 'createtextlobby'

    class CreateVoiceLobbyCMD(Command):
        NAME = 'createVoiceLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            return await module.CreateLobbyCMD.execute(client, module, message, *args, voice_channel_only=True)
    class CreateVoiceLobbyCMD_Variant1(CreateVoiceLobbyCMD): NAME = 'createvoicelobby'

    class LobbyInviteCMD(Command):
        """~invite [lobby name] <mention> [mentions]

            This will send a DM to another user(s) asking them to join a lobby you're in.
            If they accept, they'll be able to see and chat within the lobby.

            If you are in multiple lobbies, you'll need to specify the lobby name (or use
            the invite command inside the lobby you want to invite them to).
        """
        NAME = 'invite'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.id != module.lobby_channel and not module.channel_is_dm(message.channel) and not module.channel_in_lobby(message.channel):
                return

            lobby = None
            one_lobby = module.get_lobby(member=message.author) or module.get_lobby(owner=message.author)
            if module.channel_in_lobby(message.channel):
                lobby = module.active_lobbies.select(
                    where=['text_channel_id=?', message.channel.id],
                    limit=1
                )
            elif not one_lobby:
                return message.author.mention + ' ' + LOBBY_FAILURE_MISSING_LOBBY
            elif len(module.get_lobbies(member=message.author)) + len(module.get_lobbies(owner=message.author)) == 1:
                lobby = one_lobby
            elif len(args) > len(message.mentions):
                lobby = module.get_lobby(name=' '.join(args[:len(args) - len(message.mentions)]))
                if not lobby:
                    return message.author.mention + ' ' + LOBBY_FAILURE_MISSING_NAME

            if not lobby:
                return message.author.mention + ' ' + INVITATION_FAILURE_MISSING_LOBBY
            elif not message.mentions:
                return message.author.mention + ' ' + INVITATION_FAILURE_MISSING_MENTION
            elif len(message.mentions) == 1 and message.mentions[0] == message.author:
                return message.author.mention + ' ' + INVITATION_FAILURE_NARCISSISTIC
            elif message.author in message.mentions:
                message.mentions.remove(message.author)

            failed_messages = []
            failed_bot = []
            failed_pending_invite = []
            failed_joined = []
            for user in message.mentions:
                if user.bot:
                    failed_bot.append(user.mention)
                    continue

                if str(user.id) in lobby['invited_ids']:
                    failed_pending_invite.append(user.mention)
                    continue

                if str(user.id) in lobby['member_ids']:
                    failed_joined.append(user.mention)
                    continue

                try:
                    module.active_lobbies.update(
                        where=['id=?', lobby['id']],
                        invited_ids=','.join([i for i in lobby['invited_ids'].split(',') if i] + [str(user.id)])
                    )
                    await user.send(INVITATION_MESSAGE_1.format(
                            invitee=user.mention,
                            author=message.author.mention,
                            filter_status=INVITATION_MESSAGE_FILTER if not lobby['filter_enabled'] else '',
                            lobby_channel=client.focused_guild.get_channel(module.lobby_channel).name
                        )
                    )
                    await user.send(INVITATION_MESSAGE_2.format(lobby['id']))
                except discord.HTTPException as e:
                    failed_messages.append(user.mention)
            response = INVITATION_FAILURE_PARTIAL
            if failed_messages:
                response += '\n\t' + INVITATION_FAILURE_MESSAGE + ' '.join(failed_messages)
            if failed_bot:
                response += '\n\t' + INVITATION_FAILURE_BOT + ' '.join(failed_bot)
            if failed_pending_invite:
                response += '\n\t' + INVITATION_FAILURE_PENDING + ' '.join(failed_pending_invite)
            if failed_joined:
                response += '\n\t' + INVITATION_FAILURE_JOINED + ' '.join(failed_joined)
            if len(failed_messages + failed_bot + failed_pending_invite + failed_joined) == len(message.mentions):
                response = response.replace(INVITATION_FAILURE_PARTIAL, INVITATION_FAILURE_FULL)
            elif response == INVITATION_FAILURE_PARTIAL:
                response = INVITATION_SUCCESS.format(plural='s' if len(message.mentions) > 1 else '')
            else:
                response += '\n' + INVITATION_SUCCESS_PARTIAL
            return message.author.mention + ' ' + response

    class LobbyUninviteCMD(Command):
        """~uninvite [lobby name] <mention> [mentions]

            This will void an invite to your lobby that was sent to a user.
            You must be the owner of the lobby to use this command.
        """
        NAME = 'uninvite'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.id != module.lobby_channel and not module.channel_is_dm(message.channel) and not module.channel_in_lobby(message.channel):
                return
            message.author = client.focused_guild.get_member(message.author.id)
            if not message.author:
                return LOBBY_FAILURE_GUILD

            lobby = None
            one_lobby = module.get_lobby(owner=message.author)
            if module.channel_in_lobby(message.channel):
                lobby = module.active_lobbies.select(
                    where=['text_channel_id=?', message.channel.id],
                    limit=1
                )
            elif not one_lobby:
                return LOBBY_FAILURE_MISSING_LOBBY
            elif len(module.get_lobbies(owner=message.author)) == 1:
                lobby = one_lobby
            elif len(args) > len(message.mentions):
                lobby = module.get_lobby(name=' '.join(args[:len(args) - len(message.mentions)]))
                if not lobby:
                    return message.author.mention + ' ' + UNINVITE_FAILURE_NAME

            if not lobby:
                return message.author.mention + ' ' + UNINVITE_FAILURE_MISSING_LOBBY
            elif message.author.id != lobby['owner_id']:
                return message.author.mention + ' ' + UNINVITE_FAILURE_MEMBER
            elif not message.mentions:
                return message.author.mention + ' ' + UNINVITE_FAILURE_MISSING_MENTION
            elif len(message.mentions) == 1 and message.mentions[0] == message.author:
                return message.author.mention + ' ' + UNINVITE_FAILURE_SELF
            elif message.author in message.mentions:
                message.mentions.remove(message.author)

            failed_not_invited = []
            for user in message.mentions:
                if str(user.id) not in lobby['invited_ids']:
                    failed_not_invited.append(user.mention)
                    continue

                module.active_lobbies.update(
                    where=['id=?', lobby['id']],
                    invited_ids=','.join([i for i in lobby['invited_ids'] if i != user.id])
                )
            if len(failed_not_invited) == len(message.mentions):
                return message.author.mention + ' ' + UNINVITE_FAILURE_NOT_INVITED
            elif failed_not_invited:
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
            if message.channel.id != module.lobby_channel and not module.channel_is_dm(message.channel) and not module.channel_in_lobby(message.channel):
                return

            if not args:
                return message.author.mention + ' ' + RSVP_FAILURE_MISSING_ID

            try:
                lobby = int(args[0])
            except ValueError:
                lobby = args[0]

            lobby = module.get_lobby(id=lobby)
            if not lobby:
                return message.author.mention + ' ' + RSVP_FAILURE_ID
                
            message.author = client.focused_guild.get_member(message.author.id)
            if not message.author:
                return LOBBY_FAILURE_GUILD

            if str(message.author.id) not in lobby['invited_ids']:
                return message.author.mention + ' ' + RSVP_FAILURE_UNINVITED

            category = discord.utils.get(client.focused_guild.categories, id=lobby['category_id'])
            await category.set_permissions(message.author, read_messages=True, send_messages=True)

            module.active_lobbies.update(
                where=['id=?', lobby['id']],
                invited_ids=','.join([i for i in lobby['invited_ids'].split(',') if i and int(i) != message.author.id]),
                member_ids=','.join([i for i in lobby['member_ids'].split(',') if i] + [str(message.author.id)])
            )
            if lobby['text_channel_id']:
                await client.send_message(lobby['text_channel_id'], '{} has joined the lobby!'.format(message.author.mention))

            return message.author.mention + ' ' + RSVP_SUCCESS.format(name=lobby['name'])
    class LobbyInviteAcceptCMD_Variant1(LobbyInviteAcceptCMD): NAME = 'acceptlobbyinvite'

    class LobbyKickCMD(Command):
        """~kickFromLobby [lobby name] <mention>

            This allows you to remove a user from your lobby, you must be the owner to do this.
            The user must receive another invite to re-join the lobby.
        """
        NAME = 'kickFromLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            if not module.channel_is_dm(message.channel) and not module.channel_in_lobby(message.channel):
                return
            message.author = client.focused_guild.get_member(message.author.id)
            if not message.author:
                return LOBBY_FAILURE_GUILD

            lobby = None
            lobbies_owned = module.get_lobbies(owner=message.author)
            if module.channel_in_lobby(message.channel):
                lobby = module.active_lobbies.select(
                    where=['text_channel_id=?', message.channel.id],
                    limit=1
                )
            elif len(lobbies_owned) == 1:
                lobby = module.get_lobby(owner=message.author)
            elif len(args) <= len(message.mentions):
                return message.author.mention + ' ' + KICK_FAILURE_NO_NAME
            else:
                lobby = module.get_lobby(name=' '.join(args[:len(args) - len(message.mentions)]))
                if not lobby:
                    return message.author.mention + ' ' + LOBBY_FAILURE_MISSING_NAME

            if not lobby:
                return message.author.mention + ' ' + LOBBY_FAILURE_MISSING_LOBBY
            elif message.author.id != lobby['owner_id']:
                return message.author.mention + ' ' + KICK_FAILURE_MEMBER
            elif not message.mentions:
                return message.author.mention + ' ' + KICK_FAILURE_MISSING_MENTION
            elif len(message.mentions) == 1 and message.mentions[0] == message.author:
                return message.author.mention + ' ' + KICK_FAILURE_SELF
            elif message.author in message.mentions:
                message.mentions.remove(message.author)

            failed_not_member = []
            for user in message.mentions:
                if module.get_lobby(member=user) != lobby:
                    failed_not_member.append(user.mention)
                    continue

                category = discord.utils.get(client.focused_guild.categories, id=lobby['category_id'])
                await category.set_permissions(user, overwrite=None, reason='User got kicked from lobby')

                module.active_lobbies.update(where=['id=?', lobby['id']], member_ids=','.join([str(i) for i in lobby['member_ids'].split(',') if i and int(i) != user.id]))

                if lobby['text_channel_id']:
                    await client.send_message(lobby['text_channel_id'], '{} has left the lobby.'.format(user.mention))
                try:
                    await user.send(KICK_MESSAGE.format(lobby_name=lobby['name']))
                except discord.HTTPException as e:
                    pass
            if len(failed_not_member) == len(message.mentions):
                return message.author.mention + ' ' + KICK_FAILURE_NONMEMBER
            elif failed_not_member:
                return message.author.mention + ' ' + KICK_FAILURE_NONMEMBER_OTHERS
            else:
                return message.author.mention + ' ' + KICK_SUCCESS.format(plural='s were' if len(message.mentions) > 1 else ' was')
    class LobbyKickCMD_Variant1(LobbyKickCMD): NAME = 'kickfromlobby'

    class LobbyLeaveCMD(Command):
        """~leaveLobby [lobby name]

            This will leave the lobby you are currently in.
            You will no longer be able to see and chat within the lobby and you'll need to ask for another invite to rejoin.
            If you own the lobby, use `~disbandLobby` instead.
        """
        NAME = 'leaveLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.id != module.lobby_channel and not module.channel_is_dm(message.channel) and not module.channel_in_lobby(message.channel):
                return
            message.author = client.focused_guild.get_member(message.author.id)
            if not message.author:
                return LOBBY_FAILURE_GUILD

            lobby = None
            lobbies_in = module.get_lobbies(member=message.author)
            if len(args):
                lobby = module.get_lobby(name=' '.join(args))
                if not lobby:
                    return message.author.mention + ' ' + LOBBY_FAILURE_MISSING_NAME
            elif module.channel_in_lobby(message.channel):
                lobby = module.active_lobbies.select(
                    where=['text_channel_id=?', message.channel.id],
                    limit=1
                )
            elif len(lobbies_in) == 1:
                lobby = module.get_lobby(member=message.author)
            elif len(lobbies_in):
                return message.author.mention + ' ' + LEAVE_FAILURE_NO_NAME

            if lobby and message.author.id == lobby['owner_id']:
                return message.author.mention + ' ' + LEAVE_FAILURE_OWNER_SPECIFIC.format(name=lobby['name'])
            elif module.get_lobby(owner=message.author):
                return message.author.mention + ' ' + LEAVE_FAILURE_OWNER
            elif not lobby:
                return message.author.mention + ' ' + LOBBY_FAILURE_MISSING_LOBBY

            category = discord.utils.get(client.focused_guild.categories, id=lobby['category_id'])
            await category.set_permissions(message.author, overwrite=None, reason='User left lobby via ~leaveLobby')
            if lobby['text_channel_id']:
                await client.send_message(lobby['text_channel_id'], '{} has left the lobby.'.format(message.author.mention))
    class LobbyLeaveCMD_Variant1(LobbyLeaveCMD): NAME = 'leavelobby'

    class LobbyDisbandCMD(Command):
        """~disbandLobby [lobby name]

            This will disband your lobby if you are the lobby's owner.
        """
        NAME = 'disbandLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.id != module.lobby_channel and not module.channel_is_dm(message.channel) and not module.channel_in_lobby(message.channel):
                return
            message.author = client.focused_guild.get_member(message.author.id)
            if not message.author:
                return LOBBY_FAILURE_GUILD

            lobby = None
            lobbies_owned = module.get_lobbies(owner=message.author)
            if len(args):
                lobby = module.get_lobby(name=' '.join(args))
                if not lobby:
                    return message.author.mention + ' ' + LOBBY_FAILURE_MISSING_NAME
            elif module.channel_in_lobby(message.channel):
                lobby = module.active_lobbies.select(
                    where=['text_channel_id=?', message.channel.id],
                    limit=1
                )
            elif len(lobbies_owned) == 1:
                lobby = module.get_lobby(owner=message.author)
            elif len(lobbies_owned):
                return message.author.mention + ' ' + DISBAND_FAILURE_NO_NAME

            if not lobby:
                return message.author.mention + ' ' + LOBBY_FAILURE_MISSING_LOBBY
            elif message.author.id != lobby['owner_id']:
                if str(message.author.id) in lobby['member_ids']:
                    return message.author.mention + ' ' + DISBAND_FAILURE_MEMBER.format(lobby['name'])
                else:
                    return message.author.mention + ' ' + DISBAND_FAILURE_STRANGER.format(lobby['name'])
            
            if lobby['text_channel_id']:
                saving_message = DISBAND_LOG_SAVE
                saving_msg_obj = await client.send_message(message.channel, saving_message)
                async with message.channel.typing():
                    chatlog = await module.get_chat_log(lobby, saving_message)

            members = [int(i) for i in lobby['member_ids'].split(',') if i]

            audit_log_reason = 'User disbanded lobby via ~disbandLobby'
            category = discord.utils.get(client.focused_guild.categories, id=lobby['category_id'])
            if category:
                for channel in category.channels:
                    await channel.delete(reason=audit_log_reason)
                await category.delete(reason=audit_log_reason)
            for member in members:
                await client.send_message(member, DISBAND_SUCCESS_MEMBER.format(lobby['name']))
            await client.send_message(module.lobby_channel if message.channel.id == module.lobby_channel else message.author, 
                message.author.mention + ' ' + DISBAND_SUCCESS)
            module.active_lobbies.delete(where=['id=?', lobby['id']])

            if lobby['text_channel_id']:
                try:
                    # This really only matters if the command was not sent in a lobby.
                    await saving_msg_obj.delete()
                except discord.errors.NotFound:
                    pass
                confirmation_message = await client.send_message(message.author, LOG_CONFIRM_2)
                async with message.author.typing():
                    file = discord.File(BytesIO(bytes(chatlog, 'utf-8')), filename='lobby-chatlog-{}.txt'.format(lobby['name']))
                    await client.send_message(message.author, file)
                await confirmation_message.edit(content=LOG_CONFIRM_3)
                if module.log_channel:
                    await client.send_message(module.log_channel, LOG_CONFIRM_MOD.format(lobby['name']))
                    async with module.log_channel.typing():
                        file = discord.File(BytesIO(bytes(chatlog, 'utf-8')), filename='lobby-chatlog-{}.txt'.format(lobby['name']))
                        await client.send_message(module.log_channel, file)
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
            lobby = module.get_lobby(name=name)
            if not lobby and message.channel.category and message.channel.category.name.startswith('Lobby'):
                lobby = module.get_lobby(id=message.channel.category.id)

            if not name and not lobby:
                return message.author.mention + ' ' + FORCE_FAILURE_MISSING_NAME
            elif not lobby:
                return message.author.mention + ' ' + FORCE_FAILURE_MISSING_LOBBY.format(name=name)
            
            if lobby['text_channel_id']:
                #saving_message = DISBAND_LOG_SAVE
                #saving_msg_obj = await client.send_message(message.channel, saving_message)
                async with message.channel.typing():
                    chatlog = await module.get_chat_log(lobby)

            members = [int(i) for i in lobby['member_ids'].split(',') if i]
            owner = lobby['owner_id']

            audit_log_reason = 'Mod disbanded lobby via ~forceDisband'
            category = discord.utils.get(client.focused_guild.categories, id=lobby['category_id'])
            if category:
                for channel in category.channels:
                    await channel.delete(reason=audit_log_reason)
                await category.delete(reason=audit_log_reason)

            for member in members:
                await client.send_message(member, DISBAND_SUCCESS_MEMBER.format(lobby['name']))
            await client.send_message(owner, FORCE_SUCCESS_OWNER.format(name))
            await client.send_message(module.log_channel if message.channel.id == lobby['text_channel_id'] else lobby['text_channel_id'], message.author.mention + ' ' + FORCE_SUCCESS.format(name))
            module.active_lobbies.delete(where=['id=?', lobby['id']])

            if lobby['text_channel_id']:
                confirmation_message = await client.send_message(int(owner), LOG_CONFIRM_5)
                async with message.author.typing():
                    file = discord.File(BytesIO(bytes(chatlog, 'utf-8')), filename='lobby-chatlog-{}.txt'.format(lobby['name']))
                    await client.send_message(message.author, file)
                await confirmation_message.edit(content=LOG_CONFIRM_6)
                if module.log_channel:
                    await client.send_message(module.log_channel, LOG_CONFIRM_MOD.format(lobby['name']))
                    async with module.log_channel.typing():
                        file = discord.File(BytesIO(bytes(chatlog, 'utf-8')), filename='lobby-chatlog-{}.txt'.format(lobby['name']))
                        await client.send_message(module.log_channel, file)
    class LobbyForceDisbandCMD_Variant1(LobbyForceDisbandCMD): NAME = 'forcedisband'

    class LobbyFilterEnableCMD(Command):
        """~enableFilter

            This re-enables the bad word filter for the lobby.
            Half of the users in the lobby must also use the command to re-enable the bad word filter, to ensure that a majority consents to it.
        """
        NAME = 'enableFilter'

        @staticmethod
        async def execute(client, module, message, *args):
            if not module.channel_in_lobby(message.channel):
                return

            lobby = module.get_lobby(channel=message.channel)
            if not lobby:
                return message.author.mention + ' ' + LOBBY_FAILURE_MISSING_LOBBY
                # Ironic, since it shouldn't get here.

            # The number of filter votes needed is the number of users
            filter_votes_needed = int((make_count_of_string(lobby['member_ids']) - make_count_of_string(lobby['filter_vote_ids'])) / 2)

            moderation = client.request_module('moderation')
            if not moderation:
                return message.author.mention + ' ' + FILTER_ENABLE_FAILURE_MODULE
            elif lobby['filter_enabled']:
                return message.author.mention + ' ' + FILTER_ENABLE_FAILURE_ENABLED
            if filter_votes_needed < 0:
                # Just in case users leave the server or lobby, and their votes were the last ones required.
                pass
            elif str(message.author) in lobby['filter_vote_ids']:
                return message.author.mention + ' ' + FILTER_FAILURE_VOTED

            module.active_lobbies.update(
                where=['id=?', lobby['id']],
                filter_votes_required=filter_votes_needed,
                filter_vote_ids=','.join([i for i in lobby['filter_vote_ids'].split(',') if i] + [str(message.author.id)]),
            )

            if lobby['filter_vote_ids'].count(',') + 1 >= filter_votes_needed:
                module.active_lobbies.update(
                    where=['id=?', lobby['id']],
                    filter_votes_required=0,
                    filter_vote_ids='',
                    filter_enabled=1
                )
                return FILTER_ENABLE_SUCCESS
            else:
                return message.author.mention + ' ' + FILTER_ENABLE_VOTED.format(
                    count=filter_votes_needed,
                    plural='** is' if filter_votes_needed == 1 else 's** are'
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
            if not module.channel_in_lobby(message.channel):
                return

            lobby = module.get_lobby(channel=message.channel)
            if not lobby:
                return message.author.mention + ' ' + LOBBY_FAILURE_MISSING_LOBBY
                # Ironic, since it shouldn't get here.

            # The number of filter votes needed is the number of users
            filter_votes_needed = make_count_of_string(lobby['member_ids']) - make_count_of_string(lobby['filter_vote_ids'])

            if not lobby['filter_enabled']:
                return message.author.mention + ' ' + FILTER_DISABLE_FAILURE_DISABLED
            if filter_votes_needed < 0:
                # Just in case users leave the server or lobby, and their votes were the last ones required.
                pass
            elif str(message.author.id) in lobby['filter_vote_ids']:
                return message.author.mention + ' ' + FILTER_FAILURE_VOTED

            module.active_lobbies.update(
                where=['id=?', lobby['id']],
                filter_votes_required=filter_votes_needed,
                filter_vote_ids=','.join([i for i in lobby['filter_vote_ids'].split(',') if i] + [str(message.author.id)]),
            )

            if filter_votes_needed <= 0:
                module.active_lobbies.update(
                    where=['id=?', lobby['id']],
                    filter_votes_required=0,
                    filter_vote_ids='',
                    filter_enabled=0
                )
                return FILTER_DISABLE_SUCCESS
            else:
                return message.author.mention + ' ' + FILTER_DISABLE_VOTED.format(
                    count=filter_votes_needed,
                    plural='** is' if filter_votes_needed == 1 else 's** are'
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
            if not module.channel_in_lobby(message.channel):
                return

            lobby = module.get_lobby(channel=message.channel)
            if not lobby:
                return message.author.mention + ' ' + LOBBY_FAILURE_MISSING_LOBBY
            elif not lobby['text_channel_id']:
                return message.author.mention + ' ' + LOG_NO_TEXT

            confirmation_message = LOG_CONFIRM_1
            conf_msg_obj = await client.send_message(message.channel, confirmation_message)
            async with message.channel.typing():
                chatlog = await module.get_chat_log(lobby, confirmation_message)

            await conf_msg_obj.edit(content=LOG_CONFIRM_2)
            async with message.author.typing():
                file = discord.File(BytesIO(bytes(chatlog, 'utf-8')), filename='lobby-chatlog-{}.txt'.format(lobby['name']))
                await client.send_message(message.channel, file)
            await conf_msg_obj.edit(content=LOG_CONFIRM_3)
    class LobbyChatLogCMD_Variant1(LobbyChatLogCMD): NAME = 'getchatlog'
    class LobbyChatLogCMD_Variant2(LobbyChatLogCMD): NAME = 'chatlog'

    class LobbyListCMD(Command):
        """~listLobbies

            Lists the lobbies you're participating in. The lobbies that you own will be bolded.
        """
        NAME = 'listLobbies'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.id != module.lobby_channel and not module.channel_is_dm(message.channel) and not module.channel_in_lobby(message.channel):
                return
                
            # If the user is a mod and wants to lookup the lobbies of another user...
            mod = (Config.get_rank_of_user(message.author.id) >= 300 or any([Config.get_rank_of_role(role.id) >= 300 for role in message.author.roles]))
            if not args or not mod:
                user = message.author
            elif not message.mentions:
                if not message.raw_mentions:
                    try:
                        user = client.focused_guild.get_member(int(args[0])) or await client.fetch_user(int(args[0]))
                    except discord.NotFound:
                        return 'No known user'
                    except (ValueError, IndexError):
                        name = ' '.join(args)
                        discriminator = args[-1].split('#')[-1]
                        if discriminator:
                            name = ' '.join(args).rstrip('#0123456789')
                            user = discord.utils.get(message.guild.members, name=name, discriminator=discriminator)
                        user = discord.utils.get(message.guild.members, display_name=name) if not user else user
                        user = discord.utils.get(message.guild.members, name=name) if not user else user
                        if not user:
                            return 'No known user'
                else:
                    try:
                        user = client.focused_guild.get_member(message.raw_mentions[0]) or await client.fetch_user(message.raw_mentions[0])
                    except discord.NotFound:
                        return 'No known user'
            else:
                user = message.mentions[0]

            lobbies_owned = module.get_lobbies(owner=user)
            lobbies_joined = module.get_lobbies(member=user)

            if not lobbies_owned and not lobbies_joined:
                return message.author.mention + ' ' + '{} not participating in any lobbies.'.format("You're" if user==message.author else user.mention + ' is')
            return module.create_discord_embed(
                subtitle='Lobbies',
                info='{}\n{}\n{}'.format(
                    user.mention, 
                    '\n'.join(['**' + lobby['name'] + '**' for lobby in lobbies_owned]),
                    '\n'.join([lobby['name'] for lobby in lobbies_joined])
                ),
                color=discord.Color.blurple(),
                footer=('Bolded lobbies indicate {} own the lobby.'.format('you' if user==message.author else 'they') if lobbies_owned else discord.Embed.Empty)
            )
    class LobbyListCMD_Variant1(LobbyListCMD): NAME = 'listlobbies'

    def __init__(self, client):
        Module.__init__(self, client)
        
        self.active_lobbies = database.create_section(self, 'lobbies', {
            'id': [database.INT, database.PRIMARY_KEY],
            'category_id': database.INT,
            'text_channel_id': database.INT,
            'voice_channel_id': database.INT,
            'owner_id': database.INT,
            'member_ids': [database.TEXT, ''],
            'created': database.INT,
            'name': database.TEXT,
            'invited_ids': [database.TEXT, ''],
            'last_visited': [database.INT, 0],
            'expiry_warning': [database.INT, 0],
            'filter_enabled': [database.INT, 1],
            'filter_vote_ids': [database.TEXT, ''],
            'filter_votes_required': [database.INT, 0],
            'filter_warning': [database.INT, 0]
        })

        self.lobby_channel = Config.get_module_setting('lobbies', 'interaction')
        self.log_channel = client.get_channel(Config.get_module_setting('lobbies', 'log_channel'))
        self.unvisited_expiry_warning_time = assert_type(Config.get_module_setting('lobbies', 'unvisited_expiry_warning_time'), int, otherwise=600)
        self.unvisited_expiry_time = assert_type(Config.get_module_setting('lobbies', 'unvisited_expiry_time'), int, otherwise=300)
        self.visited_expiry_warning_time = assert_type(Config.get_module_setting('lobbies', 'visited_expiry_warning_time'), int, otherwise=518400)
        self.visited_expiry_time = assert_type(Config.get_module_setting('lobbies', 'visited_expiry_time'), int, otherwise=86400)
        self.max_lobby_owner = assert_type(Config.get_module_setting('lobbies', 'max_lobbies_can_own'), int, otherwise=5)
        self.max_name_length = assert_type(Config.get_module_setting('lobbies', 'max_name_length'), int, otherwise=25)

    async def loop_iteration(self):
        await self.bump_inactive_lobbies()

    def channel_in_lobby(self, channel):
        if not self.channel_is_dm(channel):
            return channel.category and channel.category.name.startswith('Lobby')
        return False

    def channel_is_dm(self, channel):
        return assert_class(channel, discord.DMChannel, otherwise=False)

    def get_member_lobbies(self, member):
        lobbies = self.active_lobbies.select(where=['member_ids LIKE ?', "%{}%".format(member.id)])
        return lobbies

    def get_owner_lobbies(self, member):
        lobbies = self.active_lobbies.select(where=['owner_id=?', member.id])
        return lobbies

    def get_lobbies(self, **kwargs):
        limit = kwargs.get('limit', None)
        lobbies = None if limit == 1 else []

        if kwargs.get('id', None):
            lobbies = self.active_lobbies.select(where=['id=?', kwargs['id']], limit=limit)
        elif kwargs.get('name', None):
            lobbies = self.active_lobbies.select(where=['name=?', kwargs['name']], limit=1)
        elif kwargs.get('channel', None):
            lobbies = self.active_lobbies.select(where=['text_channel_id=? OR voice_channel_id=?', kwargs['channel'].id, kwargs['channel'].id], limit=1)
        elif kwargs.get('member', None):
            lobbies = self.active_lobbies.select(where=['member_ids LIKE ?', '%{}%'.format(kwargs['member'].id)], limit=limit)
        elif kwargs.get('owner', None):
            lobbies = self.active_lobbies.select(where=['owner_id=?', kwargs['owner'].id], limit=limit)
        return lobbies

    def get_lobby(self, **kwargs):
        kwargs['limit'] = 1
        return self.get_lobbies(**kwargs)

    async def on_message(self, message):
        if self.channel_in_lobby(message.channel):
            lobby = self.active_lobbies.select(where=['category_id=?', message.channel.category.id], limit=1)
            self.active_lobbies.update(
                where=['id=?', lobby['id']], 
                last_visited=time.mktime(time.gmtime()),
                expiry_warning=None
            )

            moderation = self.client.request_module('moderation')
            if lobby['filter_enabled'] and moderation and message.author != self.client.focused_guild.me:
                filter_activated = await moderation.filter_bad_words(message, silent_filter=True)
                if filter_activated and not lobby['filter_warning']:
                    self.active_lobbies.update(where=['id=?', lobby['id']], filter_warning=1)
                    await self.client.send_message(
                        message.channel, 
                        message.author.mention + ' ' + FILTER_WARNING
                    )

    async def on_message_edit(self, before, after):
        if after.author != self.client.focused_guild.me:
            await self.on_message(after)

    async def on_voice_state_update(self, member, before, after):
        if after.channel and self.channel_in_lobby(after.channel):
            self.active_lobbies.update(
                where=['category_id=?', after.channel.category.id], 
                last_visited=time.mktime(time.gmtime()),
                expiry_warning=None
            )

    async def on_member_remove(self, member):
        lobbies = self.get_lobbies(member=member)
        for lobby in lobbies:
            self.active_lobbies.update(
                where=['id=?', lobby['id']],
                member_ids=','.join([str(i) for i in lobby['member_ids'].split(',') if i and int(i) != member.id])
            )
            if lobby['text_channel_id']:
                await self.client.send_message(lobby['text_channel_id'], '{} has left the lobby.'.format(member.name))

        lobbies = self.get_lobbies(owner=member)
        for lobby in lobbies:
            if lobby['text_channel_id']:
                chatlog = await self.get_chat_log(lobby)

            members = [int(i) for i in lobby['member_ids'].split(',') if i]

            audit_log_reason = 'Lobby disbanded due to owner leaving the server'
            category = discord.utils.get(self.client.focused_guild.categories, id=lobby['category_id'])
            for channel in category.channels:
                await channel.delete(reason=audit_log_reason)
            await category.delete(reason=audit_log_reason)
            for member in members:
                await self.client.send_message(member, DISBAND_SUCCESS_MEMBER.format(lobby['name']))
            self.active_lobbies.delete(where=['id=?', lobby['id']])

            if lobby['text_channel_id'] and self.log_channel:
                await self.client.send_message(self.log_channel, LOG_CONFIRM_MOD.format(lobby['name']))
                async with self.log_channel.typing():
                    file = discord.File(BytesIO(bytes(chatlog, 'utf-8')), filename='lobby-chatlog-{}.txt'.format(lobby['name']))
                    await self.client.send_message(self.log_channel, file)

    async def bump_inactive_lobbies(self):
        inactive_lobbies = []

        for lobby in self.active_lobbies.select():
            # If the lobby has not been visited...
            if not lobby['last_visited'] and not lobby['expiry_warning'] and time.time() - lobby['created'] >= self.unvisited_expiry_warning_time:
                self.active_lobbies.update(where=['id=?', lobby['id']], expiry_warning=time.time())
                target = discord.utils.get(self.client.focused_guild.members, id=lobby['owner_id']) if not lobby['text_channel_id'] else lobby['text_channel_id']
                await self.client.send_message(target, BUMP_WARNING_UNVISITED.format(time=get_time_from_seconds(self.unvisited_expiry_time, one_unit_limit=True))
                )
            # If the lobby was last visited...
            elif lobby['last_visited'] and not lobby['expiry_warning'] and time.time() - lobby['last_visited'] >= self.visited_expiry_warning_time:
                self.active_lobbies.update(where=['id=?', lobby['id']], expiry_warning=time.time())
                target = discord.utils.get(self.client.focused_guild.mebmers, id=lobby['owner_id']) if not lobby['text_channel_id'] else lobby['text_channel_id']
                await self.client.send_message(target, BUMP_WARNING_VISITED.format(time=get_time_from_seconds(self.visited_expiry_time, one_unit_limit=True))
                )
            # If the lobby was visited and an expiry warning was sent...
            # OR
            # If the lobby was not visited and an expiry warning was sent...
            elif lobby['expiry_warning'] and time.time() - lobby['expiry_warning'] >= (self.visited_expiry_time if lobby['last_visited'] else self.unvisited_expiry_time):
                for member in [int(m) for m in lobby['member_ids'].split(',') if m]:
                    try:
                        await self.client.send_message(member, BUMP_MEMBER)
                    except discord.errors.DiscordException:
                        pass

                owner = discord.utils.get(self.client.focused_guild.members, id=lobby['owner_id'])
                saving_msg_obj = None
                if owner:
                    try:
                        await self.client.send_message(owner, BUMP_OWNER)
                        if lobby['text_channel_id']:
                            saving_message = LOG_CONFIRM_4
                            saving_msg_obj = await self.client.send_message(owner, saving_message)
                            async with owner.typing():
                                chatlog = await self.get_chat_log(lobby, saving_message)
                    except discord.errors.DiscordException:
                        pass

                audit_log_reason = 'Lobby hit expiration date of {}'.format(
                    get_time_from_seconds(self.visited_expiry_time if lobby['last_visited'] else self.unvisited_expiry_time, one_unit_limit=True))
                category = discord.utils.get(self.client.focused_guild.categories, id=lobby['category_id'])
                if not category:
                    # Something's not right.
                    self.active_lobbies.delete(where=['id=?', lobby['id']])
                    continue

                for channel in category.channels:
                    await channel.delete(reason=audit_log_reason)
                await category.delete(reason=audit_log_reason)
                inactive_lobbies.append(lobby)

                if lobby['text_channel_id'] and saving_msg_obj:
                    try:
                        await saving_msg_obj.delete()
                        confirmation_message = await self.client.send_message(owner, LOG_CONFIRM_5)
                        async with owner.typing():
                            file = discord.File(BytesIO(bytes(chatlog, 'utf-8')), filename='lobby-chatlog-{}.txt'.format(lobby['name']))
                            await self.client.send_message(owner, file)
                        await confirmation_message.edit(content=LOG_CONFIRM_6)
                    except discord.errors.DiscordException:
                        pass

        for inactive_lobby in inactive_lobbies:
            self.active_lobbies.delete(where=['id=?', inactive_lobby['id']])

    async def get_chat_log(self, lobby, saving_message=None):
        if not lobby['text_channel_id']:
            return LOG_NO_TEXT

        chatlog = ""
        participants = []
        creator = self.client.get_user(lobby['owner_id'])
        text_channel = discord.utils.get(self.client.focused_guild.channels, id=lobby['text_channel_id'])
        if not text_channel:
            return

        messages = await text_channel.history(limit=None).flatten()
        messages.reverse()
        for m in messages:
            if saving_message and m.content == saving_message:
                continue
            participant = m.author.name + '#' + m.author.discriminator + (' [BOT]' if m.author.bot else '')
            if participant not in participants:
                participants.append(participant)
            message_header = '== {name}{bot} - {time}{edited}{attachments}{embeds} =='.format(
                name=m.author.name,
                bot=' [BOT]' if m.author.bot else '',
                time=m.created_at.strftime('%m/%d/%Y @ %I:%M%p'),
                edited=(' (edited on ' + m.edited_at.strftime('%m/%d/%Y @ %I:%M%p') + ')') if m.edited_at else '',
                attachments=' *' if m.attachments else '',
                embeds=' **' if m.embeds else '',
            )
            chatlog += '\r\n\r\n{message_header}\r\n{content}'.format(
                message_header=message_header,
                content=m.clean_content.replace('\n', '\r\n')
            )
        chatlog = '{} Lobby\r\nCreated by {}\r\nCreated on {}\r\nAll Lobby Participants:\r\n\t{}\r\n\r\n' \
            '* = This message included an attachment.\r\n** = This message included an embed.\r\n\r\n============= BEGIN CHAT LOG ============='.format(
            lobby['name'],
            creator.name + '#' + creator.discriminator + (' [BOT]' if creator.bot else ''),
            text_channel.created_at.strftime('%m/%d/%Y @ %I:%M%p'),
            '\r\n\t'.join(participants)
        ) + chatlog
        return chatlog


module = LobbyManagement