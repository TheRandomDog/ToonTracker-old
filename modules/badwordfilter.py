from modules.module import Module
from utils import Config
import re

class BadWordFilter(Module):
    def __init__(self, client):
        Module.__init__(self, client)

        self.words = Config.getModuleSetting('badwordfilter', 'words')
        self.pluralExceptions = Config.getModuleSetting('badwordfilter', 'plural_exceptions')
        self.links = Config.getModuleSetting('badwordfilter', 'links')
        self.exceptions = Config.getModuleSetting('badwordfilter', 'exceptions')
        self.botspam = Config.getModuleSetting('badwordfilter', 'announcements')

    async def handleMsg(self, message):
        if message.channel.id in self.exceptions or message.author.id in self.exceptions:
            return

        text = message.content

        #for link in self.links:
        #    if link.lower() in text.lower():
        #        await self.client.ban(message.author)
        #        botspam = Config.getModuleSetting('badwordfilter', 'announcements')
        #        if botspam:
        #            await self.client.send_message(botspam, "Banned {} for linking to `{}`".format(message.author.name, link))

        for word in text.split(' '):
            word = re.sub(r'\W+', '', word)
            if word.lower() in self.words or (word.lower() + 's' in self.words and word.lower() not in self.pluralExceptions):
                await self.client.delete_message(message)
                if self.botspam:
                    await self.client.send_message(self.botspam, "Removed message from {} in {}: {}".format(message.author.mention, message.channel.mention, message.content.replace(word, '**' + word + '**')))
                    return
            for badword in self.words:
                if ' ' in badword and (badword == text.lower() or badword + 's' == text.lower() or (text.lower().startswith(badword) and badword + ' ' in text.lower()) or (text.lower().endswith(badword) and ' ' + badword in text.lower()) or ' ' + badword + ' ' in text.lower()):
                    await self.client.delete_message(message)
                    if self.botspam:
                        await self.client.send_message(self.botspam, "Removed message from {} in {}: {}".format(message.author.mention, message.channel.mention, message.content.replace(badword, '**' + badword + '**')))
                        return
            whole = text.replace(' ', '')
            if whole.lower() in self.words or (whole.lower() + 's' in self.words and whole.lower() not in self.pluralExceptions):
                await self.client.delete_message(message)
                if self.botspam:
                    await self.client.send_message(self.botspam, "Removed message from {} in {}: {}".format(message.author.mention, message.channel.mention, '**' + message.content + '**'))
                    return



module = BadWordFilter