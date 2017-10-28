import os
import re
import json
import logging
from __init__ import __version__
from discord import Embed, Color, Member
from datetime import datetime

# Create config file if it doesn't exist
try:
    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    f = open(os.path.join(__location__, 'config.json'), 'r+')
    c = f.read()
    if c == '':
        f.write('{}')
except json.JSONDecodeError:
    f.write('{}')
finally:
    f.close()


# ASSERTIONS

def assertType(value, *types):
    if not type(value) in types:
        raise TypeError("Expected {} when passed value '{}', found {} instead".format(
            ", ".join([str(t) for t in types]), value, type(value))
        )
    return value

def assertTypeOrOtherwise(value, *types, otherwise):
    return value if type(value) in types else otherwise

# CONFIG

class Config:
    @staticmethod
    def openFile(mode):
        file = open(os.path.join(__location__, 'config.json'), mode)
        content = json.loads(file.read())
        file.close()
        try:
            file = open(os.path.join(__location__, 'profiles', content['profile']), mode)
        except (KeyError, FileNotFoundError) as e:
            if isinstance(e, FileNotFoundError):
                print('[!!!] Tried to open profile "{}", but the profile couldn\'t be found.'.format(content['profile']))
            file = open(os.path.join(__location__, 'config.json'), mode)
        return file

    @classmethod
    def getSetting(cls, setting, otherwise=None):
        try:
            file = cls.openFile('r')
            content = json.loads(file.read())
            return content.get(setting, otherwise)
        except json.JSONDecodeError:
            print('[!!!] Tried to read setting "{}", but {} did not have valid JSON content.'.format(
                setting, os.path.basename(file.name))
            )
            return otherwise
        finally:
            file.close()

    @classmethod
    def getModuleSetting(cls, module, setting, otherwise=None):
        pss = cls.getSetting(module)
        if not pss or pss.get(setting, None) == None:
            return otherwise
        return pss[setting]

    @classmethod
    def getUserRanks(cls):
        userRanks = {int(userID): rank for userID, rank in cls.getSetting('user_ranks').items()}
        return userRanks or {}

    @classmethod
    def getRankOfUser(cls, user):
        return cls.getUserRanks().get(user, 0)

    @classmethod
    def getUsersWithRank(cls, rank):
        users = []
        for u, r in cls.getUserRanks().items():
            if r >= rank:
                users.append(u)
        return users

    @classmethod
    def getRoleRanks(cls):
        roleRanks = {int(roleID): rank for roleID, rank in cls.getSetting('role_ranks').items()}
        return roleRanks or {}

    @classmethod
    def getRankOfRole(cls, role):
        return cls.getRoleRanks().get(role, 0)

    @classmethod
    def getRolesWithRank(cls, rank):
        roles = []
        for l, r in cls.getRoleRanks().items():
            if r >= rank:
                roles.append(l)
        return roles

    @classmethod
    def setSetting(cls, setting, value):
        try:
            file = cls.openFile('r+')
            content = json.loads(file.read())
            content[setting] = value
            file.seek(0, 0)
            file.write(json.dumps(content, indent=4, sort_keys=True))
            file.truncate()
        except json.JSONDecodeError:
            print('[!!!] Tried to write value "{}" to setting "{}", but {} did not have valid JSON content.'.format(
                value, setting, os.path.basename(file.name))
            )
        finally:
            file.close()

    @classmethod
    def setModuleSetting(cls, module, setting, value):
        settings = cls.getSetting(module)
        if settings == None:
            settings = {}
        settings[setting] = value
        cls.setSetting(module, settings)

    @classmethod
    def setUserRank(cls, user, rank):
        userRanks = cls.getUserRanks()
        userRanks[user] = rank
        cls.setSetting('user_ranks', userRanks)

    @classmethod
    def setRoleRank(cls, role, rank):
        roleRanks = cls.getRoleRanks()
        roleRanks[role] = rank
        cls.setSetting('role_ranks', userRanks)

# USERS

