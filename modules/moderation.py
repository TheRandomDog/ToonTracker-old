# -*- coding: utf-8 -*-

import discord
import asyncio
import fnmatch
import time
import re
from extra.commands import Command, CommandResponse
from extra.startmessages import Warning
from modules.module import Module
from utils import Config, database, getShortTimeLength, getLongTime
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
NO_REASON_ENTRY_NOTE = '*No reason yet. Please add one with `{}editNote {} reason goes here` as soon as possible.*'
NO_REASON_ENTRY_REGEX = r'\*No reason yet\. Please add one with `.+` as soon as possible\.\*'
MOD_LOG_ENTRY = '**User:** {}\n**Mod:** {}\n**Punishment:** {}\n**Reason:** {}\n**Edit ID:** {}'

NOTE_FAILURE_BOT = "You cannot issue a note on a bot user."
NOTE_FAILURE_MOD = "You cannot issue a note on another mod."
NOTE_FAILURE_CONTENT = "Please provide the content of your note."
NOTE_LOG_ENTRY = '**User:** {}\n**Mod:** {}\n**Note:** {}\n**Edit ID:** {}'

PUNISH_FAILURE_BOT = "You cannot punish a bot user. Please use Discord's built-in moderation tools."
PUNISH_FAILURE_MOD = "You cannot punish another mod. Please use Discord's built-in moderation tools."
PUNISH_FAILURE_NONMEMBER = 'You cannot warn or kick a user who is not currently on the server. If severe enough, use a ban instead.'
PUNISH_FAILURE_TIMEFRAME = 'Please choose a time between 15s - 2y.'

PUNISHMENT_MESSAGE_FAILURE = "Could not send {} notification to the user (probably because they have DMs disabled for users/bots who don't share a server they're in)."
WARNING_MESSAGE = "Heyo, {}!\n\nThis is just to let you know you've been given a warning by a moderator " \
                "and that this been marked down officially. Here's the reason:\n```{}```\nAs a refresher, we recommend re-reading " \
                "the Discord server's rules so you're familiar with the way we run things there. Thank you!"
WARNING_MESSAGE_FAILURE = PUNISHMENT_MESSAGE_FAILURE.format('warning')
KICK_MESSAGE = "Hey there, {}!\n\nThis is just to let you know you've been kicked from the {} " \
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

MUTE_MESSAGE = "Hey there, {}!\n\nThis is just to let you know you've been muted on the {} Discord server by a moderator for **{}**, and that this " \
            "has been marked down officially. Here's the reason:\n```{}```\nAs a refresher, we recommend re-reading the Discord server's rules so " \
            "you're familar with the way we run things there when you're unmuted. We'd love to have you back, as long as you stay Toony!"
MUTE_MESSAGE_FAILURE = PUNISHMENT_MESSAGE_FAILURE.format('mute')

WORD_FILTER_ENTRY = 'Removed{}message from {} in {}: {}'
WORD_FILTER_EMBED_ENTRY = "Removed{}message from {} in {}: {}\nThe embed {} contained: {}"
WORD_FILTER_MESSAGE = "Hey there, {}! This is just to let you know that you've said the blacklisted word `{}`, and to make clear " \
                    "that it's not an allowed word on this server. No automated action has been taken, but continued usage of the word or trying to circumvent the filter may " \
                    "result in additional punishment, depending on any previous punishments that you have received. We'd love to have you chat with us, as long as you stay Toony!"
LINK_FILTER_ENTRY = 'Removed{}message from {} in {}: {}'
LINK_FILTER_EMBED_ENTRY = "Removed{}message from {} in {}: {}\nThe embed {} contained: {}"
LINK_FILTER_MESSAGE = "Hey there, {}! This is just to let you know that you've linked to a website that we don't allow. No automated action has " \
                    "been taken, but continuing to use the link or trying to circumvent the filter may result in additional punishment, depending " \
                    "on any previous punishments that you have received. We'd love to have you chat with us, as long as you stay Toony!"
IMAGE_FILTER_REASON = 'Posting Inappropriate Content **[Rating: {}]**'
IMAGE_FILTER_REVIEW = '{} posted an image in {} that has been registered as possibly bad. **[Rating: {}]**\n' \
                    '*If the image has bad content in it, please act accordingly.*\n{}'
NICKNAME_FILTER_ENTRY = 'Changed inappropriate nickname from {}: {}'
NICKNAME_FILTER_MESSAGE = "Hey there, {}! This is just to let you know your username or nickname contained the blacklist word `{}`, and to make clear " \
                        "that it's not an allowed word on this server. No automated action has been taken, but trying to change your nickname back or trying to cirvument the " \
                        "filter may result in additional punishment, depending on any previous punishments that you have received. We'd love to have you chat with us, as long as you stay Toony!"

