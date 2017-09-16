from modules.module import Module
from utils import Config
import re
import asyncio

class BadImageFilter(Module):
    def __init__(self, client):
        Module.__init__(self, client)

        #self.words = Config.getModuleSetting('badwordfilter', 'words')
        #self.links = Config.getModuleSetting('badwordfilter', 'links')
        #self.exceptions = Config.getModuleSetting('badwordfilter', 'exceptions')

    async def handleMsg(self, message):
        #if message.channel.id in self.exceptions or message.author.id in self.exceptions:
        #    return

        await asyncio.sleep(1)
        #m = await self.client.get_message(message.channel, message.id)
        print(message.embeds)#, m.embeds)
        

        return
        #for link in self.links:
        #    if link.lower() in text.lower():
        #        await self.client.ban(message.author)
        #        botspam = Config.getModuleSetting('badwordfilter', 'announcements')
        #        if botspam:
        #            await self.client.send_message(botspam, "Banned {} for linking to `{}`".format(message.author.name, link))

        for word in text.split(' '):
            word = re.sub(r'\W+', '', word)
            if word.lower() in self.words or (word.lower() + 's' in self.words and word.lower() not in ['as', 'ff']):
                await self.client.delete_message(message)
                botspam = Config.getModuleSetting('badwordfilter', 'announcements')
                if botspam:
                    await self.client.send_message(botspam, "Removed message from {} in {}: {}".format(message.author.mention, message.channel.mention, message.content.replace(word, '**' + word + '**')))
                    return
            for badword in self.words:
                if ' ' in badword and (badword == text.lower() or badword + 's' == text.lower() or (text.lower().startswith(badword) and badword + ' ' in text.lower()) or (text.lower().endswith(badword) and ' ' + badword in text.lower()) or ' ' + badword + ' ' in text.lower()):
                    await self.client.delete_message(message)
                    botspam = Config.getModuleSetting('badwordfilter', 'announcements')
                    if botspam:
                        await self.client.send_message(botspam, "Removed message from {} in {}: {}".format(message.author.mention, message.channel.mention, message.content.replace(badword, '**' + badword + '**')))
                        return
            whole = text.replace(' ', '')
            if whole.lower() in self.words or (whole.lower() + 's' in self.words and whole.lower() not in ['as', 'ff']):
                await self.client.delete_message(message)
                botspam = Config.getModuleSetting('badwordfilter', 'announcements')
                if botspam:
                    await self.client.send_message(botspam, "Removed message from {} in {}: {}".format(message.author.mention, message.channel.mention, '**' + message.content + '**'))
                    return



module = BadImageFilter