import discord
import time
import re
from modules.module import Module
from extra.commands import Command
from utils import Config

class Moderation(Module):
    class LookupCMD(Command):
        NAME = 'lookup'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            if not message.mentions:
                name = ' '.join(args)
                user = discord.utils.get(message.server.members, display_name=name)
                if user:
                    return '{}\nAccount Creation Date: {}\nServer Join Date: {}'.format(user.mention, user.created_at, user.joined_at)
                    #await self.send_message(message.channel, '{}\nAccount Creation Date: {}\nServer Join Date: {}'.format(user.mention, user.created_at, user.joined_at))
                else:
                    return 'No known user'
                    #await self.send_message(message.channel, 'No known user')
            else:
                for mention in message.mentions:
                    return '{}\nAccount Creation Date: {}\nServer Join Date: {}'.format(mention.mention, mention.created_at, mention.joined_at)
                    #await self.send_message(message.channel, '{}\nAccount Creation Date: {}\nServer Join Date: {}'.format(mention.mention, mention.created_at, mention.joined_at))

    class AddBadWordCMD(Command):
        NAME = 'addbadword'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            word = ' '.join(args).strip()
            if not word:
                return

            badwords = Config.getModuleSetting('moderation', 'badwords')
            if word in badwords:
                return '**{}** is already classified as a bad word'.format(word)
                #await self.send_message(message.channel, '**{}** is already classified as a bad word.'.format(word))
                #return
            badwords.append(word)
            Config.setModuleSetting('moderation', 'badwords', badwords)
            module.words = badwords

            return '**{}** was added as a bad word.'.format(word)

    class RemoveBadWordCMD(Command):
        NAME = 'removebadword'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            word = ' '.join(args).strip()
            if not word:
                return

            badwords = Config.getModuleSetting('moderation', 'badwords')
            if word not in badwords:
                return '**{}** was never a bad word.'.format(word)
            badwords.remove(word)
            Config.setModuleSetting('moderation', 'badwords', badwords)
            module.words = badwords

            return '**{}** was removed from the bad word list.'.format(word)

    class AddPluralExceptionCMD(Command):
        NAME = 'addpluralexception'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            word = ' '.join(args).strip()
            if not word:
                return

            exc = Config.getModuleSetting('moderation', 'plural_exceptions')
            if word in exc:
                return '**{}** is already classified as a plural exception.'.format(word)
            exc.append(word)
            Config.setModuleSetting('moderation', 'plural_exceptions', exc)
            module.pluralExceptions = exc

            return '**{}** was added as a plural exception.'.format(word)

    class RemovePluralExceptionCMD(Command):
        NAME = 'removepluralexception'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            word = ' '.join(args).strip()
            if not word:
                return

            exc = Config.getModuleSetting('moderation', 'plural_exceptions')
            if word not in exc:
                return '**{}** was never a plural exception.'.format(word)
            exc.remove(word)
            Config.setModuleSetting('moderation', 'plural_exceptions', exc)
            module.pluralExceptions = exc
            
            return '**{}** was removed from the plural exception list.'.format(word)

    def __init__(self, client):
        Module.__init__(self, client)
        self.commands = [
            self.LookupCMD,
            self.AddBadWordCMD,
            self.RemoveBadWordCMD,
            self.AddPluralExceptionCMD,
            self.RemovePluralExceptionCMD
        ]

        self.words = Config.getModuleSetting('moderation', 'badwords')
        self.pluralExceptions = Config.getModuleSetting('moderation', 'plural_exceptions')
        self.links = Config.getModuleSetting('moderation', 'badlinks')
        self.exceptions = Config.getModuleSetting('moderation', 'exceptions')
        self.botspam = Config.getModuleSetting('moderation', 'announcements')

    async def on_member_ban(self, member):
        botspam = Config.getSetting('botspam')
        await self.client.send_message(botspam, "{} was banned.".format(member.display_name))

    async def on_member_join(self, member):
        botspam = Config.getSetting('botspam')
        await self.client.send_message(botspam, "{} joined.\nAccount Creation Date: {}\nJoin Date (Today): {}".format(member.mention, member.created_at, member.joined_at))

    async def on_member_remove(self, member):
        botspam = Config.getSetting('botspam')
        await self.client.send_message(botspam, "{} left.".format(member.display_name))


    async def filterBadWords(self, message):
        text = message.content

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

    async def handleMsg(self, message):
        if message.channel.id in self.exceptions or message.author.id in self.exceptions:
            return

        timeStart = time.time()
        await self.filterBadWords(message)


module = Moderation