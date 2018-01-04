# -*- coding: utf-8 -*-

import discord
import asyncio
import time
import re
from extra.commands import Command, CommandResponse
from extra.startmessages import Warning
from modules.module import Module
from utils import Config, Users, getShortTimeLength, getLongTime

messages = []

if Config.getModuleSetting('moderation', 'badimagefilter'):
    try:
        from clarifai.rest import ClarifaiApp, Image, Video
    except ImportError:
        messages.append(Warning('Bad Image Filter was turned off because the Clarifai library could not be imported.'))
        ClarifaiApp = None

FILTER_EVASION_CHAR_MAP = str.maketrans(
    u'ªᵃÀΆΛΑÁɅλАÂÃᴀÄдȺÅĀĂƛĄǍǺǻȀȂȦӐӒӑӓɐɑɒȧȁȃάǎāаăąàáâαãäåǞǠДǟǡßƁɃБВΒҌҌҍҍƀЪЬՅᵇԵѢѣҔҕβʙʚɮɞɓƂϦƃъեыьϐбвƄƅƆƇƈȻȼĆĈСĊČϹʗÇҪҫҀҁϽϾϿͻͼͽćĉᴄċčᶜϲçсς¢ɔɕ©ðƉƊƋƌԀᴅԁժԂԃȡĎĐÐďɖɗđƎЭƏǝεƐᴇƷƸǮǯȜȝƹƺӬӭĒĔЕЗĖĘĚÈɆÉÊΕËȄξȆЀЁԐԑʒʓȨɆΈӖӗӘәᵉӚӛӞӠӟӡɇѐёȩєȅȇēĕэըėҼҽҾҿеęϧěèέЄéêëɘəɚɛɜɝ€ϵ϶£ƒƑƒᶠϜϝʃҒғӺӻʄƓĜĞĠĢǤǦǴԌᵍԍǵǥǧĝɠɡɢפğġģʛցʜʮμʯʰʱĤԊԋԦԧĦʜҢңҤҥȞӴӵНΉнΗћЧЊЋȟцʰчĥђӇӈӉӊӋӌҶիҷҸҹҺһɦɧħЂƖƗĨĪĬĮӏіїİÌΪɪÍӀίϊΙÎΊÏĩᶦȈȊІЇȉȋīſǏǐįıìɨɩɪíîȷʲմïĴᴊʲʝЈԺјɟǰϳĵɈɉĶķĸϏǨǩкӃӄƘκƙᴋќᵏКЌΚҚқҜԞԟҝҞҟҠҡʞʟĹլȽԸԼˡĻʟĽιɬɭĿʅʆŁȴĺļľŀłƚɯᵐΜϺмҦҧМՊӍӎщԠᴍԡϻЩɰɱɲήԮԯɳΝոռИѝЙՌɴԤԥԒԓŃŅŇΏŊƝӢӣӤӥпийлͶͷƞńņňŉמηπŋՈȠחПñⁿҊҋȵÑЛҊҋǸЍϞϟǹƟƠơǾǿÒÓΌÔÕφΘÖŌסŎӦᴏӧӨөӪӫΦθŐǑǪоǬȪȬʘΟϵȮȰОѲѳϘѺѻᵒϙȫϬϭфȭȯδȱόǫǭǒōФϕŏőòóοôσõöՓøØȌȎɵȍȏƤբƥÞþρᴘᵖΡƿԲǷРҎҏϷрϸɊɋԚԛգզԳʠϤϥ®ŔŖҐրґŘгѓЯʳʴʵʶʳɹɺɻɼɽӶӷԻɾɿʀՐՒʁяŕŗřƦȐɌɍȒȑȓƻƼƽƧƨŠʂϨЅϩˢšՏ§ŚŜŞŠȘȿșśŝşѕš†ŢТԎԏҬҭŤᴛтϮϯɫŦţᵗťτŧƫʇʈƬƭƮΤͲͳȾȚȶțƯưƱƲÙÚÛÜŨŪŬŮŰŲǓטɄǕǗǙǛȔȖȕȗǔᴜᵘǖϋՍύǘǚυǜũսūŭՄůűЦΰųùԱúûüʉЏʊƔᴠѴᵛѵѶѷνʋʌʍʷᴡѠѡѿŴԜԝшΨψϢϣωŵШώƜϗϰх×ҲҳχХӼӽΧƳƴӮӯӰӱӲӳÝΫŶŸϒҮүҰұϓϔȲץצУŷýÿγʸɎΎΥЎўʎʏɏɣɤ¥ȳуƵƶŽŹŻŽźżžȤΖʐʑɀȥžՀ',
    u'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaabbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbcccccccccccccccccccccccccccccccccccccdddddddddddddddddddeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeffffffffffffgggggggggggggggggggggggghhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiijjjjjjjjjjjjjjjjjkkkkkkkkkkkkkkkkkkkkkkkkkkkkklllllllllllllllllllllllllmmmmmmmmmmmmmmmmmmmnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnoooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooppppppppppppppppppqqqqqqqqqqqrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrssssssssssssssssssssssssssttttttttttttttttttttttttttttttttuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuvvvvvvvvvvwwwwwwwwwwwwwwwwwwwxxxxxxxxxxxyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyzzzzzzzzzzzzzzzzz'
)

