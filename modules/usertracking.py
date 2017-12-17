import discord
import asyncio
import random
import time
from modules.module import Module
from utils import Config, Users

class UserTrackingModule(Module):
    def __init__(self, client):
        Module.__init__(self, client)

        self.trackMessages = Config.getModuleSetting('usertracking', 'track_messages', True)
        self.trackingExceptions = Config.getModuleSetting('usertracking', 'tracking_exceptions', [])

        self.memberStatusTimeStart = {member: time.time() for member in client.rTTR.members}
        self.trackStatuses = Config.getModuleSetting('usertracking', 'track_statuses', True)

        self.levelCooldowns = {}
        self.levelCooldown = assertTypeOrOtherwise(Config.getModuleSetting('usertracking', 'level_cooldown'), int, 60)
        self.levelCap = assertTypeOrOtherwise(Config.getModuleSetting('usertracking', 'level_cap'), int, -1)
        self.levelingExceptions = Config.getModuleSetting('usertracking', 'leveling_exceptions', [])
        self.allowUserLeveling = Config.getModuleSetting('usertracking', 'allow_user_leveling', True)
        self.allowUserRewards = Config.getModuleSetting('usertracking', 'allow_user_rewards', True)
        self.allowBotLeveling = Config.getModuleSetting('usertracking', 'allow_bot_leveling', False)
        self.allowBotRewards = Config.getModuleSetting('usertracking', 'allow_bot_rewards', False)
        self.allowModLeveling = Config.getModuleSetting('usertracking', 'allow_mod_leveling', True)
        self.allowModRewards = Config.getModuleSetting('usertracking', 'allow_mod_rewards', False)

    async def addXP(self, member):
        if time.time() < self.levelCooldowns.get(member, 0):
            return
        xp = Users.getUserXP(member.id)
        xp += random.randint(1, 10)
        Users.setUserXP(member.id, xp)
        self.levelCooldowns[member] = time.time() + self.levelCooldown

    async def level(self, member):
        response = None
        level = Users.getUserLevel(member.id)
        if level >= self.levelCap:
            return

        if Users.getUserXP(member.id) >= 5 * (level**2) + 50*n + 100:  # Sorry Mee6 I've never been good with original math
            level += 1
            response = level
        Users.setUserLevel(member.id, level)
        Users.setUserXP(member.id, 0)
        return response

    async def handleMsg(self, message):
        # You don't want to progress if there's an exception being made.
        if message.channel.id in self.levelingExceptions or message.author.id in self.levelingExceptions or \
            any([role.id in self.levelingExceptions for role in message.author.roles]):
            return
        if message.channel.id in self.trackingExceptions:
            return

        if self.trackMessages:
            channelHistory = Users.getUserChannelHistory(message.author.id, message.channel.id)
            channelHistory['messages'] += 1
            channelHistory['attachments'] += len(message.attachments)
            channelHistory['embed'] += len(message.embeds)
            Users.setUserChannelHistory(message.author.id, message.channel.id, channelHistory)

        bot = message.author.bot
        mod = any([Config.getRankOfRole(role.id) >= 300 for role in message.author.roles])

        if mod:
            if self.allowModLeveling:
                self.addXP(message.author)
                leveled = self.level(message.author)
                if leveled and self.allowModRewards:
                    pass  # Rewards TBD
        elif bot:
            if self.allowBotLeveling:
                self.addXP(message.author)
                leveled = self.level(message.author)
                if leveled and self.allowBotRewards:
                    pass  # Rewards TBD
        else:
            if self.allowUserLeveling:
                self.addXP(message.author)
                leveled = self.level(message.author)
                if leveled and self.allowUserRewards:
                    pass  # Rewards TBD

    async def on_member_update(self, before, after):
        if self.trackStatuses and before.status != after.status:
            if before.status == discord.Status.online:
                Users.setUserTimeOnline(before.id, Users.getUserTimeOnline(before.id) + (time.time() - self.memberStatusTimeStart[before.id]))
            elif before.status == discord.Status.offline:
                Users.setUserTimeOffline(before.id, Users.getUserTimeOffline(before.id) + (time.time() - self.memberStatusTimeStart[before.id]))
            elif before.status == discord.Status.idle:
                Users.setUserTimeIdle(before.id, Users.getUserTimeIdle(before.id) + (time.time() - self.memberStatusTimeStart[before.id]))
            elif before.status == discord.status.dnd:
                Users.setUserTimeDND(before.id, Users.getUserTimeDND(before.id) + (time.time() - self.memberStatusTimeStart[before.id]))
            self.memberStatusTimeStart[before.id] = time.time()