import discord
import time
from modules.module import Module
from utils import Config

class Lobby:
    def __init__(self):
        self.openLobby = False
        self.limit = 0
        self.textChannel = None
        self.voiceChannel = None
        self.role = None
        self.number = 0
        self.created = time.time()
        self.visited = False
        self.customName = ""

class LobbyManagement(Module):
    def __init__(self, client):
        Module.__init__(self, client)
        self.activeLobbies = []

        self.channelID = Config.getModuleSetting("lobbies", "interaction")

    async def on_voice_state_update(self, before, after):
        if after.voice.voice_channel and after.voice.voice_channel.name.startswith('Lobby'):
            for lobby in self.activeLobbies:
                if lobby.voiceChannel.name == after.voice.voice_channel.name:
                    lobby.visited = True
                    if lobby.openLobby:
                        await self.client.add_roles(after, lobby.role)
        if before.voice.voice_channel and before.voice.voice_channel.name.startswith('Lobby'):
            for lobby in self.activeLobbies:
                if lobby.voiceChannel and lobby.voiceChannel.name == before.voice.voice_channel.name and lobby.openLobby:
                    await self.client.remove_roles(after, lobby.role)
            await self.bumpInactiveLobbies()

    async def handleMsg(self, message):
        if message.channel.id != self.channelID or message.channel.name.startswith('Lobby'):
            return

        text = message.content
        if text.startswith('!lobby'):
            inLobby = False
            for role in message.author.roles:
                if role.name.startswith('Lobby'):
                    inLobby = role

                    l = None
                    for l1 in self.activeLobbies:
                        if l1.role == role:
                            l = l1
                            break
                    if l and l.visited and message.author.voice.voice_channel != l.voiceChannel:
                        await self.client.remove_roles(message.author, role)
                        await self.bumpInactiveLobbies()
                        inLobby = False


            if not inLobby:
                busyMembers = []
                addedMembers = []
                numbers = sorted([lobby.number for lobby in self.activeLobbies])
                newLobbyNumber = 1
                while newLobbyNumber in numbers:
                    newLobbyNumber += 1

                entered = ' Please enter the voice channel.'

                lobby = Lobby()
                lobby.number = newLobbyNumber
                self.activeLobbies.append(lobby)

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
                        self.activeLobbies.remove(lobby)
                        return '{} Your custom lobby name must be 10 characters or less.'.format(message.author.mention)
                    for l in cn:
                        if l.lower() not in 'abcdefghijklmnopqrstuvwxyz1234567890 -':
                            self.activeLobbies.remove(lobby)
                            return '{} Your custom lobby name must be alphanumeric.'.format(message.author.mention)
                    lobby.customName = cn

                lobby.openLobby = 'open' in splitText
                if lobby.openLobby:
                    try:
                        lobby.limit = int(splitText[splitText.index('open') + 1])
                        if lobby.limit > 99:
                            self.activeLobbies.remove(lobby)
                            return '{} Your lobby cannot have a limit more than 99 -- if you like, you can choose not to have a limit by not specifying a number.'.format(message.author.mention)
                        elif lobby.limit < 0:
                            self.activeLobbies.remove(lobby)
                            return '{} Your lobby cannot have a negative limit.'.format(message.author.mention)
                    except:
                        lobby.limit = 0

                lobbyName = 'Lobby {}'.format(newLobbyNumber) + (' [{}]'.format(lobby.customName) if lobby.customName else '')

                lobby.role = await self.client.create_role(
                    self.client.rTTR,
                    name=lobbyName
                )
                lobby.role.name = lobbyName  # value ensurance, doesn't send anything
                
                lobby.textChannel = await self.client.create_channel(
                    self.client.rTTR,
                    lobbyName.lower().replace(' ', '-').replace('[', '').replace(']', ''),
                    (self.client.rTTR.default_role, discord.PermissionOverwrite(read_messages=False)),
                    (lobby.role, discord.PermissionOverwrite(read_messages=True)),
                )
                #lobby.textChannel = discord.utils.get(self.client.get_all_channels(), id=tc.id)
                if lobby.openLobby:
                    lobby.voiceChannel = await self.client.create_channel(
                        self.client.rTTR,
                        lobbyName,
                        type=discord.ChannelType.voice,
                    )
                    #lobby.vcID = vc.id# = discord.utils.get(self.client.get_all_channels(), id=vc.id)
                    await self.client.edit_channel(lobby.voiceChannel, user_limit=lobby.limit)
                else:
                    lobby.voiceChannel = await self.client.create_channel(
                        self.client.rTTR,
                        lobbyName,
                        (self.client.rTTR.default_role, discord.PermissionOverwrite(connect=False)),
                        (lobby.role, discord.PermissionOverwrite(connect=True)),
                        type=discord.ChannelType.voice
                    )
                    #lobby.vcID = vc.id#l = discord.utils.get(self.client.get_all_channels(), id=vc.id)

                for member in message.mentions + [message.author]:
                    if member.id == self.client.rTTR.me.id:
                        busyMembers.append(member)

                    for role in member.roles:
                        if role.name.startswith('Lobby'):
                            if member.voice.voice_channel and member.voice.voice_channel.name == role.name:
                                busyMembers.append(member)
                                break
                            else:
                                await self.client.remove_roles(member, role)
                                break

                    if member not in busyMembers:
                        if member != message.author:
                            addedMembers.append(member)
                        await self.client.add_roles(member, lobby.role)
                        if member.voice.voice_channel:
                            entered = ''
                            await self.client.move_member(member, lobby.voiceChannel)

                #self.activeLobbies.append(lobby)

                busy = ' (**{}** busy)'.format(len(busyMembers)) if len(busyMembers) else ''
                others = ' with **{}** other people{}'.format(len(addedMembers), busy) if len(addedMembers) or len(busyMembers) else ''
                return '{} **{}** created{}!{}'.format(message.author.mention, lobby.role.name, others, entered)
            elif message.mentions:
                for l in self.activeLobbies:
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
                                await self.client.remove_roles(member, role)
                                break

                    if member not in busyMembers:
                        addedMembers.append(member)
                        await self.client.add_roles(member, lobby.role)
                        if member.voice.voice_channel:
                            await self.client.move_member(member, lobby.voiceChannel)

                busy = ' (**{}** busy)'.format(len(busyMembers)) if len(busyMembers) else ''
                others = '**{}** other people{} '.format(len(addedMembers), busy) if len(addedMembers) else ''
                return '{} {}added to **{}**.'.format(message.author.mention, others, lobby.role.name)
            else:
                return '{} You are in **{}**.'.format(message.author.mention, inLobby.name)

    async def restoreSession(self):
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