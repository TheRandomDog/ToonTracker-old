import discord
import asyncio
import random
import time
import re
from datetime import datetime, timedelta
from extra.commands import Command
from modules.module import Module
from utils import Config, database, assertType, assertClass, getTimeFromSeconds, getProgressBar

NO_REASON = 'No reason was specified at the time of this message -- once a moderator adds a reason this message will self-edit.'
NO_REASON_ENTRY = '*No reason yet. Please add one with `{}editReason {} reason goes here` as soon as possible.*'

class Users:
    def __init__(self, module):
        self.usersDB = database.createSection(module, 'users', {
            'id': [database.INT, database.PRIMARY_KEY],
            'level': database.INT,
            'xp': database.INT,
            'time_online': database.INT,
            'time_idle': database.INT,
            'time_dnd': database.INT,
            'time_offline': database.INT
        })
        self.msgsDB = database.createSection(module, 'messages', {
            'id': [database.INT, database.PRIMARY_KEY],
            'user': database.INT,
            'channel': database.INT,
            'message': database.TEXT,
            'attachments': database.INT,
            'embeds': database.INT,
            'deleted': database.INT
        })

    def getUsers(self):
        return self.usersDB.select()

    def getUserByID(self, userID, createIfNonexistent=True):
        user = self.usersDB.select(where=['id=?', userID], limit=1)
        if not user and createIfNonexistent:
            self.usersDB.insert(
                id=userID,
                level=0,
                xp=0,
                time_online=0,
                time_idle=0,
                time_dnd=0,
                time_offline=0
            )
            user = self.usersDB.select(where=['id=?', userID], limit=1)
        return user
    def getUser(self, member, createIfNonexistent=True):
        return self.getUserByID(member.id, createIfNonexistent)

    def getUserXP(self, userID):
        user = self.getUserByID(userID)
        return user['xp']

    def getUserLevel(self, userID):
        user = self.getUserByID(userID)
        return user['level']

    def getUserTimeOnline(self, userID):
        user = self.getUserByID(userID)
        return user['time_online']

    def getUserTimeOffline(self, userID):
        user = self.getUserByID(userID)
        return user['time_offline']

    def getUserTimeDND(self, userID):
        user = self.getUserByID(userID)
        return user['time_DND']

    def getUserTimeIdle(self, userID):
        user = self.getUserByID(userID)
        return user['time_idle']

    def getUserMessageOverview(self, userID, channelID=None):
        where = [['user=?', userID]]
        if channelID:
            where.append(['channel=?', channelID])

        messages = self.msgsDB.select('channel, attachments, embeds', where=where)
        overview = {}
        for message in messages:
            if message['channel'] not in overview:
                overview[message['channel']] = {'messages': 0, 'attachments': 0, 'embeds': 0}
            else:
                channelOverview = overview[message['channel']]
                channelOverview['messages'] += 1
                channelOverview['attachments'] += message['attachments']
                channelOverview['embeds'] += message['embeds']

        return overview

    def setUserXP(self, userID, value):
        self.usersDB.update(where=['id=?', userID], xp=value)

    def setUserLevel(self, userID, value):
        self.usersDB.update(where=['id=?', userID], level=value)

    def setUserTimeOnline(self, userID, value):
        self.usersDB.update(where=['id=?', userID], time_online=value)

    def setUserTimeOffline(self, userID, value):
        self.usersDB.update(where=['id=?', userID], time_offline=value)

    def setUserTimeDND(self, userID, value):
        self.usersDB.update(where=['id=?', userID], time_dnd=value)

    def setUserTimeIdle(self, userID, value):
        self.usersDB.update(where=['id=?', userID], time_idle=value)