NO_REASON = 'No reason was specified at the time of this message -- once a moderator adds a reason this message will self-edit.'
NO_REASON_MOD = 'No reason yet.'
NO_REASON_ENTRY = '*No reason yet. Please add one with `{}editReason {} reason goes here` as soon as possible.*'
MOD_LOG_ENTRY = '**User:** {}\n**Mod:** {}\n**Punishment:** {}\n**Reason:** {}\n**Edit ID:** {}'

PUNISH_FAILURE_BOT = "You cannot punish a bot user. Please use Discord's built-in moderation tools."
PUNISH_FAILURE_MOD = "You cannot punish another mod. Please use Discord's built-in moderation tools."
PUNISH_FAILURE_NONMEMBER = 'You cannot warn or kick a user who is not currently on the server. If severe enough, use a ban instead.'
PUNISH_FAILURE_TIMEFRAME = 'Please choose a time between 15s - 2y.'

PUNISHMENT_MESSAGE_FAILURE = "Could not send {} notification to the user (probably because they have DMs disabled for users/bots who don't share a server they're in)."
WARNING_MESSAGE = "Heyo, {}!\n\nThis is just to let you know you've been given a warning by a moderator " \
                "and that this been marked down officially. Here's the reason:\n```{}```\nAs a refresher, we recommend re-reading " \
                "the Discord server's rules so you're familiar with the way we run things there. Thank you!"
WARNING_MESSAGE_FAILURE = PUNISHMENT_MESSAGE_FAILURE.format('warning')
KICK_MESSAGE = "Heyo, {}!\n\nThis is just to let you know you've been kicked from the Toontown Rewritten " \
                "Discord server by a moderator, and that this has been marked down officially. Here's the reason:\n```{}```\n" \
                "As a refresher, we recommend re-reading the Discord server's rules so you're familiar with the way we run " \
                "things there if you decide to rejoin. We'd love to have you back, as long as you stay Toony!"
KICK_MESSAGE_FAILURE = PUNISHMENT_MESSAGE_FAILURE.format('kick')
KICK_FAILURE = "Could not kick the user. This is probably bad. Please use Discord's built-in moderation tools to enforce the punishment."
TEMPORARY_BAN_MESSAGE = "Hey there, {}.\n\nThis is just to let you know you've been temporarily banned from the " \
                    "Toontown Rewritten Discord server by a moderator for **{}**, and that this has been marked down officially. Here's " \
                    "the reason:\n```{}```\nAs a refresher, we recommend re-reading the Discord server's rules so you're familiar " \
                    "with the way we run things there if you decide to rejoin after your ban. We'd love to have you back, as long as you stay Toony!"
