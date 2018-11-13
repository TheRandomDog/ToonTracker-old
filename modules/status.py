import time
import socket
import logging
import requests

from .module import *
from json import JSONDecodeError
from discord import Embed, Color
from utils import Config, get_version
ua_header = Config.get_setting('ua_header', get_version())

class StatusModule(Module):
    GOOD = ':white_check_mark: The **{}** looks good!'
    UNREACHABLE = ':exclamation: Can\'t reach the **{}**.'
    CLOSED = ':exclamation: The game is closed.'
    BANNER = ':speech_balloon: {}'

    PAYLOAD_CREDENTIALS = 0
    PAYLOAD_QUEUE = 1

    def __init__(self, client):
        Module.__init__(self, client)

        self.gameserver_address = 'gameserver.toontownrewritten.com'
        self.last_updated = time.time()
        self.account = None
        self.game = None
        self.open = None
        self.banner = False

        self.status_message = self.create_permanent_messages(StatusMessage)

    def check_account_server(self):
        url = 'https://www.toontownrewritten.com/api/status'
        try:
            r = requests.get(url, headers=ua_header)
            json_data = r.json()
        except (JSONDecodeError, requests.ConnectionError):
            self.account = False
            self.open = True
            return
        self.account = True
        self.open = json_data['open']
        self.banner = json_data.get('banner', False)

    def check_game_server(self):
        address = self.gameserver_address
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

    async def loop_iteration(self):
        self.check_account_server()
        self.check_game_server()
        self.last_updated = time.time()
        await self.status_message.update()


class StatusMessage(PermaMessage):
    TITLE = 'Server Status'
    CHANNEL_ID = Config.get_module_setting('status', 'perma')

    async def update(self, *args, **kwargs):
        if self.module.is_first_loop:
            msg = self.module.create_discord_embed(subtitle=self.TITLE, info='Collecting the latest information...', color=Color.light_grey())
            return await self.send(msg)

        game_msg = (self.module.GOOD if self.module.game else self.module.UNREACHABLE).format('game server')
        if not self.module.open:
            acc_msg = self.module.CLOSED
            statuses = [acc_msg]
        else:
            acc_msg = (self.module.GOOD if self.module.account else self.module.UNREACHABLE).format('account server')
            statuses = [game_msg, acc_msg]
        ban_msg = self.module.BANNER.format(self.module.banner) if self.module.banner else None
        if ban_msg:
            statuses.append(ban_msg)

        color = Color.green()
        color = Color.blue() if self.module.banner and self.module.account else color
        color = Color.gold() if (not self.module.open and not self.module.banner) or not self.module.account else color
        color = Color.red() if not self.module.game else color

        return await self.send(self.module.create_discord_embed(subtitle=self.TITLE, info='\n\n'.join(statuses), color=color))

# ---------------------------------------------- Module ----------------------------------------------

module = StatusModule