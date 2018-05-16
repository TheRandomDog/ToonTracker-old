import os
import sys
import time
import asyncio
import aiohttp
import requests
from inspect import isclass
from discord import Color, Embed
from extra.commands import Command
from traceback import format_exc
from utils import Config, assertType, getVersion
uaHeader = Config.getSetting('ua_header', getVersion())

class Module:
    def __init__(self, client):
        self.client = client

        moduleName = os.path.basename(sys.modules[self.__module__].__file__).replace('.py', '')
        self.runWithoutRestoredSession = assertType(Config.getModuleSetting(moduleName, 'run_wo_restored_session'), bool, otherwise=False)
        self.restartOnException = assertType(Config.getModuleSetting(moduleName, 'restart_on_exception'), bool, otherwise=True)
        self.cooldownInterval = assertType(Config.getModuleSetting(moduleName, 'cooldown_interval'), int, otherwise=60)
        self.restartLimit = assertType(Config.getModuleSetting(moduleName, 'restart_limit'), int, otherwise=3)
        self.restartLimitResetInterval = assertType(
            Config.getModuleSetting(moduleName, 'restart_limit_reset_interval'), int, otherwise=1800  # 30 minutes
        )  
        self.publicModule = assertType(Config.getModuleSetting(moduleName, 'public_module'), bool, otherwise=True)
        self.isFirstLoop = True
        self.runningLoop = None

        self.commands = [attr for attr in self.__class__.__dict__.values() if isclass(attr) and issubclass(attr, Command)]

        self.restarts = 0
        self.restartTime = 0

    async def collectData(self):
        pass

    async def handleData(self, data):
        pass

    async def loopIteration(self):
        pass

    async def _loop(self):
        try:
            while True:
                data = await self.collectData()
                await self.handleData(data)
                await self.loopIteration()

                self.isFirstLoop = False
                await asyncio.sleep(self.cooldownInterval)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            await self.handleError()

    def startTracking(self):
        if self.runningLoop:
            return
        self.runningLoop = self.client.loop.create_task(self._loop())

    def stopTracking(self):
        if self.runningLoop:
            self.runningLoop.cancel()

    async def _handleMsg(self, message):
        for command in self.commands:
            if message.content and message.content.split(' ')[0] == self.client.commandPrefix + command.NAME and \
                    (Config.getRankOfUser(message.author.id) >= command.RANK or any([Config.getRankOfRole(role.id) >= command.RANK for role in message.author.roles])):
                response = await command.execute(self.client, self, message, *message.content.split(' ')[1:])
                return response

        try:
            response = await self.on_message(message)
            if response:
                return response
        except Exception as e:
            return '```\n{}```'.format(format_exc())

    async def on_message(self, message):
        pass

    def create_announcers(self, *announcers):
        instanced_announcers = []
        for announcer in announcers:
            channel = self.client.get_channel(announcer.CHANNEL_ID)
            instanced_announcers.append(announcer(self, channel))
        return instanced_announcers[0] if len(announcers) is 1 else instanced_announcers

    def create_permanent_messages(self, *perma_messages):
        instanced_perma_messages = []
        for perma_message in perma_messages:
            channel = self.client.get_channel(perma_message.CHANNEL_ID)
            instanced_perma_messages.append(perma_message(self, channel))
        return instanced_perma_messages[0] if len(perma_messages) is 1 else instanced_perma_messages

    async def handleError(self):
        e = format_exc()

        if self.restartLimitResetInterval and self.restartTime + self.restartLimitResetInterval < time.time():
            self.restarts = 0

        if self.restarts > self.restartLimit:
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

        try:
            await self.client.send_message(self.client.botspam, info + log)
        except Exception as e:
            pass
        print(info + log)
        self.stopTracking()

        if self.restarts > self.restartLimit:
            return

        if self.restartOnException:
            r = int(self.restarts) + 1  # int() creates a separate int detached from the about-to-be-updated attribute
            time.sleep(5)
            self.__init__(self.client)  # "Restarts" the module, cleans out pending messages, sets first loop, etc.
            self.restarts = r
            self.restartTime = time.time()
            self.startTracking()

    # Creates a Discord Embed.
    # This is preferred over simply creating a new instance of discord.Embed because there 
    # are some properties that require method input due to containing multiple sub-values.
    def createDiscordEmbed(self, **kwargs):
        title = kwargs.get('title', None)
        subtitle = kwargs.get('subtitle', Embed.Empty)
        info = kwargs.get('info', Embed.Empty)
        titleUrl = kwargs.get('titleUrl', Embed.Empty)
        subtitleUrl = kwargs.get('subtitleUrl', Embed.Empty)
        image = kwargs.get('image', Embed.Empty)
        icon = kwargs.get('icon', Embed.Empty)
        thumbnail = kwargs.get('thumbnail', Embed.Empty)
        fields = kwargs.get('fields', [])
        footer = kwargs.get('footer', Embed.Empty)
        footerIcon = kwargs.get('footerIcon', Embed.Empty)
        color = kwargs.get('color', Embed.Empty)

        embed = Embed(title=subtitle, description=info, url=subtitleUrl, color=color)
        embed.set_footer(text=footer, icon_url=footerIcon)
        if title:
            embed.set_author(name=title, url=titleUrl, icon_url=icon)
        if thumbnail != Embed.Empty:
            embed.set_thumbnail(url=thumbnail)
        if image != Embed.Empty:
            embed.set_image(url=image)
        for field in fields:
            embed.add_field(**field)

        return embed

