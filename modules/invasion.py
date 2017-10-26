import regex as re
import requests
import logging
import locale
import time

from .module import *
from modules.module import *
from math import ceil, floor
from extra.toontown import *
from discord import Embed, Color
from utils import Config, getTimeFromSeconds, getAttributeFromMatch, assertTypeOrOtherwise
uaHeader = Config.getSetting('ua_header', getVersion())

invasionCache = []

class Invasion:
    def __new__(cls, *args, **kwargs):
        for inv in invasionCache:
            if (
                (kwargs.get('district', None) == inv.district) and
                (kwargs.get('cog', None) == inv.cog) and
                (kwargs.get('startTime', None) == inv.startTime) and
                (kwargs.get('total', None) == inv.total)
            ): return inv

        return super(Invasion, cls).__new__(cls)

    def __init__(self, district, cog, asOf, defeated, total, defeatRate=None, startTime=None):
        global invasionCache
        invasionCache.append(self)

        self.district = district
        self.cog = cog
        self.asOf = asOf
        self.startTime = startTime
        self.defeated = defeated
        self.defeatRate = defeatRate
        self.total = total

        self.megaInvasion = self.total == 1000000
        self.department = cog.type
        self._etr = None
        self._remaining = None

    def updateInformation(self, inv):
        for attr in ('asOf', 'defeated', 'defeatRate'):
            if hasattr(self, attr) and hasattr(inv, attr):
                setattr(self, attr, getattr(inv, attr))

    # Determines the new Estimated Time Remaining
    # and returns the value after setting it.
    def getETR(self):
        if self.defeatRate:
            etr = self._etr = ((self.total - self.defeated) / self.defeatRate - (time.time() - self.asOf))    
        else:
            etr = -1
        return etr

    # Determines and returns the current length.
    def getLength(self):
        return (time.time() - self.startTime) if self.startTime else 'unknown time'

    # Determines the amount of Cogs remaining
    # and returns the value after setting it.
    def getRemaining(self):
        self._remaining = self.total - self.defeated
        
        return locale.format('%d', self._remaining, grouping=True)

    etr = property(getETR)
    length = property(getLength)
    remaining = property(getRemaining)


class InvasionModule(Module):
    CHANNEL_ID = Config.getModuleSetting('invasion', 'perma')

    TOONHQ_ROUTE = ('https://toonhq.org/api/v1/invasion', 'http://toonhq.org/invasions')
    TTR_ROUTE = ('https://toontownrewritten.com/api/invasions', 'https://toontownrewritten.com')
    ROUTES = (TOONHQ_ROUTE, TTR_ROUTE)

    def __init__(self, client):
        Module.__init__(self, client)

        self.defaultRoute = self.ROUTES[0]
        self.route = self.defaultRoute
        self.collectionSuccesses = 0
        self.collectionFailures = 0
        self.testingRoute = False
        self.lastKnownWorkingRoute = self.route
        self.lastUpdated = None

        self.invasions = []
        self.droughtStart = int(time.time())
        self.droughts = 0  # These two variables help determine when a drought starts, so a time can be set and returned 
        self.lastDrought = 0  # to the user. If they are mismatched, a drought is in progress and can be marked.
        self.setFirstLoop = False

        self.permaMsgs = [InvPermaMsg]

    def addCollectionSuccess(self):
        self.collectionSuccesses += 1
        self.collectionFailures = 0

    def addCollectionFailure(self):
        self.collectionSuccesses = 0
        self.collectionFailures += 1

    def switchRoutes(self, route=None):
        if route:
            self.route = route
        else:
            index = self.ROUTES.index(self.route) + 1
            self.route = self.ROUTES[index if index < len(self.ROUTES) else 0]

    def getLastUpdated(self, json):
        if self.route == self.TOONHQ_ROUTE:
            return int(json['meta']['last_updated'])
        else:
            return int(json['lastUpdated'])

    def getInvasions(self, json):
        return json['invasions']

    def getIterableData(self, data):
        if self.route == self.TTR_ROUTE:
            newData = []
            for district, data in data.items():
                data.update({'district': district})
                newData.append(data)
            return newData
        else:
            return data

    def getInvasionObject(self, invData):
        if self.route == self.TOONHQ_ROUTE:
            s, v = '(Skelecog)' in invData['cog'], 'Version 2.0' in invData['cog']
            cog = getAttributeFromMatch({(k.lower(),): v for k, v in zip(cogsStr, cogs)}, invData['cog'].replace('\x03', '').replace(' (Skelecog)', '').replace('Version 2.0 ', '').lower())(isV2=v, isSkelecog=s)
            inv = Invasion(
                district=invData['district'],
                cog=cog,
                asOf=invData['as_of'],
                startTime=invData['start_time'],
                defeated=invData['defeated'],
                defeatRate=invData['defeat_rate'],
                total=invData['total'],
            )
        elif self.route == self.TTR_ROUTE:
            s, v = '(Skelecog)' in invData['type'], 'Version 2.0' in invData['type']
            cog = getAttributeFromMatch({(k.lower(),): v for k, v in zip(cogsStr, cogs)}, invData['type'].replace('\x03', '').replace(' (Skelecog)', '').replace('Version 2.0 ', '').lower())(isV2=v, isSkelecog=s)
            defeated, total = [int(p) for p in invData['progress'].split('/')]
            inv = Invasion(
                district=invData['district'],
                cog=cog,
                asOf=invData['asOf'],
                defeated=defeated,
                total=total
            )
        return inv

    def collectData(self):
        try:
            r = requests.get(self.route[0], headers=uaHeader)
            json = r.json()
            self.lastUpdated = self.getLastUpdated(json)

            self.addCollectionSuccess()
            if self.collectionSuccesses % 150 == 0 and self.route != self.defaultRoute:
                self.testingRoute = True
                self.lastKnownWorkingRoute = self.route
                self.switchRoutes(self.defaultRoute)
        except (ValueError, requests.ConnectionError):
            if self.testingRoute:
                self.testingRoute = False
                self.switchRoutes(self.lastKnownWorkingRoute)
            else:
                self.addCollectionFailure()
                if self.collectionFailures % 5 == 0:
                    self.switchRoutes()
            return None

        return self.getInvasions(json)

    def handleData(self, data):
        if data == None:
            self.updatePermaMsg(InvPermaMsg)
            return

        if not data and self.lastDrought == self.droughts:
            self.droughts += 1
            self.droughtStart = int(time.time())
        elif data and self.droughts > self.lastDrought:
            self.lastDrought += 1

        data = self.getIterableData(data)
        for invData in data:
            inv = self.getInvasionObject(invData)

            if inv in self.invasions:
                inv.updateInformation(inv)
            else:
                populateDistricts(inv.district)
                # Accounts for an invasion that immediately started in the same district after one just ended.
                for i in self.invasions:
                    if inv.district == i.district:
                        self.invasions.remove(i)
                self.invasions.append(inv)

        districts = [di['district'] for di in data]
        for inv in self.invasions:
            if inv.district not in districts:
                self.invasions.remove(inv)

        self.updatePermaMsg(InvPermaMsg)

    # Returns all invasions that match the attributes passed through the method.
    def getInvs(self, **kwargs):
        modules = [module for module in ([kwargs['module']] if kwargs.get('module', None) else self.modules)]
        allInvasions = {module: module.invasions for module in modules}

        kwargs.pop('module', None)
        matchingInvs = {module: [] for module in modules}
        for module, invs in allInvasions.items():
            for inv in invs:
                if all(getattr(inv, k, None) == v for k, v in kwargs.items()):
                    matchingInvs[module].append(inv)

        return matchingInvs


