import os
import json
import logging
from __init__ import __version__
from discord import Embed, Color

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

def assertTypeOrOtherwise(value, *types, otherwise):
    return value if type(value) in types else otherwise

# CONFIG

class Config:
    @staticmethod
    def openFile(mode):
        file = open(os.path.join(__location__, 'config.json'), mode)
        content = json.loads(file.read())
        file.close()
        if assertTypeOrOtherwise(content.get("profile", None), str, None):
            file = open(os.path.join(__location__, '/profiles/' + content['profile']), mode)
        else:
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
        if not pss or not pss.get(setting, None):
            return otherwise
        return pss[setting]

    @classmethod
    def getUserRanks(cls):
        userRanks = cls.getSetting('user_ranks')
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
        roleRanks = cls.getSetting('role_ranks')
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