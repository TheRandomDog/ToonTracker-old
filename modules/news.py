import requests
import time
import re

from .module import *
from extra.server import *
from discord import Embed
from utils import Config, getVersion
uaHeader = Config.getSetting('ua_header', getVersion())

# --------------------------------------------- Servers ----------------------------------------------

class NewsModule(Module):
    ROUTE = 'https://www.toontownrewritten.com/api/news'
    CHANNEL_ID = Config.getModuleSetting('news', 'announcements')

    def __init__(self, client):
        Module.__init__(self, client)
        self.latestPostID = None

        self.announcers = [NewPostAnnouncement]

    def collectData(self):
        try:
            rn = requests.get(self.ROUTE, headers=uaHeader)
            jsonData = rn.json()
        except (ValueError, requests.ConnectionError):
            return {}

        return jsonData

    def handleData(self, data):
        if not data:
            return

        if self.latestPostID and self.latestPostID < data['postId']:
            self.announce(NewPostAnnouncement, data)
        self.latestPostID = data['postId']

class NewPostAnnouncement(Announcer):
    def announce(module, data):
        alphanumeric = re.compile('[^A-Za-z0-9-]')

        url = 'https://www.toontownrewritten.com/news/item/' + str(data['postId']) + '/' + alphanumeric.sub('', data['title'].lower().replace(' ', '-'))

        value = "**{}**\nPosted by {} on {}".format(data['title'], data['author'], data['date'])
        embed = module.createDiscordEmbed("New Blog Post!", "**{}**\nPosted by {} on {}".format(data['title'], data['author'], data['date']), url=url)
        if data['image']:
            k = data['image'].rfind('?')
            k = len(data['image']) if k == -1 else k
            embed.set_image(url=data['image'][:k])

        return embed

module = NewsModule
