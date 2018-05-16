import requests
import time
import re

from .module import *
from discord import Embed
from utils import Config, getVersion
uaHeader = Config.getSetting('ua_header', getVersion())

# --------------------------------------------- Servers ----------------------------------------------

class NewsModule(Module):
    ROUTE = 'https://www.toontownrewritten.com/api/news'

    def __init__(self, client):
        Module.__init__(self, client)
        self.latestPostID = None

        self.newsAnnouncer = self.create_announcers(NewPostAnnouncer)

    async def collectData(self):
        try:
            rn = requests.get(self.ROUTE, headers=uaHeader)
            jsonData = rn.json()
        except (ValueError, requests.ConnectionError):
            return {}

        return jsonData

    async def handleData(self, data):
        if not data:
            return

        if self.latestPostID and self.latestPostID < data['postId']:
            await self.newsAnnouncer.announce(data)
        self.latestPostID = data['postId']

class NewPostAnnouncer(Announcer):
    CHANNEL_ID = Config.getModuleSetting('news', 'announcements')
    
    async def announce(self, data):
        alphanumeric = re.compile('[^A-Za-z0-9-]')

        url = 'https://www.toontownrewritten.com/news/item/' + str(data['postId']) + '/' + alphanumeric.sub('', data['title'].lower().replace(' ', '-'))

        info = "**{}**\nPosted by {} on {}".format(data['title'], data['author'], data['date'])
        image = Embed.Empty
        if data['image']:
            k = data['image'].rfind('?')
            k = len(data['image']) if k == -1 else k
            image = data['image'][:k]
        embed = self.module.createDiscordEmbed(subtitle="New Blog Post!", subtitleUrl=url, info=info, image=image)

        return await self.send(embed)

module = NewsModule
