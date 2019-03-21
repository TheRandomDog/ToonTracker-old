import discord
import asyncio
import random
import time
import re
from datetime import datetime, timedelta
from extra.commands import Command
from modules.module import Module
from utils import Config, database, assert_type, assert_class, get_time_from_seconds, get_progress_bar

NO_REASON = 'No reason was specified at the time of this message -- once a moderator adds a reason this message will self-edit.'
NO_REASON_ENTRY = '*No reason yet. Please add one with `{}editReason {} reason goes here` as soon as possible.*'

class Users:
    def __init__(self, module):
        self.users_db = database.create_section(module, 'users', {
            'id': [database.INT, database.PRIMARY_KEY],
            'level': database.INT,
            'xp': database.INT,
            'time_online': database.INT,
            'time_idle': database.INT,
            'time_dnd': database.INT,
            'time_offline': database.INT
        })
        self.msgs_db = database.create_section(module, 'messages', {
            'id': [database.INT, database.PRIMARY_KEY],
            'user': database.INT,
            'channel': database.INT,
            'message': database.TEXT,
            'attachments': database.INT,
            'embeds': database.INT,
            'deleted': database.INT
        })

    def get_users(self):
        return self.users_db.select()

    def get_user_by_id(self, user_id, create_if_nonexistent=True):
        user = self.users_db.select(where=['id=?', user_id], limit=1)
        if not user and create_if_nonexistent:
            self.users_db.insert(
                id=user_id,
                level=0,
                xp=0,
                time_online=0,
                time_idle=0,
                time_dnd=0,
                time_offline=0
            )
            user = self.users_db.select(where=['id=?', user_id], limit=1)
        return user
    def get_user(self, member, create_if_nonexistent=True):
        return self.get_user_by_id(member.id, create_if_nonexistent)

    def get_user_xp(self, user_id):
        user = self.get_user_by_id(user_id)
        return user['xp']

    def get_user_level(self, user_id):
        user = self.get_user_by_id(user_id)
        return user['level']

    def get_user_time_online(self, user_id):
        user = self.get_user_by_id(user_id)
        return user['time_online']

    def get_user_time_offline(self, user_id):
        user = self.get_user_by_id(user_id)
        return user['time_offline']

    def get_user_time_dnd(self, user_id):
        user = self.get_user_by_id(user_id)
        return user['time_DND']

    def get_user_time_idle(self, user_id):
        user = self.get_user_by_id(user_id)
        return user['time_idle']

    def get_user_message_overview(self, user_id, channel_id=None):
        where = [['user=?', user_id]]
        if channel_id:
            where.append(['channel=?', channel_id])

        messages = self.msgs_db.select('channel, attachments, embeds', where=where)
        overview = {}
        for message in messages:
            if message['channel'] not in overview:
                overview[message['channel']] = {'messages': 0, 'attachments': 0, 'embeds': 0}
            else:
                channel_overview = overview[message['channel']]
                channel_overview['messages'] += 1
                channel_overview['attachments'] += message['attachments']
                channel_overview['embeds'] += message['embeds']

        return overview

    def set_user_xp(self, user_id, value):
        self.users_db.update(where=['id=?', user_id], xp=value)

    def set_user_level(self, user_id, value):
        self.users_db.update(where=['id=?', user_id], level=value)

    def set_user_time_online(self, user_id, value):
        self.users_db.update(where=['id=?', user_id], time_online=value)

    def set_user_time_offline(self, user_id, value):
        self.users_db.update(where=['id=?', user_id], time_offline=value)

    def set_user_time_dnd(self, user_id, value):
        self.users_db.update(where=['id=?', user_id], time_dnd=value)

    def set_user_time_idle(self, user_id, value):
        self.users_db.update(where=['id=?', user_id], time_idle=value)


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
        'Edit': {
            'color': discord.Color.blue(),
            'icon': 'https://cdn.discordapp.com/attachments/183116480089423873/394684550531383306/deleted3.png',
            'title': 'Message Edited'
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
            xp = module.users.get_user_xp(user.id)
            level = module.users.get_user_level(user.id)
            levelxp = '{}\n**Level {}**   {} / {} XP\n{}'.format(
                user.mention,
                level,
                xp,
                module.xp_needed_for_level(level),
                get_progress_bar(xp, module.xp_needed_for_level(level))
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
                        user = client.focused_guild.get_member(int(args[0])) or await client.get_user_info(int(args[0]))
                    except discord.NotFound:
                        moderation = client.request_module('moderation')
                        if moderation:
                            punishment_id = int(args[0])
                            punishment = moderation.punishments.select(where=["id=?", punishment_id], limit=1)
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
                        user = client.focused_guild.get_member(message.raw_mentions[0]) or await client.get_user_info(message.raw_mentions[0])
                    except discord.NotFound:
                        return 'No known user'
            else:
                user = message.mentions[0]

            # Get all punishments for user, each will be an individual field in the embed.
            punishment_fields = []
            notes = []

            if assert_class(message.channel, discord.DMChannel, otherwise=False) or (message.channel.category and message.channel.category.name == 'Staff'):
                moderation = client.request_module('moderation')
                for punishment in moderation.punishments.select(where=['user=?', user.id]):
                    punishment_fields.append({
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

            if len(punishment_fields) > 18:
                punishment_fields = punishment_fields[:17]
                """noteFields = noteFields[:18 - len(punishment_fields)]
                noteFields.append({
                    'name': 'MORE PUNISHMENTS / NOTES EXIST!', 
                    'value': 'All of the punishments / notes on this account cannot be displayed in an embed. Please delete some that are older or unneeded.',
                    'inline': False
                })"""

            # Get all channel participation
            messages = []
            channel_participation = module.users.get_user_message_overview(user.id)
            # A classic Computer Science solution eh? Too lazy for something clever
            most_channel_participation = [(None, -1, 0, 0, 0) for _ in range(3)]
            for channel, participation in channel_participation.items():
                channel = client.focused_guild.get_channel(int(channel))
                if not channel:
                    continue

                total_messages = participation['messages'] + participation['attachments'] + participation['embeds']
                for i in range(2, -1, -1):
                    if total_messages > most_channel_participation[i][1]:
                        if i != 0 and total_messages > most_channel_participation[i - 1][1]:
                            continue
                        else:
                            for j in range(1, i - 1, -1):
                                most_channel_participation[j + 1] = most_channel_participation[j]
                            most_channel_participation[i] = (channel, total_messages, participation['messages'], participation['attachments'], participation['embeds'])
            for channel, _, _messages, attachments, embeds in most_channel_participation:
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
                get_time_from_seconds(module.users.get_user_time_online(user.id), one_unit_limit=True),
                get_time_from_seconds(module.users.get_user_time_idle(user.id), one_unit_limit=True),
                get_time_from_seconds(module.users.get_user_time_dnd(user.id), one_unit_limit=True),
                get_time_from_seconds(module.users.get_user_time_offline(user.id), one_unit_limit=True)
            )

            # Show off user's level / xp 
            xp = module.users.get_user_xp(user.id)
            level = module.users.get_user_level(user.id)
            levelxp = '**Level {}**   {} / {} XP\n{}'.format(
                level,
                xp,
                module.xp_needed_for_level(level),
                get_progress_bar(xp, module.xp_needed_for_level(level))
            )

            # Get all of the user's roles, highlighting their top role
            if hasattr(user, 'roles'):
                roles = user.roles[1:]
                roles.reverse()
                named_roles = [role.name for role in roles]
                if named_roles:
                    named_roles[0] = '**' + named_roles[0] + '**'
                else:
                    named_roles = ['¯\_(ツ)_/¯']
            else:
                roles = []
                named_roles = ['¯\_(ツ)_/¯']

            embed = module.create_discord_embed(
                action='Lookup',
                primary_info=str(user),
                secondary_info=user.mention,
                thumbnail=user.avatar_url,
                fields=[
                    {'name': 'Account Creation Date', 'value': str(user.created_at.date()), 'inline': True},
                    {'name': 'Join Date', 'value': str(user.joined_at.date()) if hasattr(user, 'joined_at') else 'Not on the server.', 'inline': True},
                    {'name': 'Level / XP', 'value': levelxp, 'inline': True},
                    {
                        'name': 'Roles', 
                        'value': '\n'.join(named_roles),
                        'inline': True
                    },
                    {'name': 'Top 3 Channels', 'value': '\n'.join(messages), 'inline': True},
                    {'name': 'Statuses', 'value': statuses, 'inline': True}
                ] + ([{'name': 'Notes', 'value': '\n\n'.join(notes), 'inline': False}] if notes else []) + punishment_fields,
                footer={'text': "Available Commands: ~editReason | ~removePunishment | ~editNote | ~removeNote"} if punishment_fields else None,
                color=roles[0].color if roles else None
            )
            return embed

    def __init__(self, client):
        Module.__init__(self, client)

        self.users = Users(self)
        self.invites = None

        self.track_messages = Config.get_module_setting('usertracking', 'track_messages', True)
        self.tracking_exceptions = Config.get_module_setting('usertracking', 'tracking_exceptions', [])

        self.module_time_start = time.time()
        self.member_status_time_start = {}
        self.track_statuses = Config.get_module_setting('usertracking', 'track_statuses', True)

        self.audit_log_entries = {}
        self.level_cooldowns = {}
        self.level_cooldown = assert_type(Config.get_module_setting('usertracking', 'level_cooldown'), int, otherwise=5)
        self.level_cap = assert_type(Config.get_module_setting('usertracking', 'level_cap'), int, otherwise=-1)
        self.leveling_exceptions = Config.get_module_setting('usertracking', 'leveling_exceptions', [])
        self.allow_user_leveling = Config.get_module_setting('usertracking', 'allow_user_leveling', True)
        self.allow_user_rewards = Config.get_module_setting('usertracking', 'allow_user_rewards', True)
        self.allow_bot_leveling = Config.get_module_setting('usertracking', 'allow_bot_leveling', False)
        self.allow_bot_rewards = Config.get_module_setting('usertracking', 'allow_bot_rewards', False)
        self.allow_mod_leveling = Config.get_module_setting('usertracking', 'allow_mod_leveling', True)
        self.allow_mod_rewards = Config.get_module_setting('usertracking', 'allow_mod_rewards', False)
        self.regular_role = discord.utils.get(client.focused_guild.roles, id=Config.get_module_setting('usertracking', 'regular_role_id'))

        self.spam_channel = Config.get_module_setting('usertracking', 'spam_channel')
        self.log_channel = Config.get_module_setting('usertracking', 'log_channel')

    async def add_xp(self, message):
        member = message.author
        try:
            last_messages = await message.channel.history(limit=2).flatten()
            # If the cooldown hasn't expired, and the message before this one was done by us...
            if time.time() < self.level_cooldowns.get(member, 0) and (len(last_messages) != 2 or last_messages[0].author == last_messages[1].author):
                return
        except:
            # Yeesh, this generally means Discord's unavailable to check the history.
            # Spamming doesn't happen that often, let's just give them the XP.
            pass

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
        if any([message.content.startswith(bot_prefix) for bot_prefix in ('~', '!', ';;')]):
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

        prev_xp = self.users.get_user_xp(member.id)
        xp += len(words)
        xp *= multiplier
        self.users.set_user_xp(member.id, prev_xp + min(25, max(0, xp)))
        self.level_cooldowns[member] = time.time() + self.level_cooldown

    def xp_needed_for_level(self, level):
        return 5 * (level**2) + 50*level + 100

    def level(self, member):
        response = None
        level = self.users.get_user_level(member.id)
        if self.level_cap != -1 and level >= self.level_cap:
            return

        xp = self.users.get_user_xp(member.id)
        xp_needed = self.xp_needed_for_level(level)
        if xp >= xp_needed:  # Sorry Mee6 I've never been good with original math
            level += 1
            response = level
            self.users.set_user_level(member.id, level)
            self.users.set_user_xp(member.id, xp - xp_needed)
        return response

    async def on_message(self, message):
        # A hack to get invites updates as quickly as possible.
        if not self.invites:
            self.invites = await self.client.focused_guild.invites()

        # Definitely don't want to progress if it's a heckin' webhook.
        if message.webhook_id:
            return
        # You don't want to progress if there's an exception being made.
        if message.channel.__class__ == discord.DMChannel or message.channel.id in self.leveling_exceptions or message.author.id in self.leveling_exceptions or \
            any([role.id in self.leveling_exceptions for role in message.author.roles]):
            return
        if message.channel.id in self.tracking_exceptions:
            return

        if self.track_messages:
            self.users.msgs_db.insert(
                id=message.id,
                user=message.author.id,
                channel=message.channel.id,
                message=message.content,
                attachments=len(message.attachments),
                embeds=len(message.embeds),
                deleted=0
            )

        bot = message.author.bot
        mod = any([Config.get_rank_of_role(role.id) >= 300 for role in message.author.roles])

        if mod:
            if self.allow_mod_leveling:
                await self.add_xp(message)
                leveled = self.level(message.author)
                if leveled and self.allow_mod_rewards:
                    await self.assign_awards(message.author, leveled)
        elif bot:
            if self.allow_bot_leveling:
                await self.add_xp(message)
                leveled = self.level(message.author)
                if leveled and self.allow_bot_rewards:
                    await self.assign_awards(message.author, leveled)
        else:
            if self.allow_user_leveling:
                await self.add_xp(message)
                leveled = self.level(message.author)
                if leveled and self.allow_user_rewards:
                    await self.assign_awards(message.author, leveled)

    async def assign_awards(self, member, level):
        if level >= 4:
            if self.regular_role and self.regular_role not in member.roles:
                await member.add_roles(self.regular_role, reason='User leveled up to level 7')
                embed = self.create_discord_embed(
                    action='Level',
                    primary_info="You've leveled up to LEVEL {}!".format(level),
                    secondary_info="Thanks for spending some of your time to chat with us! " \
                    "You now have permission to *speak in voice channels* and *upload files and images* to the server. Have fun!",
                    thumbnail=member.avatar_url,
                    footer={'text': '- The mods from the Toontown Rewritten Discord'}
                )
                try:
                    await self.client.send_message(member, embed)
                except discord.HTTPException:
                    print("Could not send level 4 notification to {} (probably because they have DMs disabled for users/bots who don't share a server they're in).".format(str(member)))

    def create_discord_embed(self, action, primary_info=discord.Embed.Empty, secondary_info=discord.Embed.Empty, thumbnail='', fields=[], footer={}, image=None, color=None):
        action = self.ACTIONS[action]
        embed = discord.Embed(title=primary_info, description=secondary_info, color=color if color else action['color'])
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
        moderation = self.client.request_module('moderation')
        if moderation:
            punishments = moderation.punishments.select(where=["user=? AND strftime('%s', 'now') - created < 10", member.id])
        if moderation and punishments:
            punishment = punishments[-1]
            fields = [{
                'name': punishment['type'] + (' ({})'.format(punishment['end_length']) if punishment['end_length'] else ''),
                'value': '**Mod:** <@{}>\n**Date:** {}\n**Reason:** {}\n**ID:** {}'.format(
                    punishment['mod'],
                    str(datetime.fromtimestamp(punishment['created']).date()),
                    punishment['reason'].replace(NO_REASON, NO_REASON_ENTRY.format(self.client.command_prefix, punishment['id'])),
                    punishment['id']
                )
            }]
        for message in self.client._connection._messages:
            if message.author == member:
                message.nonce = 'banned'  # Read other comments editing `nonce`.
        async for entry in self.client.focused_guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            footer={'text': 'Ban performed by {}'.format(entry.user.name), 'icon_url': entry.user.avatar_url}
        mod_long_entry = await self.client.send_message(
            self.log_channel,
            self.create_discord_embed(
                action='Ban',
                primary_info=str(member),
                thumbnail=member.avatar_url,
                fields=fields,
                footer=footer
           )
        )
        if punishment:
            moderation.punishments.update(where=['id=?', punishment['id']], log=mod_long_entry.id)
        return mod_long_entry

    async def on_member_join(self, member):
        punishment_fields = []
        notes = []
        moderation = self.client.request_module('moderation')
        if moderation:
            for punishment in moderation.punishments.select(where=['user=?', member.id]):
                punishment_fields.append({
                    'name': punishment['type'] + (' ({})'.format(punishment['end_length']) if punishment['end_length'] else ''),
                    'value': '{}\n**Mod:** <@{}> | **Date:** {} | **ID:** {}'.format(
                        ('`' + punishment['reason'] + '`').replace('`' + NO_REASON + '`', '*No reason was ever specified.*'),
                        punishment['mod'],
                        str(datetime.fromtimestamp(punishment['created']).date()),
                        punishment['id']
                    ),
                    'inline': False
                })

            for note in moderation.notes.select(where=['user=?', member.id]):
                notes.append('{tilde}{}{tilde}\n**Mod:** <@{}> | **Date:** {} | **ID:** {}'.format(
                    note['content'],
                    note['mod'],
                    str(datetime.fromtimestamp(note['created']).date()),
                    note['id'],
                    tilde='`'
                ))
        if len(punishment_fields) > 18:
            punishment_fields = punishment_fields[:17]

        xp = self.users.get_user_xp(member.id)
        level = self.users.get_user_level(member.id)
        # Show off user's level / xp 
        levelxp = '**Level {}**   {} / {} XP\n{}'.format(
            level,
            xp,
            self.xp_needed_for_level(level),
            get_progress_bar(xp, self.xp_needed_for_level(level))
        )
        if level >= 4:
            await member.add_roles(self.regular_role, reason='User rejoined and had regular role')

        if self.invites:
            ni = await self.client.focused_guild.invites()
            new_invites = {i.code: i.uses for i in ni}
            old_invites = {i.code: i.uses for i in self.invites}
            code_used = 'toontown'
            for code, uses in new_invites.items():
                # In the event that a new invite code was generated, but has not been used,
                # we'll skip it hackily by calling `old_invites.get(code, uses)` to bypass the second check.
                if (code not in old_invites and uses > 0) or old_invites.get(code, uses) != uses:
                    code_used = code
                    break
            self.invites = ni
        else:
            code_used = None

        await self.client.send_message(
            self.log_channel,
            self.create_discord_embed(
                action='Join',
                primary_info=str(member),
                secondary_info=member.mention,
                thumbnail=member.avatar_url,
                fields=[
                    {'name': 'Account Creation Date', 'value': str(member.created_at.date()), 'inline': True},
                    {'name': 'Join Date', 'value': str(member.joined_at.date()), 'inline': True},
                    {'name': 'Level / XP', 'value': levelxp, 'inline': True}
                ] + ([{'name': 'Notes', 'value': '\n\n'.join(notes), 'inline': False}] if notes else []) + punishment_fields,
                footer={'text': "Joined using invite code: {}".format(code_used)} if code_used else None
            )
        )
        self.member_status_time_start[member.id] = time.time()

    async def on_member_remove(self, member):
        action = 'Leave'
        fields = []
        punishment = None
        moderation = self.client.request_module('moderation')
        if moderation:
            punishments = moderation.punishments.select(where=["user=? AND type='Kick' AND strftime('%s', 'now') - created < 10", member.id])
        if moderation and punishments:
            punishment = punishments[-1]
            fields = [{
                'name': punishment['type'] + (' ({})'.format(punishment['end_length']) if punishment['end_length'] else ''),
                'value': '**Mod:** <@{}>\n**Date:** {}\n**Reason:** {}\n**ID:** {}'.format(
                    punishment['mod'],
                    str(datetime.fromtimestamp(punishment['created']).date()),
                    punishment['reason'].replace(NO_REASON, NO_REASON_ENTRY.format(self.client.command_prefix, punishment['id'])),
                    punishment['id']
                )
            }]

        async for entry in self.client.focused_guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id and entry.created_at >= datetime.utcnow() - timedelta(seconds=2):
                action = 'Kick'
                footer={'text': 'Kick performed by {}'.format(entry.user.name), 'icon_url': entry.user.avatar_url}
        mod_long_entry = await self.client.send_message(
            self.log_channel,
            self.create_discord_embed(
                action=action,
                primary_info=str(member),
                thumbnail=member.avatar_url,
                fields=fields,
                footer=footer if action == 'Kick' else ''
           )
        )
        if punishment:
            moderation.punishments.update(where=['id=?', punishment['id']], log=mod_long_entry.id)
        return mod_long_entry

    # Specifically built for moderation module.
    async def on_member_warn(self, member, punishment):
        mod_long_entry = await self.client.send_message(
            self.log_channel,
            self.create_discord_embed(
                action='Warn',
                primary_info=str(member),
                thumbnail=member.avatar_url,
                fields=[{
                    'name': punishment['type'],
                    'value': '**Mod:** <@{}>\n**Date:** {}\n**Reason:** {}\n**ID:** {}'.format(
                        punishment['mod'],
                        str(datetime.fromtimestamp(punishment['created']).date()),
                        punishment['reason'].replace(NO_REASON, NO_REASON_ENTRY.format(self.client.command_prefix, punishment['id'])),
                        punishment['id']
                    )
                }]
           )
        )
        moderation = self.client.request_module('moderation')
        moderation.punishments.update(where=['id=?', punishment['id']], log=mod_long_entry.id)
        return mod_long_entry

    # Specifically built for moderation module.
    async def on_message_filter(self, message, *, link=False, word=None, text=None, embed=None):
        replace_from = text if text else message.content
        await self.client.send_message(
            self.log_channel,
            self.create_discord_embed(
                action='Link' if link else 'Filter',
                primary_info=str(message.author),
                secondary_info='{} in{} {}{}:\n\n{}'.format(
                    message.author.mention,
                    " the {} of an embed in".format(embed) if embed else '',
                    '**[{}]** '.format(message.channel.category.name) if message.channel.category else '',
                    message.channel.mention,
                    replace_from.replace(word, '**' + word + '**') if word else replace_from
                ),
                thumbnail=message.author.avatar_url
           )
        )

    # Specifically built for moderation module.
    async def on_nickname_filter(self, member, *, word=None, text=None):
        replace_from = text if text else member.display_name
        await self.client.send_message(
            self.log_channel,
            self.create_discord_embed(
                action='Nickname',
                primary_info=str(member),
                secondary_info=replace_from.replace(word, '**' + word + '**') if word else replace_from,
                thumbnail=member.avatar_url
            )
        )

    # Specifically built for moderation module.
    async def on_message_review_filter(self, message, rating, url):
        await self.client.send_message(
            self.log_channel,
            self.create_discord_embed(
                action='Review',
                primary_info=str(message.author),
                secondary_info='{} in {}{} **[Rating: {}]**:'.format(
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
            self.log_channel,
            self.create_discord_embed(
                action='Unpunish',
                primary_info=str(member),
                thumbnail=member.avatar_url,
                fields=[{
                    'name': punishment['type'],
                    'value': '**Mod:** <@{}>\n**Date Punished:** {}\n**Reason:** {}\n**Old ID:** {}'.format(
                        punishment['mod'],
                        str(datetime.fromtimestamp(punishment['created']).date()),
                        punishment['reason'].replace(NO_REASON, NO_REASON_ENTRY.format(self.client.command_prefix, punishment['id'])),
                        punishment['id']
                    )
                }]
           )
        )

    # Specifically built for moderation module.
    async def on_member_note(self, member, note):
        mod_long_entry = await self.client.send_message(
            self.log_channel,
            self.create_discord_embed(
                action='Note',
                primary_info=str(member),
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
        moderation = self.client.request_module('moderation')
        moderation.notes.update(where=['id=?', note['id']], log=mod_long_entry.id)
        return mod_long_entry

    async def on_message_edit(self, before, after):
        message = after
        if message.author == self.client.focused_guild.me or message.channel.__class__ == discord.DMChannel or message.nonce in ['filter', 'silent']:
            return
        elif before.content == after.content:
            return  # Embed updates will trigger the message edit event, we don't need to log it though.
        elif message.channel.id in self.tracking_exceptions:
            return

        if self.track_messages:
            try:
                self.users.msgs_db.update(
                    where=['id=?', message.id],
                    message=message.content
                )
            except sqlite3.OperationalError as e:
                pass
        await self.client.send_message(
            self.spam_channel,
            self.create_discord_embed(
                action='Edit',
                primary_info=str(message.author),
                secondary_info='{}{} in {}{}:'.format(
                    '*The message contained an embed.*\n' if before.embeds else '',
                    message.author.mention,
                    '**[{}]** '.format(message.channel.category.name) if message.channel.category else '',
                    message.channel.mention
                ),
                fields=[
                    {'name': 'New Message:', 'value': after.content, 'inline': False},
                    {'name': 'Old Message:', 'value': before.content if before.content else '*(no message)*', 'inline': False},
                ],
                thumbnail=message.author.avatar_url,
                image=before.attachments[0].proxy_url if before.attachments else None
                ## proxy_url is cached, so it is not instantly deleted when a message is deleted
           )
        )

    async def on_message_delete(self, message):
        if message.author == self.client.focused_guild.me or message.channel.__class__ == discord.DMChannel or message.nonce in ['filter', 'silent']:
            return
        elif message.channel.id in self.tracking_exceptions:
            return

        if self.track_messages:
            try:
                self.users.msgs_db.update(
                    where=['id=?', message.id],
                    deleted=1
                )
            except sqlite3.OperationalError as e:
                pass

        footer = {}
        async for entry in self.client.focused_guild.audit_logs(limit=5, action=discord.AuditLogAction.message_delete):
            # Discord Audit Logs will clump together deleted messages, saying "MOD deleted X message(s) from USER in TARGET"
            # It will still keep the creation date of the entry though, which could be as stale as a few minutes.
            #
            # So if it's not an entry made within 2 seconds, just verify the message being deleted is in the same channel
            # and by the same user and we can assume that if the count is more than 1 that it was deleted by someone else.
            # The best we can do right now.
            prev_deletion_count = self.audit_log_entries.get(entry.id, 0)
            if message.nonce == 'banned':
                footer={'text': 'Message deleted due to a ban', 'icon_url': self.ACTIONS['Ban']['icon']}
            elif entry.created_at >= datetime.utcnow() - timedelta(seconds=2) or \
              (entry.extra.channel == message.channel and entry.target == message.author and entry.extra.count > prev_deletion_count):
                footer={'text': 'Message deleted by {}'.format(entry.user.name), 'icon_url': entry.user.avatar_url}
            elif message.nonce == 'cleared':
                footer={'text': 'Message deleted via ~clear'}
            self.audit_log_entries[entry.id] = entry.extra.count
        await self.client.send_message(
            self.spam_channel,
            self.create_discord_embed(
                action='Delete',
                primary_info=str(message.author),
                secondary_info='{}{} in {}{}:\n\n{}'.format(
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
        if self.track_statuses and before.status != after.status:
            last_status_time = self.member_status_time_start.get(before.id, self.module_time_start)

            if before.status == discord.Status.online:
                self.users.set_user_time_online(before.id, self.users.get_user_time_online(before.id) + (time.time() - last_status_time))
            elif before.status == discord.Status.offline:
                self.users.set_user_time_offline(before.id, self.users.get_user_time_offline(before.id) + (time.time() - last_status_time))
            elif before.status == discord.Status.idle:
                self.users.set_user_time_idle(before.id, self.users.get_user_time_idle(before.id) + (time.time() - last_status_time))
            elif before.status == discord.Status.dnd:
                self.users.set_user_time_dnd(before.id, self.users.get_user_time_dnd(before.id) + (time.time() - last_status_time))
            self.member_status_time_start[before.id] = time.time()

        # Then mutes.
        muted_role = discord.utils.get(self.client.focused_guild.roles, name=Config.get_module_setting('moderation', 'muted_role_name') or 'Muted')
        if muted_role and (muted_role not in before.roles and muted_role in after.roles):
            fields = []
            punishment = None
            moderation = self.client.request_module('moderation')
            if moderation:
                punishments = moderation.punishments.select(where=["user=? AND strftime('%s', 'now') - created < 10", after.id])
            if moderation and punishments:
                punishment = punishments[-1]
                fields = [{
                    'name': punishment['type'] + (' ({})'.format(punishment['end_length']) if punishment['end_length'] else ''),
                    'value': '**Mod:** <@{}>\n**Date:** {}\n**Reason:** {}\n**ID:** {}'.format(
                        punishment['mod'],
                        str(datetime.fromtimestamp(punishment['created']).date()),
                        punishment['reason'].replace(NO_REASON, NO_REASON_ENTRY.format(self.client.command_prefix, punishment['id'])),
                        punishment['id']
                    )
                }]
            async for entry in self.client.focused_guild.audit_logs(limit=5, action=discord.AuditLogAction.member_role_update):
                if muted_role in entry.after.roles:
                    footer={'text': 'Mute performed by {}'.format(entry.user.name), 'icon_url': entry.user.avatar_url}
                    break
            mod_long_entry = await self.client.send_message(
                self.log_channel,
                self.create_discord_embed(
                    action='Mute',
                    primary_info=str(after),
                    thumbnail=after.avatar_url,
                    fields=fields,
                    footer=footer
               )
            )
            if punishment:
                moderation.punishments.update(where=['id=?', punishment['id']], log=mod_long_entry.id)
            return mod_long_entry

module = UserTrackingModule