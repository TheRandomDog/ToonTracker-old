import discord
import asyncio
import time
import re
from clarifai.rest import ClarifaiApp, Image, Video
from extra.commands import Command, CommandResponse
from modules.module import Module
from utils import Config, Users, getShortTimeLength, getLongTime

MOD_LOG = Config.getModuleSetting('moderation', 'mod_log', None)
NO_REASON = 'No reason was specified at the time of this message -- once a moderator adds a reason this message will self-edit.'
NO_REASON_MOD = 'No reason yet.'

async def punishUser(client, module, message, *args, punishment=None):
    if not message.mentions:
        if not message.raw_mentions:
            try:
                user = await client.get_user_info(int(args[0]))
            except (ValueError, IndexError):
                return CommandResponse(message.channel, '{} Please use a mention to refer to a user.'.format(message.author.mention), deleteIn=5, priorMessage=message)
            except discord.NotFound:
                return CommandResponse(message.channel, '{} Could not find user with ID `{}`'.format(message.author.mention, args[0]), deleteIn=5, priorMessage=message)
        else:
            try:
                user = await client.get_user_info(message.raw_mentions[0])
            except discord.NotFound:
                return CommandResponse(message.channel, '{} Could not find user with ID `{}`'.format(message.author.mention, message.raw_mentions[0]), deleteIn=5, priorMessage=message)   
    else:
        user = message.mentions[0]
    
    if user.bot:
        return CommandResponse(message.channel, '{} You cannot punish a bot user. Please use Discord\'s built-in moderation tools.'.format(message.author.mention), 
            deleteIn=5, priorMessage=message)

    if not punishment:
        punishmentScale = [None, 'Warning', 'Kick', 'Temporary Ban', 'Permanent Ban']
        highestPunishment = None
        highestPunishmentJSON = None

        punishments = Users.getUserPunishments(user.id)
        for punishment in punishments:
            if punishmentScale.index(punishment['type']) > punishmentScale.index(highestPunishment):
                highestPunishment = punishment['type']
                highestPunishmentJSON = punishment

        try:
            nextPunishment = punishmentScale[punishmentScale.index(highestPunishment) + 1]
        except IndexError:
            nextPunishment = punishmentScale[-1]
    else:
        punishments = Users.getUserPunishments(user.id)
        nextPunishment = punishment

    if nextPunishment == 'Kick' and not message.mentions:
        if not client.rTTR.get_member(user.id):
            nextPunishment = 'Warning'
            await client.send_message(message.author, 'The punishment (a kick) was downgraded to a warning because the user ' \
                'is not currently on the server and kicking would have had no effect.')

    try:
        length = getShortTimeLength(args[1] if len(args) > 1 else '')
        lengthText = getLongTime(args[1] if len(args) > 1 else '')
        nextPunishment = 'Temporary Ban'
        if not 15 <= length <= 63113852:
            return CommandResponse(message.channel, '{} Please choose a time between 15s - 2y.'.format(message.author.mention), deleteIn=5, priorMessage=message)
        reason = ' '.join(args[2:])
    except ValueError:
        if nextPunishment == 'Temporary Ban':
            lengthText = '24 hours'
            length = 86400
            reason = ' '.join(args[1:])
        else:
            lengthText = None
            reason = ' '.join(args[1:])

    if not reason:
        reason = NO_REASON

    modLog = None
    if MOD_LOG:
        modLog = await client.send_message(MOD_LOG, "**User:** {}\n**Mod:** {}\n**Punishment:** {}\n**Reason:** {}\n**Edit ID:** {}".format(
            str(user),
            message.author.mention,
            nextPunishment + (' ({})'.format(lengthText) if lengthText else ''),
            '*No reason yet. Please add one with `{}editReason {} reason goes here` as soon as possible.*'.format(client.commandPrefix, message.id) if reason == NO_REASON else reason,
            message.id
            )
        )
    await client.delete_message(message)

    punishmentAdd = {
        'type': nextPunishment,
        'mod': message.author.id,
        'reason': reason,
        'modLogID': modLog.id if modLog else None,
        'editID': message.id,
        'created': time.time(),
        'noticeID': None
    }
    if nextPunishment == 'Warning':
        try:
            notice = await client.send_message(user, 'Heyo, {}!\n\nThis is just to let you know you\'ve been given a warning by a moderator ' \
                'and has been marked down officially. Here\'s the reason:\n```{}```\nAs a refresher, we recommend re-reading ' \
                'the Discord server\'s rules so you\'re familiar with the way we run things there. Thank you!'.format(
                    user.mention, reason))
            punishmentAdd['noticeID'] = notice.id
        except Exception as e:
            await client.send_message(message.author, 'Could not send warning notification to the user (probably because they have DMs disabled for users/bots who don\'t share a server they\'re in).')
            print('Could not send warning notification message to {}'.format(user.id))
    elif nextPunishment == 'Kick':                                     
        try:
            notice = await client.send_message(user, 'Heyo, {}!\n\nThis is just to let you know you\'ve been kicked from the Toontown Rewritten ' \
                'Discord server by a moderator, and this has been marked down officially. Here\'s the reason:\n```{}```\n' \
                'As a refresher, we recommend re-reading the Discord server\'s rules so you\'re familiar with the way we run ' \
                'things there if you decide to rejoin. We\'d love to have you back, as long as you stay Toony!'.format(
                    user.mention, reason))
            punishmentAdd['noticeID'] = notice.id
        except Exception as e:
            await client.send_message(message.author, 'Could not send kick notification to the user (probably because they have DMs disabled for users/bots who don\'t share a server they\'re in).')
            print('Could not send kick notification message to {}'.format(user.id))
        try:
            await client.rTTR.kick(user, reason='On behalf of ' + str(message.author))
        except discord.HTTPException:
            await client.send_message(message.author, 'Could not kick the user. If the user was not on the server, this is expected.')
    elif nextPunishment == 'Temporary Ban':
        punishmentAdd['endTime'] = time.time() + length
        punishmentAdd['length'] = lengthText
        try:
            notice = await client.send_message(user, 'Hey there, {}.\n\nThis is just to let you know you\'ve been temporarily banned from the ' \
                'Toontown Rewritten Discord server by a moderator for **{}**, and this has been marked down officially. Here\'s ' \
                'the reason:\n```{}```\nAs a refresher, we recommend re-reading the Discord server\'s rules so you\'re familiar ' \
                'with the way we run things there if you decide to rejoin after your ban. We\'d love to have you back, as long ' \
                'as you stay Toony!'.format(user.mention, lengthText, reason))
            punishmentAdd['noticeID'] = notice.id
        except Exception as e:
            await client.send_message(message.author, 'Could not send temporary ban notification to the user (probably because they have DMs disabled for users/bots who don\'t share a server they\'re in).')
            print('Could not send temporary ban notification message to {}'.format(user.id))
        try:
            await client.rTTR.ban(user, reason='On behalf of ' + str(message.author))
        except discord.HTTPException:
            await client.send_message(message.author, 'Could not ban the user. This is probably bad. ' \
            'You should use Discord\'s built-in moderation tools to enforce the ban.')
    elif nextPunishment == 'Permanent Ban':
        try:
            notice = await client.send_message(user, 'Hey there, {}.\n\nThis is just to let you know you\'ve been permanently banned from the ' \
                'Toontown Rewritten Discord server by a moderator. Here\'s the reason:\n```{}```\nIf you feel this is illegitimate, ' \
                'please contact one of our mods. Thank you for chatting with us!'.format(user.mention, reason))
            punishmentAdd['noticeID'] = notice.id
        except Exception as e:
            await client.send_message(message.author, 'Could not send permanent ban notification to the user (probably because they have DMs disabled for users/bots who don\'t share a server they\'re in).')
            print('Could not send permanent ban notification message to {}'.format(user.id))
        try:
            await client.rTTR.ban(user, reason='On behalf of ' + str(message.author))
        except discord.HTTPException:
            await client.send_message(message.author, 'Could not ban the user. This is probably bad. ' \
            'You should use Discord\'s built-in moderation tools to enforce the ban.')
    punishments.append(punishmentAdd)

    Users.setUserPunishments(user.id, punishments)
    await module.scheduleUnbans()

