# -*- coding: utf-8 -*-

import discord
import asyncio
import time
import re
from extra.commands import Command, CommandResponse
from extra.startmessages import Warning
from modules.module import Module
from utils import Config, Users, getShortTimeLength, getLongTime
from traceback import format_exc

messages = []

if Config.getModuleSetting('moderation', 'bad_image_filter'):
    try:
        from clarifai.rest import ClarifaiApp, Image, Video
    except ImportError:
        messages.append(Warning('Bad Image Filter was turned off because the Clarifai library could not be imported.'))
        ClarifaiApp = None
else:
    ClarifaiApp = None

FILTER_EVASION_CHAR_MAP = str.maketrans(
    u'ªᵃÀΆΛΑÁɅλАÂÃᴀÄдȺÅĀĂƛĄǍǺǻȀȂȦӐӒӑӓɐɑɒȧȁȃάǎāаăąàáâαãäåǞǠДǟǡßƁɃБВΒҌҌҍҍƀЪЬՅᵇԵѢѣҔҕβʙʚɮɞɓƂϦƃъեыьϐбвƄƅƆƇƈȻȼĆĈСĊČϹʗÇҪҫҀҁϽϾϿͻͼͽćĉᴄċčᶜϲçсς¢ɔɕ©ðƉƊƋƌԀᴅԁժԂԃȡĎĐÐďɖɗđƎЭƏǝεƐᴇƷƸǮǯȜȝƹƺӬӭĒĔЕЗĖĘĚÈɆÉÊΕËȄξȆЀЁԐԑʒʓȨɆΈӖӗӘәᵉӚӛӞӠӟӡɇѐёȩєȅȇēĕэըėҼҽҾҿеęϧěèέЄéêëɘəɚɛɜɝ€ϵ϶£ƒƑƒᶠϜϝʃҒғӺӻʄƓĜĞĠĢǤǦǴԌᵍԍǵǥǧĝɠɡɢפğġģʛցʜʮμʯʰʱĤԊԋԦԧĦʜҢңҤҥȞӴӵНΉнΗћЧЊЋȟцʰчĥђӇӈӉӊӋӌҶիҷҸҹҺһɦɧħЂƖƗĨĪĬĮӏіїİÌΪɪÍӀίϊΙÎΊÏĩᶦȈȊІЇȉȋīſǏǐįıìɨɩɪíîȷʲմïĴᴊʲʝЈԺјɟǰϳĵɈɉĶķĸϏǨǩкӃӄƘκƙᴋќᵏКЌΚҚқҜԞԟҝҞҟҠҡʞʟĹլȽԸԼˡĻʟĽιɬɭĿʅʆŁȴĺļľŀłƚɯᵐΜϺмҦҧМՊӍӎщԠᴍԡϻЩɰɱɲήԮԯɳΝոռИѝЙՌɴԤԥԒԓŃŅŇΏŊƝӢӣӤӥпийлͶͷƞńņňŉמηπŋՈȠחПñⁿҊҋȵÑЛҊҋǸЍϞϟǹƟƠơǾǿÒÓΌÔÕφΘÖŌסŎӦᴏӧӨөӪӫΦθŐǑǪоǬȪȬʘΟϵȮȰОѲѳϘѺѻᵒϙȫϬϭфȭȯδȱόǫǭǒōФϕŏőòóοôσõöՓøØȌȎɵȍȏƤբƥÞþρᴘᵖΡƿԲǷРҎҏϷрϸɊɋԚԛգզԳʠϤϥ®ŔŖҐրґŘгѓЯʳʴʵʶʳɹɺɻɼɽӶӷԻɾɿʀՐՒʁяŕŗřƦȐɌɍȒȑȓƻƼƽƧƨŠʂϨЅϩˢšՏ§ŚŜŞŠȘȿșśŝşѕš†ŢТԎԏҬҭŤᴛтϮϯɫŦţᵗťτŧƫʇʈƬƭƮΤͲͳȾȚȶțƯưƱƲÙÚÛÜŨŪŬŮŰŲǓטɄǕǗǙǛȔȖȕȗǔᴜᵘǖϋՍύǘǚυǜũսūŭՄůűЦΰųùԱúûüʉЏʊƔᴠѴᵛѵѶѷνʋʌʍʷᴡѠѡѿŴԜԝшΨψϢϣωŵШώƜϗϰх×ҲҳχХӼӽΧƳƴӮӯӰӱӲӳÝΫŶŸϒҮүҰұϓϔȲץצУŷýÿγʸɎΎΥЎўʎʏɏɣɤ¥ȳуƵƶŽŹŻŽźżžȤΖʐʑɀȥžՀ',
    u'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaabbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbcccccccccccccccccccccccccccccccccccccdddddddddddddddddddeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeffffffffffffgggggggggggggggggggggggghhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiijjjjjjjjjjjjjjjjjkkkkkkkkkkkkkkkkkkkkkkkkkkkkkllllllllllllllllllllllllmmmmmmmmmmmmmmmmmmmnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnnoooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooooppppppppppppppppppqqqqqqqqqqrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrssssssssssssssssssssssssssttttttttttttttttttttttttttttttttuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuvvvvvvvvvvwwwwwwwwwwwwwwwwwwwxxxxxxxxxxxyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyzzzzzzzzzzzzzzzzz'
)

