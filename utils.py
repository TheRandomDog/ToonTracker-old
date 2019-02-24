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

def assert_type(value, *types, otherwise=TypeError):
    if not type(value) in types:
        if otherwise == TypeError:
            raise TypeError("Expected {} when passed value '{}', found {} instead".format(
                ", ".join([str(t) for t in types]), value, type(value))
            )
        else:
            return otherwise
    return value

def assert_class(value, *classes, otherwise=TypeError):
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

    def create_section(self, module, section_name, arguments):
        return super().create_table(module.__class__.__name__ + '_' + section_name, arguments)

    def get_section(self, module, section_name):
        for table in self.tables:
            if table.name == module.__class__.__name__ + '_' + section_name:
                return table
database = DBM()

# CONFIG

class Config:
    @staticmethod
    def open_file(mode):
        try:
            file = open(os.path.join(__location__, 'config.json'), mode)
        except FileNotFoundError:
            created_file = open(os.path.join(__location__, 'config.json'), 'w+')
            created_file.write('{}')
            created_file.close()
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
    def get_setting(cls, setting, otherwise=None):
        try:
            file = cls.open_file('rb')
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
    def get_module_setting(cls, module, setting, otherwise=None):
        pss = cls.get_setting(module)
        if not pss or pss.get(setting, None) == None:
            return otherwise
        return pss[setting]

    @classmethod
    def get_user_ranks(cls):
        user_ranks = {int(user_id): rank for user_id, rank in cls.get_setting('user_ranks').items()}
        return user_ranks or {}

    @classmethod
    def get_rank_of_user(cls, user):
        return cls.get_user_ranks().get(user, 0)

    @classmethod
    def get_users_with_rank(cls, rank):
        users = []
        for u, r in cls.get_user_ranks().items():
            if r >= rank:
                users.append(u)
        return users

    # Convenience method that gets top rank between
    # both the individual user and their roles.
    # This takes a Member object, unlike the other Config methods.
    @classmethod
    def get_rank_of_member(cls, member):
        if member.__class__ == Member:
            return max([cls.get_rank_of_user(member.id)] + [cls.get_rank_of_role(role.id) for role in member.roles])
        elif member.__class__ == User:
            return cls.get_rank_of_user(member.id)
        else:
            raise TypeError('"member" argument should be discord.Member or discord.User')

    @classmethod
    def get_role_ranks(cls):
        role_ranks = {int(role_id): rank for role_id, rank in cls.get_setting('role_ranks').items()}
        return role_ranks or {}

    @classmethod
    def get_rank_of_role(cls, role):
        return cls.get_role_ranks().get(role, 0)

    @classmethod
    def get_roles_with_rank(cls, rank):
        roles = []
        for l, r in cls.get_role_ranks().items():
            if r >= rank:
                roles.append(l)
        return roles

    @classmethod
    def set_setting(cls, setting, value):
        try:
            file = cls.open_file('r+b')
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
    def set_module_setting(cls, module, setting, value):
        settings = cls.get_setting(module)
        if settings == None:
            settings = {}
        settings[setting] = value
        cls.set_setting(module, settings)

    @classmethod
    def set_user_rank(cls, user, rank):
        user_ranks = cls.get_user_ranks()
        user_ranks[user] = rank
        cls.set_setting('user_ranks', user_ranks)

    @classmethod
    def set_role_rank(cls, role, rank):
        role_ranks = cls.get_role_ranks()
        role_ranks[role] = rank
        cls.set_setting('role_ranks', user_ranks)


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
def get_short_time_length(time):
    match = SHORT_TIME.match(time)
    if not match:
        raise ValueError('time must be formatted as number + letter (e.g. 15s, 2y, 1w, 7d, 24h)')
    return LENGTHS[match.group('char')] * int(match.group('num'))
def get_short_time_unit(time):
    match = SHORT_TIME.match(time)
    if not match:
        raise ValueError('time must be formatted as number + letter (e.g. 15s, 2y, 1w, 7d, 24h)')
    return FULL[match.group('char')]
def get_long_time(time):
    match = SHORT_TIME.match(time)
    if not match:
        raise ValueError('time must be formatted as number + letter (e.g. 15s, 2y, 1w, 7d, 24h)')
    return '{} {}'.format(match.group('num'), FULL[match.group('char')])

def get_time_from_seconds(seconds, *, one_unit_limit=False, short=False):
    if int(seconds) <= 60:
        if int(seconds) == 60:
            return '1 minute' if not short else '1m'
        else:
            return '{} seconds'.format(int(seconds)) if not short else '{}s'.format(int(seconds))
    elif int(seconds / 60) <= 60:
        if int(seconds / 60) == 1:
            return '1 minute' if not short else '1m'
        else:
            return '{} minutes'.format(int(seconds / 60)) if not short else '{}m'.format(int(seconds / 60))
    else:
        h = 0
        m = int(seconds / 60)
        while m > 60:
            h += 1
            m -= 60
        if not short:
            hs = 'hour' if h == 1 else 'hours'
            ms = 'minute' if m == 1 else 'minutes'
            if not one_unit_limit:
                return '{} {} and {} {}'.format(str(h), hs, str(m), ms)
            else:
                return '{} {}'.format(str(h), hs)
        else:
            return '{}h{}m'.format(h, m)

def get_attribute_from_match(iterable, match):
    for k, v in iterable.items():
        if match in k:
            return v

def get_version():
    return __version__

def get_progress_bar(progress, out_of):
    p = int((progress/out_of) * 10)
    progress = '[{}{}]'.format('■' * p, ('  '*(10-p))+(' '*ceil((10-p)/2)))
    return progress

def make_list_from_string(string):
    return string.split(',') if string else []

def make_count_of_string(string):
    return string.count(',') + 1 if string else 0
