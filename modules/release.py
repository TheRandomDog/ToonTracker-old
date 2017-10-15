import requests
import logging
import socket
import re

from .module import *
from extra.server import *
from discord import Embed, Color
from utils import Config, getVersion
uaHeader = Config.getSetting('ua_header', getVersion())

# --------------------------------------------- Servers ----------------------------------------------

class ReleaseModule(Module):
    ROUTE = 'https://www.toontownrewritten.com/api/releasenotes'
    CHANNEL_ID = Config.getModuleSetting('release', 'announcements')

    def __init__(self, client):
        Module.__init__(self, client)

        self.releaseData = []
        self.latestReleaseID = None

    def collectData(self):
        try:
            rn = requests.get(self.ROUTE, headers=uaHeader)
            jsonData = rn.json()
        except (ValueError, requests.ConnectionError):
            return {}

        self.releaseData = jsonData
        return self.releaseData

    def handleData(self, data):
        if not data:
            return

        if self.latestReleaseID and self.latestReleaseID < self.releaseData[0]['noteId']:
            ri = self.getReleaseInfo(self.releaseData[0]['noteId'])
            if ri:
                self.releaseData[0].update(ri)
            self.announce(NewReleaseAnnouncement, ri['slug'], ri['date'], ri['body'])
        self.latestReleaseID = self.releaseData[0]['noteId']

    def getReleaseInfo(self, noteId):
        try:
            url = self.ROUTE + '/' + str(noteId)
            rn = requests.get(url, headers=uaHeader)
            try:
                jsonData = rn.json()
            except ValueError:
                return None
            if jsonData.get('error', None):
                return None

            result = {
                'slug': jsonData['slug'],
                'date': jsonData['date'],
                'body': jsonData['body']
            }
            return result
        except socket.error:
            return None


class NewReleaseAnnouncement(Announcer):
    def announce(module, version, date, notes):
        html = re.compile(r'(<b>|<\/b>|<i>|<\/i>|<u>|<\/u>|<br \/>|\r|<font size="\d+">)')
        notes = html.sub('', notes).replace('•', '\t•')
        notes = notes.split('\n\n')

        content = []
        content.append('**Patch Notes [{}] :joystick:**\n*Note that just the patch notes have been released, and the game may not reflect these changes yet.*'.format(version))
        for note in notes:
            s = note.split('\n')
            type = s[0].rstrip(':')
            if type.startswith('Feature'):
                color = Color.green()
            elif type.startswith('Mainten'):
                color = Color.purple()
            elif type.startswith('Bug'):
                color = Color.red()
            elif type.startswith('Tweak'):
                color = Color.blue()
            else:
                color = Color.light_grey()

            e = Embed(color=color).add_field(name=type, value='\n'.join(s[1:]))
            content.append(e)

        return content

module = ReleaseModule