NO_REASON = 'No reason was specified at the time of this message -- once a moderator adds a reason this message will self-edit.'
NO_REASON_ENTRY = '*No reason yet. Please add one with `{}editReason {} reason goes here` as soon as possible.*'
NO_REASON_ENTRY_REGEX = r'\*No reason yet\. Please add one with `.+` as soon as possible\.\*'
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
KICK_MESSAGE = "Heyo, {}!\n\nThis is just to let you know you've been kicked from the {} " \
                "Discord server by a moderator, and that this has been marked down officially. Here's the reason:\n```{}```\n" \
                "As a refresher, we recommend re-reading the Discord server's rules so you're familiar with the way we run " \
                "things there if you decide to rejoin. We'd love to have you back, as long as you stay Toony!"
KICK_MESSAGE_FAILURE = PUNISHMENT_MESSAGE_FAILURE.format('kick')
KICK_FAILURE = "Could not kick the user. This is probably bad. Please use Discord's built-in moderation tools to enforce the punishment."
TEMPORARY_BAN_MESSAGE = "Hey there, {}.\n\nThis is just to let you know you've been temporarily banned from the " \
                    "{} Discord server by a moderator for **{}**, and that this has been marked down officially. Here's " \
                    "the reason:\n```{}```\nAs a refresher, we recommend re-reading the Discord server's rules so you're familiar " \
                    "with the way we run things there if you decide to rejoin after your ban. We'd love to have you back, as long as you stay Toony!"
TEMPORARY_BAN_MESSAGE_FAILURE = PUNISHMENT_MESSAGE_FAILURE.format('temporary ban')
PERMANENT_BAN_MESSAGE = "Hey there, {}.\n\nThis is just to let you know you've been permanently banned from the {} Discord server by " \
                    "a moderator. Here's the reason:\n```{}```\nIf you feel this is illegitimate, please contact one of our mods. Thank you for chatting with us!"
PERMANENT_BAN_MESSAGE_FAILURE = PUNISHMENT_MESSAGE_FAILURE.format('permanent ban')
BAN_FAILURE = "Could not ban the user. This is probably bad. You should use Discord's built-in moderation tools to enforce the ban."

WORD_FILTER_ENTRY = 'Removed{}message from {} in {}: {}'
WORD_FILTER_EMBED_ENTRY = "Removed{}message from {} in {}: {}\nThe embed {} contained: {}"
WORD_FILTER_MESSAGE = "Hey there, {}! This is just to let you know that you've said the blacklisted word `{}`, and to make clear " \
                    "that it's not an allowed word on this server. No automated action has been taken, but continued usage of the word or trying to circumvent the filter may " \
                    "result in additional punishment, depending on any previous punishments that you have received. We'd love to have you chat with us, as long as you stay Toony!"