TEMPORARY_BAN_MESSAGE_FAILURE = PUNISHMENT_MESSAGE_FAILURE.format('temporary ban')
PERMANENT_BAN_MESSAGE = "Hey there, {}.\n\nThis is just to let you know you've been permanently banned from the Toontown Rewritten Discord server by " \
                    "a moderator. Here's the reason:\n```{}```\nIf you feel this is illegitimate, please contact one of our mods. Thank you for chatting with us!"
TEMPORARY_BAN_MESSAGE_FAILURE = PUNISHMENT_MESSAGE_FAILURE.format('permanent ban')
BAN_FAILURE = "Could not ban the user. This is probably bad. You should use Discord's built-in moderation tools to enforce the ban."

WORD_FILTER_ENTRY = 'Removed{}message from {} in {}: {}'
WORD_FILTER_EMBED_ENTRY = "Removed{}message from {} in {}: {}\nThe embed {} contained: {}"
WORD_FILTER_MESSAGE = "Hey there, {}! This is just to let you know that you've said the blacklisted word `{}`, and to make clear " \
                    "that it's not an allowed word on this server. No automated action has been taken, but continued usage of the word or trying to circumvent the filter may " \
                    "result in additional punishment, depending on any previous punishments that you have received. We'd love to have you chat with us, as long as you stay Toony!"


