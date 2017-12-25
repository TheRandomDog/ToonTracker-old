import discord
import asyncio
import random
import time
from datetime import datetime, timedelta
from modules.module import Module
from utils import Config, Users, assertType

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
            'color': discord.Color.blue(),
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/394664540916154378/exit.png',
            'title': 'User Left'
        },
        'Warn': {
            'color': discord.Color.from_rgb(245, 165, 0),
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/394675747324821504/warn.png'
        }
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
        'Delete': {
            'color': discord.Color.dark_blue(),
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/394682117537398784/deleted2.png',
            'title': 'Message Deleted'
        }
    }

    def __init__(self, client):
        Module.__init__(self, client)

        self.trackMessages = Config.getModuleSetting('usertracking', 'track_messages', True)
        self.trackingExceptions = Config.getModuleSetting('usertracking', 'tracking_exceptions', [])

        self.memberStatusTimeStart = {member.id: time.time() for member in client.rTTR.members}
        self.trackStatuses = Config.getModuleSetting('usertracking', 'track_statuses', True)

        self.levelCooldowns = {}
        self.levelCooldown = assertType(Config.getModuleSetting('usertracking', 'level_cooldown'), int, otherwise=60)
        self.levelCap = assertType(Config.getModuleSetting('usertracking', 'level_cap'), int, otherwise=-1)
        self.levelingExceptions = Config.getModuleSetting('usertracking', 'leveling_exceptions', [])
        self.allowUserLeveling = Config.getModuleSetting('usertracking', 'allow_user_leveling', True)
        self.allowUserRewards = Config.getModuleSetting('usertracking', 'allow_user_rewards', True)
        self.allowBotLeveling = Config.getModuleSetting('usertracking', 'allow_bot_leveling', False)
        self.allowBotRewards = Config.getModuleSetting('usertracking', 'allow_bot_rewards', False)
        self.allowModLeveling = Config.getModuleSetting('usertracking', 'allow_mod_leveling', True)
        self.allowModRewards = Config.getModuleSetting('usertracking', 'allow_mod_rewards', False)

        self.botOutput = Config.getSetting('botspam')

    def addXP(self, member):
        if time.time() < self.levelCooldowns.get(member, 0):
            return
        xp = Users.getUserXP(member.id)
        xp += random.randint(1, 10)
        Users.setUserXP(member.id, xp)
        self.levelCooldowns[member] = time.time() + self.levelCooldown

    def level(self, member):
        response = None
        level = Users.getUserLevel(member.id)
        if level >= self.levelCap:
            return

        if Users.getUserXP(member.id) >= 5 * (level**2) + 50*level + 100:  # Sorry Mee6 I've never been good with original math
            level += 1
            response = level
        Users.setUserLevel(member.id, level)
        Users.setUserXP(member.id, 0)
        return response

    async def handleMsg(self, message):
        # You don't want to progress if there's an exception being made.
        if message.channel.id in self.levelingExceptions or message.author.id in self.levelingExceptions or \
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
                self.addXP(message.author)
                leveled = self.level(message.author)
                if leveled and self.allowModRewards:
                    pass  # Rewards TBD
        elif bot:
            if self.allowBotLeveling:
                self.addXP(message.author)
                leveled = self.level(message.author)
                if leveled and self.allowBotRewards:
                    pass  # Rewards TBD
        else:
            if self.allowUserLeveling:
                self.addXP(message.author)
                leveled = self.level(message.author)
                if leveled and self.allowUserRewards:
                    pass  # Rewards TBD

    def createDiscordEmbed(self, action, primaryInfo=discord.Embed.Empty, secondaryInfo=discord.Embed.Empty, thumbnail='', fields=[], footer={}):
        action = self.ACTIONS[action]
        embed = discord.Embed(title=primaryInfo, description=secondaryInfo, color=action['color'])
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
                ],
                #footer="You can use a punishment's edit ID to ~editReason or ~removePunishment" if Users.getUserPunishments(member.id) else ''
            )
        )

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
                action='Warned',
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
    async def on_message_filter(self, message):
        await self.client.send_message(
            self.botOutput,
            self.createDiscordEmbed(
                action='Filter',
                primaryInfo=str(message.author),
                secondaryInfo='{} in {}:\n\n{}'.format(message.author.mention, message.channel, message.content),
                thumbnail=message.author.avatar_url
           )
        )

    async def on_message_delete(self, message):
        await self.client.send_message(
            self.botOutput,
            self.createDiscordEmbed(
                action='Delete',
                primaryInfo=str(message.author),
                secondaryInfo='{} in {}:\n\n{}'.format(message.author.mention, message.channel, message.content),
                thumbnail=message.author.avatar_url
           )
        )

    async def on_member_update(self, before, after):
        print(self.memberStatusTimeStart)
        if self.trackStatuses and before.status != after.status:
            if before.status == discord.Status.online:
                Users.setUserTimeOnline(before.id, Users.getUserTimeOnline(before.id) + (time.time() - self.memberStatusTimeStart[before.id]))
            elif before.status == discord.Status.offline:
                Users.setUserTimeOffline(before.id, Users.getUserTimeOffline(before.id) + (time.time() - self.memberStatusTimeStart[before.id]))
            elif before.status == discord.Status.idle:
                Users.setUserTimeIdle(before.id, Users.getUserTimeIdle(before.id) + (time.time() - self.memberStatusTimeStart[before.id]))
            elif before.status == discord.status.dnd:
                Users.setUserTimeDND(before.id, Users.getUserTimeDND(before.id) + (time.time() - self.memberStatusTimeStart[before.id]))
            self.memberStatusTimeStart[before.id] = time.time()


module = UserTrackingModule