class ModerationModule(Module):
    NAME = 'Moderation'
    
    WARNING = 'Warning'
    KICK = 'Kick'
    TEMPORARY_BAN = 'Temporary Ban'
    PERMANENT_BAN = 'Permanent Ban'
    MUTE = 'Mute'

    class AddBadLinkCMD(Command):
        """~addBadLink <url format>

        Adds a bad link format to the filter list. You can use wildcard characters.
        \t* = Matches multiple characters
        \t? = Matches any single character
        \t[seq] = Matches any character in `seq`
        \t[!seq] = Matches any character not in `seq`
        
        `https://discord.gg/*` -> Filters any Discord Invite link
        """
        NAME = 'addBadLink'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            link = ' '.join(args).strip().lower()
            if not link:
                return

            badlinks = module.badLinks
            matches = [badlink for badlink in badlinks if fnmatch.fnmatch(link, badlink)]
            if any([m==link for m in matches]):
                return module.createDiscordEmbed(info='**{}** is already classified as a bad link format.'.format(link), color=discord.Color.dark_orange())
            elif matches:
                return module.createDiscordEmbed(info='**{}** is already matched under **{}**'.format(link, matches[0]), color=discord.Color.dark_orange())
            badlinks.append(link)
            Config.setModuleSetting('moderation', 'bad_links', badlinks)
            module.badLinks = badlink

            return module.createDiscordEmbed(info='**{}** was added as a bad link format.'.format(link), color=discord.Color.green())

    class RemoveBadLinkCMD(Command):
        """~removeBadLink <url format>

        Removes a bad link format from the filter list. Be sure to use the format that was added exactly.
        """
        NAME = 'removeBadLink'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            link = ' '.join(args).strip().lower()
            if not link:
                return

            badlinks = module.badLinks
            if link not in badlinks:
                return module.createDiscordEmbed(info='**{}** is not a bad link format.\nBe sure to use the format that was added exactly.'.format(link), color=discord.Color.dark_orange())
            badlinks.remove(link)
            Config.setModuleSetting('moderation', 'bad_links', badlinks)
            module.badLinks = badlinks

            return module.createDiscordEmbed(info='**{}** was removed from the bad link list.'.format(link), color=discord.Color.green())

    class AddBadWordCMD(Command):
        """~addBadWord <word>

        Adds a bad word to the filter list. It can also be a phrase. This will also be checked in nicknames.
        Any emojis or links should be added with their respective commands.
        """
        NAME = 'addBadWord'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            word = ' '.join(args).strip().lower()
            if not word:
                return

            badwords = module.badWords
            if word in badwords:
                return module.createDiscordEmbed(info='**{}** is already classified as a bad word.'.format(word), color=discord.Color.dark_orange())
            badwords.append(word)
            Config.setModuleSetting('moderation', 'bad_words', badwords)
            module.badWords = badwords

            return module.createDiscordEmbed(info='**{}** was added as a bad word.'.format(word), color=discord.Color.green())

    class RemoveBadWordCMD(Command):
        """~removeBadWord <word>

        Removes a bad word from the filter list.
        """
        NAME = 'removeBadWord'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            word = ' '.join(args).strip()
            if not word:
                return

            badwords = module.badWords
            if word not in badwords:
                return module.createDiscordEmbed(info='**{}** was never a bad word.'.format(word), color=discord.Color.dark_orange())
            badwords.remove(word)
            Config.setModuleSetting('moderation', 'bad_words', badwords)
            module.badWords = badwords

            return module.createDiscordEmbed(info='**{}** was removed from the bad word list.'.format(word), color=discord.Color.green())

    class AddBadEmojiCMD(Command):
        """~addBadEmoji <emoji>
        
        Adds a bad emoji to the filter list. This will also be checked in nicknames and reactions. 
        """
        NAME = 'addBadEmoji'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            word = ' '.join(args).strip().lower()
            if not word:
                return

            badwords = module.badEmojis
            if word in badwords:
                return module.createDiscordEmbed(info='**{}** is already classified as a bad emoji.'.format(word), color=discord.Color.dark_orange())
            badwords.append(word)
            Config.setModuleSetting('moderation', 'bad_emojis', badwords)
            module.badEmojis = badwords

            return module.createDiscordEmbed(info='**{}** was added as a bad emoji.'.format(word), color=discord.Color.green())

    class RemoveBadEmojiCMD(Command):
        """~removeBadEmoji <emoji>

        Removes a bad emoji from the filter list.
        """
        NAME = 'removeBadEmoji'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            word = ' '.join(args).strip()
            if not word:
                return

            badwords = module.badEmojis
            if word not in badwords:
                return module.createDiscordEmbed(info='**{}** was never a bad emoji.'.format(word), color=discord.Color.dark_orange())
            badwords.remove(word)
            Config.setModuleSetting('moderation', 'bad_emojis', badwords)
            module.badEmojis = badwords

            return module.createDiscordEmbed(info='**{}** was removed from the bad word emoji list.'.format(word), color=discord.Color.green())

    class AddLinkExceptionCMD(Command):
        """~addLinkException <url>

        Adds a specific link as an exception to the bad link format filter list. Unlike adding a bad link, this takes a specific address, not a wildcard format.

        `https://discord.gg/toontown` -> An exception to a bad link that blocks all Discord Invite links.
        """
        NAME = 'addLinkException'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            word = ' '.join(args).strip()
            if not word:
                return

            exc = module.linkExceptions
            if word in exc:
                return module.createDiscordEmbed(info='**{}** is already classified as a bad link exception.'.format(word), color=discord.Color.dark_orange())
            exc.append(word)
            Config.setModuleSetting('moderation', 'link_exceptions', exc)
            module.linkExceptions = exc

            return module.createDiscordEmbed(info='**{}** was added as a bad link exception.'.format(word), color=discord.Color.green())

    class RemoveLinkExceptionCMD(Command):
        """~removeLinkException <url>

        Removes a specific link from being an exception to the bad link format filter list.
        """
        NAME = 'removeLinkException'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            word = ' '.join(args).strip()
            if not word:
                return

            exc = module.linkExceptions
            if word not in exc:
                return module.createDiscordEmbed(info='**{}** was never a bad link exception.'.format(word), color=discord.Color.dark_orange())
            exc.remove(word)
            Config.setModuleSetting('moderation', 'link_exceptions', exc)
            module.linkExceptions = exc
            
            return module.createDiscordEmbed(info='**{}** was removed from the bad link exception list.'.format(word), color=discord.Color.green())

    class AddPluralExceptionCMD(Command):
        """~addPluralException <plural exception>

        Adds a word as a plural exception to the bad word filter list.
        ToonTracker considers plurals when looking for words to filter by removing the letters `e` and `s` from the end of a word and seeing if it matches any bad words.
        If this ends up creating a false positive on a legitimate word, you can add the word that's causing a problem as a plural exception.
        """
        NAME = 'addPluralException'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            word = ' '.join(args).strip()
            if not word:
                return

            exc = module.pluralExceptions
            if word in exc:
                return module.createDiscordEmbed(info='**{}** is already classified as a plural exception.'.format(word), color=discord.Color.dark_orange())
            exc.append(word)
            Config.setModuleSetting('moderation', 'plural_exceptions', exc)
            module.pluralExceptions = exc

            return module.createDiscordEmbed(info='**{}** was added as a plural exception.'.format(word), color=discord.Color.green())

    class RemovePluralExceptionCMD(Command):
        """~removePluralException <plural exception>

        Removes a word from being a plural exception to the bad word filter list.
        """
        NAME = 'removePluralException'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            word = ' '.join(args).strip()
            if not word:
                return

            exc = module.pluralExceptions
            if word not in exc:
                return module.createDiscordEmbed(info='**{}** was never a plural exception.'.format(word), color=discord.Color.dark_orange())
            exc.remove(word)
            Config.setModuleSetting('moderation', 'plural_exceptions', exc)
            module.pluralExceptions = exc
            
            return module.createDiscordEmbed(info='**{}** was removed from the plural exception list.'.format(word), color=discord.Color.green())

    class AddWordExceptionCMD(Command):
        """~addWordException <word exception>

        Adds a word as an exception to the bad word filter list.
        ToonTracker will take out any characters from a word that aren't strictly letters when looking for bad words.
        If a word relies on punctuation for a different meaning than a bad word, you can add the word that's causing a problem as a word exception.

        `he'll` -> hell
        `who're` -> whore
        """
        NAME = 'addWordException'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            word = ' '.join(args).strip()
            if not word:
                return

            exc = module.wordExceptions
            if word in exc:
                return module.createDiscordEmbed(info='**{}** is already classified as a bad word exception.'.format(word), color=discord.Color.dark_orange())
            exc.append(word)
            Config.setModuleSetting('moderation', 'word_exceptions', exc)
            module.wordExceptions = exc

            return module.createDiscordEmbed(info='**{}** was added as a bad word exception.'.format(word), color=discord.Color.green())

    class RemoveWordExceptionCMD(Command):
        """~removeWordException <word exception>

        Removes a word from being an exception to the bad word filter list.
        """
        NAME = 'removeWordException'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            word = ' '.join(args).strip()
            if not word:
                return

            exc = module.wordExceptions
            if word not in exc:
                return module.createDiscordEmbed(info='**{}** was never a bad word exception.'.format(word), color=discord.Color.dark_orange())
            exc.remove(word)
            Config.setModuleSetting('moderation', 'word_exceptions', exc)
            module.wordExceptions = exc
            
            return module.createDiscordEmbed(info='**{}** was removed from the bad word exception list.'.format(word), color=discord.Color.green())

    class SlowmodeCMD(Command):
        """~slowmode [channel] <number>

        Enables slowmode in the specified channel (or the channel the message is sent from, if no channel is specified).
        A user will only be able to send messages once per every `<number` seconds.
        You can disable slowmode by saying `off` instead of a number.
        """
        NAME = 'slowmode'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            if message.channel_mentions:
                channel = message.channel_mentions[0]
            else:
                channel = message.channel

            speed = None
            if not args:
                speed = -1
            for arg in args:
                if arg.isdigit():
                    speed = -1 if not arg else int(arg)
                    break
                elif arg == 'off':
                    speed = -1
                    break
            if not speed or speed > 120:
                return CommandResponse(
                    message.channel,
                    '{} Please use a number (up to 120) to represent how many seconds needs to pass before a user can send another message. To turn off slowmode, use `~slowmode off`.'.format(message.author.mention),
                    deleteIn=5,
                    priorMessage=message
                )

            oldSpeed = channel.slowmode_delay
            if speed == -1:
                if not oldSpeed:
                    return CommandResponse(
                        message.channel,
                        '{} This channel isn\'t in slowmode!'.format(message.author.mention),
                        deleteIn=5,
                        priorMessage=message
                    )
                await channel.edit(slowmode_delay=0, reason='Moderator requested')
                message.nonce = 'silent'
                await message.delete()
                await channel.send(embed=module.createDiscordEmbed(
                    info=':rabbit2: You\'re back up to regular speed! Happy chatting!',
                    color=discord.Color.green()
                ))
            else:
                await channel.edit(slowmode_delay=speed, reason='Moderator requested')
                message.nonce = 'silent'
                await message.delete()
                await channel.send(embed=module.createDiscordEmbed(
                    info=':turtle: This channel has been slooooooowed doooown.' if oldSpeed <= speed else ':rabbit2: This channel has been sped up, but not completely.',
                    footer='You may only send a message every {} seconds.'.format(speed),
                    color=discord.Color.red()
                ))
    class SlowmodeOffCMD(SlowmodeCMD):
        NAME = 'slowoff'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            await super(cls, cls).execute(client, module, message, 'off')

    class ClearCMD(Command):
        """~clear <number of messages to check> [by author | containing *w?rds*]

            Clears a specified number of messages from the channel the command is used in.

            If a filter is specified as the second argument, the first specified number of
            messages will be checked to see if they match the given filter...
            \teither by author (@mention),
            \tor a pattern-matched word sequence
        """
        NAME = 'clear'
        RANK = 300
        DELETE_PRIOR_MESSAGE = True

        @staticmethod
        async def execute(client, module, message, *args):
            if len(args) is 0 or not args[0].isdigit():
                return CommandResponse(message.channel, message.author.mention + ' ~clear requires a number of messages to check.', deleteIn=5)
            else:
                msgs = int(args[0])

            def matches(m):
                m.nonce = 'cleared'
                if message.mentions:
                    return m.author in message.mentions
                elif len(args) > 1:
                    return True if fnmatch.fnmatch(m.content, '*' + ' '.join(args[1:]) + '*') else False
                return True

            async with message.channel.typing():
                try:
                    await message.channel.purge(limit=msgs, check=matches)
                    return CommandResponse(message.channel, message.author.mention + " I've cleared the messages you requested.", deleteIn=5)
                except discord.HTTPException:
                    print('Tried to execute {}, but Discord raised an exception:\n\n{}'.format(
                        message.content, format_exc()
                    ))
                    return CommandResponse(message.channel, message.author.mention + " I couldn't get to all the messages, but I did the best I could.", deleteIn=5)


    class PunishCMD(Command):
        """~punish <userID / mention> <reason>

        Punishes a user based on their last received punishment.
        The scale goes as follows: `Warning -> Kick -> Temporary Ban (24h) -> Permanent Ban`

        The reason is sent to the user in their DMs if they have their DMs open. If you do not want the reason sent, use ~silentPunish in the same way.
        """
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

    class MuteCMD(PunishCMD):
        """~mute <userID / mention / channel> [length] <reason>

        If a user is mentioned, the user will be muted for the specified length (1 hour if no length is specified). This will prevent a user from typing in a text channel or speaking in a voice channel.
        
        If a channel is mentioned, the channel will be muted for the specified length (indefinitely if no length is specified). This will prevent anyone from typical to a text channel.
        """
        NAME = 'mute'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            user = await cls.getUserInPunishCMD(client, message, *args)
            channel = None
            if user.__class__ == CommandResponse:
                if message.channel_mentions:
                    user = None
                    channel = message.channel_mentions[0]
                else:
                    response = user
                    response.message = '{} Please use a mention to refer to a user or channel.'.format(message.author.mention)
                    return response
            try:
                getLongTime(args[1] if len(args) > 1 else '')
                length = args[1]
                lengthText = None
                reason = ' '.join(args[2:])
            except ValueError:
                length = None
                lengthText = None
                reason = ' '.join(args[1:])

            if user:
                return await module.punishUser(user, length=length, reason=reason, punishment=module.MUTE, message=message)
            elif channel and not channel.name.startswith('staff-'):
                punishment = module.punishments.select(where=['user=?', channel.id], limit=1)
                if punishment:
                    return CommandResponse(
                        message.channel,
                        "{} That channel is already muted.".format(message.author.mention),
                        deleteIn=5,
                        priorMessage=message
                    )
                if length:
                    lengthText = getLongTime(length)
                    length = getShortTimeLength(length)
                    if not 15 <= length <= 63113852:
                        return CommandResponse(
                            message.channel,
                            author.mention + ' ' + PUNISH_FAILURE_TIMEFRAME,
                            deleteIn=5,
                            priorMessage=priorMessage
                        )
                punishmentEntry = {
                    'user': channel.id,
                    'type': module.MUTE,
                    'mod': message.author.id,
                    'created': time.time(),
                    'end_time': time.time() + length if length else None,
                    'end_length': lengthText
                }
                module.punishments.insert(**punishmentEntry)
                discordModRole = discord.utils.get(client.rTTR.roles, name='Moderators')
                await channel.set_permissions(discordModRole, send_messages=True)
                await channel.set_permissions(client.rTTR.default_role, send_messages=False)
                await channel.send(embed=module.createDiscordEmbed(info=':mute: This channel has been temporarily muted.', color=discord.Color.red()))
                await module.scheduleUnmutes()

    class UnmuteCMD(Command):
        """~unmute <channel>

        Unmutes a previously muted channel.
        """
        NAME = 'unmute'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            try:
                if message.channel_mentions:
                    channel = message.channel_mentions[0]
                else:
                    channel = client.get_channel(int(args[0]))
                assert channel != None
            except (ValueError, IndexError, AssertionError) as e:
                return CommandResponse(
                    message.channel,
                    '{} Please use a mention to refer to a channel. If you meant to unmute a user, please use `~removePunishment`.'.format(message.author.mention),
                    deleteIn=5,
                    priorMessage=message
                )

            punishment = module.punishments.select(where=['user=?', channel.id], limit=1)
            if not punishment:
                return CommandResponse(message.channel, "{} That channel isn't muted!".format(message.author.mention), deleteIn=5, priorMessage=message)

            module.punishments.delete(where=['id=?', punishment['id']])
            await channel.set_permissions(client.rTTR.default_role, send_messages=True, reason='The channel was unmuted by a mod via ~unmute')
            await channel.send(embed=module.createDiscordEmbed(
                info=':loud_sound: This channel is now unmuted.',
                footer='Please avoid flooding the channel and follow the rules set in #welcome.',
                color=discord.Color.green()
            ))
            if channel.id in module.scheduledUnmutes:
                module.scheduledUnmutes.remove(channel.id)

    class NoteCMD(PunishCMD):
        """~note <userID / mention> <message>

        Leaves a note on a user's profile that can only be seen by moderators. All notes can be seen using ~lookup.
        """
        NAME = 'note'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            user = await cls.getUserInPunishCMD(client, message, *args)
            if user.__class__ == CommandResponse:
                return user

            member = client.rTTR.get_member(user.id)
            reason = ' '.join(args[1:])
            if not reason:
                return CommandResponse(
                    message.channel,
                    message.author.mention + ' ' + NOTE_FAILURE_CONTENT,
                    deleteIn=5,
                    priorMessage=message
                )
            if user.bot and not module.allowBotPunishments:
                return CommandResponse(
                    message.channel,
                    message.author.mention + ' ' + NOTE_FAILURE_BOT,
                    deleteIn=5,
                    priorMessage=message
                )
            if Config.getRankOfMember(user) >= 300 and not module.allowModPunishments:
                return CommandResponse(
                    message.channel,
                    message.author.mention + ' ' + NOTE_FAILURE_MOD,
                    deleteIn=5,
                    priorMessage=message
                )

            i = module.notes.insert(
                user=user.id,
                mod=message.author.id,
                log=None,
                content=reason,
                created=time.time()
            )
            note = module.notes.select(where=['id=?', i], limit=1)

            # The user tracking module makes things prettier and consistent for displaying
            # information about users (embeds <3). We can fallback to text, though.
            usertracking = module.client.requestModule('usertracking')
            modLogEntry = None
            if module.logChannel:
                if not usertracking:
                    modLogEntry = await client.send_message(module.logChannel, NOTE_LOG_ENTRY.format(
                        str(user),
                        author.mention,
                        reason,
                        note['id']
                        )
                    )
                    module.notes.update(where=['id=?', note['id']], log=modLogEntry.id)
                else:
                    modLogEntry = await usertracking.on_member_note(user, note)
            return CommandResponse(message.channel, ':thumbsup:', deleteIn=5, priorMessage=message)

    class WarnCMD(PunishCMD):
        """~warn <userID / mention> <reason>

        Sends a warning to the user.

        The reason is sent to the user in their DMs if they have their DMs open. If you do not want the reason sent, use ~silentWarn in the same way.
        """
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
        """~kick <userID / mention> <reason>

        Kicks the user from the Discord server.

        The reason is sent to the user in their DMs if they have their DMs open. If you do not want the reason sent, use ~silentKick in the same way.
        """
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
        """~tb <userID / mention> [length] <reason>

        Temporarily bans the user from the server for the length specified, or 24 hours if no length is specified.

        The reason is sent to the user in their DMs if they have their DMs open. If you do not want the reason sent, use ~silentTB in the same way.
        """
        NAME = 'tb'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            user = await cls.getUserInPunishCMD(client, message, *args)
            if user.__class__ == CommandResponse:
                return user
            try:
                getLongTime(args[1] if len(args) > 1 else '')
                length = args[1]
                reason = ' '.join(args[2:])
            except ValueError:
                length = None
                reason = ' '.join(args[1:])
            return await module.punishUser(user, length=length, reason=reason, punishment=module.TEMPORARY_BAN, message=message)

    class SilentTmpBanCMD(PunishCMD):
        NAME = 'silentTB'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            user = await cls.getUserInPunishCMD(client, message, *args)
            if user.__class__ == CommandResponse:
                return user
            try:
                getLongTime(args[1] if len(args) > 1 else '')
                length = args[1]
                reason = ' '.join(args[2:])
            except ValueError:
                length = None
                reason = ' '.join(args[1:])
            return await module.punishUser(user, length=length, reason=reason, punishment=module.TEMPORARY_BAN, silent=True, message=message)
    class SilentTmpBanCMD_Variant1(SilentTmpBanCMD):
        NAME = 'silentTb'
    class SilentTmpBanCMD_Variant2(SilentTmpBanCMD):
        NAME = 'silenttb'

    class PermBanCMD(PunishCMD):
        """~ban <userID / mention> <reason>

        Permanently bans the user from the server.

        The reason is sent to the user in their DMs if they have their DMs open. If you do not want the reason sent, use ~silentBan in the same way.
        """
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
        """~editReason <edit ID> <new reason>
        
        Changes the reason of a punishment. This will be reflected in the original log made to a log channel as well as in the DM sent to the punished user.
        Edit IDs can be obtained from ~lookup or the original log made to a log channel.
        """
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

            punishment = module.punishments.select(where=['id=?', args[0]], limit=1)
            if not punishment:
                return CommandResponse(message.channel, '{} The edit ID was not recognized.'.format(message.author.mention), deleteIn=5, priorMessage=message)

            if punishment['log']:
                logEntry = await client.get_channel(module.logChannel).get_message(punishment['log'])
                if logEntry:
                    editedMessage = logEntry.embeds[0].fields[0].value if logEntry.embeds else logEntry.content
                    if str(punishment['mod']) not in editedMessage:
                        editedMessage = editedMessage.replace('**Mod:** <@!{}>'.format(punishment['mod']), '**Mod:** <@!{}> (edited by <@!{}>)'.format(punishment['mod'], message.author.id))
                    if punishment['reason'] == NO_REASON:
                        editedMessage = re.sub(NO_REASON_ENTRY_REGEX, newReason, editedMessage)
                    else:
                        editedMessage = editedMessage.replace('**Reason:** ' + punishment['reason'], '**Reason:** ' + newReason)
                    if logEntry.embeds:
                        logEntry.embeds[0].set_field_at(0, name=logEntry.embeds[0].fields[0].name, value=editedMessage)
                        await logEntry.edit(embed=logEntry.embeds[0])
                    else:
                        await logEntry.edit(content=editedMessage)
            if punishment['notice']:
                user = await client.get_user_info(punishment['user'])
                if not user.dm_channel:
                    await user.create_dm()
                notice = await user.dm_channel.get_message(punishment['notice'])
                if notice:
                    editedMessage = notice.content.replace('```' + punishment['reason'] + '```', '```' + newReason + '```')
                    await notice.edit(content=editedMessage)
            module.punishments.update(where=['id=?', args[0]], reason=newReason)
            return CommandResponse(message.channel, ':thumbsup:', deleteIn=5, priorMessage=message)

    class EditNoteReasonCMD(Command):
        """~editNote <note id> <new message>
        
        Changes the content of a note. This will be reflected in the original log made to a log channel.
        Note IDs can be obtained frlom ~lookup or the original log made to a log channel.
        """
        NAME = 'editNote'
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

            note = module.notes.select(where=['id=?', args[0]], limit=1)
            if not note:
                return CommandResponse(message.channel, '{} The edit ID was not recognized.'.format(message.author.mention), deleteIn=5, priorMessage=message)

            if note['log']:
                logEntry = await client.get_channel(module.logChannel).get_message(note['log'])
                if logEntry:
                    editedMessage = logEntry.embeds[0].fields[0].value if logEntry.embeds else logEntry.content
                    if str(note['mod']) not in editedMessage:
                        editedMessage = editedMessage.replace('**Mod:** <@!{}>'.format(note['mod']), '**Mod:** <@!{}> (edited by <@!{}>)'.format(note['mod'], message.author.id))
                    editedMessage = editedMessage.replace('\n\n' + note['content'], '\n\n' + newReason)
                    if logEntry.embeds:
                        logEntry.embeds[0].set_field_at(0, name=logEntry.embeds[0].fields[0].name, value=editedMessage)
                        await logEntry.edit(embed=logEntry.embeds[0])
                    else:
                        await logEntry.edit(content=editedMessage)
            module.notes.update(where=['id=?', args[0]], content=newReason)
            return CommandResponse(message.channel, ':thumbsup:', deleteIn=5, priorMessage=message)

    class RemovePunishmentCMD(Command):
        """~removePunishment <edit ID>

        This removes a punishment from a user's record. The original log and DM sent to the user will be deleted, and a new log will be made to say the punishment was removed.
        Edit IDs can be obtained from ~lookup or the original log made to a log channel.
        """
        NAME = 'removePunishment'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            try:
                int(args[0])
            except (ValueError, IndexError) as e:
                return CommandResponse(message.channel, '{} Please use a proper edit ID.'.format(message.author.mention), deleteIn=5, priorMessage=message)

            punishment = module.punishments.select(where=['id=?', args[0]], limit=1)
            if not punishment:
                return CommandResponse(message.channel, '{} The edit ID was not recognized.'.format(message.author.mention), deleteIn=5, priorMessage=message)

            if punishment['log']:
                logEntry = await client.get_channel(module.logChannel).get_message(punishment['log'])
                if logEntry:
                    await logEntry.delete()
            if punishment['notice']:
                user = await client.get_user_info(punishment['user'])
                if not user.dm_channel:
                    await user.create_dm()
                notice = await user.dm_channel.get_message(punishment['notice'])
                if notice:
                    await notice.delete()
            module.punishments.delete(where=['id=?', args[0]])

            usertracking = client.requestModule('usertracking')
            await usertracking.on_member_unpunish(user, punishment)

            return CommandResponse(message.channel, ':thumbsup:', deleteIn=5, priorMessage=message)
    class RevokePunishmentCMD(RemovePunishmentCMD):
        NAME = 'revokePunishment'

    class RemoveNoteCMD(Command):
        """~removeNote <note ID>
        
        This removes a note from a user's record.
        Note IDs can be obtained frlom ~lookup or the original log made to a log channel.
        """
        NAME = 'removeNote'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            try:
                int(args[0])
            except (ValueError, IndexError) as e:
                return CommandResponse(message.channel, '{} Please use a proper edit ID.'.format(message.author.mention), deleteIn=5, priorMessage=message)

            note = module.notes.select(where=['id=?', args[0]], limit=1)
            if not note:
                return CommandResponse(message.channel, '{} The edit ID was not recognized.'.format(message.author.mention), deleteIn=5, priorMessage=message)

            if note['log']:
                logEntry = await client.get_channel(module.logChannel).get_message(note['log'])
                if logEntry:
                    await logEntry.delete()
            module.notes.delete(where=['id=?', args[0]])

            return CommandResponse(message.channel, ':thumbsup:', deleteIn=5, priorMessage=message)

    class ViewBadWordsCMD(Command):
        """~viewBadWords
    
        Lists all words in the bad word filter list.
        """
        NAME = 'viewBadWords'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            if not hasattr(module, 'badWords'):
                return "{} The bad word filter isn't turned on in the channel".format(message.author.mention)
            blacklistLength = len(module.badWords)
            words = sorted(module.badWords)
            for i in range(int(blacklistLength / 100) + 1):
                embed = module.createDiscordEmbed(
                    subtitle='Bad Words (Page {} of {})'.format(i + 1, int(blacklistLength / 100) + 1), 
                    info='\n'.join(words[100 * i:100 * (i + 1)])
                )
                await client.send_message(message.channel, embed)

    class ViewBadLinksCMD(Command):
        """~viewBadLinks

        Lists all url formats in the bad link filter list.
        """
        NAME = 'viewBadLinks'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            if not hasattr(module, 'badLinks'):
                return "{} The bad link filter isn't turned on in the channel".format(message.author.mention)
            blacklistLength = len(module.badLinks)
            links = sorted(module.badLinks, key=lambda x: x.lstrip('htps:/*?[!]w.'))
            for i in range(int(blacklistLength / 100) + 1):
                embed = module.createDiscordEmbed(
                    subtitle='Bad Words (Page {} of {})'.format(i + 1, int(blacklistLength / 100) + 1), 
                    info='\n'.join(['`' + str(l) + '`' for l in links[100 * i:100 * (i + 1)]])
                )
                await client.send_message(message.channel, embed)

    class ViewBadEmojisCMD(Command):
        """~viewBadEmojis

        Lists all emojis in the bad emoji filter list.
        """
        NAME = 'viewBadEmojis'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            if not hasattr(module, 'badWords'):
                return "{} The bad word filter isn't turned on in the channel".format(message.author.mention)
            blacklistLength = len(module.badEmojis)
            words = sorted(module.badEmojis)
            for i in range(int(blacklistLength / 100) + 1):
                embed = module.createDiscordEmbed(
                    subtitle='Bad Emojis (Page {} of {})'.format(i + 1, int(blacklistLength / 100) + 1), 
                    info='\n'.join(words[100 * i:100 * (i + 1)])
                )
                await client.send_message(message.channel, embed)

    def __init__(self, client):
        Module.__init__(self, client)

        self.punishments = database.createSection(self, 'punishments', {
            'id': [database.INT, database.PRIMARY_KEY],
            'created': database.INT,
            'mod': database.INT,
            'user': database.INT,
            'log': database.INT,
            'notice': database.INT,
            'end_time': database.INT,
            'end_length': database.TEXT,
            'reason': database.TEXT,
            'type': database.TEXT
        })
        self.notes = database.createSection(self, 'notes', {
            'id': [database.INT, database.PRIMARY_KEY],
            'created': database.INT,
            'mod': database.INT,
            'user': database.INT,
            'log': database.INT,
            'content': database.TEXT
        })
        self.muted = database.createSection(self, 'muted', {
            'id': [database.INT, database.PRIMARY_KEY],
            'mention_type': database.TEXT,
            'end_time': database.INT,
            'end_length': database.TEXT
        })

        self.badWordFilterOn = Config.getModuleSetting('moderation', 'bad_word_filter', True)
        self.badImageFilterOn = Config.getModuleSetting('moderation', 'bad_image_filter', True) and ClarifaiApp
        self.badLinkFilterOn = Config.getModuleSetting('moderation', 'bad_link_filter', True)
        self.spamChannel = Config.getModuleSetting('moderation', 'spam_channel')
        self.logChannel = Config.getModuleSetting('moderation', 'log_channel')
        self.filterBots = Config.getModuleSetting('moderation', 'filter_bots', False)
        self.filterMods = Config.getModuleSetting('moderation', 'filter_mods', True)
        self.allowBotPunishments = Config.getModuleSetting('moderation', 'allow_bot_punishments', False)
        self.allowModPunishments = Config.getModuleSetting('moderation', 'allow_mod_punishments', False)

        self.spamProtection = Config.getModuleSetting('moderation', 'spam_protection', False)
        self.spamTracking = {}
        self.floodProtection = Config.getModuleSetting('moderation', 'flood_protection', False)
        self.floodTracking = {}

        self.scheduledUnbans = []
        self.scheduledUnmutes = []
        self.mutedRole = discord.utils.get(self.client.rTTR.roles, name=Config.getModuleSetting('moderation', 'muted_role_name') or 'Muted')
        asyncio.get_event_loop().create_task(self.scheduleUnbans())
        asyncio.get_event_loop().create_task(self.scheduleUnmutes())

        self.slowmode = Config.getModuleSetting('moderation', 'slowmode', {})

        if self.badWordFilterOn:
            self.badWords = [word.lower() for word in Config.getModuleSetting('moderation', 'bad_words', [])]
            self.badEmojis = Config.getModuleSetting('moderation', 'bad_emojis', [])
            self.filterExceptions = Config.getModuleSetting('moderation', 'filter_exceptions', [])
            self.pluralExceptions = Config.getModuleSetting('moderation', 'plural_exceptions', [])
            self.wordExceptions = Config.getModuleSetting('moderation', 'word_exceptions', [])
        if self.badLinkFilterOn:
            self.badLinks = [link.lower() for link in Config.getModuleSetting('moderation', 'bad_links', [])]
            self.linkExceptions = Config.getModuleSetting('moderation', 'link_exceptions', [])

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
        if (Config.getRankOfMember(member) >= 300 or Config.getRankOfMember(user) >= 300) and not self.allowModPunishments:
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

            punishments = self.punishments.select('type', where=['user=?', user.id])
            for punishment in punishments:
                if punishment['type'] in punishmentScale and punishmentScale.index(punishment['type']) > punishmentScale.index(highestPunishment):
                    highestPunishment = punishment['type']
                    highestPunishmentJSON = punishment
            try:
                nextPunishment = punishmentScale[punishmentScale.index(highestPunishment) + 1]
            except IndexError:
                nextPunishment = punishmentScale[-1]
        # Otherwise, just go along with the specific punishment.
        else:
            nextPunishment = punishment

        # There's no real need to warn users who aren't on the server,
        # nor can we kick them if they aren't on the server. Can't mute 'em either.
        if not member and nextPunishment in (self.WARNING, self.KICK, self.MUTE):
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
            nextPunishment = self.TEMPORARY_BAN if nextPunishment not in (self.TEMPORARY_BAN, self.MUTE) else nextPunishment
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
                nextPunishment = self.TEMPORARY_BAN if nextPunishment not in (self.TEMPORARY_BAN, self.MUTE) else nextPunishment
                if not 15 <= length <= 63113852:
                    return CommandResponse(
                        channel,
                        author.mention + ' ' + PUNISH_FAILURE_TIMEFRAME,
                        deleteIn=5,
                        priorMessage=priorMessage
                    )
            except ValueError:
                if nextPunishment == self.MUTE:
                    length = 3600
                    lengthText = '1 hour'
                else:
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
            'user': user.id,
            'type': nextPunishment,
            'mod': author.id,
            'reason': reason,
            'log': modLogEntry.id if modLogEntry else None,
            'created': time.time(),
            'notice': None,
            'end_time': None,
            'end_length': None
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
            punishmentEntry['end_time'] = time.time() + length
            punishmentEntry['end_length'] = lengthText
            punishMessage = TEMPORARY_BAN_MESSAGE.format(user.mention, self.client.rTTR.name, lengthText, reason)
            messageFailed = TEMPORARY_BAN_MESSAGE_FAILURE
            punishAction = self.client.rTTR.ban
            actionFailure = BAN_FAILURE
        elif nextPunishment == self.PERMANENT_BAN:
            punishMessage = PERMANENT_BAN_MESSAGE.format(user.mention, self.client.rTTR.name, reason)
            messageFailed = PERMANENT_BAN_MESSAGE_FAILURE
            punishAction = self.client.rTTR.ban
            actionFailure = BAN_FAILURE
        elif nextPunishment == self.MUTE:
            punishmentEntry['end_time'] = time.time() + length
            punishmentEntry['end_length'] = lengthText
            punishMessage = MUTE_MESSAGE.format(user.mention, self.client.rTTR.name, lengthText, reason)
            messageFailed = MUTE_MESSAGE_FAILURE
            punishAction = None
            actionFailure = None

        if not silent and punishMessage:
            try:
                notice = await self.client.send_message(user, punishMessage)
                punishmentEntry['notice'] = notice.id
            except Exception as e:
                await self.client.send_message(author, messageFailed)
                print('Could not send {} notification message to {}'.format(nextPunishment.lower(), user.id))
        try:
            punishmentEntry['id'] = self.punishments.insert(**punishmentEntry)
            if punishAction:
                await punishAction(user, reason=str(punishmentEntry['id']))
            elif nextPunishment == self.WARNING:  # Can't do everything cleanly :(
                await usertracking.on_member_warn(user, punishmentEntry)
            elif nextPunishment == self.MUTE:
                if not self.mutedRole:
                    raise ValueError
                await member.add_roles(self.mutedRole, reason=str(punishmentEntry['id']))
        except (discord.HTTPException, ValueError):
            await self.client.send_message(author, actionFailure if actionFailure else 'The {} failed.'.format(nextPunishment.lower()))

        await self.scheduleUnbans()
        await self.scheduleUnmutes()

    async def scheduleUnbans(self):
        punishments = self.punishments.select(where=['type=?', self.TEMPORARY_BAN])
        for punishment in punishments:
            if punishment['user'] in self.scheduledUnbans or punishment['end_time'] <= time.time():
                continue  # Don't schedule an unban for someone already scheduled for one, or if the ban hasn't expired.
            permaBanned = self.punishments.select(where=['user=? AND type=?', punishment['user'], self.PERMANENT_BAN], limit=1)
            if permaBanned:
                continue  # Don't schedule an unban for someone who was since permanently banned.
            self.scheduledUnbans.append(punishment['user'])
            await self.scheduledUnban(punishment['user'], punishment['end_time'])

    async def scheduledUnban(self, userID, endTime=None):
        user = await self.client.get_user_info(userID)
        if endTime:
            await asyncio.sleep(endTime - time.time())
        await self.client.rTTR.unban(user, reason='The user\'s temporary ban expired.')
        self.scheduledUnbans.remove(userID)

    async def scheduleUnmutes(self):
        punishments = self.punishments.select(where=['type=?', self.MUTE])
        for punishment in punishments:
            if punishment['user'] in self.scheduledUnmutes or not punishment['end_time'] or punishment['end_time'] <= time.time():
                continue  # Don't schedule an unmute for someone already scheduled for one, or if the mute hasn't or won't expire(d).
            self.scheduledUnmutes.append(punishment['user'])
            await self.scheduledUnmute(punishment['user'], punishment['end_time'])

    async def scheduledUnmute(self, id, endTime=None):
        user = self.client.rTTR.get_member(id)
        channel = self.client.rTTR.get_channel(id)
        if endTime:
            await asyncio.sleep(endTime - time.time())
        if id not in self.scheduledUnmutes:  # The channel was prematurely unmuted.
            return
        if user:
            await user.remove_roles(self.mutedRole, reason='The user\'s mute expired.')
        elif channel:
            await channel.set_permissions(self.client.rTTR.default_role, send_messages=True, reason='The channel\'s mute expired.')
            await channel.send(embed=self.createDiscordEmbed(
                info=':loud_sound: This channel is now unmuted.',
                footer='Please avoid flooding the channel and follow the rules set in #welcome.',
                color=discord.Color.green()
            ))
            self.punishments.delete(where=['user=?', channel.id])
        self.scheduledUnmutes.remove(id)

    async def scheduleUnmuteFromSlowmode(self, channel, member, seconds):
        for _ in range(seconds):
            await asyncio.sleep(1)
            if str(channel.id) not in self.slowmode:
                break
        await channel.set_permissions(member, overwrite=None, reason='Slowmode expired')

    def _testForBadWord(self, evadedWord):
        # Tests for a bad word against the provided word.
        # Runs through the config list after taking out unicode and non-alphabetic characters.
        response = {'word': None, 'evadedWord': evadedWord}

        word = evadedWord.translate(FILTER_EVASION_CHAR_MAP).lower()
        if word in self.wordExceptions:  # For example, "he'll" or "who're"
            return response

        word = re.sub(r'\W+', '', word)
        wordNoPlural = word.rstrip('s').rstrip('e')
        if word in self.badWords or (wordNoPlural in self.badWords and word not in self.pluralExceptions):
            response['word'] = word
        return response

    def _testForBadPhrase(self, evadedText):
        # This tests the text for bad phrases.
        # Bad phrases are essentially bad words with spaces in them.
        response = {'word': None, 'evadedWord': None}

        evadedText = evadedText.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        text = evadedText.translate(FILTER_EVASION_CHAR_MAP).lower()
        for phrase in filter(lambda word: ' ' in word, self.badWords):
            phrase = phrase.lower()  # Sanity check, you never know if a mod'll add caps to a bad word entry.
            phraseNoPlural = phrase.rstrip('s').rstrip('e')
            if phraseNoPlural in self.pluralExceptions:
                phraseNoPlural = '~-=PLACEHOLDER=-~'
            if (phrase == text or phraseNoPlural == text                                    # If the message is literally the phrase.
              or text.startswith(phrase + ' ') or text.startswith(phraseNoPlural + ' ')     # If the message starts with the phrase.
              or text.endswith(' ' + phrase) or text.endswith(' ' + phraseNoPlural)         # If the message ends in the phrase.
              or ' ' + phrase + ' ' in text or ' ' + phraseNoPlural + ' ' in text):         # If the message contains the phrase.
                textIndex = text.find(phrase)
                if textIndex == -1: textIndex = text.find(phraseNoPlural)
                response['word'] = phrase
                response['evadedWord'] = evadedText[textIndex:textIndex + len(phrase)]
        return response

    def _testForBadWhole(self, evadedText):
        # This smooshes the whole message together (no spaces) and tests if it matches a bad word.
        text = evadedText.replace('\r', '').replace('\n', '').replace('\t', '').replace(' ', '')
        return self._testForBadWord(evadedText)

    def _testForBadEmoji(self, evadedText):
        # A simple check, naturally.
        response = {'word': None, 'evadedWord': None}

        evadedText = evadedText.replace('\r', '').replace('\n', '').replace('\t', '').replace(' ', '')
        for emoji in self.badEmojis:
            if emoji in evadedText:
                response['word'] = emoji
                response['evadedWord'] = emoji
        return response

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
        emojiResponse = self._testForBadEmoji(evadedText)
        if not response and emojiResponse['word']:
            response = emojiResponse
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

    async def _filterBadName(self, member, evadedText, silentFilter=False):
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
        emojiResponse = self._testForBadEmoji(evadedText)
        if not response and emojiResponse['word']:
            response = emojiResponse
        if not response:
            return False

        await member.edit(nick='{Change Your Nickname}')
        if self.spamChannel:
            usertracking = self.client.requestModule('usertracking')
            if usertracking:
                await usertracking.on_nickname_filter(member, word=response['evadedWord'], text=evadedText)
            else:
                nameFilterFormat = NICKNAME_FILTER_ENTRY
                await self.client.send_message(self.logChannel, nameFilterFormat.format(
                    member.mention,
                    member.display_name.replace(response['evadedWord'], '**' + response['evadedWord'] + '**'),
                ))
        try:
            if silentFilter:
                return True
            await self.client.send_message(member, NICKNAME_FILTER_MESSAGE.format(member.mention, response['word']))
        except discord.HTTPException:
            print('Tried to send bad name filter notification message to a user, but Discord threw an HTTP Error:\n\n{}'.format(format_exc()))
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

    async def filterBadLinks(self, message, edited=' ', silentFilter=False):
        response = None

        text = message.content.translate(FILTER_EVASION_CHAR_MAP).lower().replace(' ', '')
        for link in self.badLinks:
            if fnmatch.fnmatch(text, '*' + link + '*') and not any([linkException in text for linkException in self.linkExceptions]):
                response = link
        if not response:
            return False

        await self.client.delete_message(message)
        if self.spamChannel:
            message.nonce = 'filter'  # We're taking this variable because discord.py said it was nonimportant and it won't let me add any more custom attributes.
            usertracking = self.client.requestModule('usertracking')
            if usertracking:
                await usertracking.on_message_filter(message, link=True)
            else:
                await self.client.send_message(self.spamChannel, LINK_FILTER_ENTRY.format(
                    edited,
                    message.author.mention,
                    message.channel.mention,
                    message.content
                ))
        try:
            if silentFilter:
                return True
            await self.client.send_message(message.author, LINK_FILTER_MESSAGE.format(message.author.mention))
        except discord.HTTPException:
            print('Tried to send bad link filter notification message to a user, but Discord threw an HTTP Error:\n\n{}'.format(format_exc()))
        return True

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

        if self.spamProtection:
            spamAuthor = self.spamTracking.get(message.author, {})
            for msg in spamAuthor.keys():
                if not spamAuthor[msg]['count'] or time.time() - spamAuthor[msg]['time'] >= (self.spamProtection['minute_duration'] * 60):
                    del spamAuthor[msg]

            spamMessage = spamAuthor.get(message.content.lower(), {'time': 0, 'count': 0})
            if spamMessage['count'] == self.spamProtection['message_count'] - 2:
                await message.channel.send('{} Please stop spamming the same message.'.format(message.author.mention))
            elif spamMessage['count'] >= self.spamProtection['message_count']:
                await self.punishUser(
                    message.author,
                    punishment=self.spamProtection['action'],
                    length=self.spamProtection['punish_length'],
                    reason='Spamming'
                )
                spamMessage['count'] = -1

            spamMessage['time'] = time.time()
            spamMessage['count'] += 1
            spamAuthor[message.content.lower()] = spamMessage
            self.spamTracking[message.author] = spamAuthor

        if self.floodProtection:
            floodMessage = self.floodTracking.get(message.content.lower(), {'time': 0, 'count': 0, 'members': []})
            if floodMessage['time'] and (not floodMessage['count'] or time.time() - floodMessage['time'] >= (self.floodProtection['minute_duration'] * 60)):
                del self.floodTracking[message.content.lower()]

            if floodMessage['count'] == self.floodProtection['message_count'] - 3:
                await message.channel.send('Please stop spamming the same message.')
            elif floodMessage['count'] >= self.floodProtection['message_count']:
                for member in floodMessage['members']:
                    await self.punishUser(
                        member,
                        punishment=self.floodProtection['action'],
                        length=self.floodProtection['punish_length'],
                        reason='Flooding the server'
                    )
                if message.author not in floodMessage['members']:
                    await self.punishUser(
                        member,
                        punishment=self.floodProtection['action'],
                        length=self.floodProtection['punish_length'],
                        reason='Flooding the server'
                    )
                floodMessage['count'] = -1

            floodMessage['time'] = time.time()
            floodMessage['count'] += 1
            if message.author not in floodMessage['members']:
                floodMessage['members'].append(message.author)
            self.floodTracking[message.content.lower()] = floodMessage

        timeStart = time.time()
        try:
            filtered = None
            if self.badWordFilterOn:
                filtered = await self.filterBadWords(message)
            if not filtered and self.badLinkFilterOn:
                await self.filterBadLinks(message)
        except discord.errors.NotFound:
            print('Tried to remove message in bad word/link filter but message wasn\'t found.')
            return

        if str(message.channel.id) in self.slowmode:
            await message.channel.set_permissions(message.author, send_messages=False, reason='Slowmode triggered')
            await self.scheduleUnmuteFromSlowmode(message.channel, message.author, self.slowmode[str(message.channel.id)])
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
            filtered = None
            if self.badWordFilterOn:
                filtered = await self.filterBadWords(message, edited=' edited ')
            if not filtered and self.badLinkFilterOn:
                await self.filterBadLinks(message)
        except discord.errors.NotFound:
            print('Tried to remove edited message in bad word/link filter but message wasn\'t found.')
            return

    async def on_member_update(self, before, after):
        if self.badWordFilterOn:
            await self._filterBadName(after, after.display_name)

module = ModerationModule