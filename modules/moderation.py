# -*- coding: utf-8 -*-

import discord
import asyncio
import fnmatch
import time
import random
import re
from extra.commands import Command, CommandResponse
from extra.startmessages import Warning
from modules.module import Module
from utils import Config, database, get_short_time_length, get_long_time
from traceback import format_exc

messages = []

if Config.get_module_setting('moderation', 'bad_image_filter'):
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
PUNISH_FAILURE_NONMEMBER = 'You cannot warn, kick, or mute a user who is not currently on the server. If severe enough, use a ban instead.'
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
                        "that it's not an allowed word on this server. We've changed your nickname to something random, but trying to change your nickname back or trying to cirvument the " \
                        "filter may result in additional punishment, depending on any previous punishments that you have received. We'd love to have you chat with us, as long as you stay Toony!"
NICKNAME_FILTER_REPLACEMENTS = [
    'Prince Poppensong',
    'Domino Ruffleglow',
    'Lucky Dizzy Toppensticks',
    'Rover Frazzleburger',
    'Deputy Leo Fumblewhatsit',
    'Spotty Glitterbumper',
    'Fluffy Mizzenfussen',
    'Dr. Jellyroll Laffenfluff',
    'Doctor Gale Jinglescooter',
    'Winnie Sourgadget',
    'Grumpy Phil',
    'Scooter Wildteeth',
    'Master Wildblabber',
    "Good ol' Kit Fuzzysocks",
    'Cricket Palewicket',
    'Rollie Zillerthud',
    'Judge Chirpy Jiffytooth',
    'Freckles Whiskerloop',
    'Count Dynocrump',
    'Zany Peppermarble',
    'Master Harry Swinklebubble',
    'Star Peppergrump',
    'Scooter Razzlenerd'
]

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

            badlinks = module.bad_links
            matches = [badlink for badlink in badlinks if fnmatch.fnmatch(link, badlink)]
            if any([m==link for m in matches]):
                return module.create_discord_embed(info='**{}** is already classified as a bad link format.'.format(link), color=discord.Color.dark_orange())
            elif matches:
                return module.create_discord_embed(info='**{}** is already matched under **{}**'.format(link, matches[0]), color=discord.Color.dark_orange())
            badlinks.append(link)
            Config.set_module_setting('moderation', 'bad_links', badlinks)
            module.bad_links = badlinks

            return module.create_discord_embed(info='**{}** was added as a bad link format.'.format(link), color=discord.Color.green())

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

            badlinks = module.bad_links
            if link not in badlinks:
                return module.create_discord_embed(info='**{}** is not a bad link format.\nBe sure to use the format that was added exactly.'.format(link), color=discord.Color.dark_orange())
            badlinks.remove(link)
            Config.set_module_setting('moderation', 'bad_links', badlinks)
            module.bad_links = badlinks

            return module.create_discord_embed(info='**{}** was removed from the bad link list.'.format(link), color=discord.Color.green())

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

            badwords = module.bad_words
            if word in badwords:
                return module.create_discord_embed(info='**{}** is already classified as a bad word.'.format(word), color=discord.Color.dark_orange())
            badwords.append(word)
            Config.set_module_setting('moderation', 'bad_words', badwords)
            module.bad_words = badwords

            return module.create_discord_embed(info='**{}** was added as a bad word.'.format(word), color=discord.Color.green())

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

            badwords = module.bad_words
            if word not in badwords:
                return module.create_discord_embed(info='**{}** was never a bad word.'.format(word), color=discord.Color.dark_orange())
            badwords.remove(word)
            Config.set_module_setting('moderation', 'bad_words', badwords)
            module.bad_words = badwords

            return module.create_discord_embed(info='**{}** was removed from the bad word list.'.format(word), color=discord.Color.green())

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

            badwords = module.bad_emojis
            if word in badwords:
                return module.create_discord_embed(info='**{}** is already classified as a bad emoji.'.format(word), color=discord.Color.dark_orange())
            badwords.append(word)
            Config.set_module_setting('moderation', 'bad_emojis', badwords)
            module.bad_emojis = badwords

            return module.create_discord_embed(info='**{}** was added as a bad emoji.'.format(word), color=discord.Color.green())

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

            badwords = module.bad_emojis
            if word not in badwords:
                return module.create_discord_embed(info='**{}** was never a bad emoji.'.format(word), color=discord.Color.dark_orange())
            badwords.remove(word)
            Config.set_module_setting('moderation', 'bad_emojis', badwords)
            module.bad_emojis = badwords

            return module.create_discord_embed(info='**{}** was removed from the bad word emoji list.'.format(word), color=discord.Color.green())

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

            exc = module.link_exceptions
            if word in exc:
                return module.create_discord_embed(info='**{}** is already classified as a bad link exception.'.format(word), color=discord.Color.dark_orange())
            exc.append(word)
            Config.set_module_setting('moderation', 'link_exceptions', exc)
            module.link_exceptions = exc

            return module.create_discord_embed(info='**{}** was added as a bad link exception.'.format(word), color=discord.Color.green())

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

            exc = module.link_exceptions
            if word not in exc:
                return module.create_discord_embed(info='**{}** was never a bad link exception.'.format(word), color=discord.Color.dark_orange())
            exc.remove(word)
            Config.set_module_setting('moderation', 'link_exceptions', exc)
            module.link_exceptions = exc
            
            return module.create_discord_embed(info='**{}** was removed from the bad link exception list.'.format(word), color=discord.Color.green())

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

            exc = module.plural_exceptions
            if word in exc:
                return module.create_discord_embed(info='**{}** is already classified as a plural exception.'.format(word), color=discord.Color.dark_orange())
            exc.append(word)
            Config.set_module_setting('moderation', 'plural_exceptions', exc)
            module.plural_exceptions = exc

            return module.create_discord_embed(info='**{}** was added as a plural exception.'.format(word), color=discord.Color.green())

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

            exc = module.plural_exceptions
            if word not in exc:
                return module.create_discord_embed(info='**{}** was never a plural exception.'.format(word), color=discord.Color.dark_orange())
            exc.remove(word)
            Config.set_module_setting('moderation', 'plural_exceptions', exc)
            module.plural_exceptions = exc
            
            return module.create_discord_embed(info='**{}** was removed from the plural exception list.'.format(word), color=discord.Color.green())

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

            exc = module.word_exceptions
            if word in exc:
                return module.create_discord_embed(info='**{}** is already classified as a bad word exception.'.format(word), color=discord.Color.dark_orange())
            exc.append(word)
            Config.set_module_setting('moderation', 'word_exceptions', exc)
            module.word_exceptions = exc

            return module.create_discord_embed(info='**{}** was added as a bad word exception.'.format(word), color=discord.Color.green())

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

            exc = module.word_exceptions
            if word not in exc:
                return module.create_discord_embed(info='**{}** was never a bad word exception.'.format(word), color=discord.Color.dark_orange())
            exc.remove(word)
            Config.set_module_setting('moderation', 'word_exceptions', exc)
            module.word_exceptions = exc
            
            return module.create_discord_embed(info='**{}** was removed from the bad word exception list.'.format(word), color=discord.Color.green())

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
                    delete_in=5,
                    prior_message=message
                )

            old_speed = channel.slowmode_delay
            if speed == -1:
                if not old_speed:
                    return CommandResponse(
                        message.channel,
                        '{} This channel isn\'t in slowmode!'.format(message.author.mention),
                        delete_in=5,
                        prior_message=message
                    )
                await channel.edit(slowmode_delay=0, reason='Moderator requested')
                message.nonce = 'silent'
                await message.delete()
                await channel.send(embed=module.create_discord_embed(
                    info=':rabbit2: You\'re back up to regular speed! Happy chatting!',
                    color=discord.Color.green()
                ))
            else:
                await channel.edit(slowmode_delay=speed, reason='Moderator requested')
                message.nonce = 'silent'
                await message.delete()
                await channel.send(embed=module.create_discord_embed(
                    info=':turtle: This channel has been slooooooowed doooown.' if old_speed <= speed else ':rabbit2: This channel has been sped up, but not completely.',
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
                return CommandResponse(message.channel, message.author.mention + ' ~clear requires a number of messages to check.', delete_in=5)
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
                    return CommandResponse(message.channel, message.author.mention + " I've cleared the messages you requested.", delete_in=5)
                except discord.HTTPException:
                    print('Tried to execute {}, but Discord raised an exception:\n\n{}'.format(
                        message.content, format_exc()
                    ))
                    return CommandResponse(message.channel, message.author.mention + " I couldn't get to all the messages, but I did the best I could.", delete_in=5)


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
            user = await cls.get_user_in_punish_cmd(client, message, *args)
            if user.__class__ == CommandResponse:
                return user
            return await module.punish_user(user, reason=' '.join(args[1:]), message=message)

        @classmethod
        async def get_user_in_punish_cmd(cls, client, message, *args, want_member=False):
            if not message.mentions:
                if not message.raw_mentions:
                    try:
                        user = await client.get_user_info(int(args[0]))
                    except (ValueError, IndexError):
                        return CommandResponse(message.channel, '{} Please use a mention to refer to a user.'.format(message.author.mention), delete_in=5, prior_message=message)
                    except discord.NotFound:
                        return CommandResponse(message.channel, '{} Could not find user with ID `{}`'.format(message.author.mention, args[0]), delete_in=5, prior_message=message)
                else:
                    try:
                        user = await client.get_user_info(message.raw_mentions[0])
                    except discord.NotFound:
                        return CommandResponse(message.channel, '{} Could not find user with ID `{}`'.format(message.author.mention, message.raw_mentions[0]), delete_in=5, prior_message=message)   
            else:
                user = message.mentions[0]

            if want_member:
                member = client.focused_guild.get_member(user.id)
                return member or CommandResponse(
                    message.channel,
                    '{} The user must be on the server to use this command. *(If they are on the server, try to `~reload` and tell TRD to get his butt in gear.)*'.format(message.author.mention),
                    delete_in=10,
                    prior_message=message
                )
            else:
                return user

    class SilentPunishCMD(PunishCMD):
        NAME = 'silentPunish'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            user = await cls.get_user_in_punish_cmd(client, message, *args, want_member=True)
            if user.__class__ == CommandResponse:
                return user
            return await module.punish_user(user, reason=' '.join(args[1:]), silent=True, message=message)

    class MuteCMD(PunishCMD):
        """~mute <userID / mention / channel> [length] <reason>

        If a user is mentioned, the user will be muted for the specified length (1 hour if no length is specified). This will prevent a user from typing in a text channel or speaking in a voice channel.
        
        If a channel is mentioned, the channel will be muted for the specified length (indefinitely if no length is specified). This will prevent anyone from typical to a text channel.
        """
        NAME = 'mute'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            member = await cls.get_user_in_punish_cmd(client, message, *args, want_member=True)
            channel = None
            if member.__class__ == CommandResponse:
                if message.channel_mentions:
                    member = None
                    channel = message.channel_mentions[0]
                else:
                    response = member
                    response.message = '{} Please use a mention to refer to a user or channel.'.format(message.author.mention)
                    return response
            try:
                get_long_time(args[1] if len(args) > 1 else '')
                length = args[1]
                length_text = None
                reason = ' '.join(args[2:])
            except ValueError:
                length = None
                length_text = None
                reason = ' '.join(args[1:])

            if member:
                return await module.punish_user(member, length=length, reason=reason, punishment=module.MUTE, message=message)
            elif channel and not channel.name.startswith('staff-'):
                punishment = module.punishments.select(where=['user=?', channel.id], limit=1)
                if punishment:
                    return CommandResponse(
                        message.channel,
                        "{} That channel is already muted.".format(message.author.mention),
                        delete_in=5,
                        prior_message=message
                    )
                if length:
                    length_text = get_long_time(length)
                    length = get_short_time_length(length)
                    if not 15 <= length <= 63113852:
                        return CommandResponse(
                            message.channel,
                            author.mention + ' ' + PUNISH_FAILURE_TIMEFRAME,
                            delete_in=5,
                            prior_message=prior_message
                        )
                punishment_entry = {
                    'user': channel.id,
                    'type': module.MUTE,
                    'mod': message.author.id,
                    'created': time.time(),
                    'end_time': time.time() + length if length else None,
                    'end_length': length_text
                }
                module.punishments.insert(**punishment_entry)
                mod_role = discord.utils.get(client.focused_guild.roles, name='Moderators')
                await channel.set_permissions(mod_role, send_messages=True)
                await channel.set_permissions(client.focused_guild.default_role, send_messages=False)
                await channel.send(embed=module.create_discord_embed(info=':mute: This channel has been temporarily muted.', color=discord.Color.red()))
                await module.schedule_unmutes()

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
                    delete_in=5,
                    prior_message=message
                )

            punishment = module.punishments.select(where=['user=?', channel.id], limit=1)
            if not punishment:
                return CommandResponse(message.channel, "{} That channel isn't muted!".format(message.author.mention), delete_in=5, prior_message=message)

            module.punishments.delete(where=['id=?', punishment['id']])
            await channel.set_permissions(client.focused_guild.default_role, send_messages=True, reason='The channel was unmuted by a mod via ~unmute')
            await channel.send(embed=module.create_discord_embed(
                info=':loud_sound: This channel is now unmuted.',
                footer='Please avoid flooding the channel and follow the rules set in #welcome.',
                color=discord.Color.green()
            ))
            if channel.id in module.scheduled_unmutes:
                module.scheduled_unmutes.remove(channel.id)

    class NoteCMD(PunishCMD):
        """~note <userID / mention> <message>

        Leaves a note on a user's profile that can only be seen by moderators. All notes can be seen using ~lookup.
        """
        NAME = 'note'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            user = await cls.get_user_in_punish_cmd(client, message, *args)
            if user.__class__ == CommandResponse:
                return user

            reason = ' '.join(args[1:])
            if not reason:
                return CommandResponse(
                    message.channel,
                    message.author.mention + ' ' + NOTE_FAILURE_CONTENT,
                    delete_in=5,
                    prior_message=message
                )
            if user.bot and not module.allow_bot_punishments:
                return CommandResponse(
                    message.channel,
                    message.author.mention + ' ' + NOTE_FAILURE_BOT,
                    delete_in=5,
                    prior_message=message
                )
            if Config.get_rank_of_member(user) >= 300 and not module.allow_mod_punishments:
                return CommandResponse(
                    message.channel,
                    message.author.mention + ' ' + NOTE_FAILURE_MOD,
                    delete_in=5,
                    prior_message=message
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
            usertracking = module.client.request_module('usertracking')
            mod_log_entry = None
            if module.log_channel:
                if not usertracking:
                    mod_log_entry = await client.send_message(module.log_channel, NOTE_LOG_ENTRY.format(
                        str(user),
                        author.mention,
                        reason,
                        note['id']
                        )
                    )
                    module.notes.update(where=['id=?', note['id']], log=mod_log_entry.id)
                else:
                    mod_log_entry = await usertracking.on_member_note(user, note)
            return CommandResponse(message.channel, ':thumbsup:', delete_in=5, prior_message=message)

    class WarnCMD(PunishCMD):
        """~warn <userID / mention> <reason>

        Sends a warning to the user.

        The reason is sent to the user in their DMs if they have their DMs open. If you do not want the reason sent, use ~silentWarn in the same way.
        """
        NAME = 'warn'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            member = await cls.get_user_in_punish_cmd(client, message, *args, want_member=True)
            if member.__class__ == CommandResponse:
                return member
            return await module.punish_user(member, reason=' '.join(args[1:]), punishment=module.WARNING, message=message)

    class SilentWarnCMD(PunishCMD):
        NAME = 'silentWarn'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            member = await cls.get_user_in_punish_cmd(client, message, *args, want_member=True)
            if member.__class__ == CommandResponse:
                return member
            return await module.punish_user(member, reason=' '.join(args[1:]), punishment=module.WARNING, silent=True, message=message)

    class KickCMD(PunishCMD):
        """~kick <userID / mention> <reason>

        Kicks the user from the Discord server.

        The reason is sent to the user in their DMs if they have their DMs open. If you do not want the reason sent, use ~silentKick in the same way.
        """
        NAME = 'kick'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            member = await cls.get_user_in_punish_cmd(client, message, *args, want_member=True)
            if member.__class__ == CommandResponse:
                return member
            return await module.punish_user(member, reason=' '.join(args[1:]), punishment=module.KICK, message=message)

    class SilentKickCMD(PunishCMD):
        NAME = 'silentKick'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            member = await cls.get_user_in_punish_cmd(client, message, *args, want_member=True)
            if member.__class__ == CommandResponse:
                return member
            return await module.punish_user(member, reason=' '.join(args[1:]), punishment=module.KICK, silent=True, message=message)

    class TmpBanCMD(PunishCMD):
        """~tb <userID / mention> [length] <reason>

        Temporarily bans the user from the server for the length specified, or 24 hours if no length is specified.

        The reason is sent to the user in their DMs if they have their DMs open. If you do not want the reason sent, use ~silentTB in the same way.
        """
        NAME = 'tb'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            user = await cls.get_user_in_punish_cmd(client, message, *args)
            if user.__class__ == CommandResponse:
                return user
            try:
                get_long_time(args[1] if len(args) > 1 else '')
                length = args[1]
                reason = ' '.join(args[2:])
            except ValueError:
                length = None
                reason = ' '.join(args[1:])
            return await module.punish_user(user, length=length, reason=reason, punishment=module.TEMPORARY_BAN, message=message)

    class SilentTmpBanCMD(PunishCMD):
        NAME = 'silentTB'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            user = await cls.get_user_in_punish_cmd(client, message, *args, want_member=True)
            if user.__class__ == CommandResponse:
                return member
            try:
                get_long_time(args[1] if len(args) > 1 else '')
                length = args[1]
                reason = ' '.join(args[2:])
            except ValueError:
                length = None
                reason = ' '.join(args[1:])
            return await module.punish_user(user, length=length, reason=reason, punishment=module.TEMPORARY_BAN, silent=True, message=message)
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
            user = await cls.get_user_in_punish_cmd(client, message, *args)
            if user.__class__ == CommandResponse:
                return user
            return await module.punish_user(user, reason=' '.join(args[1:]), punishment=module.PERMANENT_BAN, message=message)

    class SilentPermBanCMD(PunishCMD):
        NAME = 'silentBan'
        RANK = 300

        @classmethod
        async def execute(cls, client, module, message, *args):
            user = await cls.get_user_in_punish_cmd(client, message, *args)
            if user.__class__ == CommandResponse:
                return user
            return await module.punish_user(user, reason=' '.join(args[1:]), punishment=module.PERMANENT_BAN, silent=True, message=message)

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
                return CommandResponse(message.channel, '{} Please use a proper edit ID.'.format(message.author.mention), delete_in=5, prior_message=message)

            if not args[1:]:
                return CommandResponse(message.channel, '{} A reason must be given.'.format(message.author.mention), delete_in=5, prior_message=message)
            new_reason = ' '.join(args[1:])

            punishment = module.punishments.select(where=['id=?', args[0]], limit=1)
            if not punishment:
                return CommandResponse(message.channel, '{} The edit ID was not recognized.'.format(message.author.mention), delete_in=5, prior_message=message)

            if punishment['log']:
                log_entry = await client.get_channel(module.log_channel).get_message(punishment['log'])
                if log_entry:
                    edited_message = log_entry.embeds[0].fields[0].value if log_entry.embeds else log_entry.content
                    if str(punishment['mod']) not in edited_message:
                        edited_message = edited_message.replace('**Mod:** <@!{}>'.format(punishment['mod']), '**Mod:** <@!{}> (edited by <@!{}>)'.format(punishment['mod'], message.author.id))
                    if punishment['reason'] == NO_REASON:
                        edited_message = re.sub(NO_REASON_ENTRY_REGEX, new_reason, edited_message)
                    else:
                        edited_message = edited_message.replace('**Reason:** ' + punishment['reason'], '**Reason:** ' + new_reason)
                    if log_entry.embeds:
                        log_entry.embeds[0].set_field_at(0, name=log_entry.embeds[0].fields[0].name, value=edited_message)
                        await log_entry.edit(embed=log_entry.embeds[0])
                    else:
                        await log_entry.edit(content=edited_message)
            if punishment['notice']:
                user = await client.get_user_info(punishment['user'])
                if not user.dm_channel:
                    await user.create_dm()
                notice = await user.dm_channel.get_message(punishment['notice'])
                if notice:
                    edited_message = notice.content.replace('```' + punishment['reason'] + '```', '```' + new_reason + '```')
                    await notice.edit(content=edited_message)
            module.punishments.update(where=['id=?', args[0]], reason=new_reason)
            return CommandResponse(message.channel, ':thumbsup:', delete_in=5, prior_message=message)

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
                return CommandResponse(message.channel, '{} Please use a proper edit ID.'.format(message.author.mention), delete_in=5, prior_message=message)

            if not args[1:]:
                return CommandResponse(message.channel, '{} A reason must be given.'.format(message.author.mention), delete_in=5, prior_message=message)
            new_reason = ' '.join(args[1:])

            note = module.notes.select(where=['id=?', args[0]], limit=1)
            if not note:
                return CommandResponse(message.channel, '{} The edit ID was not recognized.'.format(message.author.mention), delete_in=5, prior_message=message)

            if note['log']:
                log_entry = await client.get_channel(module.log_channel).get_message(note['log'])
                if log_entry:
                    edited_message = log_entry.embeds[0].fields[0].value if log_entry.embeds else log_entry.content
                    if str(note['mod']) not in edited_message:
                        edited_message = edited_message.replace('**Mod:** <@!{}>'.format(note['mod']), '**Mod:** <@!{}> (edited by <@!{}>)'.format(note['mod'], message.author.id))
                    edited_message = edited_message.replace('\n\n' + note['content'], '\n\n' + new_reason)
                    if log_entry.embeds:
                        log_entry.embeds[0].set_field_at(0, name=log_entry.embeds[0].fields[0].name, value=edited_message)
                        await log_entry.edit(embed=log_entry.embeds[0])
                    else:
                        await log_entry.edit(content=edited_message)
            module.notes.update(where=['id=?', args[0]], content=new_reason)
            return CommandResponse(message.channel, ':thumbsup:', delete_in=5, prior_message=message)

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
                return CommandResponse(message.channel, '{} Please use a proper edit ID.'.format(message.author.mention), delete_in=5, prior_message=message)

            punishment = module.punishments.select(where=['id=?', args[0]], limit=1)
            if not punishment:
                return CommandResponse(message.channel, '{} The edit ID was not recognized.'.format(message.author.mention), delete_in=5, prior_message=message)

            if punishment['log']:
                log_entry = await client.get_channel(module.log_channel).get_message(punishment['log'])
                if log_entry:
                    await log_entry.delete()
            if punishment['notice']:
                user = await client.get_user_info(punishment['user'])
                if not user.dm_channel:
                    await user.create_dm()
                notice = await user.dm_channel.get_message(punishment['notice'])
                if notice:
                    await notice.delete()
                usertracking = client.request_module('usertracking')
                if usertracking:
                    await usertracking.on_member_unpunish(user, punishment)

            module.punishments.delete(where=['id=?', args[0]])
            return CommandResponse(message.channel, ':thumbsup:', delete_in=5, prior_message=message)
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
                return CommandResponse(message.channel, '{} Please use a proper edit ID.'.format(message.author.mention), delete_in=5, prior_message=message)

            note = module.notes.select(where=['id=?', args[0]], limit=1)
            if not note:
                return CommandResponse(message.channel, '{} The edit ID was not recognized.'.format(message.author.mention), delete_in=5, prior_message=message)

            if note['log']:
                log_entry = await client.get_channel(module.log_channel).get_message(note['log'])
                if log_entry:
                    await log_entry.delete()
            module.notes.delete(where=['id=?', args[0]])

            return CommandResponse(message.channel, ':thumbsup:', delete_in=5, prior_message=message)

    class ViewBadWordsCMD(Command):
        """~viewBadWords
    
        Lists all words in the bad word filter list.
        """
        NAME = 'viewBadWords'
        RANK = 300

        @staticmethod
        async def execute(client, module, message, *args):
            if not hasattr(module, 'bad_words'):
                return "{} The bad word filter isn't turned on in the channel".format(message.author.mention)
            blacklist_length = len(module.bad_words)
            words = sorted(module.bad_words)
            for i in range(int(blacklist_length / 100) + 1):
                embed = module.create_discord_embed(
                    subtitle='Bad Words (Page {} of {})'.format(i + 1, int(blacklist_length / 100) + 1), 
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
            if not hasattr(module, 'bad_links'):
                return "{} The bad link filter isn't turned on in the channel".format(message.author.mention)
            blacklist_length = len(module.bad_links)
            links = sorted(module.bad_links, key=lambda x: x.lstrip('htps:/*?[!]w.'))
            for i in range(int(blacklist_length / 100) + 1):
                embed = module.create_discord_embed(
                    subtitle='Bad Words (Page {} of {})'.format(i + 1, int(blacklist_length / 100) + 1), 
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
            if not hasattr(module, 'bad_words'):
                return "{} The bad word filter isn't turned on in the channel".format(message.author.mention)
            blacklist_length = len(module.bad_emojis)
            words = sorted(module.bad_emojis)
            for i in range(int(blacklist_length / 100) + 1):
                embed = module.create_discord_embed(
                    subtitle='Bad Emojis (Page {} of {})'.format(i + 1, int(blacklist_length / 100) + 1), 
                    info='\n'.join(words[100 * i:100 * (i + 1)])
                )
                await client.send_message(message.channel, embed)

    def __init__(self, client):
        Module.__init__(self, client)

        self.punishments = database.create_section(self, 'punishments', {
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
        self.notes = database.create_section(self, 'notes', {
            'id': [database.INT, database.PRIMARY_KEY],
            'created': database.INT,
            'mod': database.INT,
            'user': database.INT,
            'log': database.INT,
            'content': database.TEXT
        })
        self.muted = database.create_section(self, 'muted', {
            'id': [database.INT, database.PRIMARY_KEY],
            'mention_type': database.TEXT,
            'end_time': database.INT,
            'end_length': database.TEXT
        })

        self.bad_word_filter_on = Config.get_module_setting('moderation', 'bad_word_filter', True)
        self.bad_image_filter_on = Config.get_module_setting('moderation', 'bad_image_filter', True) and ClarifaiApp
        self.bad_link_filter_on = Config.get_module_setting('moderation', 'bad_link_filter', True)
        self.spam_channel = Config.get_module_setting('moderation', 'spam_channel')
        self.log_channel = Config.get_module_setting('moderation', 'log_channel')
        self.filter_bots = Config.get_module_setting('moderation', 'filter_bots', False)
        self.filter_mods = Config.get_module_setting('moderation', 'filter_mods', True)
        self.allow_bot_punishments = Config.get_module_setting('moderation', 'allow_bot_punishments', False)
        self.allow_mod_punishments = Config.get_module_setting('moderation', 'allow_mod_punishments', False)

        self.spam_protection = Config.get_module_setting('moderation', 'spam_protection', False)
        self.spam_tracking = {}
        self.flood_protection = Config.get_module_setting('moderation', 'flood_protection', False)
        self.flood_tracking = {}

        self.scheduled_unbans = []
        self.scheduled_unmutes = []
        self.muted_role = discord.utils.get(self.client.focused_guild.roles, name=Config.get_module_setting('moderation', 'muted_role_name') or 'Muted')
        asyncio.get_event_loop().create_task(self.schedule_unbans())
        asyncio.get_event_loop().create_task(self.schedule_unmutes())

        self.slowmode = Config.get_module_setting('moderation', 'slowmode', {})

        if self.bad_word_filter_on:
            self.bad_words = [word.lower() for word in Config.get_module_setting('moderation', 'bad_words', [])]
            self.bad_emojis = Config.get_module_setting('moderation', 'bad_emojis', [])
            self.filter_exceptions = Config.get_module_setting('moderation', 'filter_exceptions', [])
            self.plural_exceptions = Config.get_module_setting('moderation', 'plural_exceptions', [])
            self.word_exceptions = Config.get_module_setting('moderation', 'word_exceptions', [])
        if self.bad_link_filter_on:
            self.bad_links = [link.lower() for link in Config.get_module_setting('moderation', 'bad_links', [])]
            self.link_exceptions = Config.get_module_setting('moderation', 'link_exceptions', [])

        if self.bad_image_filter_on:
            gif_key = Config.get_module_setting('moderation', 'clarifai_mod_key')
            if not gif_key:
                raise ValueError('Clarifai API Key could not be found ["clarifai_mod_key" in config.json]')
            self.image_filter_app = ClarifaiApp(api_key=gif_key)
            self.general_image_filter = self.image_filter_app.models.get('moderation')
            self.nsfw_image_filter = self.image_filter_app.models.get('nsfw-v1.0')

    async def punish_user(self, user, punishment=None, length=None, reason=NO_REASON, silent=False, message=None, snowflake=None):
        member = self.client.focused_guild.get_member(user.id)

        if message:
            channel = message.channel
            author = message.author
            feedback = message.author.mention
            prior_message = message
            snowflake = message.id
            message.nonce = 'silent'
            await message.delete()
        else:
            channel = self.log_channel
            author = self.client.focused_guild.me
            feedback = self.log_channel
            prior_message = None
            snowflake = snowflake

        if user.bot and not self.allow_bot_punishments:
            return CommandResponse(
                channel,
                author.mention + ' ' + PUNISH_FAILURE_BOT,
                delete_in=5,
                prior_message=prior_message
            )
        if ((member and Config.get_rank_of_member(member) >= 300) or Config.get_rank_of_member(user) >= 300) and not self.allow_mod_punishments:
            return CommandResponse(
                channel,
                author.mention + ' ' + PUNISH_FAILURE_MOD,
                delete_in=5,
                prior_message=prior_message
            )

        # If a specific punishment isn't provided, use the next level of punishment
        # above the highest level of punishment they've already received.
        if not punishment:
            punishment_scale = [None, self.WARNING, self.KICK, self.TEMPORARY_BAN, self.PERMANENT_BAN]
            highest_punishment = None
            highest_punishment_json = None

            punishments = self.punishments.select('type', where=['user=?', user.id])
            for punishment in punishments:
                if punishment['type'] in punishment_scale and punishment_scale.index(punishment['type']) > punishment_scale.index(highest_punishment):
                    highest_punishment = punishment['type']
                    highest_punishment_json = punishment
            try:
                next_punishment = punishment_scale[punishment_scale.index(highest_punishment) + 1]
            except IndexError:
                next_punishment = punishment_scale[-1]
        # Otherwise, just go along with the specific punishment.
        else:
            next_punishment = punishment

        # There's no real need to warn users who aren't on the server,
        # nor can we kick them if they aren't on the server. Can't mute 'em either.
        if not member and next_punishment in (self.WARNING, self.KICK, self.MUTE):
            return CommandResponse(
                channel, 
                author.mention + ' ' + PUNISH_FAILURE_NONMEMBER,
                delete_in=5,
                prior_message=prior_message
            )

        # In case the reason provided by a command returns an empty string,
        # rather than the method argument default of NO_REASON.
        if not reason:
            reason = NO_REASON

        if length:
            length_text = get_long_time(length)
            length = get_short_time_length(length)
            next_punishment = self.TEMPORARY_BAN if next_punishment not in (self.TEMPORARY_BAN, self.MUTE) else next_punishment
            if not 15 <= length <= 63113852:
                return CommandResponse(
                    channel,
                    author.mention + ' ' + PUNISH_FAILURE_TIMEFRAME,
                    delete_in=5,
                    prior_message=prior_message
                )
        else:
            try:
                length = get_short_time_length(reason.split(' ')[0])
                length_text = get_long_time(reason.split(' ')[0])
                next_punishment = self.TEMPORARY_BAN if next_punishment not in (self.TEMPORARY_BAN, self.MUTE) else next_punishment
                if not 15 <= length <= 63113852:
                    return CommandResponse(
                        channel,
                        author.mention + ' ' + PUNISH_FAILURE_TIMEFRAME,
                        delete_in=5,
                        prior_message=prior_message
                    )
            except ValueError:
                if next_punishment == self.MUTE:
                    length = 3600
                    length_text = '1 hour'
                else:
                    length = 86400
                    length_text = '24 hours'

        # The user tracking module makes things prettier and consistent for displaying
        # information about users (embeds <3). We can fallback to text, though.
        usertracking = self.client.request_module('usertracking')
        mod_log_entry = None
        if self.log_channel:
            if not usertracking:
                mod_log_entry = await self.client.send_message(self.log_channel, MOD_LOG_ENTRY.format(
                    str(user),
                    author.mention,
                    next_punishment + (' ({})'.format(length_text) if length_text else ''),
                    NO_REASON_ENTRY.format(self.client.command_prefix, snowflake) if reason == NO_REASON else reason,
                    snowflake
                    )
                )

        punishment_entry = {
            'user': user.id,
            'type': next_punishment,
            'mod': author.id,
            'reason': reason,
            'log': mod_log_entry.id if mod_log_entry else None,
            'created': time.time(),
            'notice': None,
            'end_time': None,
            'end_length': None
        }
        if next_punishment == self.WARNING:
            punish_message = WARNING_MESSAGE.format(user.mention, reason)
            message_failed = WARNING_MESSAGE_FAILURE
            punish_action = None
            action_failure = None
        elif next_punishment == self.KICK:
            punish_message = KICK_MESSAGE.format(user.mention, self.client.focused_guild.name, reason)
            message_failed = KICK_MESSAGE_FAILURE
            punish_action = self.client.focused_guild.kick
            action_failure = KICK_FAILURE
        elif next_punishment == self.TEMPORARY_BAN:
            punishment_entry['end_time'] = time.time() + length
            punishment_entry['end_length'] = length_text
            punish_message = TEMPORARY_BAN_MESSAGE.format(user.mention, self.client.focused_guild.name, length_text, reason)
            message_failed = TEMPORARY_BAN_MESSAGE_FAILURE
            punish_action = self.client.focused_guild.ban
            action_failure = BAN_FAILURE
        elif next_punishment == self.PERMANENT_BAN:
            punish_message = PERMANENT_BAN_MESSAGE.format(user.mention, self.client.focused_guild.name, reason)
            message_failed = PERMANENT_BAN_MESSAGE_FAILURE
            punish_action = self.client.focused_guild.ban
            action_failure = BAN_FAILURE
        elif next_punishment == self.MUTE:
            punishment_entry['end_time'] = time.time() + length
            punishment_entry['end_length'] = length_text
            punish_message = MUTE_MESSAGE.format(user.mention, self.client.focused_guild.name, length_text, reason)
            message_failed = MUTE_MESSAGE_FAILURE
            punish_action = None
            action_failure = None

        if not silent and punish_message:
            try:
                notice = await self.client.send_message(user, punish_message)
                punishment_entry['notice'] = notice.id
            except Exception as e:
                await self.client.send_message(author, message_failed)
                print('Could not send {} notification message to {}'.format(next_punishment.lower(), user.id))
        try:
            punishment_entry['id'] = self.punishments.insert(**punishment_entry)
            if punish_action:
                await punish_action(user, reason=str(punishment_entry['id']))
            elif next_punishment == self.WARNING:  # Can't do everything cleanly :(
                await usertracking.on_member_warn(user, punishment_entry)
            elif next_punishment == self.MUTE:
                if not self.muted_role:
                    raise ValueError
                await member.add_roles(self.muted_role, reason=str(punishment_entry['id']))
        except (discord.HTTPException, ValueError):
            await self.client.send_message(author, action_failure if action_failure else 'The {} failed.'.format(next_punishment.lower()))

        await self.schedule_unbans()
        await self.schedule_unmutes()

    async def schedule_unbans(self):
        punishments = self.punishments.select(where=['type=?', self.TEMPORARY_BAN])
        for punishment in punishments:
            if punishment['user'] in self.scheduled_unbans or punishment['end_time'] <= time.time():
                continue  # Don't schedule an unban for someone already scheduled for one, or if the ban hasn't expired.
            perma_banned = self.punishments.select(where=['user=? AND type=?', punishment['user'], self.PERMANENT_BAN], limit=1)
            if perma_banned:
                continue  # Don't schedule an unban for someone who was since permanently banned.
            self.scheduled_unbans.append(punishment['user'])
            await self.scheduled_unban(punishment['user'], punishment['end_time'])

    async def scheduled_unban(self, user_id, end_time=None):
        user = await self.client.get_user_info(user_id)
        if end_time:
            await asyncio.sleep(end_time - time.time())
        await self.client.focused_guild.unban(user, reason='The user\'s temporary ban expired.')
        self.scheduled_unbans.remove(user_id)

    async def schedule_unmutes(self):
        punishments = self.punishments.select(where=['type=?', self.MUTE])
        for punishment in punishments:
            if punishment['user'] in self.scheduled_unmutes or not punishment['end_time'] or punishment['end_time'] <= time.time():
                continue  # Don't schedule an unmute for someone already scheduled for one, or if the mute hasn't or won't expire(d).
            self.scheduled_unmutes.append(punishment['user'])
            await self.scheduled_unmute(punishment['user'], punishment['end_time'])

    async def scheduled_unmute(self, id, end_time=None):
        user = self.client.focused_guild.get_member(id)
        channel = self.client.focused_guild.get_channel(id)
        if end_time:
            await asyncio.sleep(end_time - time.time())
        if id not in self.scheduled_unmutes:  # The channel was prematurely unmuted.
            return
        if user:
            await user.remove_roles(self.muted_role, reason='The user\'s mute expired.')
        elif channel:
            await channel.set_permissions(self.client.focused_guild.default_role, send_messages=True, reason='The channel\'s mute expired.')
            await channel.send(embed=self.create_discord_embed(
                info=':loud_sound: This channel is now unmuted.',
                footer='Please avoid flooding the channel and follow the rules set in #welcome.',
                color=discord.Color.green()
            ))
            self.punishments.delete(where=['user=?', channel.id])
        self.scheduled_unmutes.remove(id)

    async def schedule_unmute_from_slowmode(self, channel, member, seconds):
        for _ in range(seconds):
            await asyncio.sleep(1)
            if str(channel.id) not in self.slowmode:
                break
        await channel.set_permissions(member, overwrite=None, reason='Slowmode expired')

    def _test_for_bad_word(self, evaded_word):
        # Tests for a bad word against the provided word.
        # Runs through the config list after taking out unicode and non-alphabetic characters.
        response = {'word': None, 'evaded_word': evaded_word}

        word = evaded_word.translate(FILTER_EVASION_CHAR_MAP).lower()
        if word in self.word_exceptions:  # For example, "he'll" or "who're"
            return response

        word = re.sub(r'\W+', '', word)
        word_no_plural = word.rstrip('s').rstrip('e')
        if word in self.bad_words or (word_no_plural in self.bad_words and word not in self.plural_exceptions):
            response['word'] = word
        return response

    def _test_for_bad_phrase(self, evaded_text):
        # This tests the text for bad phrases.
        # Bad phrases are essentially bad words with spaces in them.
        response = {'word': None, 'evaded_word': None}

        evaded_text = evaded_text.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
        text = evaded_text.translate(FILTER_EVASION_CHAR_MAP).lower()
        for phrase in filter(lambda word: ' ' in word, self.bad_words):
            phrase = phrase.lower()  # Sanity check, you never know if a mod'll add caps to a bad word entry.
            phrase_no_plural = phrase.rstrip('s').rstrip('e')
            if phrase_no_plural in self.plural_exceptions:
                phrase_no_plural = '~-=PLACEHOLDER=-~'
            if (phrase == text or phrase_no_plural == text                                    # If the message is literally the phrase.
              or text.startswith(phrase + ' ') or text.startswith(phrase_no_plural + ' ')     # If the message starts with the phrase.
              or text.endswith(' ' + phrase) or text.endswith(' ' + phrase_no_plural)         # If the message ends in the phrase.
              or ' ' + phrase + ' ' in text or ' ' + phrase_no_plural + ' ' in text):         # If the message contains the phrase.
                text_index = text.find(phrase)
                if text_index == -1: text_index = text.find(phrase_no_plural)
                response['word'] = phrase
                response['evaded_word'] = evaded_text[text_index:text_index + len(phrase)]
        return response

    def _test_for_bad_whole(self, evaded_text):
        # This smooshes the whole message together (no spaces) and tests if it matches a bad word.
        text = evaded_text.replace('\r', '').replace('\n', '').replace('\t', '').replace(' ', '')
        return self._test_for_bad_word(evaded_text)

    def _test_for_bad_emoji(self, evaded_text):
        # A simple check, naturally.
        response = {'word': None, 'evaded_word': None}

        evaded_text = evaded_text.replace('\r', '').replace('\n', '').replace('\t', '').replace(' ', '')
        for emoji in self.bad_emojis:
            if emoji in evaded_text:
                response['word'] = emoji
                response['evaded_word'] = emoji
        return response

    async def _filter_bad_words(self, message, evaded_text, edited=' ', silent_filter=False, embed=None):
        response = {}
        for word in evaded_text.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ').split(' '):
            word_response = self._test_for_bad_word(word)
            if word_response['word']:
                response = word_response
        phrase_response = self._test_for_bad_phrase(evaded_text)
        if not response and phrase_response['word']:
            response = phrase_response
        whole_response = self._test_for_bad_whole(evaded_text)
        if not response and whole_response['word']:
            response = whole_response
        emoji_response = self._test_for_bad_emoji(evaded_text)
        if not response and emoji_response['word']:
            response = emoji_response
        if not response:
            return False

        await self.client.delete_message(message)
        if self.spam_channel:
            message.nonce = 'filter'  # We're taking this variable because discord.py said it was nonimportant and it won't let me add any more custom attributes.
            usertracking = self.client.request_module('usertracking')
            if usertracking:
                await usertracking.on_message_filter(message, word=response['evaded_word'], text=evaded_text, embed=embed)
            else:
                word_filter_format = WORD_FILTER_EMBED_ENTRY if embed else WORD_FILTER_ENTRY
                await self.client.send_message(self.spam_channel, word_filter_format.format(
                    edited,
                    message.author.mention,
                    message.channel.mention,
                    message.content.replace(response['evaded_word'], '**' + response['evaded_word'] + '**'),
                    embed,
                    '**' + response['evaded_word'] + '**' if embed else ''
                ))
        try:
            if silent_filter:
                return True
            await self.client.send_message(message.author, WORD_FILTER_MESSAGE.format(message.author.mention, response['word']))
        except discord.HTTPException:
            print('Tried to send bad word filter notification message to a user, but Discord threw an HTTP Error:\n\n{}'.format(format_exc()))
        return True

    async def _filter_bad_name(self, member, evaded_text, silent_filter=False):
        response = {}
        for word in evaded_text.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ').split(' '):
            word_response = self._test_for_bad_word(word)
            if word_response['word']:
                response = word_response
        phrase_response = self._test_for_bad_phrase(evaded_text)
        if not response and phrase_response['word']:
            response = phrase_response
        whole_response = self._test_for_bad_whole(evaded_text)
        if not response and whole_response['word']:
            response = whole_response
        emoji_response = self._test_for_bad_emoji(evaded_text)
        if not response and emoji_response['word']:
            response = emoji_response
        if not response:
            return False

        await member.edit(nick=random.choice(NICKNAME_FILTER_REPLACEMENTS))
        if self.spam_channel:
            usertracking = self.client.request_module('usertracking')
            if usertracking:
                await usertracking.on_nickname_filter(member, word=response['word'], text=evaded_text)
            else:
                name_filter_format = NICKNAME_FILTER_ENTRY
                await self.client.send_message(self.log_channel, name_filter_format.format(
                    member.mention,
                    member.display_name.replace(response['word'], '**' + response['word'] + '**'),
                ))
        try:
            if silent_filter:
                return True
            await self.client.send_message(member, NICKNAME_FILTER_MESSAGE.format(member.mention, response['word']))
        except discord.HTTPException:
            print('Tried to send bad name filter notification message to a user, but Discord threw an HTTP Error:\n\n{}'.format(format_exc()))
        return True

    async def filter_bad_words(self, message, edited=' ', silent_filter=False):
        if await self._filter_bad_words(message, message.content, edited, silent_filter):
            return True
        for embed in message.embeds:
            for attr in [(embed.title, 'title'), (embed.description, 'description'), (embed.footer, 'footer'), (embed.author, 'author')]:
                if type(attr[0]) != str:
                    continue
                if await self._filter_bad_words(message, attr[0], edited, silent_filter, embed=attr[1]):
                    return True
            for field in embed.fields:
                for fieldattr in [(field.name, 'field name'), (field.value, 'field value')]:
                    if type(fieldattr[0]) != str:
                        continue
                    if await self._filter_bad_words(message, fieldattr[0], edited, silent_filter, embed=fieldattr[1]):
                        return True
        return False

    async def filter_bad_links(self, message, edited=' ', silent_filter=False):
        response = None

        text = message.content.translate(FILTER_EVASION_CHAR_MAP).lower().replace(' ', '')
        for link in self.bad_links:
            if fnmatch.fnmatch(text, '*' + link + '*') and not any([link_exception in text for link_exception in self.link_exceptions]):
                response = link
        if not response:
            return False

        await self.client.delete_message(message)
        if self.spam_channel:
            message.nonce = 'filter'  # We're taking this variable because discord.py said it was nonimportant and it won't let me add any more custom attributes.
            usertracking = self.client.request_module('usertracking')
            if usertracking:
                await usertracking.on_message_filter(message, link=True)
            else:
                await self.client.send_message(self.spam_channel, LINK_FILTER_ENTRY.format(
                    edited,
                    message.author.mention,
                    message.channel.mention,
                    message.content
                ))
        try:
            if silent_filter:
                return True
            await self.client.send_message(message.author, LINK_FILTER_MESSAGE.format(message.author.mention))
        except discord.HTTPException:
            print('Tried to send bad link filter notification message to a user, but Discord threw an HTTP Error:\n\n{}'.format(format_exc()))
        return True

    async def filter_bad_images(self, message):
        # Refreshes embed info from the API.
        try:
            message = await message.channel.get_message(message.id)
        except discord.errors.NotFound:
            print('Tried to rediscover message {} to filter bad images but message wasn\'t found.'.format(message.id))

        if not message.embeds and not message.attachments:
            return

        for embed in message.embeds:
            if embed.type in ['image', 'gif', 'gifv']:
                rating = self.run_image_filter(embed.thumbnail.url, gif=True if embed.type in ['gif', 'gifv'] or embed.url.endswith('gif') else False)
                await self.determine_image_rating_action(message, rating, embed.url)

        for attachment in message.attachments:
            if any([attachment.filename.endswith(extension) for extension in ('.jpg', '.png', '.gif', '.bmp')]):
                rating = self.run_image_filter(attachment.url, gif=True if attachment.filename.endswith('.gif') or attachment.filename.endswith('.gifv') else False)
                await self.determine_image_rating_action(message, rating, attachment.url)

    def run_image_filter(self, url, gif=False):
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
        general_filter_response = self.general_image_filter.predict([image])
        nsfw_filter_response = self.nsfw_image_filter.predict([image])

        if gif:
            ratings = []
            i = 0
            for frame in general_filter_response['outputs'][0]['data']['frames']:
                nframe = nsfw_filter_response['outputs'][0]['data']['frames'][i]
                ratings.append(self.get_image_rating(frame['data']['concepts'], nframe['data']['concepts']))
                i += 1
            return max(ratings)
        else:
            return self.get_image_rating(general_filter_response['outputs'][0]['data']['concepts'], nsfw_filter_response['outputs'][0]['data']['concepts'])

        for concept in general_filter_response['outputs'][0]['data']['concepts']:
            if concept['name'] == 'explicit':
                rating += concept['value']
            elif concept['name'] in ['suggestive', 'drug', 'gore']:
                rating += concept['value'] / 2
        for concept in nsfw_filter_response['outputs'][0]['data']['concepts']:
            if concept['name'] == 'nsfw':
                rating += concept['value']

        return rating

    def get_image_rating(self, general_concepts, nsfw_concepts):
        rating = 0
        for concept in general_concepts:
            if concept['name'] == 'explicit':
                rating += concept['value']
            elif concept['name'] in ['suggestive', 'drug', 'gore']:
                rating += concept['value'] / 2
        for concept in nsfw_concepts:
            if concept['name'] == 'nsfw':
                rating += concept['value']

        return rating

    async def determine_image_rating_action(self, message, rating, url):
        usertracking = self.client.request_module('usertracking')

        if rating > 1.5:
            rating = round(rating, 2)
            await self.client.delete_message(message)
            if usertracking:
                # On this specific instance, using `nonce` is more unreliable than usual.
                # We'll unhack it up later and figure out a better way. For the rest of them too.
                message.nonce = 'filter'  # See other code that edits `nonce` for explanation.
                await usertracking.on_message_filter(message)
            await self.punish_user(message.author, punishment=self.PERMANENT_BAN, reason=IMAGE_FILTER_REASON.format(rating), snowflake=message.id)
        elif rating > 1:
            rating = round(rating, 2)
            await self.client.delete_message(message)
            if usertracking:
                message.nonce = 'filter'
                await usertracking.on_message_filter(message)
            await self.punish_user(message.author, punishment=self.KICK, reason=IMAGE_FILTER_REASON.format(rating), snowflake=message.id)
        elif rating > .5:
            rating = round(rating, 2)
            if usertracking:
                await usertracking.on_message_review_filter(message, rating, url)
            else:
                await self.client.send_message(self.log_channel, IMAGE_FILTER_REVIEW.format(
                    message.author.mention, message.channel.mention, rating, url))
        # For debug.
        #else:
        #    rating = round(rating, 2)
        #   await self.client.send_message(self.spam_channel, "Image posted was fine. **[Rating: {}]**".format(rating))

    async def on_message(self, message):
        if message.channel.id in self.filter_exceptions or message.author.id in self.filter_exceptions or \
            (message.channel.__class__ == discord.DMChannel or (message.channel.category and message.channel.category.name.startswith('Lobby'))) or \
            (message.author.bot and not self.filter_bots) or (Config.get_rank_of_member(message.author) >= 300 and not self.filter_mods):
            return

        if self.spam_protection:
            spam_author = self.spam_tracking.get(message.author, {})
            for msg in spam_author.keys():
                if not spam_author[msg]['count'] or time.time() - spam_author[msg]['time'] >= (self.spam_protection['minute_duration'] * 60):
                    del spam_author[msg]

            spam_message = spam_author.get(message.content.lower(), {'time': 0, 'count': 0})
            if spam_message['count'] == self.spam_protection['message_count'] - 2:
                await message.channel.send('{} Please stop spamming the same message.'.format(message.author.mention))
            elif spam_message['count'] >= self.spam_protection['message_count']:
                await self.punish_user(
                    message.author,
                    punishment=self.spam_protection['action'],
                    length=self.spam_protection['punish_length'],
                    reason='Spamming'
                )
                spam_message['count'] = -1

            spam_message['time'] = time.time()
            spam_message['count'] += 1
            spam_author[message.content.lower()] = spam_message
            self.spam_tracking[message.author] = spam_author

        if self.flood_protection:
            flood_message = self.flood_tracking.get(message.content.lower(), {'time': 0, 'count': 0, 'members': []})
            if flood_message['time'] and (not flood_message['count'] or time.time() - flood_message['time'] >= (self.flood_protection['minute_duration'] * 60)):
                del self.flood_tracking[message.content.lower()]

            if flood_message['count'] == self.flood_protection['message_count'] - 3:
                await message.channel.send('Please stop spamming the same message.')
            elif flood_message['count'] >= self.flood_protection['message_count']:
                for member in flood_message['members']:
                    await self.punish_user(
                        member,
                        punishment=self.flood_protection['action'],
                        length=self.flood_protection['punish_length'],
                        reason='Flooding the server'
                    )
                if message.author not in flood_message['members']:
                    await self.punish_user(
                        member,
                        punishment=self.flood_protection['action'],
                        length=self.flood_protection['punish_length'],
                        reason='Flooding the server'
                    )
                flood_message['count'] = -1

            flood_message['time'] = time.time()
            flood_message['count'] += 1
            if message.author not in flood_message['members']:
                flood_message['members'].append(message.author)
            self.flood_tracking[message.content.lower()] = flood_message

        time_start = time.time()
        try:
            filtered = None
            if self.bad_word_filter_on:
                filtered = await self.filter_bad_words(message)
            if not filtered and self.bad_link_filter_on:
                await self.filter_bad_links(message)
        except discord.errors.NotFound:
            print('Tried to remove message in bad word/link filter but message wasn\'t found.')
            return

        if str(message.channel.id) in self.slowmode:
            await message.channel.set_permissions(message.author, send_messages=False, reason='Slowmode triggered')
            await self.schedule_unmute_from_slowmode(message.channel, message.author, self.slowmode[str(message.channel.id)])
            return

        if not self.bad_image_filter_on:
            return

        # This is for the bad image filter. Discord's servers usually needs a
        # moment to process embedded / attached images before the API can use it.
        if time.time() - time_start < 1:
            await asyncio.sleep(2)
        else:
            await asyncio.sleep(1)
        await self.filter_bad_images(message)

    async def on_message_edit(self, before, after):
        message = after
        if message.channel.id in self.filter_exceptions or message.author.id in self.filter_exceptions or \
            (message.channel.__class__ == discord.DMChannel or (message.channel.category and message.channel.category.name.startswith('Lobby'))) or \
            (message.author.bot and not self.filter_bots) or (Config.get_rank_of_member(message.author) >= 300 and not self.filter_mods):
            return

        # We'll only check for edited-in bad words for right now.
        try:
            filtered = None
            if self.bad_word_filter_on:
                filtered = await self.filter_bad_words(message, edited=' edited ')
            if not filtered and self.bad_link_filter_on:
                await self.filter_bad_links(message)
        except discord.errors.NotFound:
            print('Tried to remove edited message in bad word/link filter but message wasn\'t found.')
            return

    async def on_member_update(self, before, after):
        if self.bad_word_filter_on:
            await self._filter_bad_name(after, after.display_name)

module = ModerationModule