class ModerationModule(Module):
    class LookupCMD(Command):
        NAME = 'lookup'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            if not message.mentions:
                if not message.raw_mentions:
                    try:
                        user = await client.get_user_info(int(args[0]))
                    except (ValueError, IndexError, discord.NotFound):
                        name = ' '.join(args)
                        user = discord.utils.get(message.guild.members, display_name=name)
                        user = discord.utils.get(message.guild.members, name=name) if not user else user
                        if not user:
                            return 'No known user'
                else:
                    try:
                        user = await client.get_user_info(message.raw_mentions[0])
                    except discord.NotFound:
                        return 'No known user'
            else:
                user = message.mentions[0]
            return Users.getUserEmbed(user)
 
    class AddBadWordCMD(Command):
        NAME = 'addBadWord'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            word = ' '.join(args).strip()
            if not word:
                return

            badwords = Config.getModuleSetting('moderation', 'badwords')
            if word in badwords:
                return '**{}** is already classified as a bad word'.format(word)
            badwords.append(word)
            Config.setModuleSetting('moderation', 'badwords', badwords)
            module.words = badwords

            return '**{}** was added as a bad word.'.format(word)

    class RemoveBadWordCMD(Command):
        NAME = 'removeBadWord'
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
        NAME = 'addPluralException'
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
        NAME = 'removePluralException'
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

    class PunishCMD(Command):
        NAME = 'punish'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            return await punishUser(client, module, message, *args)

    class WarnCMD(Command):
        NAME = 'warn'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            return await punishUser(client, module, message, *args, punishment='Warning')

    class KickCMD(Command):
        NAME = 'kick'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            return await punishUser(client, module, message, *args, punishment='Kick')

    class TmpBanCMD(Command):
        NAME = 'tb'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            return await punishUser(client, module, message, *args, punishment='Temporary Ban')

    class PermBanCMD(Command):
        NAME = 'ban'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            return await punishUser(client, module, message, *args, punishment='Permanent Ban')

    class EditPunishReasonCMD(Command):
        NAME = 'editReason'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            try:
                int(args[0])
            except ValueError as e:
                return CommandResponse(message.channel, '{} Please use a proper edit ID.'.format(message.author.mention), deleteIn=5, priorMessage=message)

            if not args[1:]:
                return CommandResponse(message.channel, '{} A reason must be given.'.format(message.author.mention), deleteIn=5, priorMessage=message)
            newReason = ' '.join(args[1:])

            for userID, userData in Users.getUsers().items():
                somethingChanged = False
                i = 0
                for punishment in userData['punishments']:
                    if punishment['editID'] == int(args[0]):
                        somethingChanged = True
                        if punishment['modLogID']:
                            modLogMessage = await client.get_channel(MOD_LOG).get_message(punishment['modLogID'])
                            if modLogMessage:
                                mod = modLogMessage.mentions[0]
                                editedMessage = modLogMessage.content
                                if mod.id != message.author.id:
                                    editedMessage = editedMessage.replace('**Mod:** <@!{}>'.format(mod.id), '**Mod:** <@!{}> (edited by <@!{}>)'.format(mod.id, message.author.id))
                                editedMessage = re.sub(r'\*No reason yet\. Please add one with `.+` as soon as possible\.\*', newReason, editedMessage)
                                await modLogMessage.edit(content=editedMessage)
                        if punishment['noticeID']:
                            user = await client.get_user_info(userID)
                            if not user.dm_channel:
                                await user.create_dm()
                            notice = await user.dm_channel.get_message(punishment['noticeID'])
                            if notice:
                                editedMessage = notice.content.replace(NO_REASON, newReason)
                                await notice.edit(content=editedMessage)
                        punishment['reason'] = newReason
                        userData['punishments'][i] = punishment
                    i += 1
                if somethingChanged:
                    Users.setUserPunishments(userID, userData['punishments'])
                    return CommandResponse(message.channel, ':thumbsup:', deleteIn=5, priorMessage=message)
            return CommandResponse(message.channel, '{} The edit ID was not recognized.'.format(message.author.mention), deleteIn=5, priorMessage=message)

    class RemovePunishmentCMD(Command):
        NAME = 'removePunishment'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            try:
                int(args[0])
            except ValueError as e:
                return CommandResponse(message.channel, '{} Please use a proper edit ID.'.format(message.author.mention), deleteIn=5, priorMessage=message)

            for userID, userData in Users.getUsers().items():
                somethingChanged = False
                newPunishments = userData['punishments']
                for punishment in userData['punishments']:
                    if punishment['editID'] == int(args[0]):
                        newPunishments.remove(punishment)
                        Users.setUserPunishments(userID, newPunishments)
                        return CommandResponse(message.channel, ':thumbsup:', deleteIn=5, priorMessage=message)
            return CommandResponse(message.channel, '{} The edit ID was not recognized.'.format(message.author.mention), deleteIn=5, priorMessage=message)

    def __init__(self, client):
        Module.__init__(self, client)

        self.badWordFilterOn = Config.getModuleSetting('moderation', 'badwordfilter')
        self.badImageFilterOn = Config.getModuleSetting('moderation', 'badimagefilter')
        self.botspam = Config.getModuleSetting('moderation', 'announcements')
        self.exceptions = Config.getModuleSetting('moderation', 'exceptions')
        self.filterBots = Config.getModuleSetting('moderation', 'filter_bots', False)

        self.scheduledUnbans = []
        asyncio.get_event_loop().create_task(self.scheduleUnbans())

        if self.badWordFilterOn:
            self.words = Config.getModuleSetting('moderation', 'badwords')
            self.pluralExceptions = Config.getModuleSetting('moderation', 'plural_exceptions')

        if self.badImageFilterOn:
            gifKey = Config.getModuleSetting('moderation', 'clarifai_mod_key')
            if not gifKey:
                raise ValueError('Clarifai API Key could not be found ["clarifai_mod_key" in config.json]')
            self.imageFilterApp = ClarifaiApp(api_key=gifKey)
            self.generalImageFilter = self.imageFilterApp.models.get('moderation')
            self.nsfwImageFilter = self.imageFilterApp.models.get('nsfw-v1.0')
            self.nsfwspam = Config.getModuleSetting('moderation', 'nsfw_location')

    async def on_member_ban(self, guild, member):
        botspam = Config.getSetting('botspam')
        await self.client.send_message(botspam, "{} was banned.".format(member.display_name))

    async def on_member_join(self, member):
        botspam = Config.getSetting('botspam')
        for channel in botspam:
            await self.client.get_channel(channel).send(content='{} joined.'.format(member.mention), embed=Users.getUserEmbed(member))

    async def on_member_remove(self, member):
        botspam = Config.getSetting('botspam')
        await self.client.send_message(botspam, "{} left.".format(member.display_name))

    async def scheduleUnbans(self):
        for userID, user in Users.getUsers().items():
            for punishment in user['punishments']:
                if punishment['type'] == 'Temporary Ban':
                    if userID not in self.scheduledUnbans and punishment['endTime'] > time.time():
                        self.scheduledUnbans.append(userID)
                        await self.scheduledUnban(userID, punishment['endTime'])

    async def scheduledUnban(self, userID, endTime=None):
        user = await self.client.get_user_info(userID)
        if endTime:
            await asyncio.sleep(endTime - time.time())
        await self.client.rTTR.unban(user, reason='The user\'s temporary ban expired.')
        self.scheduledUnbans.remove(userID)

    async def filterBadWords(self, message):
        text = message.content

        for word in text.split(' '):
            if word.lower() == "he'll":
                continue

            word = re.sub(r'\W+', '', word)
            if word.lower() in self.words or (word.lower().rstrip('s').rstrip('e') in self.words and word.lower() not in self.pluralExceptions):
                await self.client.delete_message(message)
                if self.botspam:
                    await self.client.send_message(self.botspam, "Removed message from {} in {}: {}".format(message.author.mention, message.channel.mention, message.content.replace(word, '**' + word + '**')))
                    return True
            for badword in self.words:
                if ' ' in badword and (badword == text.lower() or badword.rstrip('s').rstrip('e') == text.lower() or (text.lower().startswith(badword) and badword + ' ' in text.lower()) or (text.lower().endswith(badword) and ' ' + badword in text.lower()) or ' ' + badword + ' ' in text.lower()):
                    await self.client.delete_message(message)
                    if self.botspam:
                        await self.client.send_message(self.botspam, "Removed message from {} in {}: {}".format(message.author.mention, message.channel.mention, message.content.replace(badword, '**' + badword + '**')))
                        return True
            whole = text.replace(' ', '')
            if whole.lower() in self.words or (whole.lower().rstrip('s').rstrip('e') in self.words and whole.lower() not in self.pluralExceptions):
                await self.client.delete_message(message)
                if self.botspam:
                    await self.client.send_message(self.botspam, "Removed message from {} in {}: {}".format(message.author.mention, message.channel.mention, '**' + message.content + '**'))
                    return True

    async def filterBadImages(self, message):
        # Refreshes embed info from the API.
        try:
            message = await self.client.get_message(message.channel, message.id)
        except discord.errors.NotFound:
            print('Tried to rediscover message {} to filter bad images but message wasn\'t found.'.format(message.id))

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
                ratings.append(self.getImageRating(frame['data']['concepts'], nframe['data']['concepts']))
                i += 1
            return max(ratings)
        else:
            return self.getImageRating(generalFilterResponse['outputs'][0]['data']['concepts'], nsfwFilterResponse['outputs'][0]['data']['concepts'])

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
                    message.author.display_name, message.channel.mention, rating, self.client.get_channel(self.nsfwspam).mention))
        elif rating > 1:
            rating = round(rating, 2)
            await self.client.delete_message(message)
            await self.client.kick(message.author)
            await self.client.send_message(self.nsfwspam, "Kicked and removed message with bad image from {} in {}. **[Rating: {}]**" \
                "\n*If this was a mistake, please apologize to the user and provide a Discord link back to the server.*\n{}".format(
                    message.author.display_name, message.channel.mention, rating, url))
            await self.client.send_message(self.botspam, "Kicked and removed message with bad image from {} in {}. **[Rating: {}]**" \
                "\nDue to its high rating, the image is located in {}.".format(
                    message.author.display_name, message.channel.mention, rating, self.client.get_channel(self.nsfwspam).mention))
        elif rating > .5:
            rating = round(rating, 2)
            await self.client.send_message(self.botspam, "{} posted an image in {} that has been registered as possibly bad. " \
                "**[Rating: {}]**\n*If the image has bad content in it, please act accordingly.*\n{}".format(
                    message.author.mention, message.channel.mention, rating, url))
        # For debug.
        #else:
        #    rating = round(rating, 2)
        #    await self.client.send_message(self.botspam, "Image posted was fine. **[Rating: {}]**".format(rating))

    async def handleMsg(self, message):
        if message.channel.id in self.exceptions or message.author.id in self.exceptions or (message.author.bot and not self.filterBots):
            return

        timeStart = time.time()
        try:
            if self.badWordFilterOn:
                await self.filterBadWords(message)
        except discord.errors.NotFound:
            print('Tried to remove message in bad word filter but message wasn\'t found.')
            return

        if not self.badImageFilterOn:
            return

        # This is for the bad image filter. Discord's servers usually needs a
        # moment to process embedded / attached images before the API can use it.
        if time.time() - timeStart < 1:
            await asyncio.sleep(2)
        else:
            await asyncio.sleep(1)
        await self.filterBadImages(message)


module = ModerationModule