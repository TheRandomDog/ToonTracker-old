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
    CHANNEL_ID = Config.getModuleSetting('status', 'perma')

    GOOD = ':white_check_mark: The **{}** looks good!'
    UNREACHABLE = ':exclamation: Can\'t reach the **{}**.'
    CLOSED = ':exclamation: The game is closed.'
    BANNER = ':speech_balloon: {}'

    PAYLOAD_CREDENTIALS = 0
    PAYLOAD_QUEUE = 1

    def __init__(self, client):
        Module.__init__(self, client)

        self.gameserverAddress = 'gameserver.toontownrewritten.com'
        self.lastUpdated = time.time()
        self.account = None
        self.game = None
        self.open = None
        self.banner = False

        self.permaMsgs = [StatusPermaMsg]

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

    def loopIteration(self):
        self.checkAccountServer()
        self.checkGameServer()
        self.lastUpdated = time.time()
        self.updatePermaMsg(StatusPermaMsg)


class StatusPermaMsg(PermaMsg):
    TITLE = 'Server Status'

    def update(module):
        title = 'Server Status'

        if module.isFirstLoop:
            msg = module.createDiscordEmbed(subtitle=title, info='Collecting the latest information...', color=Color.light_grey())
            return msg

        gameMsg = (module.GOOD if module.game else module.UNREACHABLE).format('game server')
        if not module.open:
            accMsg = module.CLOSED
            statuses = [accMsg]
        else:
            accMsg = (module.GOOD if module.account else module.UNREACHABLE).format('account server')
            statuses = [gameMsg, accMsg]
        banMsg = module.BANNER.format(module.banner) if module.banner else None
        if banMsg:
            statuses.append(banMsg)

        color = Color.green()
        color = Color.blue() if module.banner and module.account else color
        color = Color.gold() if (not module.open and not module.banner) or not module.account else color
        color = Color.red() if not module.game else color

        return module.createDiscordEmbed(subtitle=title, info='\n\n'.join(statuses), color=color)

# ---------------------------------------------- Module ----------------------------------------------

module = StatusModule