class UserTrackingModule(Module):
    NAME = 'User Info'

    ACTIONS = {
        'Join': {
            'color': discord.Color.green(),
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/394664535430004756/enter.png',
            'title': 'User Joined'
        },
        'Leave': {
            'color': discord.Color.dark_blue(),
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/394664540916154378/exit.png',
            'title': 'User Left'
        },
        'Mute': {
            'color': discord.Color.dark_blue(),
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/431896437488615435/deleted.png',
            'title': 'Muted'
        },
        'Note': {
            'color': discord.Color.from_rgb(156, 43, 255),
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/430426293021179934/note.png',
            'title': 'Note'
        },
        'Warn': {
            'color': discord.Color.from_rgb(245, 165, 0),
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/430425633424801803/warn2.png',
            'title': 'Warned'
        },
        'Kick': {
            'color': discord.Color.from_rgb(130, 75, 36),
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/394635272748269569/kick.png',
            'title': 'Kicked'
        },
        'Ban': {
            'color': discord.Color.red(),
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/394664529302126593/ban.png',
            'title': 'Banned'
        },
        'Filter': {
            'color': discord.Color.dark_red(),
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/394677395472252928/filtered.png',
            'title': 'Message Filtered'
        },
        'Link': {
            'color': discord.Color.dark_red(),
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/394677395472252928/filtered.png',
            'title': 'Link Filtered'
        },
        'Nickname': {
            'color': discord.Color.dark_red(),
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/394677395472252928/filtered.png',
            'title': 'Nickname Filtered'
        },
        'Review': {
            'color': discord.Color.dark_red(),
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/394677395472252928/filtered.png',
            'title': 'Image Review Required'
        },
        'Delete': {
            'color': discord.Color.blue(),
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/394684550531383306/deleted3.png',
            'title': 'Message Deleted'
        },
        'Lookup': {
            'color': discord.Embed.Empty,
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/394635296098222100/lookup.png',
            'title': 'Look Up'
        },
        'Level': {
            'color': discord.Color.purple(),
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/395337596240396288/levelup2.png',
            'title': 'Level Up'
        },
        'Unpunish': {
            'color': discord.Color.from_rgb(80, 80, 80),
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/421132488094777354/swords.png',
            'title': 'Punishment Revoked'
        }
    }

    class LevelCMD(Command):
        NAME = 'level'

        @staticmethod
        async def execute(client, module, message, *args):
            # Show off user's level / xp 
            if message.channel.id != 358032526763360277:
                return

            user = message.author
            xp = module.users.getUserXP(user.id)
            level = module.users.getUserLevel(user.id)
            levelxp = '{}\n**Level {}**   {} / {} XP\n{}'.format(
                user.mention,
                level,
                xp,
                module.xpNeededForLevel(level),
                getProgressBar(xp, module.xpNeededForLevel(level))
            )
            embed = discord.Embed(description=levelxp, color=discord.Color.purple())
            return embed

    class LookupCMD(Command):
        NAME = 'lookup'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            # Get user the mod wants to lookup.
            if not args:
                user = message.author
            elif not message.mentions:
                if not message.raw_mentions:
                    try:
                        user = client.rTTR.get_member(int(args[0])) or await client.get_user_info(int(args[0]))
                    except discord.NotFound:
                        moderation = client.requestModule('moderation')
                        if moderation:
                            punishmentID = int(args[0])
                            punishment = moderation.punishments.select(where=["id=?", punishmentID], limit=1)
                            if not punishment:
                                return 'No known user / lookup ID'
                            try:
                                user = await client.get_user_info(punishment['user'])
                            except discord.NotFound:
                                return 'No known user / lookup ID'
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
                        user = client.rTTR.get_member(message.raw_mentions[0]) or await client.get_user_info(message.raw_mentions[0])
                    except discord.NotFound:
                        return 'No known user'
            else:
                user = message.mentions[0]

            # Get all punishments for user, each will be an individual field in the embed.
            punishmentFields = []
            notes = []

            if assertClass(message.channel, discord.DMChannel, otherwise=False) or (message.channel.category and message.channel.category.name == 'Staff'):
                moderation = client.requestModule('moderation')
                for punishment in moderation.punishments.select(where=['user=?', user.id]):
                    punishmentFields.append({
                        'name': punishment['type'] + (' ({})'.format(punishment['end_length']) if punishment['end_length'] else ''),
                        'value': '{}\n**Mod:** <@{}> | **Date:** {} | **ID:** {}'.format(
                            ('`' + punishment['reason'] + '`').replace('`' + NO_REASON + '`', '*No reason was ever specified.*'),
                            punishment['mod'],
                            str(datetime.fromtimestamp(punishment['created']).date()),
                            punishment['id']
                        ),
                        'inline': False
                    })

                for note in moderation.notes.select(where=['user=?', user.id]):
                    notes.append('{tilde}{}{tilde}\n**Mod:** <@{}> | **Date:** {} | **ID:** {}'.format(
                        note['content'],
                        note['mod'],
                        str(datetime.fromtimestamp(note['created']).date()),
                        note['id'],
                        tilde='`'
                    ))

            if len(punishmentFields) > 18:
                punishmentFields = punishmentFields[:17]
                """noteFields = noteFields[:18 - len(punishmentFields)]
                noteFields.append({
                    'name': 'MORE PUNISHMENTS / NOTES EXIST!', 
                    'value': 'All of the punishments / notes on this account cannot be displayed in an embed. Please delete some that are older or unneeded.',
                    'inline': False
                })"""

            # Get all channel participation
            messages = []
            channelParticipation = module.users.getUserMessageOverview(user.id)
            # A classic Computer Science solution eh? Too lazy for something clever
            mostChannelParticipation = [(None, -1, 0, 0, 0) for _ in range(3)]
            for channel, participation in channelParticipation.items():
                channel = client.rTTR.get_channel(int(channel))
                if not channel:
                    continue

                totalMessages = participation['messages'] + participation['attachments'] + participation['embeds']
                for i in range(2, -1, -1):
                    if totalMessages > mostChannelParticipation[i][1]:
                        if i != 0 and totalMessages > mostChannelParticipation[i - 1][1]:
                            continue
                        else:
                            for j in range(1, i - 1, -1):
                                mostChannelParticipation[j + 1] = mostChannelParticipation[j]
                            mostChannelParticipation[i] = (channel, totalMessages, participation['messages'], participation['attachments'], participation['embeds'])
            for channel, _, _messages, attachments, embeds in mostChannelParticipation:
                if channel:
                    messages.append('{} -> :envelope: **{}** | :paperclip: **{}** | :page_facing_up: **{}**'.format(
                        channel.mention,
                        _messages,
                        attachments,
                        embeds
                    ))
            if not messages:
                messages = ['¯\_(ツ)_/¯']

            # Get Discord statuses for the past however long we've been recording them...
            statuses = '**Online:** {}\n**Idle:** {}\n**Do Not Disturb:** {}\n**Offline / Invisible:** {}'.format(
                getTimeFromSeconds(module.users.getUserTimeOnline(user.id), oneUnitLimit=True),
                getTimeFromSeconds(module.users.getUserTimeIdle(user.id), oneUnitLimit=True),
                getTimeFromSeconds(module.users.getUserTimeDND(user.id), oneUnitLimit=True),
                getTimeFromSeconds(module.users.getUserTimeOffline(user.id), oneUnitLimit=True)
            )

            # Show off user's level / xp 
            xp = module.users.getUserXP(user.id)
            level = module.users.getUserLevel(user.id)
            levelxp = '**Level {}**   {} / {} XP\n{}'.format(
                level,
                xp,
                module.xpNeededForLevel(level),
                getProgressBar(xp, module.xpNeededForLevel(level))
            )

            # Get all of the user's roles, highlighting their top role
            if hasattr(user, 'roles'):
                roles = user.roles[1:]
                roles.reverse()
                namedRoles = [role.name for role in roles]
                if namedRoles:
                    namedRoles[0] = '**' + namedRoles[0] + '**'
                else:
                    namedRoles = ['¯\_(ツ)_/¯']
            else:
                roles = []
                namedRoles = ['¯\_(ツ)_/¯']

            embed = module.createDiscordEmbed(
                action='Lookup',
                primaryInfo=str(user),
                secondaryInfo=user.mention,
                thumbnail=user.avatar_url,
                fields=[
                    {'name': 'Account Creation Date', 'value': str(user.created_at.date()), 'inline': True},
                    {'name': 'Join Date', 'value': str(user.joined_at.date()) if hasattr(user, 'joined_at') else 'Not on the server.', 'inline': True},
                    {'name': 'Level / XP', 'value': levelxp, 'inline': True},
                    {
                        'name': 'Roles', 
                        'value': '\n'.join(namedRoles),
                        'inline': True
                    },
                    {'name': 'Top 3 Channels', 'value': '\n'.join(messages), 'inline': True},
                    {'name': 'Statuses', 'value': statuses, 'inline': True}
                ] + ([{'name': 'Notes', 'value': '\n\n'.join(notes), 'inline': False}] if notes else []) + punishmentFields,
                footer={'text': "Available Commands: ~editReason | ~removePunishment | ~editNote | ~removeNote"} if punishmentFields else None,
                color=roles[0].color if roles else None
            )
            return embed

    def __init__(self, client):
        Module.__init__(self, client)

        self.users = Users(self)
        self.invites = None

        self.trackMessages = Config.getModuleSetting('usertracking', 'track_messages', True)
        self.trackingExceptions = Config.getModuleSetting('usertracking', 'tracking_exceptions', [])

        self.moduleTimeStart = time.time()
        self.memberStatusTimeStart = {}
        self.trackStatuses = Config.getModuleSetting('usertracking', 'track_statuses', True)

        self.auditLogEntries = {}
        self.levelCooldowns = {}
        self.levelCooldown = assertType(Config.getModuleSetting('usertracking', 'level_cooldown'), int, otherwise=5)
        self.levelCap = assertType(Config.getModuleSetting('usertracking', 'level_cap'), int, otherwise=-1)
        self.levelingExceptions = Config.getModuleSetting('usertracking', 'leveling_exceptions', [])
        self.allowUserLeveling = Config.getModuleSetting('usertracking', 'allow_user_leveling', True)
        self.allowUserRewards = Config.getModuleSetting('usertracking', 'allow_user_rewards', True)
        self.allowBotLeveling = Config.getModuleSetting('usertracking', 'allow_bot_leveling', False)
        self.allowBotRewards = Config.getModuleSetting('usertracking', 'allow_bot_rewards', False)
        self.allowModLeveling = Config.getModuleSetting('usertracking', 'allow_mod_leveling', True)
        self.allowModRewards = Config.getModuleSetting('usertracking', 'allow_mod_rewards', False)
        self.regularRole = discord.utils.get(client.rTTR.roles, id=Config.getModuleSetting('usertracking', 'regular_role_id'))

        self.spamChannel = Config.getModuleSetting('usertracking', 'spam_channel')
        self.logChannel = Config.getModuleSetting('usertracking', 'log_channel')

    async def addXP(self, message):
        member = message.author
        lastMessages = await message.channel.history(limit=2).flatten()
        # If the cooldown hasn't expired, and the message before this one was done by us...
        if time.time() < self.levelCooldowns.get(member, 0) and (len(lastMessages) != 2 or lastMessages[0].author == lastMessages[1].author):
            return

        xp = 0
        multiplier = 1
        # Memes don't contribute as much, not as much XP needs to be given.
        if message.channel.name == 'memes':
            multiplier = .5
        # Staff channels don't count.
        # Bot channels don't count.
        if message.channel.name.startswith('staff') or message.channel.name == 'bots':
            multiplier = 0
        # Informational channels don't count.
        if message.channel.category and message.channel.category.name == 'Information':
            multiplier = 0
        # Commands don't count.
        if message.content.startswith('~'):
            multiplier = 0

        # Community contribution is good.
        if message.channel.name in ['art', 'community'] and message.attachments:
            xp = 15
        words = []
        for word in message.content.split(' '):
            word = re.sub(r'(<.+>|\W)+', '', word)
            if len(word) > 3:
                words.append(word.lower().rstrip('s').rstrip('e'))
        words = list(set(words))

        prevXP = self.users.getUserXP(member.id)
        xp += len(words)
        xp *= multiplier
        self.users.setUserXP(member.id, prevXP + min(25, max(0, xp)))
        self.levelCooldowns[member] = time.time() + self.levelCooldown

    def xpNeededForLevel(self, level):
        return 5 * (level**2) + 50*level + 100

    def level(self, member):
        response = None
        level = self.users.getUserLevel(member.id)
        if self.levelCap != -1 and level >= self.levelCap:
            return

        xp = self.users.getUserXP(member.id)
        xpNeeded = self.xpNeededForLevel(level)
        if xp >= xpNeeded:  # Sorry Mee6 I've never been good with original math
            level += 1
            response = level
            self.users.setUserLevel(member.id, level)
            self.users.setUserXP(member.id, xp - xpNeeded)
        return response

    async def on_message(self, message):
        # A hack to get invites updates as quickly as possible.
        if not self.invites:
            self.invites = await self.client.rTTR.invites()

        # Definitely don't want to progress if it's a heckin' webhook.
        if message.webhook_id:
            return
        # You don't want to progress if there's an exception being made.
        if message.channel.__class__ == discord.DMChannel or message.channel.id in self.levelingExceptions or message.author.id in self.levelingExceptions or \
            any([role.id in self.levelingExceptions for role in message.author.roles]):
            return
        if message.channel.id in self.trackingExceptions:
            return

        if self.trackMessages:
            self.users.msgsDB.insert(
                id=message.id,
                user=message.author.id,
                channel=message.channel.id,
                message=message.content,
                attachments=len(message.attachments),
                embeds=len(message.embeds),
                deleted=0
            )

        bot = message.author.bot
        mod = any([Config.getRankOfRole(role.id) >= 300 for role in message.author.roles])

        if mod:
            if self.allowModLeveling:
                await self.addXP(message)
                leveled = self.level(message.author)
                if leveled and self.allowModRewards:
                    await self.assignAwards(message.author, leveled)
        elif bot:
            if self.allowBotLeveling:
                await self.addXP(message)
                leveled = self.level(message.author)
                if leveled and self.allowBotRewards:
                    await self.assignAwards(message.author, leveled)
        else:
            if self.allowUserLeveling:
                await self.addXP(message)
                leveled = self.level(message.author)
                if leveled and self.allowUserRewards:
                    await self.assignAwards(message.author, leveled)

    async def assignAwards(self, member, level):
        if level == 7:
            if self.regularRole and self.regularRole not in member.roles:
                await member.add_roles(self.regularRole, reason='User leveled up to level 7')
                embed = self.createDiscordEmbed(
                    action='Level',
                    primaryInfo="You've leveled up to LEVEL 7!",
                    secondaryInfo="Thanks for spending some of your time to chat with us! " \
                    "You now have permission to *create your own private lobbies* and *upload files and images* to the server. Have fun!",
                    thumbnail=member.avatar_url,
                    footer={'text': '- The mods from the Toontown Rewritten Discord'}
                )
                try:
                    await self.client.send_message(member, embed)
                except discord.HTTPException:
                    print("Could not send level 7 notification to {} (probably because they have DMs disabled for users/bots who don't share a server they're in).".format(str(member)))

    def createDiscordEmbed(self, action, primaryInfo=discord.Embed.Empty, secondaryInfo=discord.Embed.Empty, thumbnail='', fields=[], footer={}, image=None, color=None):
        action = self.ACTIONS[action]
        embed = discord.Embed(title=primaryInfo, description=secondaryInfo, color=color if color else action['color'])
        embed.set_author(name=action['title'], icon_url=action['icon'])
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        if footer:
            embed.set_footer(**footer)
        if image:
            embed.set_image(url=image)
        for field in fields:
            embed.add_field(**field)

        return embed

    async def on_member_ban(self, guild, member):
        fields = []
        punishment = None
        moderation = self.client.requestModule('moderation')
        if moderation:
            punishments = moderation.punishments.select(where=["user=? AND strftime('%s', 'now') - created < 10", member.id])
        if moderation and punishments:
            punishment = punishments[-1]
            fields = [{
                'name': punishment['type'] + (' ({})'.format(punishment['end_length']) if punishment['end_length'] else ''),
                'value': '**Mod:** <@{}>\n**Date:** {}\n**Reason:** {}\n**ID:** {}'.format(
                    punishment['mod'],
                    str(datetime.fromtimestamp(punishment['created']).date()),
                    punishment['reason'].replace(NO_REASON, NO_REASON_ENTRY.format(self.client.commandPrefix, punishment['id'])),
                    punishment['id']
                )
            }]
        for message in self.client._connection._messages:
            if message.author == member:
                message.nonce = 'banned'  # Read other comments editing `nonce`.
        async for entry in self.client.rTTR.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            footer={'text': 'Ban performed by {}'.format(entry.user.name), 'icon_url': entry.user.avatar_url}
        modLogEntry = await self.client.send_message(
            self.logChannel,
            self.createDiscordEmbed(
                action='Ban',
                primaryInfo=str(member),
                thumbnail=member.avatar_url,
                fields=fields,
                footer=footer
           )
        )
        if punishment:
            moderation.punishments.update(where=['id=?', punishment['id']], log=modLogEntry.id)
        return modLogEntry

    async def on_member_join(self, member):
        punishmentFields = []
        moderation = self.client.requestModule('moderation')
        if moderation:
            for punishment in moderation.punishments.select(where=['user=?', member.id]):
                punishmentFields.append({
                    'name': punishment['type'] + (' ({})'.format(punishment['end_length']) if punishment['end_length'] else ''),
                    'value': '**Mod:** <@{}>\n**Date:** {}\n**Reason:** {}\n**ID:** {}'.format(
                        punishment['mod'],
                        str(datetime.fromtimestamp(punishment['created']).date()),
                        punishment['reason'].replace(NO_REASON, '*No reason was ever specified.*'),
                        punishment['id']
                    ),
                    'inline': False
                })
        xp = self.users.getUserXP(member.id)
        level = self.users.getUserLevel(member.id)
        # Show off user's level / xp 
        levelxp = '**Level {}**   {} / {} XP\n{}'.format(
            level,
            xp,
            self.xpNeededForLevel(level),
            getProgressBar(xp, self.xpNeededForLevel(level))
        )
        if level >= 7:
            await member.add_roles(self.regularRole, reason='User rejoined and had regular role')

        if self.invites:
            ni = await self.client.rTTR.invites()
            new_invites = {i.code: i.uses for i in ni}
            old_invites = {i.code: i.uses for i in self.invites}
            code_used = 'toontown'
            for code, uses in new_invites.items():
                if code not in old_invites or old_invites[code] != uses:
                    code_used = code
                    break
            self.invites = ni
        else:
            code_used = None

        await self.client.send_message(
            self.logChannel,
            self.createDiscordEmbed(
                action='Join',
                primaryInfo=str(member),
                secondaryInfo=member.mention,
                thumbnail=member.avatar_url,
                fields=[
                    {'name': 'Account Creation Date', 'value': str(member.created_at.date()), 'inline': True},
                    {'name': 'Join Date', 'value': str(member.joined_at.date()), 'inline': True},
                    {'name': 'Level / XP', 'value': levelxp, 'inline': True}
                ] + punishmentFields,
                footer={'text': "Joined using invite code: {}".format(code_used)} if code_used else None
            )
        )
        self.memberStatusTimeStart[member.id] = time.time()

    async def on_member_remove(self, member):
        action = 'Leave'
        fields = []
        punishment = None
        moderation = self.client.requestModule('moderation')
        if moderation:
            punishments = moderation.punishments.select(where=["user=? AND type='Kick' AND strftime('%s', 'now') - created < 10", member.id])
        if moderation and punishments:
            punishment = punishments[-1]
            fields = [{
                'name': punishment['type'] + (' ({})'.format(punishment['end_length']) if punishment['end_length'] else ''),
                'value': '**Mod:** <@{}>\n**Date:** {}\n**Reason:** {}\n**ID:** {}'.format(
                    punishment['mod'],
                    str(datetime.fromtimestamp(punishment['created']).date()),
                    punishment['reason'].replace(NO_REASON, NO_REASON_ENTRY.format(self.client.commandPrefix, punishment['id'])),
                    punishment['id']
                )
            }]

        async for entry in self.client.rTTR.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id and entry.created_at >= datetime.utcnow() - timedelta(seconds=2):
                action = 'Kick'
                footer={'text': 'Kick performed by {}'.format(entry.user.name), 'icon_url': entry.user.avatar_url}
        modLogEntry = await self.client.send_message(
            self.logChannel,
            self.createDiscordEmbed(
                action=action,
                primaryInfo=str(member),
                thumbnail=member.avatar_url,
                fields=fields,
                footer=footer if action == 'Kick' else ''
           )
        )
        if punishment:
            moderation.punishments.update(where=['id=?', punishment['id']], log=modLogEntry.id)
        return modLogEntry

    # Specifically built for moderation module.
    async def on_member_warn(self, member, punishment):
        modLogEntry = await self.client.send_message(
            self.logChannel,
            self.createDiscordEmbed(
                action='Warn',
                primaryInfo=str(member),
                thumbnail=member.avatar_url,
                fields=[{
                    'name': punishment['type'],
                    'value': '**Mod:** <@{}>\n**Date:** {}\n**Reason:** {}\n**ID:** {}'.format(
                        punishment['mod'],
                        str(datetime.fromtimestamp(punishment['created']).date()),
                        punishment['reason'].replace(NO_REASON, NO_REASON_ENTRY.format(self.client.commandPrefix, punishment['id'])),
                        punishment['id']
                    )
                }]
           )
        )
        moderation = self.client.requestModule('moderation')
        moderation.punishments.update(where=['id=?', punishment['id']], log=modLogEntry.id)
        return modLogEntry

    # Specifically built for moderation module.
    async def on_message_filter(self, message, *, link=False, word=None, text=None, embed=None):
        replaceFrom = text if text else message.content
        await self.client.send_message(
            self.logChannel,
            self.createDiscordEmbed(
                action='Link' if link else 'Filter',
                primaryInfo=str(message.author),
                secondaryInfo='{} in{} {}{}:\n\n{}'.format(
                    message.author.mention,
                    " the {} of an embed in".format(embed) if embed else '',
                    '**[{}]** '.format(message.channel.category.name) if message.channel.category else '',
                    message.channel.mention,
                    replaceFrom.replace(word, '**' + word + '**') if word else replaceFrom
                ),
                thumbnail=message.author.avatar_url
           )
        )

    # Specifically built for moderation module.
    async def on_nickname_filter(self, member, *, word=None, text=None):
        replaceFrom = text if text else member.display_name
        await self.client.send_message(
            self.logChannel,
            self.createDiscordEmbed(
                action='Nickname',
                primaryInfo=str(member),
                secondaryInfo=replaceFrom.replace(word, '**' + word + '**') if word else replaceFrom,
                thumbnail=member.avatar_url
            )
        )

    # Specifically built for moderation module.
    async def on_message_review_filter(self, message, rating, url):
        await self.client.send_message(
            self.logChannel,
            self.createDiscordEmbed(
                action='Review',
                primaryInfo=str(message.author),
                secondaryInfo='{} in {}{} **[Rating: {}]**:'.format(
                    message.author.mention,
                    '**[{}]** '.format(message.channel.category.name) if message.channel.category else '',
                    message.channel.mention,
                    rating
                ),
                image=url,
                thumbnail=message.author.avatar_url
           )
        )

    # Specifically built for moderation module.
    async def on_member_unpunish(self, member, punishment):
        await self.client.send_message(
            self.logChannel,
            self.createDiscordEmbed(
                action='Unpunish',
                primaryInfo=str(member),
                thumbnail=member.avatar_url,
                fields=[{
                    'name': punishment['type'],
                    'value': '**Mod:** <@{}>\n**Date Punished:** {}\n**Reason:** {}\n**Old ID:** {}'.format(
                        punishment['mod'],
                        str(datetime.fromtimestamp(punishment['created']).date()),
                        punishment['reason'].replace(NO_REASON, NO_REASON_ENTRY.format(self.client.commandPrefix, punishment['id'])),
                        punishment['id']
                    )
                }]
           )
        )

    # Specifically built for moderation module.
    async def on_member_note(self, member, note):
        modLogEntry = await self.client.send_message(
            self.logChannel,
            self.createDiscordEmbed(
                action='Note',
                primaryInfo=str(member),
                thumbnail=member.avatar_url,
                fields=[{
                    'name': 'Note',
                    'value': '**Mod:** <@{}>\n**Date:** {}\n**ID:** {}\n\n{}'.format(
                        note['mod'],
                        str(datetime.fromtimestamp(note['created']).date()),
                        note['id'],
                        note['content']
                    )
                }]
           )
        )
        moderation = self.client.requestModule('moderation')
        moderation.notes.update(where=['id=?', note['id']], log=modLogEntry.id)
        return modLogEntry


    async def on_message_delete(self, message):
        if message.author == self.client.rTTR.me or message.channel.__class__ == discord.DMChannel or message.nonce in ['filter', 'silent']:
            return

        if self.trackMessages:
            try:
                self.users.msgsDB.update(
                    where=['id=?', message.id],
                    deleted=1
                )
            except sqlite3.OperationalError as e:
                pass

        footer = {}
        async for entry in self.client.rTTR.audit_logs(limit=5, action=discord.AuditLogAction.message_delete):
            # Discord Audit Logs will clump together deleted messages, saying "MOD deleted X message(s) from USER in TARGET"
            # It will still keep the creation date of the entry though, which could be as stale as a few minutes.
            #
            # So if it's not an entry made within 2 seconds, just verify the message being deleted is in the same channel
            # and by the same user and we can assume that if the count is more than 1 that it was deleted by someone else.
            # The best we can do right now.
            prevDeletionCount = self.auditLogEntries.get(entry.id, 0)
            if message.nonce == 'banned':
                footer={'text': 'Message deleted due to a ban', 'icon_url': self.ACTIONS['Ban']['icon']}
            elif entry.created_at >= datetime.utcnow() - timedelta(seconds=2) or \
              (entry.extra.channel == message.channel and entry.target == message.author and entry.extra.count > prevDeletionCount):
                footer={'text': 'Message deleted by {}'.format(entry.user.name), 'icon_url': entry.user.avatar_url}
            elif message.nonce == 'cleared':
                footer={'text': 'Message deleted via ~clear'}
            self.auditLogEntries[entry.id] = entry.extra.count
        await self.client.send_message(
            self.spamChannel,
            self.createDiscordEmbed(
                action='Delete',
                primaryInfo=str(message.author),
                secondaryInfo='{}{} in {}{}:\n\n{}'.format(
                    '*This message contained an embed.*\n' if message.embeds else '',
                    message.author.mention,
                    '**[{}]** '.format(message.channel.category.name) if message.channel.category else '',
                    message.channel.mention,
                    message.content
                ),
                thumbnail=message.author.avatar_url,
                footer=footer,
                image=message.attachments[0].proxy_url if message.attachments else None
                # proxy_url is cached, so it is not instantly deleted when a message is deleted
           )
        )

    async def on_member_update(self, before, after):
        # First, track statues.
        if self.trackStatuses and before.status != after.status:
            lastStatusTime = self.memberStatusTimeStart.get(before.id, self.moduleTimeStart)

            if before.status == discord.Status.online:
                self.users.setUserTimeOnline(before.id, self.users.getUserTimeOnline(before.id) + (time.time() - lastStatusTime))
            elif before.status == discord.Status.offline:
                self.users.setUserTimeOffline(before.id, self.users.getUserTimeOffline(before.id) + (time.time() - lastStatusTime))
            elif before.status == discord.Status.idle:
                self.users.setUserTimeIdle(before.id, self.users.getUserTimeIdle(before.id) + (time.time() - lastStatusTime))
            elif before.status == discord.Status.dnd:
                self.users.setUserTimeDND(before.id, self.users.getUserTimeDND(before.id) + (time.time() - lastStatusTime))
            self.memberStatusTimeStart[before.id] = time.time()

        # Then mutes.
        mutedRole = discord.utils.get(self.client.rTTR.roles, name=Config.getModuleSetting('moderation', 'muted_role_name') or 'Muted')
        if mutedRole and (mutedRole not in before.roles and mutedRole in after.roles):
            fields = []
            punishment = None
            moderation = self.client.requestModule('moderation')
            if moderation:
                punishments = moderation.punishments.select(where=["user=? AND strftime('%s', 'now') - created < 10", after.id])
            if moderation and punishments:
                punishment = punishments[-1]
                fields = [{
                    'name': punishment['type'] + (' ({})'.format(punishment['end_length']) if punishment['end_length'] else ''),
                    'value': '**Mod:** <@{}>\n**Date:** {}\n**Reason:** {}\n**ID:** {}'.format(
                        punishment['mod'],
                        str(datetime.fromtimestamp(punishment['created']).date()),
                        punishment['reason'].replace(NO_REASON, NO_REASON_ENTRY.format(self.client.commandPrefix, punishment['id'])),
                        punishment['id']
                    )
                }]
            async for entry in self.client.rTTR.audit_logs(limit=5, action=discord.AuditLogAction.member_role_update):
                if mutedRole in entry.after.roles:
                    footer={'text': 'Mute performed by {}'.format(entry.user.name), 'icon_url': entry.user.avatar_url}
                    break
            modLogEntry = await self.client.send_message(
                self.logChannel,
                self.createDiscordEmbed(
                    action='Mute',
                    primaryInfo=str(after),
                    thumbnail=after.avatar_url,
                    fields=fields,
                    footer=footer
               )
            )
            if punishment:
                moderation.punishments.update(where=['id=?', punishment['id']], log=modLogEntry.id)
            return modLogEntry

module = UserTrackingModule