import requests
import logging
import socket
import re

from .module import *
from discord import Embed, Color
from utils import Config, get_version
ua_header = Config.get_setting('ua_header', get_version())

# --------------------------------------------- Servers ----------------------------------------------

class ReleaseModule(Module):
    ROUTE = 'https://www.toontownrewritten.com/api/releasenotes'

    def __init__(self, client):
        Module.__init__(self, client)

        self.release_data = []
        self.latest_release_id = None

        self.release_announcer = self.create_announcers(NewReleaseAnnouncer)

    async def collect_data(self):
        try:
            rn = requests.get(self.ROUTE, headers=ua_header)
            json_data = rn.json()
        except (ValueError, requests.ConnectionError):
            return {}

        self.release_data = json_data
        return self.release_data

    async def handle_data(self, data):
        if not data:
            return

        if self.latest_release_id and self.latest_release_id < self.release_data[0]['noteId']:
            ri = self.get_release_info(self.release_data[0]['noteId'])
            if ri:
                self.release_data[0].update(ri)
            await self.release_announcer.announce(ri['slug'], ri['date'], ri['body'])
        self.latest_release_id = self.release_data[0]['noteId']

    def get_release_info(self, note_id):
        try:
            url = self.ROUTE + '/' + str(note_id)
            rn = requests.get(url, headers=ua_header)
            try:
                json_data = rn.json()
            except ValueError:
                return None
            if json_data.get('error', None):
                return None

            result = {
                'slug': json_data['slug'],
                'date': json_data['date'],
                'body': json_data['body']
            }
            return result
        except socket.error:
            return None


class NewReleaseAnnouncer(Announcer):
    CHANNEL_ID = Config.get_module_setting('release', 'announcements')

    async def announce(self, version, date, notes):
        html = re.compile(r'(<b>|<\/b>|<i>|<\/i>|<u>|<\/u>|<br \/>|\r|<font size="\d+">)')
        notes = html.sub('', notes).replace('•', '\t•')
        notes = notes.split('\n\n')

        e = Embed(title='**Patch Notes [{}]**  :joystick:'.format(version), color=Color.from_rgb(26, 153, 216))
        e.set_footer(text='Note that just the patch notes have been released; the game may not reflect these changes yet.')
        for note in notes:
            s = note.split('\n')
            type = s[0].rstrip(':')
            type_notes = '\n'.join(s[1:])
            if len(type_notes) > 1024:  # Discord Embed Field Value Limit
                type_notes = type_notes[:type_notes.rfind('\n', 0, 954)]
                type_notes += '\n\t• ...and more! *Check the Toontown Rewritten website for more info.*'
            e.add_field(name=type, value=type_notes)

        return await self.send(embed=e)

module = ReleaseModule