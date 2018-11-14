import requests
import logging
import locale
import time

from .module import *
from modules.module import *
from math import ceil, floor
from extra.toontown import *
from discord import Embed, Color
from utils import Config, get_time_from_seconds, get_attribute_from_match, assert_type
ua_header = Config.get_setting('ua_header', get_version())

invasion_cache = []

class Invasion:
    def __new__(cls, *args, **kwargs):
        for inv in invasion_cache:
            if (
                (kwargs.get('district', None) == inv.district) and
                (kwargs.get('cog', None) == inv.cog) and
                (kwargs.get('start_time', None) == inv.start_time) and
                (kwargs.get('total', None) == inv.total)
            ): return inv

        return super(Invasion, cls).__new__(cls)

    def __init__(self, district, cog, as_of, defeated, total, defeat_rate=None, start_time=None):
        global invasion_cache
        if self in invasion_cache:
            return
        else:
            invasion_cache.append(self)

        self.district = district
        self.cog = cog
        self.as_of = as_of
        self.start_time = start_time
        self.defeated = defeated
        self.defeat_rate = defeat_rate
        self.total = total

        self.mega_invasion = self.total == 1000000
        self.department = cog.type
        self._etr = None
        self._remaining = None

    def update_information(self, inv):
        for attr in ('as_of', 'defeated', 'defeat_rate'):
            if hasattr(self, attr) and hasattr(inv, attr):
                setattr(self, attr, getattr(inv, attr))

    # Determines the new Estimated Time Remaining
    # and returns the value after setting it.
    def get_etr(self):
        if self.defeat_rate:
            etr = self._etr = ((self.total - self.defeated) / self.defeat_rate - (time.time() - self.as_of))    
        else:
            etr = -1
        return etr

    # Determines and returns the current length.
    def get_length(self):
        return (time.time() - self.start_time) if self.start_time else 'unknown time'

    # Determines the amount of Cogs remaining
    # and returns the value after setting it.
    def get_remaining(self):
        self._remaining = self.total - self.defeated
        
        return locale.format('%d', self._remaining, grouping=True)

    etr = property(get_etr)
    length = property(get_length)
    remaining = property(get_remaining)


class InvasionModule(Module):
    TOONHQ_ROUTE = ('https://toonhq.org/api/v1/invasion', 'http://toonhq.org/invasions')
    TTR_ROUTE = ('https://toontownrewritten.com/api/invasions', 'https://toontownrewritten.com')
    ROUTES = (TOONHQ_ROUTE, TTR_ROUTE)

    def __init__(self, client):
        Module.__init__(self, client)

        self.default_route = self.ROUTES[0]
        self.route = self.default_route
        self.collection_successes = 0
        self.collection_failures = 0
        self.testing_route = False
        self.last_known_working_route = self.route
        self.last_updated = None

        self.invasions = []
        self.drought_start = int(time.time())
        self.droughts = 0  # These two variables help determine when a drought starts, so a time can be set and returned 
        self.last_drought = 0  # to the user. If they are mismatched, a drought is in progress and can be marked.
        self.set_first_loop = False

        self.invasion_message = self.create_permanent_messages(InvasionPermaMessage)

    def add_collection_success(self):
        self.collection_successes += 1
        self.collection_failures = 0

    def add_collection_failure(self):
        self.collection_successes = 0
        self.collection_failures += 1

    def switch_routes(self, route=None):
        if route:
            self.route = route
        else:
            index = self.ROUTES.index(self.route) + 1
            self.route = self.ROUTES[index if index < len(self.ROUTES) else 0]

    def get_last_updated(self, json):
        if self.route == self.TOONHQ_ROUTE:
            return int(json['meta']['last_updated'])
        else:
            return int(json['last_updated'])

    def get_invasions(self, json):
        return json['invasions']

    def get_iterable_data(self, data):
        if self.route == self.TTR_ROUTE:
            new_data = []
            for district, data in data.items():
                data.update({'district': district})
                new_data.append(data)
            return new_data
        else:
            return data

    def get_invasion_object(self, inv_data):
        if self.route == self.TOONHQ_ROUTE:
            s, v = '(Skelecog)' in inv_data['cog'], 'Version 2.0' in inv_data['cog']
            cog = get_attribute_from_match({(k.lower(),): v for k, v in zip(cogs_str, cogs)}, inv_data['cog'].replace('\x03', '').replace(' (Skelecog)', '').replace('Version 2.0 ', '').lower())(is_v2=v, is_skelecog=s)
            inv = Invasion(
                district=inv_data['district'],
                cog=cog,
                as_of=inv_data['as_of'],
                start_time=inv_data['start_time'],
                defeated=inv_data['defeated'],
                defeat_rate=inv_data['defeat_rate'],
                total=inv_data['total'],
            )
        elif self.route == self.TTR_ROUTE:
            s, v = '(Skelecog)' in inv_data['type'], 'Version 2.0' in inv_data['type']
            cog = get_attribute_from_match({(k.lower(),): v for k, v in zip(cogs_str, cogs)}, inv_data['type'].replace('\x03', '').replace(' (Skelecog)', '').replace('Version 2.0 ', '').lower())(is_v2=v, is_skelecog=s)
            defeated, total = [int(p) for p in inv_data['progress'].split('/')]
            inv = Invasion(
                district=inv_data['district'],
                cog=cog,
                as_of=inv_data['as_of'],
                defeated=defeated,
                total=total
            )
        return inv

    async def collect_data(self):
        try:
            r = requests.get(self.route[0], headers=ua_header)
            json = r.json()
            self.last_updated = self.get_last_updated(json)

            self.add_collection_success()
            if self.collection_successes % 150 == 0 and self.route != self.default_route:
                self.testing_route = True
                self.last_known_working_route = self.route
                self.switch_routes(self.default_route)
        except (ValueError, requests.ConnectionError):
            if self.testing_route:
                self.testing_route = False
                self.switch_routes(self.last_known_working_route)
            else:
                self.add_collection_failure()
                if self.collection_failures % 5 == 0:
                    self.switch_routes()
            return None

        return self.get_invasions(json)

    async def handle_data(self, data):
        if data == None:
            self.update_perma_msg(InvPermaMsg)
            return

        if not data and self.last_drought == self.droughts:
            self.droughts += 1
            self.drought_start = int(time.time())
        elif data and self.droughts > self.last_drought:
            self.last_drought += 1

        data = self.get_iterable_data(data)
        for inv_data in data:
            inv = self.get_invasion_object(inv_data)

            if inv in self.invasions:
                inv.update_information(inv)
            else:
                # Accounts for an invasion that immediately started in the same district after one just ended.
                for i in self.invasions:
                    if inv.district == i.district:
                        self.invasions.remove(i)
                self.invasions.append(inv)

        districts = [di['district'] for di in data]
        for inv in self.invasions:
            if inv.district not in districts:
                global invasion_cache
                invasion_cache.remove(inv)
                self.invasions.remove(inv)

        await self.invasion_message.update()

    # Returns all invasions that match the attributes passed through the method.
    def get_invs(self, **kwargs):
        modules = [module for module in ([kwargs['module']] if kwargs.get('module', None) else self.modules)]
        all_invasions = {module: module.invasions for module in modules}

        kwargs.pop('module', None)
        matching_Invs = {module: [] for module in modules}
        for module, invs in all_invasions.items():
            for inv in invs:
                if all(getattr(inv, k, None) == v for k, v in kwargs.items()):
                    matching_Invs[module].append(inv)

        return matching_Invs


