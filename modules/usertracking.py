import discord
import asyncio
import random
import time
import re
from datetime import datetime, timedelta
from extra.commands import Command
from modules.module import Module
from utils import Config, Users, assertType, getTimeFromSeconds, getProgressBar

NO_REASON = 'No reason was specified at the time of this message -- once a moderator adds a reason this message will self-edit.'
NO_REASON_MOD = 'No reason yet.'

class UserTrackingModule(Module):
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
        'Warn': {
            'color': discord.Color.from_rgb(245, 165, 0),
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/394675747324821504/warn.png',
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
        }
    }

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
                        user = await client.get_user_info(int(args[0]))
                    except (ValueError, IndexError, discord.NotFound):
                        name = ' '.join(args)
                        discriminator = args[-1].split('#')[-1]
                        if discriminator:
                            name = ' '.join(args).rstrip('#0123456789')
                        user = discord.utils.get(message.guild.members, display_name=name)
                        user = discord.utils.get(message.guild.members, name=name, discriminator=discriminator) if not user else user
                        user = discord.utils.get(message.guild.members, name=name) if not user else user
                        if not user:
                            return 'No known user'
                else:
                    try:
                        user = await client.get_user_info(message.raw_mentions[0])
                    except discord.NotFound:
                        return 'No known user'
            else:
                user = message.mentions[0]

            # Get all punishments for user, each will be an individual field in the embed.
            punishmentFields = []
            for punishment in Users.getUserPunishments(user.id):
                if punishment.get('length', None):
                    punishmentFields.append({
                        'name': 'Temporary Ban ({})'.format(punishment['length']),
                        'value': '**Mod:** <@{}>\n**Date:** {}\n**Reason:** {}\n**ID:** {}'.format(
                            punishment['mod'],
                            str(datetime.fromtimestamp(punishment['created']).date()),
                            punishment['reason'].replace(NO_REASON, '*No reason was ever specified.*'),
                            punishment['editID']
                        ),
                        'inline': False
                    })
                else:
                    punishmentFields.append({
                        'name': punishment['type'],
                        'value': '**Mod:** <@{}>\n**Date:** {}\n**Reason:** {}\n**ID:** {}'.format(
                            punishment['mod'],
                            str(datetime.fromtimestamp(punishment['created']).date()),
                            punishment['reason'].replace(NO_REASON, '*No reason was ever specified.*'),
                            punishment['editID']
                        ),
                        'inline': False
                    })
            xp = Users.getUserXP(user.id)
            level = Users.getUserLevel(user.id)
            # Get all channel participation
            messages = []
            channelParticipation = Users.getUserChannelHistory(user.id)
            for channel, participation in channelParticipation.items():
                channel = client.rTTR.get_channel(int(channel))
                if not channel:
                    continue
                messages.append('{} -> :envelope: **{}** | :paperclip: **{}** | :page_facing_up: **{}**'.format(
                    channel.mention,
                    participation['messages'],
                    participation['attachments'],
                    participation['embeds']
                ))
            if not messages:
                messages = ['¯\_(ツ)_/¯']
            # Get Discord statuses for the past however long we've been recording them...
            statuses = '**Online:** {}\n**Idle:** {}\n**Do Not Disturb:** {}\n**Offline / Invisible:** {}'.format(
                getTimeFromSeconds(Users.getUserTimeOnline(user.id), oneUnitLimit=True),
                getTimeFromSeconds(Users.getUserTimeIdle(user.id), oneUnitLimit=True),
                getTimeFromSeconds(Users.getUserTimeDND(user.id), oneUnitLimit=True),
                getTimeFromSeconds(Users.getUserTimeOffline(user.id), oneUnitLimit=True)
            )
            # Show off user's level / xp 
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
                    {'name': 'Messages', 'value': '\n'.join(messages), 'inline': True},
                    {'name': 'Statuses', 'value': statuses, 'inline': True}
                ] + punishmentFields,
                footer={'text': "You can use a punishment's edit ID to ~editReason or ~removePunishment"} if punishmentFields else None,
                color=roles[0].color if roles else None
            )
            return embed

    def __init__(self, client):
        Module.__init__(self, client)

        self.trackMessages = Config.getModuleSetting('usertracking', 'track_messages', True)
        self.trackingExceptions = Config.getModuleSetting('usertracking', 'tracking_exceptions', [])

        self.memberStatusTimeStart = {member.id: time.time() for member in client.rTTR.members}
        self.trackStatuses = Config.getModuleSetting('usertracking', 'track_statuses', True)

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

        self.botOutput = Config.getSetting('botspam')

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
        # Music channels don't count.
        # Make-a-lobby doesn't count.
        if message.channel.name.startswith('staff') or message.channel.name == 'make-a-lobby' or message.channel.name == 'music':
            multiplier = 0
        # Informational channels don't count.
        if message.channel.category and message.channel.category.name == 'Information':
            multiplier = 0
        # Commands don't count.
        if message.content.startswith('~'):
            multiplier = 0

        if message.channel.name in ['art', 'community'] and message.attachments:
            xp = 15
        words = []
        for word in message.content.split(' '):
            word = re.sub(r'(<.+>|\W)+', '', word)
            if len(word) > 3:
                words.append(word.lower().rstrip('s').rstrip('e'))
        words = list(set(words))

        prevXP = Users.getUserXP(member.id)
        xp += len(words)
        xp *= multiplier
        Users.setUserXP(member.id, prevXP + min(25, max(0, xp)))
        self.levelCooldowns[member] = time.time() + self.levelCooldown

    def xpNeededForLevel(self, level):
        return 5 * (level**2) + 50*level + 100

    def level(self, member):
        response = None
        level = Users.getUserLevel(member.id)
        if self.levelCap != -1 and level >= self.levelCap:
            return

        xp = Users.getUserXP(member.id)
        xpNeeded = self.xpNeededForLevel(level)
        if xp >= xpNeeded:  # Sorry Mee6 I've never been good with original math
            level += 1
            response = level
            Users.setUserLevel(member.id, level)
            Users.setUserXP(member.id, xp - xpNeeded)
        return response

    async def handleMsg(self, message):
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
            channelHistory = Users.getUserChannelHistory(message.author.id, message.channel.id)
            channelHistory['messages'] += 1
            channelHistory['attachments'] += len(message.attachments)
            channelHistory['embeds'] += len(message.embeds)
            Users.setUserChannelHistory(message.author.id, message.channel.id, channelHistory)

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
                await self.client.send_message(member, embed)

    def createDiscordEmbed(self, action, primaryInfo=discord.Embed.Empty, secondaryInfo=discord.Embed.Empty, thumbnail='', fields=[], footer={}, color=None):
        action = self.ACTIONS[action]
        embed = discord.Embed(title=primaryInfo, description=secondaryInfo, color=color if color else action['color'])
        embed.set_author(name=action['title'], icon_url=action['icon'])
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        if footer:
            embed.set_footer(**footer)
        for field in fields:
            embed.add_field(**field)
        return embed

    async def on_member_ban(self, guild, member):
        punishments = Users.getUserPunishments(member.id)
        fields = []
        if punishments:
            punishment = punishments[-1]
            if time.time() - punishment['created'] < 10:
                fields = [{
                    'name': punishment['type'],
                    'value': '**Mod:** <@{}>\n**Date:** {}\n**Reason:** {}\n**ID:** {}'.format(
                        punishment['mod'],
                        str(datetime.fromtimestamp(punishment['created']).date()),
                        punishment['reason'].replace(NO_REASON, '*No reason was ever specified.*'),
                        punishment['editID']
                    )
                }]
        async for entry in self.client.rTTR.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            footer={'text': 'Ban performed by {}'.format(entry.user.name), 'icon_url': entry.user.avatar_url}
        await self.client.send_message(
            self.botOutput,
            self.createDiscordEmbed(
                action='Ban',
                primaryInfo=str(member),
                thumbnail=member.avatar_url,
                fields=fields,
                footer=footer
           )
        )

    async def on_member_join(self, member):
        punishmentFields = []
        for punishment in Users.getUserPunishments(member.id):
            if punishment.get('length', None):
                punishmentFields.append({
                    'name': 'Temporary Ban ({})'.format(punishment['length']),
                    'value': '**Mod:** <@{}>\n**Date:** {}\n**Reason:** {}\n**ID:** {}'.format(
                        punishment['mod'],
                        str(datetime.fromtimestamp(punishment['created']).date()),
                        punishment['reason'].replace(NO_REASON, '*No reason was ever specified.*'),
                        punishment['editID']
                    ),
                    'inline': False
                })
            else:
                punishmentFields.append({
                    'name': punishment['type'],
                    'value': '**Mod:** <@{}>\n**Date:** {}\n**Reason:** {}\n**ID:** {}'.format(
                        punishment['mod'],
                        str(datetime.fromtimestamp(punishment['created']).date()),
                        punishment['reason'].replace(NO_REASON, '*No reason was ever specified.*'),
                        punishment['editID']
                    ),
                    'inline': False
                })
        await self.client.send_message(
            self.botOutput,
            self.createDiscordEmbed(
                action='Join',
                primaryInfo=str(member),
                secondaryInfo=member.mention,
                thumbnail=member.avatar_url,
                fields=[
                    {'name': 'Account Creation Date', 'value': str(member.created_at.date()), 'inline': True},
                    {'name': 'Join Date', 'value': str(member.joined_at.date()), 'inline': True},
                    {'name': 'Level', 'value': str(Users.getUserLevel(member.id)), 'inline': True},
                    {'name': 'XP', 'value': str(Users.getUserXP(member.id)), 'inline': True}
                ] + punishmentFields,
                #footer="You can use a punishment's edit ID to ~editReason or ~removePunishment" if Users.getUserPunishments(member.id) else ''
            )
        )
        self.memberStatusTimeStart[member.id] = time.time()


    async def on_member_remove(self, member):
        punishments = Users.getUserPunishments(member.id)
        action = 'Leave'
        fields = []
        if punishments:
            punishment = punishments[-1]
            if time.time() - punishment['created'] < 10:
                fields = [{
                    'name': punishment['type'],
                    'value': '**Mod:** <@{}>\n**Date:** {}\n**Reason:** {}\n**ID:** {}'.format(
                        punishment['mod'],
                        str(datetime.fromtimestamp(punishment['created']).date()),
                        punishment['reason'].replace(NO_REASON, '*No reason was ever specified.*'),
                        punishment['editID']
                    )
                }]
        async for entry in self.client.rTTR.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            print(entry.created_at, datetime.utcnow(), datetime.utcnow() - timedelta(seconds=10))
            if entry.target.id == member.id and entry.created_at >= datetime.utcnow() - timedelta(seconds=10):
                action = 'Kick'
                footer={'text': 'Kick performed by {}'.format(entry.user.name), 'icon_url': entry.user.avatar_url}
        await self.client.send_message(
            self.botOutput,
            self.createDiscordEmbed(
                action=action,
                primaryInfo=str(member),
                thumbnail=member.avatar_url,
                fields=fields,
                footer=footer if action == 'Kick' else ''
           )
        )

    # Specifically built for moderation module.
    async def on_member_warn(self, member, punishment):
        await self.client.send_message(
            self.botOutput,
            self.createDiscordEmbed(
                action='Warn',
                primaryInfo=str(member),
                thumbnail=member.avatar_url,
                fields=[{
                    'name': punishment['type'],
                    'value': '**Mod:** <@{}>\n**Date:** {}\n**Reason:** {}\n**ID:** {}'.format(
                        punishment['mod'],
                        str(datetime.fromtimestamp(punishment['created']).date()),
                        punishment['reason'].replace(NO_REASON, '*No reason was ever specified.*'),
                        punishment['editID']
                    )
                }]
           )
        )

    # Specifically built for moderation module.
    async def on_message_filter(self, message, embed=None):
        await self.client.send_message(
            self.botOutput,
            self.createDiscordEmbed(
                action='Filter',
                primaryInfo=str(message.author),
                secondaryInfo='{} in{} {}{}:\n\n{}'.format(
                    message.author.mention,
                    " the {} of an embed in".format(embed) if embed else '',
                    '**[{}]** '.format(message.channel.category.name) if message.channel.category else '',
                    message.channel.mention,
                    message.content
                ),
                thumbnail=message.author.avatar_url
           )
        )

    # Specifically built for moderation module.
    async def on_message_review_filter(self, message, rating, url):
        await self.client.send_message(
            self.botOutput,
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

    async def on_message_delete(self, message):
        if message.author == self.client.rTTR.me or message.channel.__class__ == discord.DMChannel or getattr(message, filtered, False):
            return
        await self.client.send_message(
            self.botOutput,
            self.createDiscordEmbed(
                action='Delete',
                primaryInfo=str(message.author),
                secondaryInfo='{} in {}{}:\n\n{}'.format(
                    message.author.mention,
                    '**[{}]** '.format(message.channel.category.name) if message.channel.category else '',
                    message.channel.mention,
                    message.content
                ),
                thumbnail=message.author.avatar_url
           )
        )

    async def on_member_update(self, before, after):
        if self.trackStatuses and before.status != after.status:
            if before.status == discord.Status.online:
                Users.setUserTimeOnline(before.id, Users.getUserTimeOnline(before.id) + (time.time() - self.memberStatusTimeStart[before.id]))
            elif before.status == discord.Status.offline:
                Users.setUserTimeOffline(before.id, Users.getUserTimeOffline(before.id) + (time.time() - self.memberStatusTimeStart[before.id]))
            elif before.status == discord.Status.idle:
                Users.setUserTimeIdle(before.id, Users.getUserTimeIdle(before.id) + (time.time() - self.memberStatusTimeStart[before.id]))
            elif before.status == discord.Status.dnd:
                Users.setUserTimeDND(before.id, Users.getUserTimeDND(before.id) + (time.time() - self.memberStatusTimeStart[before.id]))
            self.memberStatusTimeStart[before.id] = time.time()


module = UserTrackingModule