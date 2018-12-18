import requests
import time
import re

from .module import *
from discord import Embed
from utils import Config, get_version, assert_type
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
    NOTIFICATION_ROLES = assert_type(Config.get_module_setting('news', 'notification_roles'), list, otherwise=[])
    
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

        roles = []
        for role_id in self.NOTIFICATION_ROLES:
            role = discord.utils.get(self.module.client.focused_guild.roles, id=role_id)
            if role:
                roles.append(role)

        if roles:
            ping_string = ' '.join([r.mention for r in roles])
            return await self.send(content=ping_string, embed=embed)
        else:
            return await self.send(embed=embed)

module = NewsModule
