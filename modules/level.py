import discord
import asyncio
from math import sqrt, pow
from random import randint
from modules.module import Module
from extra.commands import Command
from utils import Config, Users

class LevelModule(Module):

    def __init__(self, client):
        Module.__init__(self, client)
        self.commands = []
        self.usersCooldowned = []

        self.xpMinPerMsg = Config.getModuleSetting('level', 'xpminpermsg')
        self.xpMaxPerMsg = Config.getModuleSetting('level', 'xpmaxpermsg')
        self.xpCooldown = Config.getModuleSetting('level', 'xpcooldown')

    def getXpFormula(self, level):						
        return round(sqrt(level) * 250 + pow(level, 2))

    def userLevelUp(self, id):
        print('LEVEL UP! ' + str(id))
        level = Users.getUserLevel(id)
        level += 1
        Users.setUserLevel(id, level)

    async def handleMsg(self, message):
        if message.author.id in self.usersCooldowned:
            return # nope, wait a bit <3
        if not message.author.id in self.usersCooldowned:
            cooldowned = True
            self.usersCooldowned.append(message.author.id) # get the user on our cooldown list
        xp = Users.getUserXP(message.author.id)
        xpReward = randint(self.xpMinPerMsg, self.xpMaxPerMsg) 
        xp += xpReward
        level = Users.getUserLevel(message.author.id)
        if xp >= self.getXpFormula(level):
            self.userLevelUp(message.author.id) # LEVEL UP!
        Users.setUserXP(message.author.id, xp)
        if cooldowned:
            await asyncio.sleep(self.xpCooldown)
            self.usersCooldowned.remove(message.author.id) # And.. cooldown's over.

module = LevelModule