class Users:
    NO_REASON = 'No reason was specified at the time of this message -- once a moderator adds a reason this message will self-edit.'

    @staticmethod
    def openFile(mode):
        file = open(os.path.join(__location__, 'users.json'), mode)
        return file

    @classmethod
    def getUsers(cls):
        try:
            file = cls.openFile('r')
            content = {int(userID): data for userID, data in json.loads(file.read()).items()}
            return content
        except json.JSONDecodeError:
            print('[!!!] Tried to read user id "{}", but {} did not have valid JSON content.'.format(
                userID, os.path.basename(file.name))
            )
            return otherwise
        finally:
            file.close()

    @classmethod
    def getUserJSON(cls, userID):
        content = cls.getUsers()
        if not content.get(userID, None):
            cls.createUser(userID)
            content = cls.getUsers()
        return content.get(userID, None)

    @classmethod
    def getUserEmbed(cls, member):
        content = cls.getUsers()
        if not content.get(member.id, None):
            cls.createUser(member.id)
            content = cls.getUsers()
        user = content[member.id]

        embed = Embed(title='User Details', color=member.top_role.color if isinstance(member, Member) else Color.default())
        embed.set_author(name=str(member), icon_url=member.avatar_url)
        embed.add_field(name='Account Creation Date', value=str(member.created_at.date()), inline=True)
        embed.add_field(name='Join Date', value=str(member.joined_at.date()) if isinstance(member, Member) else 'Not on the server.', inline=True)
        embed.add_field(name='Level | XP', value='{} | {}'.format(user['level'], user['xp']), inline=True)
        for punishment in user['punishments']:
            if punishment.get('length', None):
                embed.add_field(
                    name='Temporary Ban ({})'.format(punishment['length']),
                    value='**Mod:** <@{}>\n**Date:** {}\n**Reason:** {}\n**ID:** {}'.format(
                        punishment['mod'],
                        str(datetime.fromtimestamp(punishment['created']).date()),
                        punishment['reason'].replace(cls.NO_REASON, '*No reason was ever specified.*'),
                        punishment['editID']
                    ),
                    inline=False
                )
            else:
                embed.add_field(
                    name=punishment['type'],
                    value='**Mod:** <@{}>\n**Date:** {}\n**Reason:** {}\n**ID:** {}'.format(
                        punishment['mod'],
                        str(datetime.fromtimestamp(punishment['created']).date()),
                        punishment['reason'].replace(cls.NO_REASON, '*No reason was ever specified.*'),
                        punishment['editID']
                    ),
                    inline=False
                )
        if len(user['punishments']):
            embed.set_footer(text="You can use a punishment's edit ID to ~editReason or ~removePunishment")
        return embed

    @classmethod
    def getUserXP(cls, userID):
        user = cls.getUserJSON(userID)
        return user['xp']

    @classmethod
    def getUserLevel(cls, userID):
        user = cls.getUserJSON(userID)
        return user['level']

    @classmethod
    def getUserTimeOnline(cls, userID):
        user = cls.getUserJSON(userID)
        return user['time_online']

    @classmethod
    def getUserTimeOffline(cls, userID):
        user = cls.getUserJSON(userID)
        return user['time_offline']

    @classmethod
    def getUserTimeDND(cls, userID):
        user = cls.getUserJSON(userID)
        return user['time_DND']

    @classmethod
    def getUserTimeIdle(cls, userID):
        user = cls.getUserJSON(userID)
        return user['time_idle']

    @classmethod
    def getUserChannelHistory(cls, userID, channelID=None):
        user = cls.getUserJSON(userID)
        channelHistory = user['channel_history']
        if channelID:
            return channelHistory.get(channelID, {'messages': 0, 'attachments': 0})
        return channelHistory

    @classmethod
    def getUserPunishments(cls, userID):
        user = cls.getUserJSON(userID)
        return user['punishments']

    @classmethod
    def createUser(cls, userID, **kwargs):
        data = {
            'xp': kwargs.get('xp', 0),
            'level': kwargs.get('level', 0),
            'time_online': kwargs.get('time_online', 0),
            'time_offline': kwargs.get('time_offline', 0),
            'time_DND': kwargs.get('time_DND', 0),
            'time_idle': kwargs.get('time_idle', 0),
            'channel_history': kwargs.get('channel_history', {}),
            'punishments': kwargs.get('punishments', [])
        }
        cls.setUserJSON(userID, data)

    @classmethod
    def setUserJSON(cls, userID, value):
        userID = str(userID)
        try:
            file = cls.openFile('r+')
            content = json.loads(file.read())
            content[str(userID)] = value
            file.seek(0, 0)
            file.write(json.dumps(content, indent=4, sort_keys=True))
            file.truncate()
        except json.JSONDecodeError:
            print('[!!!] Tried to write value "{}" to user "{}", but {} did not have valid JSON content.'.format(
                value, userID, os.path.basename(file.name))
            )
        finally:
            file.close()

    @classmethod
    def setUserXP(cls, userID, value):
        userJSON = cls.getUserJSON(userID)
        userJSON['xp'] = value
        cls.setUserJSON(userID, userJSON)

    @classmethod
    def setUserLevel(cls, userID, value):
        userJSON = cls.getUserJSON(userID)
        userJSON['level'] = value
        cls.setUserJSON(userID, userJSON)

    @classmethod
    def setUserTimeOnline(cls, userID, value):
        userJSON = cls.getUserJSON(userID)
        userJSON['time_online'] = value
        cls.setUserJSON(userID, userJSON)

    @classmethod
    def setUserTimeOffline(cls, userID, value):
        userJSON = cls.getUserJSON(userID)
        userJSON['time_offline'] = value
        cls.setUserJSON(userID, userJSON)

    @classmethod
    def setUserTimeDND(cls, userID, value):
        userJSON = cls.getUserJSON(userID)
        userJSON['time_DND'] = value
        cls.setUserJSON(userID, userJSON)

    @classmethod
    def setUserTimeIdle(cls, userID, value):
        userJSON = cls.getUserJSON(userID)
        userJSON['time_idle'] = value
        cls.setUserJSON(userID, userJSON)

    @classmethod
    def setUserChannelHistory(cls, userID, channelID, **kwargs):
        userJSON = cls.getUserJSON(userID)
        userJSON['channel_history'][channelID] = kwargs
        cls.setUserJSON(userID, userJSON)

    @classmethod
    def setUserPunishments(cls, userID, punishments):
        userJSON = cls.getUserJSON(userID)
        userJSON['punishments'] = punishments
        cls.setUserJSON(userID, userJSON)

