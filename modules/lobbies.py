import discord
import time
from extra.commands import Command
from modules.module import Module
from utils import Config

class Lobby:
    def __init__(self):
        self.id = None
        self.publicLobby = False
        self.voiceLimit = 0
        self.category = None
        self.textChannel = None
        self.voiceChannel = None
        self.role = None
        self.ownerRole = None
        self.created = time.time()
        self.customName = ""


async def createLobby(client, module, message, *args, textChannelOnly=False, voiceChannelOnly=False):
    if message.channel.id != module.channelID:
        return

    residingLobby = discord.utils.find(lambda r: 'lobby-' in r.name, message.author.roles)
    ownsLobby = 'owner' in residingLobby.name if residingLobby else False
    auditLogReason = 'Lobby created by {}'.format(str(message.author))

    if ownsLobby:
        return '{} You own a lobby right now. You\'ll have to `~disbandLobby` to create a new one.'.format(message.author.mention)
    elif residingLobby:
        return '{} You are in a lobby right now. You\'ll have to `~leaveLobby` to create a new one.'.format(message.author.mention)

    lobby = Lobby()
    module.activeLobbies.append(lobby)

    name = ' '.join(args)
    if len(name) > 30:
        module.activeLobbies.remove(lobby)
        return '{} Your lobby name must be 30 characters or less.'.format(message.author.mention)
    elif not name:
        module.activeLobbies.remove(lobby)
        return '{} Give your lobby a name!'.format(message.author.mention)
    lobby.customName = name
    lobby.id = message.id

    lobbyID = message.id
    lobby.role = await client.rTTR.create_role(
        name='lobby-{}-owner'.format(lobbyID),
        reason=auditLogReason
    )
    await message.author.add_roles(lobby.role, reason=auditLogReason)

    categoryName = 'Lobby [{}]'.format(name)
    discordModRole = discord.utils.get(client.rTTR.roles, name='Discord Mods')
    lobby.category = await client.rTTR.create_category(
        name=categoryName,
        overwrites={
            client.rTTR.default_role: discord.PermissionOverwrite(read_messages=False),
            lobby.role: discord.PermissionOverwrite(read_messages=True),
            discordModRole: discord.PermissionOverwrite(read_messages=True, send_messages=False)
        },
        reason=auditLogReason
    )

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