# ----------------------------------------- Message Handlers -----------------------------------------

class InvasionPermaMessage(PermaMessage):
    TITLE = 'Invasions'
    CHANNEL_ID = Config.get_module_setting('invasion', 'perma')

    async def update(self, *args, **kwargs):
        if self.module.is_first_loop:
            msg = self.module.create_discord_embed(title=self.TITLE, info='Collecting the latest information...', color=Color.light_grey())
            return await self.send(msg)

        megainvs = []
        invs = []
        for inv in self.module.invasions:
            if inv.mega_invasion:
                megainvs.append(inv)
            else:
                invs.append(inv)
        megainvs = sorted(megainvs, key=lambda k: -k.start_time)
        invs = sorted(invs, key=lambda k: (-k.etr if k.etr != -1 else (k.defeated/k.total)))

        invs = megainvs + invs

        if time.time() >= (assert_type(self.module.last_updated, int, otherwise=0) + 300):
            desc = 'We\'re experiencing some technical difficulties.\nInvasion tracking will be made reavailable as soon as possible.'
            msg = self.module.create_discord_embed(title=self.TITLE, info=desc, color=Color.light_grey())
            msg.set_footer(text='We apologize for the inconvenience.')
        elif len(invs) > 0:
            cogs = []
            districts = []
            etrs = []
            progress = []
            for inv in invs:
                if inv.etr != -1:
                    etr = get_time_from_seconds(inv.etr)
                    etr = 'A few seconds' if inv.etr < 0 else etr
                    etr = 'Calculating...' if time.time() - inv.start_time < 60 else etr
                    etr = 'Mega Invasion!' if inv.mega_invasion else etr
                    etrs.append(etr)
                else:
                    p = int((inv.defeated/inv.total) * 10)
                    # Pray this never has to be debugged.
                    progress.append('[{}{}]'.format('■' * p, ('  '*(10-p))+(' '*ceil((10-p)/2))))
                cogs.append(inv.cog.plural())
                districts.append(inv.district)
            fields = [
                {'name': 'Cog', 'value': '\n'.join(cogs)},
                {'name': 'District', 'value': '\n'.join(districts)},
                {'name': 'Time Remaining', 'value': '\n'.join(etrs)} if etrs else {'name': 'Progress', 'value': '\n'.join(progress)}
            ]
            msg = self.module.create_discord_embed(title=self.TITLE, title_url=self.module.route[1], color=Color.light_grey(), fields=fields)
        else:
            desc = 'No invasions to report.\nThe last invasion seen was __{} ago__.'.format(
                get_time_from_seconds(int(time.time()) - self.module.drought_start))
            msg = self.module.create_discord_embed(title=self.TITLE, info=desc, color=Color.light_grey())
        return await self.send(msg)

module = InvasionModule