IMAGE_FILTER_REASON = 'Posting Inappropriate Content **[Rating: {}]**'
IMAGE_FILTER_REVIEW = '{} posted an image in {} that has been registered as possibly bad. **[Rating: {}]**\n' \
                    '*If the image has bad content in it, please act accordingly.*\n{}'

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

            badwords = Config.getModuleSetting('moderation', 'bad_words')
            if word in badwords:
                return module.createDiscordEmbed(info='**{}** is already classified as a bad word'.format(word), color=discord.Color.dark_orange())
            badwords.append(word)
            Config.setModuleSetting('moderation', 'bad_words', badwords)
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

            badwords = Config.getModuleSetting('moderation', 'bad_words')
            if word not in badwords:
                return module.createDiscordEmbed(info='**{}** was never a bad word.'.format(word), color=discord.Color.dark_orange())
            badwords.remove(word)
            Config.setModuleSetting('moderation', 'bad_words', badwords)
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

    class AddWordExceptionCMD(Command):
        NAME = 'addWordException'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            word = ' '.join(args).strip()
            if not word:
                return

            exc = Config.getModuleSetting('moderation', 'word_exceptions')
            if word in exc:
                return module.createDiscordEmbed(info='**{}** is already classified as a bad word exception.'.format(word), color=discord.Color.dark_orange())
            exc.append(word)
            Config.setModuleSetting('moderation', 'word_exceptions', exc)
            module.pluralExceptions = exc

            return module.createDiscordEmbed(info='**{}** was added as a bad word exception.'.format(word), color=discord.Color.green())

    class RemoveWordExceptionCMD(Command):
        NAME = 'removeWordException'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            word = ' '.join(args).strip()
            if not word:
                return

            exc = Config.getModuleSetting('moderation', 'word_exceptions')
            if word not in exc:
                return module.createDiscordEmbed(info='**{}** was never a bad word exception.'.format(word), color=discord.Color.dark_orange())
            exc.remove(word)
            Config.setModuleSetting('moderation', 'word_exceptions', exc)
            module.pluralExceptions = exc
            
            return module.createDiscordEmbed(info='**{}** was removed from the bad word exception list.'.format(word), color=discord.Color.green())

    class PunishCMD(Command):
        NAME = 'punish'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            user = await cls.getUserInPunishCMD(client, message, *args)
            if user.__class__ == CommandResponse:
                return user
            return await module.punishUser(user, reason=' '.join(args[1:]), message=message)

        @classmethod
        async def getUserInPunishCMD(cls, client, message, *args):
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
            return user

    class SilentPunishCMD(PunishCMD):
        NAME = 'silentPunish'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            user = await cls.getUserInPunishCMD(client, message, *args)
            if user.__class__ == CommandResponse:
                return user
            return await module.punishUser(user, reason=' '.join(args[1:]), silent=True, message=message)

    class WarnCMD(PunishCMD):
        NAME = 'warn'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            user = await cls.getUserInPunishCMD(client, message, *args)
            if user.__class__ == CommandResponse:
                return user
            return await module.punishUser(user, reason=' '.join(args[1:]), punishment=module.WARNING, message=message)

    class SilentWarnCMD(PunishCMD):
        NAME = 'silentWarn'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            user = await cls.getUserInPunishCMD(client, message, *args)
            if user.__class__ == CommandResponse:
                return user
            return await module.punishUser(user, reason=' '.join(args[1:]), punishment=module.WARNING, silent=True, message=message)

    class KickCMD(PunishCMD):
        NAME = 'kick'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            user = await cls.getUserInPunishCMD(client, message, *args)
            if user.__class__ == CommandResponse:
                return user
            return await module.punishUser(user, reason=' '.join(args[1:]), punishment=module.KICK, message=message)

    class SilentKickCMD(PunishCMD):
        NAME = 'silentKick'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            user = await cls.getUserInPunishCMD(client, message, *args)
            if user.__class__ == CommandResponse:
                return user
            return await module.punishUser(user, reason=' '.join(args[1:]), punishment=module.KICK, silent=True, message=message)

    class TmpBanCMD(PunishCMD):
        NAME = 'tb'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            user = await cls.getUserInPunishCMD(client, message, *args)
            if user.__class__ == CommandResponse:
                return user
            return await module.punishUser(user, length=args[1] if len(args) > 1 else None, reason=' '.join(args[2:]), punishment=module.TEMPORARY_BAN, message=message)

    class SilentTmpBanCMD(PunishCMD):
        NAME = 'silentTB'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            user = await cls.getUserInPunishCMD(client, message, *args)
            if user.__class__ == CommandResponse:
                return user
            return await module.punishUser(user, length=args[1] if len(args) > 1 else None, reason=' '.join(args[2:]), punishment=module.TEMPORARY_BAN, silent=True, message=message)
    class SilentTmpBanCMD_Variant1(SilentTmpBanCMD):
        NAME = 'silentTb'
    class SilentTmpBanCMD_Variant2(SilentTmpBanCMD):
        NAME = 'silenttb'

    class PermBanCMD(PunishCMD):
        NAME = 'ban'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            user = await cls.getUserInPunishCMD(client, message, *args)
            if user.__class__ == CommandResponse:
                return user
            return await module.punishUser(user, reason=' '.join(args[1:]), punishment=module.PERMANENT_BAN, message=message)

    class SilentPermBanCMD(PunishCMD):
        NAME = 'silentBan'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            user = await cls.getUserInPunishCMD(client, message, *args)
            if user.__class__ == CommandResponse:
                return user
            return await module.punishUser(user, reason=' '.join(args[1:]), punishment=module.PERMANENT_BAN, silent=True, message=message)

    class EditPunishReasonCMD(Command):
        NAME = 'editReason'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            try:
                int(args[0])
            except (ValueError, IndexError) as e:
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
                            modLogEntryMessage = await client.get_channel(module.logChannel).get_message(punishment['modLogEntryID'])

                            # User Tracking
                            if modLogEntryMessage:
                                if modLogEntryMessage.embeds:
                                    modLogEntryEmbed = modLogEntryMessage.embeds[0]
                                    editedMessage = modLogEntryEmbed.fields[0].value
                                    if str(message.author.id) not in editedMessage:
                                        editedMessage = editedMessage.replace('**Mod:** <@!{}>'.format(mod.id), '**Mod:** <@!{}> (edited by <@!{}>)'.format(mod.id, message.author.id))
                                    editedMessage = re.sub(NO_REASON_ENTRY_REGEX, newReason, editedMessage)
                                    modLogEntryEmbed.set_field_at(0, name=modLogEntryEmbed.fields[0].name, value=editedMessage)
                                    await modLogEntryMessage.edit(embed=modLogEntryEmbed)
                                else:
                                    mod = modLogEntryMessage.mentions[0]
                                    editedMessage = modLogEntryMessage.content
                                    if mod.id != message.author.id:
                                        editedMessage = editedMessage.replace('**Mod:** <@!{}>'.format(mod.id), '**Mod:** <@!{}> (edited by <@!{}>)'.format(mod.id, message.author.id))
                                    editedMessage = re.sub(NO_REASON_ENTRY_REGEX, newReason, editedMessage)
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
            except (ValueError, IndexError) as e:
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

    class ViewBadWordsCMD(Command):
        NAME = 'viewBadWords'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            if not hasattr(module, 'words'):
                return "{} The bad word filter isn't turned on in the channel".format(message.author.mention)
            blacklistLength = len(module.words)
            words = sorted(module.words)
            for i in range(int(blacklistLength / 100) + 1):
                embed = module.createDiscordEmbed(
                    subtitle='Bad Words (Page {} of {})'.format(i + 1, int(blacklistLength / 100) + 1), 
                    info='\n'.join(words[100 * i:100 * (i + 1)])
                )
                await client.send_message(message.channel, embed)

    def __init__(self, client):
        Module.__init__(self, client)

        self.badWordFilterOn = Config.getModuleSetting('moderation', 'bad_word_filter', True)
        self.badImageFilterOn = Config.getModuleSetting('moderation', 'bad_image_filter', True) and ClarifaiApp
        self.spamChannel = Config.getModuleSetting('moderation', 'spam_channel')
        self.logChannel = Config.getModuleSetting('moderation', 'log_channel')
        self.filterBots = Config.getModuleSetting('moderation', 'filter_bots', False)
        self.filterMods = Config.getModuleSetting('moderation', 'filter_mods', True)
        self.allowBotPunishments = Config.getModuleSetting('moderation', 'allow_bot_punishments', False)
        self.allowModPunishments = Config.getModuleSetting('moderation', 'allow_mod_punishments', False)

        self.scheduledUnbans = []
        asyncio.get_event_loop().create_task(self.scheduleUnbans())

        if self.badWordFilterOn:
            self.words = [word.lower() for word in Config.getModuleSetting('moderation', 'bad_words')]
            self.filterExceptions = Config.getModuleSetting('moderation', 'filter_exceptions')
            self.pluralExceptions = Config.getModuleSetting('moderation', 'plural_exceptions')
            self.wordExceptions = Config.getModuleSetting('moderation', 'word_exceptions')

        if self.badImageFilterOn:
            gifKey = Config.getModuleSetting('moderation', 'clarifai_mod_key')
            if not gifKey:
                raise ValueError('Clarifai API Key could not be found ["clarifai_mod_key" in config.json]')
            self.imageFilterApp = ClarifaiApp(api_key=gifKey)
            self.generalImageFilter = self.imageFilterApp.models.get('moderation')
            self.nsfwImageFilter = self.imageFilterApp.models.get('nsfw-v1.0')

    async def punishUser(self, user, punishment=None, length=None, reason=NO_REASON, silent=False, message=None, snowflake=None):
        member = self.client.rTTR.get_member(user.id)

        if message:
            channel = message.channel
            author = message.author
            feedback = message.author.mention
            priorMessage = message
            snowflake = message.id
            message.nonce = 'silent'
            await message.delete()
        else:
            channel = self.logChannel
            author = self.client.rTTR.me
            feedback = self.logChannel
            priorMessage = None
            snowflake = snowflake

        if user.bot and not self.allowBotPunishments:
            return CommandResponse(
                channel,
                author.mention + ' ' + PUNISH_FAILURE_BOT,
                deleteIn=5,
                priorMessage=priorMessage
            )
        if Config.getRankOfMember(user) >= 300 and not self.allowModPunishments:
            return CommandResponse(
                channel,
                author.mention + ' ' + PUNISH_FAILURE_MOD,
                deleteIn=5,
                priorMessage=priorMessage
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
                channel, 
                author.mention + ' ' + PUNISH_FAILURE_NONMEMBER,
                deleteIn=5,
                priorMessage=priorMessage
            )

        # In case the reason provided by a command returns an empty string,
        # rather than the method argument default of NO_REASON.
        if not reason:
            reason = NO_REASON

        if length:
            lengthText = getLongTime(length)
            length = getShortTimeLength(length)
            nextPunishment = self.TEMPORARY_BAN  # Just asserts this if we have a time.
            if not 15 <= length <= 63113852:
                return CommandResponse(
                    channel,
                    author.mention + ' ' + PUNISH_FAILURE_TIMEFRAME,
                    deleteIn=5,
                    priorMessage=priorMessage
                )
        else:
            try:
                length = getShortTimeLength(reason.split(' ')[0])
                lengthText = getLongTime(reason.split(' ')[0])
                nextPunishment = self.TEMPORARY_BAN
                if not 15 <= length <= 63113852:
                    return CommandResponse(
                        channel,
                        author.mention + ' ' + PUNISH_FAILURE_TIMEFRAME,
                        deleteIn=5,
                        priorMessage=priorMessage
                    )
            except ValueError:
                length = 86400
                lengthText = '24 hours'

        # The user tracking module makes things prettier and consistent for displaying
        # information about users (embeds <3). We can fallback to text, though.
        usertracking = self.client.requestModule('usertracking')
        modLogEntry = None
        if self.logChannel:
            if not usertracking:
                modLogEntry = await self.client.send_message(self.logChannel, MOD_LOG_ENTRY.format(
                    str(user),
                    author.mention,
                    nextPunishment + (' ({})'.format(lengthText) if lengthText else ''),
                    NO_REASON_ENTRY.format(self.client.commandPrefix, snowflake) if reason == NO_REASON else reason,
                    snowflake
                    )
                )

        punishmentEntry = {
            'type': nextPunishment,
            'mod': author.id,
            'reason': reason,
            'modLogEntryID': modLogEntry.id if modLogEntry else None,
            'editID': snowflake,
            'created': time.time(),
            'noticeID': None
        }
        if nextPunishment == self.WARNING:
            punishMessage = WARNING_MESSAGE.format(user.mention, reason)
            messageFailed = WARNING_MESSAGE_FAILURE
            punishAction = None
            actionFailure = None
        elif nextPunishment == self.KICK:
            punishMessage = KICK_MESSAGE.format(user.mention, self.client.rTTR.name, reason)
            messageFailed = KICK_MESSAGE_FAILURE
            punishAction = self.client.rTTR.kick
            actionFailure = KICK_FAILURE
        elif nextPunishment == self.TEMPORARY_BAN:
            punishmentEntry['endTime'] = time.time() + length
            punishmentEntry['length'] = lengthText
            punishMessage = TEMPORARY_BAN_MESSAGE.format(user.mention, self.client.rTTR.name, lengthText, reason)
            messageFailed = TEMPORARY_BAN_MESSAGE_FAILURE
            punishAction = self.client.rTTR.ban
            actionFailure = BAN_FAILURE
        elif nextPunishment == self.PERMANENT_BAN:
            punishMessage = PERMANENT_BAN_MESSAGE.format(user.mention, self.client.rTTR.name, reason)
            messageFailed = PERMANENT_BAN_MESSAGE_FAILURE
            punishAction = self.client.rTTR.ban
            actionFailure = BAN_FAILURE

        if not silent and punishMessage:
            try:
                notice = await self.client.send_message(user, punishMessage)
                punishmentEntry['noticeID'] = notice.id
            except Exception as e:
                await self.client.send_message(author, messageFailed)
                print('Could not send {} notification message to {}'.format(nextPunishment.lower(), user.id))
        try:
            punishments.append(punishmentEntry)
            Users.setUserPunishments(user.id, punishments)
            if punishAction:
                await punishAction(user, reason=str(punishmentEntry['editID']))
            elif nextPunishment == self.WARNING:  # Can't do everything cleanly :(
                await usertracking.on_member_warn(user, punishmentEntry)
        except discord.HTTPException:
            await self.client.send_message(author, actionFailure)

        await self.scheduleUnbans()

    async def scheduleUnbans(self):
        for userID, user in Users.getUsers().items():
            for punishment in user['punishments']:
                if punishment['type'] == self.TEMPORARY_BAN:
                    if userID not in self.scheduledUnbans and punishment['endTime'] > time.time():
                        self.scheduledUnbans.append(userID)
                        await self.scheduledUnban(userID, punishment['endTime'])

    async def scheduledUnban(self, userID, endTime=None):
        user = await self.client.get_user_info(userID)
        if endTime:
            await asyncio.sleep(endTime - time.time())
        await self.client.rTTR.unban(user, reason='The user\'s temporary ban expired.')
        self.scheduledUnbans.remove(userID)

    def _testForBadWord(self, evadedWord):
        # Tests for a bad word against the provided word.
        # Runs through the config list after taking out unicode and non-alphabetic characters.
        response = {'word': None, 'evadedWord': evadedWord}

        word = evadedWord.translate(FILTER_EVASION_CHAR_MAP).lower()
        if word in self.wordExceptions:  # For example, "he'll" or "who're"
            return response

        word = re.sub(r'\W+', '', word)
        wordNoPlural = word.rstrip('s').rstrip('e')
        if word in self.words or (wordNoPlural in self.words and word not in self.pluralExceptions):
            response['word'] = word
        return response

    def _testForBadPhrase(self, evadedText):
        # This tests the text for bad phrases.
        # Bad phrases are essentially bad words with spaces in them.
        response = {'word': None, 'evadedWord': None}

        evadedText = evadedText.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        text = evadedText.translate(FILTER_EVASION_CHAR_MAP).lower()
        for phrase in filter(lambda word: ' ' in word, self.words):
            phrase = phrase.lower()  # Sanity check, you never know if a mod'll add caps to a bad word entry.
            phraseNoPlural = phrase.rstrip('s').rstrip('e')
            if (phrase == text or phraseNoPlural == text                                    # If the message is literally the phrase.
              or text.startswith(phrase + ' ') or text.startswith(phraseNoPlural + ' ')     # If the message starts with the phrase.
              or text.endswith(' ' + phrase) or text.endswith(' ' + phraseNoPlural)         # If the message ends in the phrase.
              or ' ' + phrase + ' ' in text or ' ' + phraseNoPlural + ' ' in text):         # If the message contains the phrase.
                textIndex = text.find(phrase)
                response['word'] = phrase
                response['evadedWord'] = evadedText[textIndex:textIndex + len(phrase)]
        return response

    def _testForBadWhole(self, evadedText):
        # This smooshes the whole message together (no spaces) and tests if it matches a bad word.
        text = evadedText.replace('\r', '').replace('\n', '').replace('\t', '').replace(' ', '')
        return self._testForBadWord(evadedText)

    async def _filterBadWords(self, message, evadedText, edited=' ', silentFilter=False, embed=None):
        response = {}
        for word in evadedText.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ').split(' '):
            wordResponse = self._testForBadWord(word)
            if wordResponse['word']:
                response = wordResponse
        phraseResponse = self._testForBadPhrase(evadedText)
        if not response and phraseResponse['word']:
            response = phraseResponse
        wholeResponse = self._testForBadWhole(evadedText)
        if not response and wholeResponse['word']:
            response = wholeResponse
        if not response:
            return False

        await self.client.delete_message(message)
        if self.spamChannel:
            message.nonce = 'filter'  # We're taking this variable because discord.py said it was nonimportant and it won't let me add any more custom attributes.
            usertracking = self.client.requestModule('usertracking')
            if usertracking:
                await usertracking.on_message_filter(message, word=response['evadedWord'], text=evadedText, embed=embed)
            else:
                wordFilterFormat = WORD_FILTER_EMBED_ENTRY if embed else WORD_FILTER_ENTRY
                await self.client.send_message(self.spamChannel, wordFilterFormat.format(
                    edited,
                    message.author.mention,
                    message.channel.mention,
                    message.content.replace(response['evadedWord'], '**' + response['evadedWord'] + '**'),
                    embed,
                    '**' + response['evadedWord'] + '**' if embed else ''
                ))
        try:
            if silentFilter:
                return True
            await self.client.send_message(message.author, WORD_FILTER_MESSAGE.format(message.author.mention, response['word']))
        except discord.HTTPException:
            print('Tried to send bad word filter notification message to a user, but Discord threw an HTTP Error:\n\n{}'.format(format_exc()))
        return True

    async def filterBadWords(self, message, edited=' ', silentFilter=False):
        if await self._filterBadWords(message, message.content, edited, silentFilter):
            return True
        for embed in message.embeds:
            for attr in [(embed.title, 'title'), (embed.description, 'description'), (embed.footer, 'footer'), (embed.author, 'author')]:
                if type(attr[0]) != str:
                    continue
                if await self._filterBadWords(message, attr[0], edited, silentFilter, embed=attr[1]):
                    return True
            for field in embed.fields:
                for fieldattr in [(field.name, 'field name'), (field.value, 'field value')]:
                    if type(fieldattr[0]) != str:
                        continue
                    if await self._filterBadWords(message, fieldattr[0], edited, silentFilter, embed=fieldattr[1]):
                        return True
        return False

    async def filterBadImages(self, message):
        # Refreshes embed info from the API.
        try:
            message = await message.channel.get_message(message.id)
        except discord.errors.NotFound:
            print('Tried to rediscover message {} to filter bad images but message wasn\'t found.'.format(message.id))

        if not message.embeds and not message.attachments:
            return

        for embed in message.embeds:
            if embed.type in ['image', 'gif', 'gifv']:
                rating = self.runImageFilter(embed.thumbnail.url, gif=True if embed.type in ['gif', 'gifv'] or embed.url.endswith('gif') else False)
                await self.determineImageRatingAction(message, rating, embed.url)

        for attachment in message.attachments:
            if any([attachment.filename.endswith(extension) for extension in ('.jpg', '.png', '.gif', '.bmp')]):
                rating = self.runImageFilter(attachment.url, gif=True if attachment.filename.endswith('.gif') or attachment.filename.endswith('.gifv') else False)
                await self.determineImageRatingAction(message, rating, attachment.url)

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
        usertracking = self.client.requestModule('usertracking')

        if rating > 1.5:
            rating = round(rating, 2)
            await self.client.delete_message(message)
            if usertracking:
                # On this specific instance, using `nonce` is more unreliable than usual.
                # We'll unhack it up later and figure out a better way. For the rest of them too.
                message.nonce = 'filter'  # See other code that edits `nonce` for explanation.
                await usertracking.on_message_filter(message)
            await self.punishUser(message.author, punishment=self.PERMANENT_BAN, reason=IMAGE_FILTER_REASON.format(rating), snowflake=message.id)
        elif rating > 1:
            rating = round(rating, 2)
            await self.client.delete_message(message)
            if usertracking:
                message.nonce = 'filter'
                await usertracking.on_message_filter(message)
            await self.punishUser(message.author, punishment=self.KICK, reason=IMAGE_FILTER_REASON.format(rating), snowflake=message.id)
        elif rating > .5:
            rating = round(rating, 2)
            if usertracking:
                await usertracking.on_message_review_filter(message, rating, url)
            else:
                await self.client.send_message(self.logChannel, IMAGE_FILTER_REVIEW.format(
                    message.author.mention, message.channel.mention, rating, url))
        # For debug.
        #else:
        #    rating = round(rating, 2)
        #   await self.client.send_message(self.spamChannel, "Image posted was fine. **[Rating: {}]**".format(rating))

    async def on_message(self, message):
        if message.channel.id in self.filterExceptions or message.author.id in self.filterExceptions or \
            (message.channel.__class__ == discord.DMChannel or (message.channel.category and message.channel.category.name.startswith('Lobby'))) or \
            (message.author.bot and not self.filterBots) or (Config.getRankOfMember(message.author) >= 300 and not self.filterMods):
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
        if message.channel.id in self.filterExceptions or message.author.id in self.filterExceptions or \
            (message.channel.__class__ == discord.DMChannel or (message.channel.category and message.channel.category.name.startswith('Lobby'))) or \
            (message.author.bot and not self.filterBots) or (Config.getRankOfMember(message.author) >= 300 and not self.filterMods):
            return

        # We'll only check for edited-in bad words for right now.
        try:
            if self.badWordFilterOn:
                await self.filterBadWords(message, edited=' edited ')
        except discord.errors.NotFound:
            print('Tried to remove edited message in bad word filter but message wasn\'t found.')
            return

module = ModerationModule