class Announcer:
    CHANNEL_ID = None

    def __init__(self, module, channel):
        self.module = module
        self.channel = channel

    async def announce(self, *args, **kwargs):
        pass

    async def send(self, content):
        try:
            if content.__class__ == Embed:
                await self.channel.send(content=None, embed=content)
            else:
                await self.channel.send(content=content)
        except Exception as e:
            e = format_exc()
            info = '{} tried to send an announcement to channel ID {}, but an exception was raised.\nAnnouncer: {}\n'.format(
                self.module.__class__.__name__, self.channel.id, self.__class__.__name__)
            log = '```{}```'.format(e)

            print(info + log)
            info = info.replace('channel ID {}'.format(self.channel.id), self.channel.name)
            if len(info + log) > 2000:
                r = requests.post('https://hastebin.com/documents', data=e)
                try:
                    json = r.json()
                    key = json['key']
                    log = 'https://hastebin.com/raw/' + key
                except (KeyError, ValueError):
                    log = '*Unable to post long log to Discord or Hastebin. The log can be found in the console.*'

            await self.module.client.send_message(self.module.client.botspam, info + log)

class PermaMessage:
    CHANNEL_ID = None
    TITLE = None

    def __init__(self, module, channel):
        self.module = module
        self.channel = channel
        self.message = None

    async def update(self, *args, **kwargs):
        pass

    async def send(self, content):
        # Kind of a dirty trick to look for a message here, but create_perma_messages is usually called in __init__s,
        # so it's difficult to call a coroutine looking for message history that would require an async def.
        if not self.message:
            async for message in self.channel.history(limit=10):
                for embed in message.embeds:
                    # Find the message that has a matching title / author to replace with the new message.
                    if (embed.fields and embed.fields[0].name == self.TITLE) or embed.author.name == self.TITLE or embed.title == self.TITLE:
                        self.message = message

        messageEdited = False
        try:
            send = self.message.edit if self.message else self.channel.send
            if content.__class__ == Embed:
                await send(content=None, embed=content)
            else:
                await send(content=content)
        except discord.errors.DiscordException as e:
            msg = '**{}** tried to update the **{}** perma-message, but Discord raised an exception: {}'.format(
                self.module.__class__.__name__, self.__class__.__name__, str(e))
            print(msg)
            await self.module.client.send_message(self.module.client.botspam, msg)
        except (asyncio.TimeoutError, aiohttp.client_exceptions.ClientOSError):
            msg = '**{}** tried to update the **{}** perma-message, but the async call errored / timed out.'.format(module.__class__.__name__, update[1])
            print(msg)
            self.module.client.send_message(self.module.client.botspam, msg)