class ModerationModule(Module):
    WARNING = 'Warning'
    KICK = 'Kick'
    TEMPORARY_BAN = 'Temporary Ban'
    PERMANENT_BAN = 'Permanent Ban'

    class AddBadWordCMD(Command):
        NAME = 'addBadWord'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            word = ' '.join(args).strip().lower()
            if not word:
                return

            badwords = Config.getModuleSetting('moderation', 'badwords')
            if word in badwords:
                return module.createDiscordEmbed(info='**{}** is already classified as a bad word'.format(word), color=discord.Color.dark_orange())
            badwords.append(word)
            Config.setModuleSetting('moderation', 'badwords', badwords)
            module.words = badwords

            return module.createDiscordEmbed(info='**{}** was added as a bad word.'.format(word), color=discord.Color.green())

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
                return module.createDiscordEmbed(info='**{}** was never a bad word.'.format(word), color=discord.Color.dark_orange())
            badwords.remove(word)
            Config.setModuleSetting('moderation', 'badwords', badwords)
            module.words = badwords

            return module.createDiscordEmbed(info='**{}** was removed from the bad word list.'.format(word), color=discord.Color.green())

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
                return module.createDiscordEmbed(info='**{}** is already classified as a plural exception.'.format(word), color=discord.Color.dark_orange())
            exc.append(word)
            Config.setModuleSetting('moderation', 'plural_exceptions', exc)
            module.pluralExceptions = exc

            return module.createDiscordEmbed(info='**{}** was added as a plural exception.'.format(word), color=discord.Color.green())

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
                return module.createDiscordEmbed(info='**{}** was never a plural exception.'.format(word), color=discord.Color.dark_orange())
            exc.remove(word)
            Config.setModuleSetting('moderation', 'plural_exceptions', exc)
            module.pluralExceptions = exc
            
            return module.createDiscordEmbed(info='**{}** was removed from the plural exception list.'.format(word), color=discord.Color.green())

    class PunishCMD(Command):
        NAME = 'punish'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            return await punishUser(client, module, message, *args)

    class SilentPunishCMD(Command):
        NAME = 'silentPunish'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            return await punishUser(client, module, message, *args, silent=True)

    class WarnCMD(Command):
        NAME = 'warn'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            return await punishUser(client, module, message, *args, punishment='Warning')

    class SilentWarnCMD(Command):
        NAME = 'silentWarn'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            return await punishUser(client, module, message, *args, punishment='Warning', silent=True)

    class KickCMD(Command):
        NAME = 'kick'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            return await punishUser(client, module, message, *args, punishment='Kick')

    class SilentKickCMD(Command):
        NAME = 'silentKick'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            return await punishUser(client, module, message, *args, punishment='Kick', silent=True)

    class TmpBanCMD(Command):
        NAME = 'tb'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            return await punishUser(client, module, message, *args, punishment='Temporary Ban')

    class SilentTmpBanCMD(Command):
        NAME = 'silentTB'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            return await punishUser(client, module, message, *args, punishment='Temporary Ban', silent=True)
    class SilentTmpBanCMD_Variant1(SilentTmpBanCMD):
        NAME = 'silentTb'
    class SilentTmpBanCMD_Variant2(SilentTmpBanCMD):
        NAME = 'silenttb'

    class PermBanCMD(Command):
        NAME = 'ban'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            return await punishUser(client, module, message, *args, punishment='Permanent Ban')

    class SilentPermBanCMD(Command):
        NAME = 'silentBan'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            return await punishUser(client, module, message, *args, punishment='Permanent Ban', silent=True)

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
                        if punishment['modLogEntryID']:
                            modLogEntryMessage = await client.get_channel(MOD_LOG).get_message(punishment['modLogEntryID'])
                            if modLogEntryMessage:
                                mod = modLogEntryMessage.mentions[0]
                                editedMessage = modLogEntryMessage.content
                                if mod.id != message.author.id:
                                    editedMessage = editedMessage.replace('**Mod:** <@!{}>'.format(mod.id), '**Mod:** <@!{}> (edited by <@!{}>)'.format(mod.id, message.author.id))
                                editedMessage = re.sub(r'\*No reason yet\. Please add one with `.+` as soon as possible\.\*', newReason, editedMessage)
                                await modLogEntryMessage.edit(content=editedMessage)
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

        self.badWordFilterOn = Config.getModuleSetting('moderation', 'bad_word_filter', True)
        self.badImageFilterOn = Config.getModuleSetting('moderation', 'bad_image_filter', True) and ClarifaiApp
        self.spamChannel = Config.getModuleSetting('moderation', 'spam_channel')
        self.logChannel = Config.getModuleSetting('moderation', 'log_channel')
        self.exceptions = Config.getModuleSetting('moderation', 'exceptions')
        self.filterBots = Config.getModuleSetting('moderation', 'filter_bots', False)
        self.filterMods = Config.getModuleSetting('moderation', 'filter_mods', True)
        self.allowBotPunishments = Config.getModuleSetting('moderation', 'allow_bot_punishments', False)
        self.allowModPunishments = Config.getModuleSetting('moderation', 'allow_mod_punishments', False)

        self.scheduledUnbans = []
        asyncio.get_event_loop().create_task(self.scheduleUnbans())

        if self.badWordFilterOn:
            self.words = [word.lower() for word in Config.getModuleSetting('moderation', 'badwords')]
            self.pluralExceptions = Config.getModuleSetting('moderation', 'plural_exceptions')

        if self.badImageFilterOn:
            gifKey = Config.getModuleSetting('moderation', 'clarifai_mod_key')
            if not gifKey:
                raise ValueError('Clarifai API Key could not be found ["clarifai_mod_key" in config.json]')
            self.imageFilterApp = ClarifaiApp(api_key=gifKey)
            self.generalImageFilter = self.imageFilterApp.models.get('moderation')
            self.nsfwImageFilter = self.imageFilterApp.models.get('nsfw-v1.0')
            self.nsfwspam = Config.getModuleSetting('moderation', 'nsfw_location')

    async def punishUser(self, user, punishment=None, silent=False):
        member = self.client.rTTR.get_member(user.id)

        if user.bot and not self.allowBotPunishments:
            return CommandResponse(
                message.channel,
                message.author.mention + ' ' + PUNISH_FAILURE_BOT,
                deleteIn=5,
                priorMessage=message
            )
        if Config.getRankOfMember(user) >= 300 and not self.allowModPunishments:
            return CommandResponse(
                message.channel,
                message.author.mention + ' ' + PUNISH_FAILURE_MOD,
                deleteIn=5,
                priorMessage=message
            )

        # If a specific punishment isn't provided, use the next level of punishment
        # above the highest level of punishment they've already received.
        if not punishment:
            punishmentScale = [None, self.WARNING, self.KICK, self.TEMPORARY_BAN, self.PERMANENT_BAN]
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
        # Otherwise, just go along with the specific punishment.
        else:
            punishments = Users.getUserPunishments(user.id)
            nextPunishment = punishment

        # There's no real need to warn users who aren't on the server,
        # nor can we kick them if they aren't on the server.
        if not member and nextPunishment in (self.WARNING, self.KICK):
            return CommandResponse(
                message.channel, 
                message.author.mention + ' ' + PUNISH_FAILURE_NONMEMBER,
                deleteIn=5,
                priorMessage=message
            )

        try:
            # So, if we're given a time period, regardless of what punish command was used, we'll make it a temporary ban.
            # If there's not a time period provided at the correct argument, it will error out into the except command block.
            length = getShortTimeLength(args[1] if len(args) > 1 else '')
            lengthText = getLongTime(args[1] if len(args) > 1 else '')
            nextPunishment = self.TEMPORARY_BAN
            if not 15 <= length <= 63113852:
                return CommandResponse(
                    message.channel,
                    message.author.mention + ' ' + PUNISH_FAILURE_TIMEFRAME,
                    deleteIn=5,
                    priorMessage=message
                )
            reason = ' '.join(args[2:])
        except ValueError:
            # If the command provided to us was for a temporary ban and we didn't get a length, we'll default to 24 hours.
            # If it's not a temporary ban it doesn't matter.
            if nextPunishment == self.TEMPORARY_BAN:
                lengthText = '24 hours'
                length = 86400
            else:
                lengthText = None
            reason = ' '.join(args[1:])

        if not reason:
            reason = NO_REASON

        # The user tracking module makes things prettier and consistent for displaying
        # information about users (embeds <3). We can fallback to text, though.
        usertracking = self.client.requestModule('usertracking')
        modLogEntry = None
        if self.logChannel:
            if not usertracking:
                modLogEntry = await self.client.send_message(self.logChannel, MOD_LOG_ENTRY.format(
                    str(user),
                    message.author.mention,
                    nextPunishment + (' ({})'.format(lengthText) if lengthText else ''),
                    NO_REASON_ENTRY.format(self.client.commandPrefix, message.id) if reason == NO_REASON else reason,
                    message.id
                    )
                )

        punishmentEntry = {
            'type': nextPunishment,
            'mod': message.author.id,
            'reason': reason,
            'modLogEntryID': modLogEntry.id if modLogEntry else None,
            'editID': message.id,
            'created': time.time(),
            'noticeID': None
        }
        if nextPunishment == self.WARNING:
            if not silent:
                try:
                    notice = await self.client.send_message(user, WARNING_MESSAGE.format(user.mention, reason))
                    punishmentEntry['noticeID'] = notice.id
                except Exception as e:
                    await self.client.send_message(message.author, WARNING_MESSAGE_FAILURE)
                    print('Could not send warning notification message to {}'.format(user.id))
            punishments.append(punishmentEntry)
            Users.setUserPunishments(user.id, punishments)
            if usertracking:
                await usertracking.on_member_warn(user, punishmentEntry)
        elif nextPunishment == self.KICK:
            if not silent:                   
                try:
                    notice = await self.client.send_message(user, KICK_MESSAGE.format(user.mention, reason))
                    punishmentEntry['noticeID'] = notice.id
                except Exception as e:
                    await self.client.send_message(message.author, KICK_MESSAGE_FAILURE)
                    print('Could not send kick notification message to {}'.format(user.id))
            try:
                punishments.append(punishmentEntry)
                Users.setUserPunishments(user.id, punishments)
                await self.client.rTTR.kick(user, reason='On behalf of ' + str(message.author))
            except discord.HTTPException:
                await self.client.send_message(message.author, KICK_FAILURE)
        elif nextPunishment == self.TEMPORARY_BAN:
            punishmentEntry['endTime'] = time.time() + length
            punishmentEntry['length'] = lengthText
            if not silent:
                try:
                    notice = await self.client.send_message(user, TEMPORARY_BAN_MESSAGE.format(user.mention, lengthText, reason))
                    punishmentEntry['noticeID'] = notice.id
                except Exception as e:
                    await self.client.send_message(message.author, TEMPORARY_BAN_MESSAGE_FAILURE)
                    print('Could not send temporary ban notification message to {}'.format(user.id))
            try:
                punishments.append(punishmentEntry)
                Users.setUserPunishments(user.id, punishments)
                await self.client.rTTR.ban(user, reason='On behalf of ' + str(message.author))
            except discord.HTTPException:
                await self.client.send_message(message.author, BAN_FAILURE)
        elif nextPunishment == self.PERMANENT_BAN:
            if not silent:
                try:
                    notice = await self.client.send_message(user, PERMANENT_BAN_MESSAGE.format(user.mention, reason))
                    punishmentEntry['noticeID'] = notice.id
                except Exception as e:
                    await self.client.send_message(message.author, PERMANENT_BAN_MESSAGE_FAILURE)
                    print('Could not send permanent ban notification message to {}'.format(user.id))
            try:
                punishments.append(punishmentEntry)
                Users.setUserPunishments(user.id, punishments)
                await self.client.rTTR.ban(user, reason='On behalf of ' + str(message.author))
            except discord.HTTPException:
                await self.client.send_message(message.author, BAN_FAILURE)
        await module.scheduleUnbans()

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

    async def _testForBadWord(self, word, text):
        if word.lower() == "he'll": return ('', '')  # I'll get rid of this someday.
        elif word.lower() == "who're": return ('', '')  # This one too.

        word = re.sub(r'\W+', '', word)
        if word.lower() in self.words or (word.lower().rstrip('s').rstrip('e') in self.words and word.lower() not in self.pluralExceptions):
            return ('DIRECT', word)
        for badword in self.words:
            if ' ' in badword and (badword == text.lower() or badword.rstrip('s').rstrip('e') == text.lower() or (text.lower().startswith(badword) and badword + ' ' in text.lower()) or (text.lower().endswith(badword) and ' ' + badword in text.lower()) or ' ' + badword + ' ' in text.lower()):
                return ('PHRASE', badword)
        whole = text.replace(' ', '')
        if whole.lower() in self.words or (whole.lower().rstrip('s').rstrip('e') in self.words and whole.lower() not in self.pluralExceptions):
            return ('WHOLE', text)
        return ('', '')

    async def filterBadWords(self, message, edited=' ', silentFilter=False):
        text = message.content.translate(FILTER_EVASION_CHAR_MAP)
        for word in text.split(' '):
            badWord = await self._testForBadWord(word, text)
            if badWord[1] and self.spamChannel:
                usertracking = self.client.requestModule('usertracking')
                if usertracking:
                    usertracking.filtered.append(message)
                    await self.client.delete_message(message)
                    await usertracking.on_message_filter(message)
                else:
                    await self.client.delete_message(message)
                    await self.client.send_message(self.spamChannel, WORD_FILTER_ENTRY.format(edited, message.author.mention, message.channel.mention, message.content.replace(word, '**' + badWord[1] + '**')))
                try:
                    if silentFilter:
                        return True
                    await self.client.send_message(message.author, WORD_FILTER_MESSAGE.format(message.author.mention, badWord[1]))
                except discord.HTTPException:
                    pass
                return True

        for embed in message.embeds:
            for attr in [(embed.title, 'title'), (embed.description, 'description'), (embed.footer, 'footer'), (embed.author, 'author')]:
                if type(attr[0]) != str:
                    continue
                for word in attr[0].split(' '):
                    badWord = await self._testForBadWord(word, attr[0])
                    if badWord[1] and self.spamChannel:
                        await self.client.delete_message(message)
                        await self.client.send_message(self.spamChannel, WORD_FILTER_EMBED_ENTRY.format(
                            edited, message.author.mention, message.channel.mention, message.content, attr[1], attr[0].replace(word, '**' + badWord[1] + '**'))
                        )
                        try:
                            if silentFilter:
                                return True
                            await self.client.send_message(message.author, WORD_FILTER_MESSAGE.format(message.author.mention, badWord[1]))
                        except discord.HTTPException:
                            pass
                        return True
            for field in embed.fields:
                for fieldattr in [(field.name, 'field name'), (field.value, 'field value')]:
                    for word in fieldattr[0].split(' '):
                        badWord = await self._testForBadWord(word, fieldattr[0])
                        if badWord[1] and self.spamChannel:
                            await self.client.delete_message(message)
                            await self.client.send_message(self.spamChannel, WORD_FILTER_EMBED_ENTRY.format(
                                edited, message.author.mention, message.channel.mention, message.content, fieldattr[1], fieldattr[0].replace(word, '**' + badWord[1] + '**'))
                            )
                            try:
                                if silentFilter:
                                    return True
                                await self.client.send_message(message.author, WORD_FILTER_ENTRY.format(message.author.mention, badWord[1]))
                            except discord.HTTPException:
                                pass
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
            await self.client.send_message(self.spamChannel, "Banned and removed message with bad image from {} in {}. **[Rating: {}]**" \
                "\nDue to its high rating, the image is located in {}.".format(
                    message.author.display_name, message.channel.mention, rating, self.client.get_channel(self.nsfwspam).mention))
        elif rating > 1:
            rating = round(rating, 2)
            await self.client.delete_message(message)
            await self.client.kick(message.author)
            await self.client.send_message(self.nsfwspam, "Kicked and removed message with bad image from {} in {}. **[Rating: {}]**" \
                "\n*If this was a mistake, please apologize to the user and provide a Discord link back to the server.*\n{}".format(
                    message.author.display_name, message.channel.mention, rating, url))
            await self.client.send_message(self.spamChannel, "Kicked and removed message with bad image from {} in {}. **[Rating: {}]**" \
                "\nDue to its high rating, the image is located in {}.".format(
                    message.author.display_name, message.channel.mention, rating, self.client.get_channel(self.nsfwspam).mention))
        elif rating > .5:
            rating = round(rating, 2)
            await self.client.send_message(self.spamChannel, "{} posted an image in {} that has been registered as possibly bad. " \
                "**[Rating: {}]**\n*If the image has bad content in it, please act accordingly.*\n{}".format(
                    message.author.mention, message.channel.mention, rating, url))
        # For debug.
        #else:
        #    rating = round(rating, 2)
        #    await self.client.send_message(self.spamChannel, "Image posted was fine. **[Rating: {}]**".format(rating))

    async def handleMsg(self, message):
        if message.channel.id in self.exceptions or message.author.id in self.exceptions or \
            (message.channel.__class__ == discord.DMChannel or (message.channel.category and message.channel.category.name.startswith('Lobby'))) or \
            (message.author.bot and not self.filterBots) or ((Config.getRankOfUser(message.author.id) >= 300 or any([Config.getRankOfRole(role.id) >= 300 for role in message.author.roles])) and not self.filterMods):
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

    async def on_message_edit(self, before, after):
        message = after
        if message.channel.id in self.exceptions or message.author.id in self.exceptions or (message.author.bot and not self.filterBots):
            return

        # We'll only check for edited-in bad words for right now.
        try:
            if self.badWordFilterOn:
                await self.filterBadWords(message, edited=' edited ')
        except discord.errors.NotFound:
            print('Tried to remove edited message in bad word filter but message wasn\'t found.')
            return

module = ModerationModule