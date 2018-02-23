import os
import re
import json
import logging
from __init__ import __version__
from discord import Embed, Color, Member, User
from datetime import datetime
from math import ceil

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

# ASSERTIONS

def assertType(value, *types, otherwise=TypeError):
    if not type(value) in types:
        if otherwise == TypeError:
            raise TypeError("Expected {} when passed value '{}', found {} instead".format(
                ", ".join([str(t) for t in types]), value, type(value))
            )
        else:
            return otherwise
    return value

def assertClass(value, *classes, otherwise=TypeError):
    if not value.__class__ in classes:
        if otherwise == TypeError:
            raise TypeError("Expected {} when passed value '{}', found {} instead".format(
                ", ".join([str(c) for c in classes]), value, value.__class__)
            )
        else:
            return otherwise
    return value

# DATABASE

from db import DatabaseManager
class DBM(DatabaseManager):
    def __init__(self):
        super().__init__('toontracker.db')

    def createSection(self, module, sectionName, arguments):
        return super().createTable(module.__class__.__name__ + '-' + sectionName, arguments)

    def getSection(self, module, sectionName):
        for table in self.tables:
            if table.name == module.__class__.__name__ + '-' + sectionName:
                return table

# CONFIG

class Config:
    @staticmethod
    def openFile(mode):
        try:
            file = open(os.path.join(__location__, 'config.json'), mode)
        except FileNotFoundError:
            createdFile = open(os.path.join(__location__, 'config.json'), 'w+')
            createdFile.write('{}')
            createdFile.close()
            file = open(os.path.join(__location__, 'config.json'), mode)
            print('config.json was not found, so the file was created.')
        content = json.loads(file.read().decode('utf-8'))
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
            file = cls.openFile('rb')
            content = json.loads(file.read().decode('utf-8'))
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

    # Convenience method that gets top rank between
    # both the individual user and their roles.
    # This takes a Member object, unlike the other Config methods.
    @classmethod
    def getRankOfMember(cls, member):
        if member.__class__ == Member:
            return max([cls.getRankOfUser(member.id)] + [cls.getRankOfRole(role.id) for role in member.roles])
        elif member.__class__ == User:
            return cls.getRankOfUser(member.id)
        else:
            raise TypeError('"member" argument should be discord.Member or discord.User')

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
            file = cls.openFile('r+b')
            content = json.loads(file.read().decode('utf-8'))
            content[setting] = value
            file.seek(0, 0)
            file.write(json.dumps(content, indent=4, sort_keys=True).encode('utf-8'))
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
        try:
            file = open(os.path.join(__location__, 'users.json'), mode)
        except FileNotFoundError:
            createdFile = open(os.path.join(__location__, 'users.json'), 'w+')
            createdFile.write('{}')
            createdFile.close()
            file = open(os.path.join(__location__, 'users.json'), mode)
            print('users.json was not found, so the file was created.')
        return file

    @classmethod
    def getUsers(cls):
        try:
            file = cls.openFile('rb')
            content = {int(userID): data for userID, data in json.loads(file.read().decode('utf-8')).items()}
            return content
        except json.JSONDecodeError:
            print('[!!!] Tried to read user data, but {} did not have valid JSON content.'.format(
                os.path.basename(file.name))
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

        embed = Embed(title='{} Details'.format('Bot' if member.bot else 'User'), color=member.top_role.color if isinstance(member, Member) else Color.default())
        embed.set_author(name=str(member), icon_url=member.avatar_url)
        embed.add_field(name='Account Creation Date', value=str(member.created_at.date()), inline=True)
        embed.add_field(name='Join Date', value=str(member.joined_at.date()) if isinstance(member, Member) else 'Not on the server.', inline=True)
        embed.add_field(name='Level | XP', value='N/A' if member.bot else '{} | {}'.format(user['level'], user['xp']), inline=True)
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
            return channelHistory.get(str(channelID), {'messages': 0, 'attachments': 0, 'embeds': 0})
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
            file = cls.openFile('r+b')
            content = json.loads(file.read().decode('utf-8'))
            content[str(userID)] = value
            file.seek(0, 0)
            file.write(json.dumps(content, indent=4, sort_keys=True).encode('utf-8'))
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
    def setUserChannelHistory(cls, userID, channelID, channelHistory):
        userJSON = cls.getUserJSON(userID)
        userJSON['channel_history'][str(channelID)] = channelHistory
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
    if int(seconds) <= 60:
        if int(seconds) == 60:
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

def getProgressBar(progress, outOf):
    p = int((progress/outOf) * 10)
    # Pray this never has to be debugged.
    progress = '[{}{}]'.format('■' * p, ('  '*(10-p))+(' '*ceil((10-p)/2)))
    return progress