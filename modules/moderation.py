import discord
import asyncio
import time
import re
from clarifai.rest import ClarifaiApp, Image, Video
from modules.module import Module
from extra.commands import Command
from utils import Config

class ModerationModule(Module):
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
        self.nsfwspam = Config.getModuleSetting('moderation', 'nsfw_location')

        gifKey = Config.getModuleSetting('moderation', 'clarifai_mod_key')
        self.imageFilterApp = ClarifaiApp(api_key=gifKey) if gifKey else None
        self.generalImageFilter = self.imageFilterApp.models.get('moderation')
        self.nsfwImageFilter = self.imageFilterApp.models.get('nsfw-v1.0')

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
            if word.lower() == "he'll":
                continue

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

    async def filterBadImages(self, message):
        # Refreshes embed info from the API.
        message = await self.client.get_message(message.channel, message.id)

        if not message.embeds and not message.attachments:
            return

        for embed in message.embeds:
            if embed['type'] in ['image', 'gif', 'gifv']:
                rating = self.runImageFilter(embed['thumbnail']['url'], gif=True if embed['type'] in ['gif', 'gifv'] or embed['url'].endswith('gif') else False)
                await self.determineImageRatingAction(message, rating, embed['url'])

        for attachment in message.attachments:
            if any([attachment['filename'].endswith(extension) for extension in ('.jpg', '.png', '.gif', '.bmp')]):
                rating = self.runImageFilter(attachment['url'], gif=True if attachment['filename'].endswith('.gif') or attachment['filename'].endswith('.gifv') else False)
                await self.determineImageRatingAction(message, rating, attachment['url'])

    def runImageFilter(self, url, gif=False):
        # The image content is based on a scale from 0-2.
        #
        # 0  .2  .4  .6  .8   1   1.2  1.4  1.6  1.8  2
        # APPROPRIATE                     INAPPROPRIATE
        #
        # Content landing in INAPPROPRIATE will be removed
        # automatically, with an extremely high score resulting
        # in a ban. Content in the middle may or may not be
        # removed but will be sent to mods for manual review.
        #
        # Anything that's not strictly NSFW, such as possible
        # drug references, gore, or suggestive material is
        # scored at half of the API's certainty to allow
        # a higher chance to pass through human approval.

        rating = 0

        image = Video(url=url) if gif else Image(url=url)
        generalFilterResponse = self.generalImageFilter.predict([image])
        nsfwFilterResponse = self.nsfwImageFilter.predict([image])

        if gif:
            ratings = []
            i = 0
            for frame in generalFilterResponse['outputs'][0]['data']['frames']:
                nframe = nsfwFilterResponse['outputs'][0]['data']['frames'][i]
                ratings.append(self.getRating(frame['data']['concepts'], nframe['data']['concepts']))
                i += 1
            return max(ratings)
        else:
            return self.getRating(generalFilterResponse['outputs'][0]['data']['concepts'], nsfwFilterResponse['outputs'][0]['data']['concepts'])

        for concept in generalFilterResponse['outputs'][0]['data']['concepts']:
            if concept['name'] == 'explicit':
                rating += concept['value']
            elif concept['name'] in ['suggestive', 'drug', 'gore']:
                rating += concept['value'] / 2
        for concept in nsfwFilterResponse['outputs'][0]['data']['concepts']:
            if concept['name'] == 'nsfw':
                rating += concept['value']

        return rating

    def getImageRating(self, generalConcepts, nsfwConcepts):
        rating = 0
        for concept in generalConcepts:
            if concept['name'] == 'explicit':
                rating += concept['value']
            elif concept['name'] in ['suggestive', 'drug', 'gore']:
                rating += concept['value'] / 2
        for concept in nsfwConcepts:
            if concept['name'] == 'nsfw':
                rating += concept['value']

        return rating

    async def determineImageRatingAction(self, message, rating, url):
        print(rating)
        if rating > 1.5:
            rating = round(rating, 2)
            await self.client.ban(message.author)
            await self.client.send_message(self.nsfwspam, "Banned and removed message with bad image from {} in {}. **[Rating: {}]**" \
                "\n*If this was a mistake, please unban the user, apologize, and provide a Discord link back to the server.*\n{}".format(
                    message.author.display_name, message.channel.mention, rating, url))
            await self.client.send_message(self.botspam, "Banned and removed message with bad image from {} in {}. **[Rating: {}]**" \
                "\nDue to its high rating, the image is located in {}.".format(
                    message.author.display_name, message.channel.mention, rating, self.client.get_channel(self.nsfwspam)))
        elif rating > 1:
            rating = round(rating, 2)
            await self.client.delete_message(message)
            await self.client.kick(message.author)
            await self.client.send_message(self.nsfwspam, "Kicked and removed message with bad image from {} in {}. **[Rating: {}]**" \
                "\n*If this was a mistake, please apologize to the user and provide a Discord link back to the server.*\n{}".format(
                    message.author.display_name, message.channel.mention, rating, url))
            await self.client.send_message(self.botspam, "Kicked and removed message with bad image from {} in {}. **[Rating: {}]**" \
                "\nDue to its high rating, the image is located in {}.".format(
                    message.author.display_name, message.channel.mention, rating, self.client.get_channel(self.nsfwspam)))
        elif rating > .5:
            rating = round(rating, 2)
            await self.client.send_message(self.botspam, "{} posted an image in {} that has been registered as possibly bad. " \
                "**[Rating: {}]**\n*If the image has bad content in it, please act accordingly.*\n{}".format(
                    message.author.mention, message.channel.mention, rating, url))

    async def handleMsg(self, message):
        if message.channel.id in self.exceptions or message.author.id in self.exceptions:
            return

        timeStart = time.time()
        await self.filterBadWords(message)

        # This is for the bad image filter. Discord's servers usually needs a
        # moment to process embedded / attached images before the API can use it.
        if time.time() - timeStart < 1:
            await asyncio.sleep(2)
        else:
            await asyncio.sleep(1)
        await self.filterBadImages(message)


module = ModerationModule