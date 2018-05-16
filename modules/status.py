import time
import socket
import logging
import requests

from .module import *
from json import JSONDecodeError
from discord import Embed, Color
from utils import Config, getVersion
uaHeader = Config.getSetting('ua_header', getVersion())

class StatusModule(Module):
    GOOD = ':white_check_mark: The **{}** looks good!'
    UNREACHABLE = ':exclamation: Can\'t reach the **{}**.'
    CLOSED = ':exclamation: The game is closed.'
    BANNER = ':speech_balloon: {}'

    PAYLOAD_CREDENTIALS = 0
    PAYLOAD_QUEUE = 1

    def __init__(self, client):
        Module.__init__(self, client)

        self.gameserverAddress = '162.243.14.152'
        self.lastUpdated = time.time()
        self.account = None
        self.game = None
        self.open = None
        self.banner = False

        self.statusMessage = self.create_permanent_messages(StatusMessage)

    def checkAccountServer(self):
        url = 'https://www.toontownrewritten.com/api/status'
        try:
            r = requests.get(url, headers=uaHeader)
            jsonData = r.json()
        except (JSONDecodeError, requests.ConnectionError):
            self.account = False
            self.open = True
            return
        self.account = True
        self.open = jsonData['open']
        self.banner = jsonData.get('banner', False)

    def checkGameServer(self):
        address = self.gameserverAddress
        try:
            s = socket.socket()
            try:
                address, port = address.split(':')[0], int(address.split(':')[1])
            except (IndexError, ValueError):
                port = 7198
            s.connect((address, port))
            if not self.game:
                self.game = True
        except socket.error as e:
            if ('[Errno 10060]' in str(e) or '[Errno 10061]' in str(e)):
                self.game = False
        finally:
            s.close()

    async def loopIteration(self):
        self.checkAccountServer()
        self.checkGameServer()
        self.lastUpdated = time.time()
        await self.statusMessage.update()


class StatusMessage(PermaMessage):
    TITLE = 'Server Status'
    CHANNEL_ID = Config.getModuleSetting('status', 'perma')

    async def update(self, *args, **kwargs):
        if self.module.isFirstLoop:
            msg = self.module.createDiscordEmbed(subtitle=self.TITLE, info='Collecting the latest information...', color=Color.light_grey())
            return await self.send(msg)

        gameMsg = (self.module.GOOD if self.module.game else self.module.UNREACHABLE).format('game server')
        if not self.module.open:
            accMsg = self.module.CLOSED
            statuses = [accMsg]
        else:
            accMsg = (self.module.GOOD if self.module.account else self.module.UNREACHABLE).format('account server')
            statuses = [gameMsg, accMsg]
        banMsg = self.module.BANNER.format(self.module.banner) if self.module.banner else None
        if banMsg:
            statuses.append(banMsg)

        color = Color.green()
        color = Color.blue() if self.module.banner and self.module.account else color
        color = Color.gold() if (not self.module.open and not self.module.banner) or not self.module.account else color
        color = Color.red() if not self.module.game else color

        return await self.send(self.module.createDiscordEmbed(subtitle=self.TITLE, info='\n\n'.join(statuses), color=color))

# ---------------------------------------------- Module ----------------------------------------------

module = StatusModule