class LobbyManagement(Module):
    class CreateLobbyCMD(Command):
        NAME = 'createLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            return await createLobby(client, module, message, *args)

    class CreateTextLobbyCMD(Command):
        NAME = 'createTextLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            return await createLobby(client, module, message, *args, textChannelOnly=True)

    class CreateVoiceLobbyCMD(Command):
        NAME = 'createVoiceLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            return await createLobby(client, module, message, *args, voiceChannelOnly=True)

    class LobbyInviteCMD(Command):
        NAME = 'inviteToLobby'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.id != module.channelID:
                return

            residingLobby = discord.utils.find(lambda r: 'lobby-' in r.name, message.author.roles)
            ownsLobby = 'owner' in residingLobby.name if residingLobby else False

            if not residingLobby:
                return '{} You\'re not in a lobby yourself -- create a lobby before you invite users.'.format(message.author.mention)
            elif not message.mentions:
                return '{} I need a mention of the user you want to invite to your lobby.'.format(message.author.mention)

            failedMessages = []
            for user in message.mentions:
                try:
                    await user.send("Hey there, {}! {} has invited you to join their private lobby on the Toontown Rewritten Discord. " \
                        "\n\nTo accept, {}copy & paste `~acceptLobbyInvite {}`. If you're not interested, you can ignore this message.".format(
                            user.mention,
                            message.author.mention,
                            'first leave your current lobby with `~leaveLobby` *(or `~disbandLobby` if you created the lobby)* and then ' \
                            if discord.utils.find(lambda r: 'lobby-' in r.name, user.roles) else '',
                            residingLobby.id
                        )
                    )
                except discord.HTTPException as e:
                    failedMessages.append(user.mention)
            if failedMessages:
                return '{} Could not send out messages to {} {} *({})*... the channel is still open for them if they use `~acceptLobbyInvite {}`'.format(
                    message.author.mention,
                    len(failedMessages),
                    'person' if len(failedMessages) == 1 else 'people',
                    ', '.join(failedMessages),
                    residingLobby.id
                )
            return '{} Invite{} sent!'.format('s' if len(message.mentions) > 1 else '')


    class LobbyCMD(Command):
        NAME = 'lobby'

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel.id != module.channelID or message.channel.name.startswith('Lobby'):
                return

                entered = ' Please enter the voice channel.'

                lobby = Lobby()
                lobby.number = newLobbyNumber
                module.activeLobbies.append(lobby)

                # I forgot regex existed when making the following code block.
                # Please forgive.
                splitText = text.split(' ')
                cns = []
                ca = False
                for word in splitText:
                    if word.startswith('"') and word.endswith('"') and len(word) > 2:
                        cns.append(word[1:-1])
                        break
                    if word.startswith('"') and not ca:
                        ca = True
                        cns.append(word[1:])
                    elif word.endswith('"') and ca:
                        ca = False
                        cns.append(word[:-1])
                        break
                    elif ca:
                        cns.append(word)
                cn = ' '.join(cns)
                if cns and not ca:
                    if len(cn) > 10:
                        module.activeLobbies.remove(lobby)
                        return '{} Your custom lobby name must be 10 characters or less.'.format(message.author.mention)
                    for l in cn:
                        if l.lower() not in 'abcdefghijklmnopqrstuvwxyz1234567890 -':
                            module.activeLobbies.remove(lobby)
                            return '{} Your custom lobby name must be alphanumeric.'.format(message.author.mention)
                    lobby.customName = cn

                lobby.openLobby = 'open' in splitText
                if lobby.openLobby:
                    try:
                        lobby.limit = int(splitText[splitText.index('open') + 1])
                        if lobby.limit > 99:
                            module.activeLobbies.remove(lobby)
                            return '{} Your lobby cannot have a limit more than 99 -- if you like, you can choose not to have a limit by not specifying a number.'.format(message.author.mention)
                        elif lobby.limit < 0:
                            module.activeLobbies.remove(lobby)
                            return '{} Your lobby cannot have a negative limit.'.format(message.author.mention)
                    except:
                        lobby.limit = 0

                lobbyName = 'Lobby {}'.format(newLobbyNumber) + (' [{}]'.format(lobby.customName) if lobby.customName else '')

                lobby.role = await client.create_role(
                    client.rTTR,
                    name=lobbyName
                )
                lobby.role.name = lobbyName  # value ensurance, doesn't send anything
                
                lobby.textChannel = await client.create_channel(
                    client.rTTR,
                    lobbyName.lower().replace(' ', '-').replace('[', '').replace(']', ''),
                    (client.rTTR.default_role, discord.PermissionOverwrite(read_messages=False)),
                    (lobby.role, discord.PermissionOverwrite(read_messages=True)),
                )
                #lobby.textChannel = discord.utils.get(self.client.get_all_channels(), id=tc.id)
                if lobby.openLobby:
                    lobby.voiceChannel = await client.create_channel(
                        client.rTTR,
                        lobbyName,
                        type=discord.ChannelType.voice,
                    )
                    #lobby.vcID = vc.id# = discord.utils.get(self.client.get_all_channels(), id=vc.id)
                    await client.edit_channel(lobby.voiceChannel, user_limit=lobby.limit)
                else:
                    lobby.voiceChannel = await client.create_channel(
                        client.rTTR,
                        lobbyName,
                        (client.rTTR.default_role, discord.PermissionOverwrite(connect=False)),
                        (lobby.role, discord.PermissionOverwrite(connect=True)),
                        type=discord.ChannelType.voice
                    )
                    #lobby.vcID = vc.id#l = discord.utils.get(self.client.get_all_channels(), id=vc.id)

                for member in message.mentions + [message.author]:
                    if member.id == client.rTTR.me.id:
                        busyMembers.append(member)

                    for role in member.roles:
                        if role.name.startswith('Lobby'):
                            if member.voice.voice_channel and member.voice.voice_channel.name == role.name:
                                busyMembers.append(member)
                                break
                            else:
                                await client.remove_roles(member, role)
                                break

                    if member not in busyMembers:
                        if member != message.author:
                            addedMembers.append(member)
                        await client.add_roles(member, lobby.role)
                        if member.voice.voice_channel:
                            entered = ''
                            await client.move_member(member, lobby.voiceChannel)

                #self.activeLobbies.append(lobby)

                busy = ' (**{}** busy)'.format(len(busyMembers)) if len(busyMembers) else ''
                others = ' with **{}** other people{}'.format(len(addedMembers), busy) if len(addedMembers) or len(busyMembers) else ''
                return '{} **{}** created{}!{}'.format(message.author.mention, lobby.role.name, others, entered)
            elif message.mentions:
                for l in module.activeLobbies:
                    if l.role.name == inLobby.name:
                        lobby = l
                        break

                busyMembers = []
                addedMembers = []
                for member in message.mentions:
                    for role in member.roles:
                        if role.name.startswith('Lobby'):
                            if member.voice.voice_channel and member.voice.voice_channel.name == role.name:
                                busyMembers.append(member)
                                break
                            else:
                                await client.remove_roles(member, role)
                                break

                    if member not in busyMembers:
                        addedMembers.append(member)
                        await client.add_roles(member, lobby.role)
                        if member.voice.voice_channel:
                            await client.move_member(member, lobby.voiceChannel)

                busy = ' (**{}** busy)'.format(len(busyMembers)) if len(busyMembers) else ''
                others = '**{}** other people{} '.format(len(addedMembers), busy) if len(addedMembers) else ''
                return '{} {}added to **{}**.'.format(message.author.mention, others, lobby.role.name)
            else:
                return '{} You are in **{}**.'.format(message.author.mention, inLobby.name)


    def __init__(self, client):
        Module.__init__(self, client)
        self.activeLobbies = []

        self.commands = [
            self.CreateLobbyCMD,
            self.CreateTextLobbyCMD,
            self.CreateVoiceLobbyCMD,
            self.LobbyInviteCMD
        ]
        self.channelID = Config.getModuleSetting("lobbies", "interaction")

    async def on_voice_state_update(self, member, before, after):
        if after.channel and after.channel.name.startswith('Lobby'):
            for lobby in self.activeLobbies:
                if lobby.voiceChannel.name == after.channel.name:
                    lobby.visited = True
                    if lobby.openLobby:
                        await member.add_roles(lobby.role)
        if before.channel and before.channel.name.startswith('Lobby'):
            for lobby in self.activeLobbies:
                if lobby.voiceChannel and lobby.voiceChannel.name == before.channel.name and lobby.openLobby:
                    await member.remove_roles(lobby.role)
            await self.bumpInactiveLobbies()

    async def restoreSession(self):
        return
        await self.bumpInactiveLobbies(fromRestore=True)
        for channel in self.client.rTTR.channels:
            if channel.type == discord.ChannelType.voice and channel.name.startswith('Lobby'):
                lobby = Lobby()
                lobby.openLobby = not not channel.user_limit
                lobby.textChannel = discord.utils.get(self.client.rTTR.channels, type=discord.ChannelType.text, name=channel.name.lower().replace(' ', '-').replace('[', '').replace(']', ''))
                lobby.voiceChannel = channel
                lobby.role = discord.utils.get(self.client.rTTR.roles, name=channel.name)
                lobby.number = int(channel.name.split(' ')[1])
                lobby.limit = channel.user_limit
                if channel.name.find('[') != -1:
                    lobby.customName = channel.name[channel.name.find('[') + 1:-1]

                self.activeLobbies.append(lobby)

    async def bumpInactiveLobbies(self, fromRestore=False):
        if fromRestore:
            toRemove = []
            for channel in self.client.rTTR.channels:
                if channel.type == discord.ChannelType.voice and channel.name.startswith('Lobby') and len(channel.voice_members) == 0:
                    role = discord.utils.get(self.client.rTTR.roles, name=channel.name)
                    textChannel = discord.utils.get(self.client.rTTR.channels, type=discord.ChannelType.text, name=channel.name.lower().replace(' ', '-').replace('[', '').replace(']', ''))
                    toRemove.extend([channel, textChannel])
                    print('deleting role')
                    if role:
                        await self.client.delete_role(self.client.rTTR, role)
                    print('deletingg role')
            for channel in toRemove:
                print('deleting channel')
                if channel:
                    await self.client.delete_channel(channel)
                print('deletingg channel')
        else:
            inactiveLobbies = []
            for lobby in self.activeLobbies:
                voiceChannel = discord.utils.get(self.client.rTTR.channels, type=discord.ChannelType.voice, name=lobby.role.name)
                textChannel = discord.utils.get(self.client.rTTR.channels, type=discord.ChannelType.text, name=lobby.role.name.lower().replace(' ', '-').replace('[', '').replace(']', ''))
                role = discord.utils.get(self.client.rTTR.roles, name=lobby.role.name)
                if len(voiceChannel.voice_members) == 0 and (lobby.visited or time.time() - lobby.created > 300):
                    await self.client.delete_channel(voiceChannel)
                    await self.client.delete_channel(textChannel)
                    await self.client.delete_role(self.client.rTTR, role)
                    inactiveLobbies.append(lobby)
            for inactiveLobby in inactiveLobbies:
                self.activeLobbies.remove(inactiveLobby)

module = LobbyManagement