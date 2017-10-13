import os
import sys
import time
import requests
import threading
from inspect import isclass
from functools import wraps
from traceback import format_exception, format_exc
from platform import *
from utils import Config, assertTypeOrOtherwise, getVersion
from extra.toontown import TTR_ICON
from discord import Color, Embed
import types
uaHeader = Config.getSetting('ua_header', getVersion())

class Module:
    def __init__(self, client):
        self.client = client

        moduleName = os.path.basename(sys.modules[self.__module__].__file__).replace('.py', '')
        self.restartOnException = assertTypeOrOtherwise(Config.getModuleSetting(moduleName, 'restart_on_exception'), bool, otherwise=True)
        self.cooldownInterval = assertTypeOrOtherwise(Config.getModuleSetting(moduleName, 'cooldown_interval'), int, otherwise=60)
        self.isFirstLoop = True
        self.isTracking = False

        self.commands = []
        self.handlers = []
        self.announcers = []
        self.permaMsgs = []
        self.pendingAnnouncements = []
        self.pendingUpdates = []

        self.restarts = 0

    # --------------------------------------------- TRACKING ---------------------------------------------

    def collectData(self):
        pass

    def handleData(self, data):
        pass

    def loopIteration(self):
        pass

    def __sleepAndTestForBreak(self, period):
        self.isFirstLoop = False
        for _ in range(period):
            if not self.isTracking:
                return True
            time.sleep(1)

    def _loop(self):
        try:
            while self.isTracking:
                data = self.collectData()
                self.handleData(data)
                self.loopIteration()
                
                self.__sleepAndTestForBreak(self.cooldownInterval)

        except Exception as e:
            self.handleError()


    def startTracking(self):
        if self.isTracking:
            return

        self.isTracking = True
        threading.Thread(target=self._loop, name='{}-Thread'.format(self.__class__.__name__)).start()

    def stopTracking(self):
        self.isTracking = False

    async def _handleMsg(self, message):
        for command in self.commands:
            if message.content.startswith(self.client.commandPrefix + command.NAME) and \
                    (Config.getRankOfUser(message.author.id) >= command.RANK or any([Config.getRankOfRole(role.id) >= command.RANK for role in message.author.roles])):
                response = await command.execute(self.client, self, message, *message.content.split(' ')[1:])
                return response

        try:
            response = await self.handleMsg(message)
            if response:
                return response
        except Exception as e:
            return '```\n{}```'.format(format_exc())

    async def handleMsg(self, message):
        pass

    def announce(self, announcer, *args, **kwargs):
        try:
            assert issubclass(announcer, Announcer)
            response = announcer.announce(self, *args)
            kwargs.update({'module': self})
            if response:
                self.pendingAnnouncements.append((announcer.CHANNEL_ID or self.CHANNEL_ID, response, kwargs))
        except Exception as e:
            self.handleError()

    def updatePermaMsg(self, pm, *args, **kwargs):
        try:
            assert issubclass(pm, PermaMsg)
            response = pm.update(self, *args)
            kwargs.update({'module': self})
            if response:
                self.pendingUpdates.append((pm.CHANNEL_ID or self.CHANNEL_ID, pm.TITLE, response, kwargs))
        except Exception as e:
            self.handleError()

    def handleError(self):
        e = format_exc()

        if self.restarts > 3:
            n = 'The module has encountered a high number of exceptions. It will be disabled until the issue can be resolved.'
            print('{} was disabled for encountering a high number of exceptions.\n\n{}'.format(self.__class__.__name__, e))
        else:
            n = 'The module will restart momentarily.'
            print('{} was restarted after encountering an exception.\n\n{}'.format(self.__class__.__name__, e))

        info = '**An unprompted exception occured in _{}_.**\n{}\n'.format(self.__class__.__name__, n)
        log = '```\n{}```'.format(e)
        if len(info + log) > 2000:
            r = requests.post('https://hastebin.com/documents', data=e)
            try:
                json = r.json()
                key = json['key']
                log = 'https://hastebin.com/raw/' + key
            except (KeyError, ValueError):
                log = '*Unable to post long log to Discord or Hastebin. The log can be found in the console.*'

        self.pendingAnnouncements.append(
            (
                Config.getSetting('botspam'), 
                info + log,
                {'module': self}
            )
        )

        if self.restarts > 3:
            return

        if self.RESTART_ON_EXCEPTION:
            r = self.restarts + 1
            self.stopTracking()
            time.sleep(5)
            self.__init__(self.client)  # "Restarts" the module, cleans out pending messages, sets first loop, etc.
            self.restarts = r
            self.startTracking()

    def createDiscordEmbed(self, title, description=Embed.Empty, *, multipleFields=False, color=None, url=None, **kwargs):
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

class Announcer:
    CHANNEL_ID = None

    def announce(module, *args, **kwargs):
        pass

class PermaMsg:
    CHANNEL_ID = None

    def update(module):
        pass