SHORT_TIME = re.compile(r'(?P<num>[0-9]+)(?P<char>[smhdwMy])')
LENGTHS = {
    's': 1,
    'm': 60,
    'h': 3600,
    'd': 86400,
    'w': 604800,
    'M': 2629743,
    'y': 31556926
}
FULL = {
    's': 'seconds',
    'm': 'minutes',
    'h': 'hours',
    'd': 'days',
    'w': 'weeks',
    'M': 'months',
    'y': 'years'
}
def getShortTimeLength(time):
    match = SHORT_TIME.match(time)
    if not match:
        raise ValueError('time must be formatted as number + letter (e.g. 15s, 2y, 1w, 7d, 24h)')
    return LENGTHS[match.group('char')] * int(match.group('num'))
def getShortTimeUnit(time):
    match = SHORT_TIME.match(time)
    if not match:
        raise ValueError('time must be formatted as number + letter (e.g. 15s, 2y, 1w, 7d, 24h)')
    return FULL[match.group('char')]
def getLongTime(time):
    match = SHORT_TIME.match(time)
    if not match:
        raise ValueError('time must be formatted as number + letter (e.g. 15s, 2y, 1w, 7d, 24h)')
    return '{} {}'.format(match.group('num'), FULL[match.group('char')])

def getTimeFromSeconds(seconds, oneUnitLimit=False):
    if int(seconds <= 60):
        if int(seconds == 60):
            return '1 minute'
        else:
            return '{} seconds'.format(int(seconds))
    elif int(seconds / 60) <= 60:
        if int(seconds / 60) == 1:
            return '1 minute'
        else:
            return '{} minutes'.format(int(seconds / 60))
    else:
        h = 0
        m = int(seconds / 60)
        while m > 60:
            h += 1
            m -= 60
        hs = 'hour' if h == 1 else 'hours'
        ms = 'minute' if m == 1 else 'minutes'
        if not oneUnitLimit:
            return '{} {} and {} {}'.format(str(h), hs, str(m), ms)
        else:
            return '{} {}'.format(str(h), hs)

def getAttributeFromMatch(iterable, match):
    for k, v in iterable.items():
        if match in k:
            return v

def getVersion():
    return __version__

def createDiscordEmbed(title, description=Embed.Empty, *, multipleFields=False, color=None, url=None, **kwargs):
    if multipleFields:
        embed = Embed(color=color if color else Color.green(), **kwargs)
        # If we have multiple inline fields, the thumbnail might push them off.
        # Therefore, we'll use the author space to include the icon url.
        embed.set_author(name=title)#, icon_url=TTR_ICON)
    elif url:
        embed = Embed(title=title, description=description, url=url, color=color if color else Color.default(), **kwargs)
        #embed.set_thumbnail(url=TTR_ICON)
    else:
        embed = Embed(color=color if color else Color.green(), **kwargs)
        embed.add_field(name=title, value=description)
        #embed.set_thumbnail(url=TTR_ICON)

    return embed