# ----------------------------------------- Message Handlers -----------------------------------------

class InvPermaMsg(PermaMsg):
    TITLE = 'Invasions'

    def update(module):
        title = 'Invasions'

        if module.isFirstLoop:
            msg = module.createDiscordEmbed(title=title, description='Collecting the latest information...', color=Color.light_grey())
            return msg

        megainvs = []
        invs = []
        for inv in module.invasions:
            if inv.megaInvasion:
                megainvs.append(inv)
            else:
                invs.append(inv)
        megainvs = sorted(megainvs, key=lambda k: -k.startTime)
        invs = sorted(invs, key=lambda k: (-k.etr if k.etr != -1 else (k.defeated/k.total)))

        invs = megainvs + invs

        if time.time() >= (assertTypeOrOtherwise(module.lastUpdated, int, otherwise=0) + 300):
            desc = 'We\'re experiencing some technical difficulties.\nInvasion tracking will be made reavailable as soon as possible.'
            msg = module.createDiscordEmbed(title=title, description=desc, color=Color.light_grey())
            msg.set_footer(text='We apologize for the inconvenience.')
        elif len(invs) > 0:
            msg = module.createDiscordEmbed(title=title, url=module.route[1], multipleFields=True, color=Color.light_grey())
            cogs = []
            districts = []
            etrs = []
            progress = []
            for inv in invs:
                if inv.etr != -1:
                    etr = getTimeFromSeconds(inv.etr)
                    etr = 'A few seconds' if inv.etr < 0 else etr
                    etr = 'Calculating...' if time.time() - inv.startTime < 60 else etr
                    etr = 'Mega Invasion!' if inv.megaInvasion else etr
                    etrs.append(etr)
                else:
                    p = int((inv.defeated/inv.total) * 10)
                    # Pray this never has to be debugged.
                    progress.append('[{}{}]'.format('■' * p, ('  '*(10-p))+(' '*ceil((10-p)/2))))
                cogs.append(inv.cog.plural())
                districts.append(inv.district)
            msg.add_field(name="Cog", value='\n'.join(cogs))
            msg.add_field(name="District", value='\n'.join(districts))
            if etrs:
                msg.add_field(name="Time Remaining", value='\n'.join(etrs))
            else:
                msg.add_field(name="Progress", value='\n'.join(progress))
        else:
            desc = 'No invasions to report.\nThe last invasion seen was __{} ago__.'.format(
                getTimeFromSeconds(int(time.time()) - module.droughtStart))
            msg = module.createDiscordEmbed(title=title, description=desc, color=Color.light_grey())
        return msg

module = InvasionModule