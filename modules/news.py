import requests
import time
import re

from .module import *
from discord import Embed
from utils import Config, get_version
ua_header = Config.get_setting('ua_header', get_version())

# --------------------------------------------- Servers ----------------------------------------------

class NewsModule(Module):
    ROUTE = 'https://www.toontownrewritten.com/api/news'

    def __init__(self, client):
        Module.__init__(self, client)
        self.latest_post_id = None

        self.news_announcer = self.create_announcers(NewPostAnnouncer)

    async def collect_data(self):
        try:
            rn = requests.get(self.ROUTE, headers=ua_header)
            json_data = rn.json()
        except (ValueError, requests.ConnectionError):
            return {}

        return json_data

    async def handle_data(self, data):
        if not data:
            return

        if self.latest_post_id and self.latest_post_id < data['postId']:
            await self.news_announcer.announce(data)
        self.latest_post_id = data['postId']

class NewPostAnnouncer(Announcer):
    CHANNEL_ID = Config.get_module_setting('news', 'announcements')
    
    async def announce(self, data):
        alphanumeric = re.compile('[^A-Za-z0-9-]')

        url = 'https://www.toontownrewritten.com/news/item/' + str(data['postId']) + '/' + alphanumeric.sub('', data['title'].lower().replace(' ', '-'))

        info = "**{}**\nPosted by {} on {}".format(data['title'], data['author'], data['date'])
        image = Embed.Empty
        if data['image']:
            k = data['image'].rfind('?')
            k = len(data['image']) if k == -1 else k
            image = data['image'][:k]
        embed = self.module.create_discord_embed(subtitle="New Blog Post!", subtitle_url=url, info=info, image=image)

        return await self.send(embed)

module = NewsModule
