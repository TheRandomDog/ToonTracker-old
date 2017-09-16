import time
import socket
import logging
import requests
import regex as re

from .module import *
from extra.server import *
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

        self.gameserverAddress = 'gameserver-us-east-1-prod.toontownrewritten.com'
        self.lastUpdated = time.time()
        self.account = None
        self.game = None
        self.open = None
        self.banner = False

        self.permaMsgs = [StatusPermaMsg]

    def checkAccountServer(self):
        payloadState = self.PAYLOAD_CREDENTIALS
        while True:
            url = 'https://www.toontownrewritten.com/api/login?format=json'
            if payloadState == self.PAYLOAD_QUEUE:
                payload = {'queueToken': qt}
            else:
                payload = Config.getModuleSetting('status', 'ttr_credentials')
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            headers.update(uaHeader)

            #self.logger.debug('POSTing to {} ({})'.format(url, {'data': payload, 'headers': headers}))
            r = requests.post(url, data=payload, headers=headers)
            jsonData = None
            try:
                jsonData = r.json()
                success = jsonData['success']
            except JSONDecodeError:
                success = 'false'

            #self.logger.debug('jsonData == {}'.format(jsonData))
            if success == 'true':
                if not self.account:
                    if self.account != None:
                        pass
                        #self.announce(AccountStatusAnnouncement, self, True, deleteIn=0)
                    self.account = True
                self.gameserverAddress = jsonData['gameserver']
                break
            elif success == 'delayed':
                payloadState = self.PAYLOAD_QUEUE
                pos = jsonData['position']
                eta = jsonData['eta']
                qt = jsonData['queueToken']
                if int(eta) < 60:
                    time.sleep(max(5, int(eta)))
                else:
                    if self.account:
                        pass
                    self.account = False
                    break
            elif success == 'false':
                if self.account:
                    pass
                    #self.announce(AccountStatusAnnouncement, self, False, deleteIn=0)
                self.account = False
                break

    def checkGameServer(self):
        address = self.gameserverAddress
        try:
            s = socket.socket()
            try:
                address, port = address.split(':')[0], int(address.split(':')[1])
            except (IndexError, ValueError):
                port = 7198
            #self.logger.debug('Attempting to connect to {}:{}'.format(address, port))
            s.connect((address, port))
            if not self.game:
                if self.game != None:
                    pass
                    #self.announce(GameStatusAnnouncement, self, True, deleteIn=0)
                self.game = True
        except socket.error as e:
            if ('[Errno 10060]' in str(e) or '[Errno 10061]' in str(e)):
                if self.game:
                    pass
                    #self.announce(GameStatusAnnouncement, self, False, deleteIn=0)
                self.game = False
        finally:
            s.close()

    def checkStatus(self):
        url = 'https://www.toontownrewritten.com/api/status'
        #self.logger.debug('Checking status from toontownrewritten.com...')
        r = requests.get(url, headers=uaHeader)
        try:
            jsonData = r.json()
        except JSONDecodeError:
            jsonData = {'open': True}
        #self.logger.debug('response: {}'.format(jsonData))
        open = jsonData['open']
        try:
            banner = jsonData['banner']
        except KeyError:
            banner = False
        if self.open == None:
            self.open = open
        elif open != self.open:
            #self.announce(LoginGateAnnouncement, self, True if open else False, deleteIn=0)
            self.open = open
        if banner != self.banner:
            if banner and not self.banner == False:
                pass
                #self.announce(BannerAnnouncement, self, banner, deleteIn=0)
            self.banner = banner

    def loopIteration(self):
        self.checkAccountServer()
        self.checkGameServer()
        self.checkStatus()
        self.lastUpdated = time.time()
        self.updatePermaMsg(StatusPermaMsg)


class StatusPermaMsg(PermaMsg):
    TITLE = 'Server Status'

    def update(module):
        title = 'Server Status'

        if module.isFirstLoop:
            msg = module.createDiscordEmbed(title=title, description='Collecting the latest information...', color=Color.light_grey())
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

        return module.createDiscordEmbed(title=title, description='\n\n'.join(statuses), color=color)

# ---------------------------------------------- Module ----------------------------------------------

module = StatusModule