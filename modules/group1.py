import threading
import requests
import logging
import json
import time
import os

from .module import *
from platform import *
from utils import Config, getVersion
from extra.toontown import *

uaHeader = Config.getSetting('ua_header', getVersion())
__location__ = (os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

# A good ol' group.
class Group:
    def __init__(self, owner, groupType, groupOptions, groupLocation, district, members, bumpTime=None, id=None, toonHQ=False):
        # For the sake of conversion, these attribute values should only be JSON serializable attributes.
        # (The exception to this rule is groupType, groupOptions, and groupLocation -- they're meant to be classes.)
        self.owner = owner
        self.type = groupType
        self.options = groupOptions
        self.location = groupLocation
        self.district = district
        self.members = members
        self.bumpTime = bumpTime if bumpTime else time.time()
        self.id = id

        self.toonHQ = toonHQ

    # Change JSON-serialized objects into classes
    # that are used by ToonTracker.
    @staticmethod
    def _extractFromJSON(j):
        if type(j) == str:
            j = json.loads(j)

        j['type'] = typeIDs[j['type']]
        j['options'] = [optionIDs[option] for option in j['options']]
        j['location'] = locationNames[j['location']]

        return j

    # Returns a new Group object given JSON
    @classmethod
    def createGroupFromJSON(cls, j):
        j = cls._extractFromJSON(j)

        members = GroupMembers.createMembersFromJSON(j['members'])
        
        return cls(j['owner'], j['type'], j['options'], j['location'], j['district'], members, j['bumpTime'])

    # Changes classes that are used by ToonTracker
    # into JSON-serializable objects.
    def _extractToJSONConvertible(self):
        attrs = {k: v for k, v in vars(self).items()}
        attrs['type'] = attrs['type'].id
        attrs['options'] = [option.id for option in attrs['options']]
        attrs['location'] = attrs['location'].name

        return attrs

    # Returns a JSON-compatible version of this Group.
    #
    # For if any reason one of the other attributes is not JSON serializable,
    # the default action is to just convert it to a string.
    #
    # This method be overriden, but don't forget to call __extractToJSONConvertible()
    # to automatically handle attributes like "type", "options", and "location".
    def getJSON(self, convertibleOnly=True):
        attrs = self._extractToJSONConvertible()

        data = {}
        for attr, value in attrs.items():
            try:
                json.dumps({attr: value})
            except TypeError:
                value = str(value)
            data[attr] = value

        if convertibleOnly:
            return data
        else:
            return json.dumps(data)

class GroupMember:
    def __init__(self, user, company, isOwner, joined=None):
        if not joined:
            joined = time.time()

        self.user = user
        self.company = company
        self.isOwner = isOwner
        self.joined = joined

    # Returns a new GroupMember object given JSON
    @classmethod
    def createMemberFromJSON(cls, j):
        if type(j) == str:
            j = json.loads(j)

        return cls(j['user'], j['company'], j['isOwner'], j['joined'])

    # Changes classes that are used by ToonTracker
    # into JSON-serializable objects.
    def _extractToJSONConvertible(self):
        return {k: v for k, v in vars(self).items()}

    # Returns a JSON-compatible version of this GroupMember.
    #
    # For if any reason one of the other attributes is not JSON serializable,
    # the default action is to just convert it to a string.
    #
    # This method be overriden, but don't forget to call __extractToJSONConvertible()
    def getJSON(self, convertibleOnly=True):
        attrs = __extractToJSONConvertible()

        data = {}
        for attr, value in attrs.items():
            try:
                json.dumps({attr: value})
            except TypeError:
                value = str(value)
            data[attr] = value

        if convertibleOnly:
            return data
        else:
            return json.dumps(data)

    def getJSONValue(**kwargs):
        key, value = None, None
        for key, value in kwargs.items():
            break

        return value

class GroupMembers:
    memberClass = GroupMember

    def __init__(self, members, memberClass=GroupMember):
        self.memberObjs = []
        self.memberClass = memberClass

        for member in members:
            assert isinstance(member, self.memberClass), "arguments must only consist of instances of {}".format(memberClass.__name__)
            self.memberObjs.append(member)

    # Returns a new GroupMembers object given JSON
    @classmethod
    def createMembersFromJSON(cls, j):
        if type(j) == str:
            j = json.loads(j)

        members = []
        for member in j:
            members.append(cls.memberClass.createMemberFromJSON(member))

        return cls(members, cls.memberClass)

    # Returns a JSON-compatible version of this GroupMembers.
    #
    # For if any reason one of the other attributes is not JSON serializable,
    # the default action is to just convert it to a string.
    def getJSON(self, convertibleOnly=True):
        jsonMembers = []

        for member in self.memberObjs:
            jsonMembers.append(member.getJSON())

        if convertibleOnly:
            return jsonMembers
        else:
            return json.dumps(jsonMembers)

    def getPlayerCount(self):
        players = 0
        for member in self.memberObjs:
            players += member.company

        return players

    def getOwner(self):
        for member in self.memberObjs:
            if member.isOwner:
                return member

    def userInMembers(self, user):
        for member in self.memberObjs:
            if member.user == user:
                return True
        return False

    def addGroupMember(self, groupMember):
        self.memberObjs.append(groupMember)

    def addMember(self, user, company, isOwner, joined=None):
        member = self.memberClass(user, company, isOwner, joined)
        self.addGroupMember(member)

    def getMemberObject(self, user):
        for member in self.memberObjs:
            if member.user == user:
                return member

    def removeGroupMember(self, groupMember):
        self.memberObjs.remove(groupMember)

    def removeMember(self, user):
        for member in self.memberObjs:
            if member.user == user:
                self.memberObjs.remove(member)

class DiscordGroup(Group):
    ToonTracker = None

    # Overwritten method to use a Discord Object
    @classmethod
    def _extractFromJSON(cls, j):
        if type(j) == str:
            j = json.loads(j)

        j['type'] = typeIDs[j['type']]
        j['options'] = [optionIDs[option] for option in j['options']]
        j['location'] = locationNames[j['location']]
        j['owner'] = discord.utils.get(cls.ToonTracker.get_all_members(), id=j['owner'])

        return j

    @classmethod
    def createGroupFromJSON(cls, j):
        j = cls._extractFromJSON(j)

        members = DiscordGroupMembers.createMembersFromJSON(j['members'])

        return cls(j['owner'], j['type'], j['options'], j['location'], j['district'], members, j['bumpTime'])

    # Overwritten method to handle a Discord Object
    def getJSON(self, convertibleOnly=True):
        data = self._extractToJSONConvertible()

        data['owner'] = self.owner.id
        data['members'] = self.members.getJSON()

        if convertibleOnly:
            return data
        else:
            return json.dumps(data)

    def getJSONValue(**kwargs):
        key, value = None, None
        for key, value in kwargs.items():
            break

        if key == 'type':
            value = value.id
        elif key == 'location':
            value = value.name
        elif key == 'options':
            value = [option.id for option in value]

        return value


class DiscordGroupMember(GroupMember):
    ToonTracker = None

    # Overwritten method to use a Discord Object
    @classmethod
    def createMemberFromJSON(cls, j):
        if type(j) == str:
            j = json.loads(j)

        user = discord.utils.get(cls.ToonTracker.get_all_members(), id=j['user'])
        return cls(user, j['company'], j['isOwner'], j['joined'])

    # Overwritten method to handle a Discord Object
    def getJSON(self, convertibleOnly=True):
        data = self._extractToJSONConvertible()

        data['user'] = data['user'].id

        if convertibleOnly:
            return data
        else:
            return json.loads(data)

    def getJSONValue(**kwargs):
        key, value = None, None
        for key, value in kwargs.items():
            break

        if key == 'user':
            value = value.id

        return value


class DiscordGroupMembers(GroupMembers):
    memberClass = DiscordGroupMember

    def __init__(self, members, memberClass=DiscordGroupMember):
        super(DiscordGroupMembers, self).__init__(members, memberClass)



class GroupManagement(threading.Thread):
    CREATE_MODE = 1
    EDIT_MODE = 2
    REMOVE_MODE = 3
    FIND_MODE = 4
    JOIN_MODE = 5
    LEAVE_MODE = 6
    BUMP_MODE = 7

    def __init__(self, groupClass=Group, groupMembersClass=GroupMembers, groupMemberClass=GroupMember):
        super(GroupManagement, self).__init__()

        self.groups = []
        self.noGroupStarted = int(time.time())
        self.isFirstLoop = True
        self.setName('GroupThread')
        self.cooldownInterval = 60
        self.bumpLimit = 900  # 15 minutes
        self.requestStop = False

        self.groupClass = groupClass
        self.groupMembersClass = groupMembersClass
        self.groupMemberClass = groupMemberClass

    def startTracking(self, timer=60):
        self.requestStop = False
        self.cooldownInterval = timer

        groups = self.readFromGroups()
        for group in groups:
            self.groups.append(self.groupClass.createGroupFromJSON(group))

        threading.Thread(target=self.__bumpLoop, name='GroupThread').start()

    def stopTracking(self):
        self.requestStop = True

    def __bumpLoop(self):
        while True:
            if self.requestStop:
                self.requestStop = False
                break

            for group in self.groups:
                if time.time() > group.bumpTime + self.bumpLimit:
                    self.removeGroup(group.owner)
                    #for member in group.members.memberObjs:
                    #    if member.isOwner:
                    #        self.ToonTracker.loop.create_task(self.ToonTracker.send_message(member.user, 
                    #            'You\'ve been inactive for {} minutes, so your group has been automatically disbanded.'.format(int(self.bumpLimit / 60))))
                    #    else:
                    #        self.ToonTracker.loop.create_task(self.send_message(member.user, 
                    #            'Your group\'s owner has been inactive for {} minutes, so your group has been automatically disbanded.'.format(int(self.bumpLimit / 60))))

            for x in range(self.cooldownInterval):
                if self.requestStop:
                    return
                time.sleep(1)
                
    def readFromGroups(self):
        readOptionsFile = open(os.path.join(__location__, 'groups.json'), 'r')
        try:
            options = json.loads(readOptionsFile.read())
        except json.JSONDecodeError:
            options = []
        finally:
            readOptionsFile.close()
        return options

    def writeToGroups(self, toWrite):
        writeOptionsFile = open(os.path.join(__location__, 'groups.json'), 'w')
        writeOptionsFile.seek(0, 0)
        try:
            writeOptionsFile.write(json.dumps(toWrite))
        finally:
            writeOptionsFile.close()

    # This handles all of the ugly JSON so the other methods can look pretty <3
    def handleJSON(self, mode, **kwargs):
        groups = self.readFromGroups()

        if mode == self.CREATE_MODE:
            groups.append(kwargs['json'])

        elif mode == self.EDIT_MODE:
            for group in groups:
                for member in group['members']:
                    if member['user'] == kwargs['user']:
                        if kwargs['key'] == 'company':
                            member['company'] = kwargs['value']
                        else:
                            group[kwargs['key']] = kwargs['value']

        elif mode == self.JOIN_MODE:
            for group in groups:
                if group['owner'] == kwargs['owner']:
                    group['members'].append({'user': kwargs['user'], 'company': kwargs['company'], 'isOwner': False, 'joined': kwargs.get('joined', time.time())})

        elif mode == self.LEAVE_MODE:
            for group in groups:
                for member in group['members']:
                    if member['user'] == kwargs['user']:
                        group['members'].remove(member)

        elif mode == self.REMOVE_MODE:
            for group in groups:
                if group['owner'] == kwargs['owner']:
                    groups.remove(group)

        elif mode == self.BUMP_MODE:
            for group in groups:
                if group['owner'] == kwargs['owner']:
                    group['bumpTime'] = kwargs['bumpTime']

        self.writeToGroups(groups)

    def bumpGroup(self, owner):
        group = self.userOwnsGroup(owner)
        if not group:
            raise OwnerException()

        bumpTime = time.time()
        group.bumpTime = bumpTime
        self.handleJSON(self.BUMP_MODE, owner=self.groupMemberClass.getJSONValue(owner=owner), bumpTime=bumpTime)

    def createGroup(self, owner, groupType, groupOptions, groupLocation, district, company):
        assert issubclass(groupType, GroupType) or isinstance(groupType, GroupType), "groupTpe must be GroupType or a subclass of GroupType"
        assert issubclass(groupLocation, GroupLocation) or isinstance(groupLocation, GroupLocation), "groupLocation must be GroupLocation or a subclass of GroupLocation"
        for option in groupOptions:
            assert issubclass(option, GroupOption) or isinstance(option, GroupOption), "groupOptions must only include GroupOption or subclasses of GroupOption"

        if self.userInGroup(owner):
            raise MaximumGroupException()

        if (groupType.maxPlayers and company >= groupType.maxPlayers) or company > companyLimit:
            raise TooManyPlayersException()

        if company <= 0:
            raise TooFewPlayersException()

        for option in groupOptions:
            if option not in groupType.options:
                groupOptions.remove(option)

        members = self.groupMembersClass([], memberClass=self.groupMemberClass)
        members.addMember(owner, company, True, time.time())
        newGroup = self.groupClass(owner, groupType, groupOptions, groupLocation, district, members)
        self.groups.append(newGroup)

        self.handleJSON(self.CREATE_MODE, json=newGroup.getJSON())

        return newGroup

    def editGroup(self, user, editType, applyType, value):
        group = self.userOwnsGroup(user)
        if not group and self.userInGroup(user):
            if editType == 'company':
                group = self.userInGroup(user)
            else:
                raise OwnerException()
        elif not group:
            raise NoGroupException()

        if editType == 'company':
            if applyType == 'by':
                theoreticalCount = group.members.getPlayerCount() + value
                if (group.type.maxPlayers and theoreticalCount > group.type.maxPlayers) or group.members.getMemberObject(user).company + value > companyLimit:
                    raise TooManyPlayersException()
                elif group.members.getMemberObject(user).company + value <= 0:
                    raise TooFewPlayersException()
                elif value == 0:
                    raise ValueError()

                # Setting the value here lets us have an easier time setting the JSON later.
                value = group.members.getMemberObject(user).company + value
            elif applyType == 'to':
                theoreticalCount = group.members.getPlayerCount() - group.members.getMemberObject(user).company + value
                if (group.type.maxPlayers and theoreticalCount > group.type.maxPlayers) or value > companyLimit:
                    raise TooManyPlayersException()
                elif value <= 0:
                    raise TooFewPlayersException()
            
            group.members.getMemberObject(user).company = value

        elif editType == 'type':
            group.type = value

        elif editType == 'location':
            group.location = value

        elif editType == 'options':
            for option in value:
                if option not in group.type.options:
                    value.remove(option)
            group.options = value

        elif editType == 'district':
            group.district = value

        self.handleJSON(self.EDIT_MODE, user=self.groupMemberClass.getJSONValue(user=user), key=editType, value=self.groupClass.getJSONValue(**{editType: value}))

    def joinGroup(self, user, owner, company):
        if self.userInGroup(user):
            raise MaximumGroupException()

        group = self.userOwnsGroup(owner)
        if not group:
            raise NoGroupException()
        elif group.toonHQ:
            raise ToonHQException()

        if (group.type.maxPlayers and group.members.getPlayerCount() + company >= group.type.maxPlayers) or company > companyLimit:
            raise TooManyPlayersException()

        self.handleJSON(self.JOIN_MODE, owner=self.groupMemberClass.getJSONValue(user=owner), user=self.groupMemberClass.getJSONValue(user=user), company=company, orgGroup=group)
        group.members.addMember(user, company, False)

    def leaveGroup(self, user):
        if self.userOwnsGroup(user):
            raise OwnerException()
        
        group = self.userInGroup(user)
        if not group:
            raise NoGroupException()

        self.handleJSON(self.LEAVE_MODE, user=self.groupMemberClass.getJSONValue(user=user), orgGroup=group)
        group.members.removeMember(user)

    def getGroups(self, groupType, options=[]):
        matchingGroups = []

        for group in self.groups:
            if group.type == groupType or issubclass(group.type, groupType) and all(option in group.type.options for option in options):
                matchingGroups.append(group)

        return matchingGroups

    def removeGroup(self, user):
        group = self.userOwnsGroup(user)
        if not group:
            raise NoGroupException()

        self.handleJSON(self.REMOVE_MODE, owner=self.groupMemberClass.getJSONValue(user=user), orgGroup=group)
        self.groups.remove(group)

    def userInGroup(self, user, group=None):
        if group:
            groups = [group]
        else:
            groups = self.groups

        for g in groups:
            if g.members.userInMembers(user):
                return g
        return False

    def userOwnsGroup(self, user, group=None):
        if group:
            groups = [group]
        else:
            groups = self.groups

        for g in groups:
            if g.owner == user:
                return g
        return False


class MaximumGroupException(Exception):
    pass

class TooManyPlayersException(Exception):
    pass

class TooFewPlayersException(Exception):
    pass

class NoGroupException(Exception):
    pass

class OwnerException(Exception):
    pass

class ToonHQException(Exception):
    pass


class GroupModule(Module):
    PLATFORMS = {
        Discord: (DiscordGroup, DiscordGroupMember, DiscordGroupMembers),
        'else': (Group, GroupMember, GroupMembers)
    }

    def __init__(self, platform):
        #super(GroupTracker, self).__init__(ToonTracker)
        Module.__init__(self, platform)

        classes = PLATFORMS.get(platform, PLATFORMS['else'])
        self.groupManager = GroupManagement(*classes)
        #self.groupManager = groupManager

    def collectData(self):
        #self.logger.debug('Collecting latest group information...')
        url = 'https://toonhq.org/api/v1/group'
        r = requests.get(url, headers=uaHeader)
        try:
            return r.json()
        except ValueError:
            self.logger.debug('Raw JSON: None')
            return None

    def handleData(self, groupData):
        #self.logger.debug('Removing ToonHQ groups to avoid conflicts: {}'.format(
        #    [group for group in self.groupManager.groups if group.id]))
        self.groupManager.groups = [group for group in self.groupManager.groups if not group.id]
        for group in groupData:
            members = []
            for member in group['members']:
                members.append(self.groupManager.groupMemberClass(member['toon_name'], member['num_players'], member['owner'], member['joined']))
            members = self.groupManager.groupMembersClass(members, memberClass=self.groupManager.groupMemberClass)
            
            if not members.getOwner():
                print(group['members'], members.getOwner())
            group = self.groupManager.groupClass(
                members.getOwner().user,
                typeIDs[group['type']],
                [optionIDs[oid] for oid in group.get('options', [])],
                locationNames.get(group['location'], GroupLocation),
                group['district'],
                members,
                toonHQ=True,
                id=group['id']
            )
            self.logger.debug('Created Group instance (id: {}; owner: {}; type: {}; options: {}; location: {}; district: {}; members: {}; '
                'toonHQ: {})'.format(group.id, group.owner, group.type, group.options, group.location, group.district, group.members, group.toonHQ))

            populateDistricts(group.district)
            self.groupManager.groups.append(group)

    def startTracking(self):
        Module.startTracking(self)
        self.groupManager.startTracking()

    def stopTracking(self):
        Module.stopTracking(self)
        self.groupManager.stopTracking()


class GroupRequest:
    typeNameIDs = {
        ('all',): GroupType,
        ('bldg', 'building'): BuildingType,
        ('factory',): FactoryType,
        ('vp',): VPType,
        ('mint',): MintType,
        ('cfo',): CFOType,
        ('da', 'office'): DAType,
        ('cj',): CJType,
        ('cgc', 'cog golf course', 'cog golf'): CGCType,
        ('ceo',): CEOType,
        ('bean', 'beans', 'beanfest'): BeanfestType,
        ('task', 'toontask'): TaskType,
        ('gag training', 'gag', 'gags', 'training'): TrainingType,
        ('kart', 'racing', 'race', 'kart racing'): RacingType,
        ('golf', 'golfing'): GolfType,
        ('trolley',): TrolleyType,
        ('table', 'board game', 'game', 'table game'): GameType
    }

    optNameIDs = {
        ('one story', '1 story'): OneStoryOption,
        ('two story', '2 story'): TwoStoryOption,
        ('three story', '3 story'): ThreeStoryOption,
        ('four story', '4 story'): FourStoryOption,
        ('five story', '5 story'): FiveStoryOption,
        ('sellbot',): SellbotOption,
        ('cashbot',): CashbotOption,
        ('lawbot',): LawbotOption,
        ('bossbot',): BossbotOption,
        ('short',): ShortOption,
        ('long',): LongOption,
        ('front',): FrontOption,
        ('side',): SideOption,
        #('sound_f',): SOUND_F,
        #('soundless_f',): SOUNDLESS_F,
        #('sound_m',): SOUND_M,
        #('soundless_m',): SOUNDLESS_M,
        ('sound',): SoundOption,
        ('soundless',): SoundlessOption,
        ('no sos shopping', 'no shopping'): NoShopOption,
        ('sos shopping', 'shopping'): ShopOption,
        ('coin',): CoinOption,
        ('dollar',): DollarOption,
        ('bull', 'bullion'): BullionOption,
        ('a',): AOption, ('b',): BOption, ('c',): COption, ('d',): DOption,
        ('front 3', 'front three'): FrontThreeOption,
        ('middle', 'middle 6', 'middle six'): MiddleSixOption,
        ('back', 'back 9', 'back nine'): BackNineOption,
        ('checkers',): CheckersOption,
        ('chinese checkers',): ChineseCheckersOption,
        ('find four',): FindFourOption
    }

    locNameIDs = {
        ('alto', 'avenue'): AltoAvenueLocation,
        ('baritone',): BaritoneBoulevardLocation,
        ('barnacle',): BarnacleBoulevardLocation,
        ('elm',): ElmStreetLocation,
        ('lighthouse',): LighthouseLaneLocation,
        ('loopy',): LoopyLaneLocation,
        ('lullaby',): LullabyLaneLocation,
        ('maple',): MapleStreetLocation,
        ('oak',): OakStreetLocation,
        ('pajama',): PajamaPlaceLocation,
        ('polar',): PolarPlaceLocation,
        ('punchline',): PunchlinePlaceLocation,
        ('seaweed',): SeaweedStreetLocation,
        ('silly',): SillyStreetLocation,
        ('sleet',): SleetStreetLocation,
        ('tenor',): TenorTerranceLocation,
        ('walrus', 'way'): WalrusWayLocation,
        ('sellbot hq', 'sbhq'): SellbotHQLocation,
        ('cashbot hq', 'cbhq'): CashbotHQLocation,
        ('lawbot hq', 'lbhq'): LawbotHQLocation,
        ('bossbot hq', 'bbhq'): BossbotHQLocation,
        ('toontown central', 'ttc'): ToontownCentralLocation,
        ('donald\'s dock', 'donalds dock', 'dd'): DonaldsDockLocation,
        ('daisy gardens', 'daisy garden', 'daisy\'s garden', 'daisy\'s gardens', 'daisys garden', 'daisys gardens', 'dg'): DaisyGardensLocation,
        ('minnie\'s melodyland', 'minnie melodyland', 'minnies melodyland'): MinnieMelodylandLocation,
        ('the brrrgh', 'brrrgh', 'tb'): TheBrrrghLocation,
        ('donald\'s dreamland', 'donalds dreamland', 'ddl'): DonaldsDreamlandLocation,
        ('goofy\'s speedway', 'goofys speedway', 'goofy speedway', 'gs'): GoofySpeedwayLocation,
        ('acorn acres', 'acorn', 'acres', 'aa'): AcornAcresLocation
    }

    def __init__(self, module, message):
        self.module = module

    # Users may use various words to refer to a certain mode.
    # This is a list of the common ones that are picked up.
    @classmethod
    def getGroupMode(cls, mode, msg=''):
        #cls.logger.debug('mode (original): {}'.format(mode))
        if mode in ['create', 'make', 'add']:
            mode = GroupManagement.CREATE_MODE
        elif mode in ['edit', 'change'] and gedReq.match(msg):
            mode = GroupManagement.EDIT_MODE
        elif mode in ['delete', 'remove', 'kill', 'rip', 'cancel', 'disband', 'destroy', 'clear']:
            mode = GroupManagement.REMOVE_MODE
        elif mode in ['find', 'list', 'get']:
            mode = GroupManagement.FIND_MODE
        elif mode in ['join'] and gjlReq.match(msg):
            mode = GroupManagement.JOIN_MODE
        elif mode in ['leave']:
            mode = GroupManagement.LEAVE_MODE

        #cls.logger.debug('mode: {}'.format(mode))
        return mode

    # Creates a group for the user
    def createRequest(self, user, target, groupType, groupLocation, groupOptions, district, company):
        #self.logger.debug('{} requested CREATE_MODE: groupType: {}; groupLocation: {}; groupOptions: {}; district: {}; company: {}'.format(
        #    user, groupType, groupLocation, groupOptions, district, company))
        # Verify we have everything we need.
        if not groupType:
            return 'I didn\'t catch what kind of group you wanted, {}.'.format(user.mention)
        if not groupLocation:
            return 'I didn\'t catch where this group was going to be, {}.'.format(user.mention)

        # If the group is not in a valid location (say, a Factory in Lawbot HQ) and the valid locations
        # list does not consist of an inheritable class (say, AltoAvenueLocation and StreetLocation)
        elif groupLocation not in groupType.locations and (len(groupType.locations) == 1 and not issubclass(groupLocation, groupType.locations[0])):
            return 'You can\'t create a **{}** group in **{}**, {}.'.format(groupType.name, groupLocation.name, user.mention)

        if not district:
            return 'I didn\'t catch what district this group was going to be in, {}.'.format(user.mention)

        try:
            self.TTGroup.createGroup(user, groupType, groupOptions, groupLocation, district, company)
            o = ' '.join([option.name for option in groupOptions])
            s = ' ' if groupOptions else ''
            self.logger.info('@{} created a {}{}{} group in {}, {} (company: {})'.format(
                user.name, o, s, groupType.name, groupLocation.name, district, company))
            return 'Your **{}{}{}** group has been created, {}.'.format(o, s, groupType.name, user.mention)
        except MaximumGroupException:
            return 'You already have a group, {}!'.format(user.mention)
        except TooManyPlayersException:
            return 'Woah there! You can\'t have *that* many Toons in your group, {}! {}'.format(user.mention, 'We don\'t need to create groups that are already full.' if company == groupType.maxPlayers else 'Try a few less.')
        except TooFewPlayersException:
            return 'Woah there! You\'ve gotta have *somebody* in your group, {}!'.format(user.mention)

    # Edits an attribute of a user's group
    def editRequest(self, user, target, editType, applyType, value, **optionalValues):
        self.logger.debug('{} requested EDIT_MODE: editType: {}; applyType: {}, value: {}, optionalValues: {}'.format(
            user, editType, applyType, value, optionalValues))
        group = self.TTGroup.userOwnsGroup(user)
        if not group and self.TTGroup.userInGroup(user):
            if editType == 'company':
                group = self.TTGroup.userInGroup(user)
            else:
                return 'Woah there, {}! You can\'t make those changes! You don\'t own the group.'.format(user.mention)
        elif not group:
            return 'You don\'t have a group, {}!'.format(user.mention)
        if applyType == 'by' and editType != 'company':
            return 'You cannot use the term \'by\' when editing your group {}, {}.'.format(editType, user.mention)

        newLocation = None
        orgOptions = []
        droppedOptions = []

        if editType == 'company':
            try:
                value = int(value)
            except ValueError:
                if value in ['one', 'two', 'three', 'four', 'five', 'six']:
                    value = ['zero', 'one', 'two', 'three', 'four', 'five', 'six'].index(value)
                else:
                    return 'You must specify a number when editing your group company, {}.'.format(user.mention)

        elif editType == 'type':
            if not optionalValues['groupType']:
                return 'I didn\'t catch what kind of group you wanted to change to, {}.'.format(user.mention)

            if group.type.maxPlayers and group.type.maxPlayers < group.members.getPlayerCount():
                return 'You can\'t change your group type to **{}** {}, you currently have too many players.'.format(optionalValues['groupType'], user.mention)

            if group.location not in optionalValues['groupType'].locations and optionalValues['groupType'].locations[0] != GroupLocation:
                # Change group location to a valid location for the group type if it's invalid.
                newLocation = optionalValues['groupType'].locations[0]
                # Fallback in case the group can be in any playground or street.
                if newLocation == PlaygroundLocation:
                    newLocation = ToontownCentralLocation
                elif newLocation == StreetLocation:
                    newLocation = LoopyLaneLocation
                self.TTGroup.editGroup(user, 'location', applyType, newLocation)

            orgOptions.extend(group.options)
            self.TTGroup.editGroup(user, 'options', applyType, group.options)
            for option in orgOptions:
                if option not in group.options:
                    droppedOptions.append(option)

            value = optionalValues['groupType']

        elif editType == 'location':
            if not optionalValues['groupLocation']:
                return 'I didn\'t catch where you wanted to change your group\'s location to, {}.'.format(user.mention)
            elif optionalValues['groupLocation'] not in group.type.locations and (len(group.type.locations) == 1 and not issubclass(optionalValues['groupLocation'], group.type.locations[0])):
                return 'You can\'t change your group\'s location to **{}**, {}.'.format(optionalValues['groupLocation'].name, user.mention)
            value = optionalValues['groupLocation']

        elif editType == 'options':
            value = optionalValues['groupOptions']

        elif editType == 'district':
            if not optionalValues['district']:
                return 'I didn\'t catch what district you wanted to change your group to, {}.'.format(user.mention)
            value = optionalValues['district']

        try:
            self.TTGroup.editGroup(user, editType, applyType, value)
            self.logger.info('@{} edited group {} {} {}'.format(user.name, editType, applyType, value))
            msg = 'Your group\'s {} {} changed {} {}, {}.'.format(
                editType, 'were' if editType == 'options' else 'was', applyType, value, user.mention)
            if newLocation:
                msg += '\nYour group\'s location was also automatically changed to **{}**.'.format(newLocation.name)
            if droppedOptions:
                msg += '\nThese group options were also automatically removed: *{}*'.format(', '.join([option.name for option in droppedOptions]))
            return msg
        except OwnerException:
            return 'Woah there, {}! You can\'t make those changes! You don\'t own the group.'.format(user.mention)
        except NoGroupException:
            return 'You don\'t have a group, {}!'.format(user.mention)
        except ValueError:
            return 'You must choose a value other than 0, {}.'.format(user.mention)
        except TooManyPlayersException:
            if applyType == 'to':
                return 'Woah there! You can\'t have *that* many Toons in your group, {}! Try a few less.'.format(user.mention)
            else:
                return 'There\'s too many people in this group already, {}! You can\'t add anymore.'.format(user.mention)
        except TooFewPlayersException:
            return 'You can\'t change your company to that, {}! {}'.format(user.mention,
                'There wouldn\'t be anybody left in the group.' if applyType == 'by' else 'You must choose a value higher than 0.')

    # Delete a group if the user owns it.
    def removeRequest(self, user, target):
        self.logger.debug('{} requested REMOVE_MODE'.format(user))
        try:
            self.TTGroup.removeGroup(user)
            self.logger.info('@{} deleted their group.'.format(user.name))
            return 'Your group has been deleted, {}.'.format(user.mention)
        except NoGroupException:
            return 'You don\'t have a group, {}!'.format(user.mention)

    # Join a group another user owns.
    def joinRequest(self, user, target, info, company):
        self.logger.debug('{} requested JOIN_MODE: info: {}; company: {}'.format(user, info, company))
        if info.mentions:
            owner = info.mentions[0]
        else:
            name = gjlReq.match(info.content.lower()).group(2)
            names = []
            names.extend([group.owner if group.toonHQ else group.ower.name for group in self.TTGroup.groups])

            owner = discord.utils.get(self.ToonTracker.get_all_members(), name=name)
            if not owner:
                if didyoumean.didYouMean(name, names):
                    owner = didyoumean.didYouMean(name, names)
        if not owner:
            return 'I don\'t know who **{}** is, {}.'.format(gjlReq.match(info.content.lower()).group(2).strip(), user.mention)

        if type(owner) == str:
            return 'You can\'t interact with ToonHQ groups as of yet {}, sorry.'.format(user.mention)

        try:
            self.TTGroup.joinGroup(user, owner, company)
            self.logger.info('@{} joined @{}\'s group (company: {}).'.format(user.name, pwner.name, company))
            return 'You\'ve joined **{}**\'s group, {}.'.format(owner.mention, user.mention)
        except NoGroupException:
            return '**{}** doesn\'t have a group, {}.'.format(owner.mention, user.mention)
        except MaximumGroupException:
            return 'You\'re already in a group, {}!'.format(user.mention)
        except TooManyPlayersException:
            return 'There\'s too many people in this group already, {}! Try another one{}'.format(user.mention, '.' if company == 1 else ', or work it out with your friends so that some of you can join.')
        except ToonHQException:
            return 'You can\'t interact with ToonHQ groups as of yet {}, sorry.'.format(user.mention)

    # Remove a user from a group
    def leaveRequest(self, user, target):
        self.logger.debug('{} requested LEAVE_MODE'.format(user))
        try:
            self.TTGroup.leaveGroup(user)
            self.logger.info('@{} left the group they were in.'.format(user.name))
            return 'You have left the group you were in, {}.'.format(user.mention)
        except OwnerException:
            return '{} You must remove your group with the "remove" command as you are the owner of the group.'.format(user.mention)
        except NoGroupException:
            return 'You\'re not in a group, {}!'.format(user.mention)

    # Look up groups with certain parameters
    def findRequest(self, user, target, info, groupType, groupOptions):
        USER = 1
        GTYPE = 2
        SEARCH_BY = GTYPE
        owner = None
        readyToSend = False

        self.logger.debug('{} requested FIND_MODE: info: {}; groupType: {}; groupOptions: {}'.format(
            user, info, groupType, groupOptions))
        if gifReq.match(self.message.content) and not groupType:
            if info.mentions:
                owner = info.mentions[0]
            else:
                name = gifReq.match(self.message.content).group(2)
                names = []
                names.extend([group.owner if group.toonHQ else group.owner.name for group in self.TTGroup.groups])
                names.extend([member.name for member in self.ToonTracker.get_all_members()])
                if didyoumean.didYouMean(name, names):
                    owner = didyoumean.didYouMean(name, names)
                else:
                    return 'I don\'t know who **{}** is, {}.'.format(name, user.mention)
            group = self.TTGroup.userOwnsGroup(user=owner)
            if not group:
                return '**{}** doesn\'t have a group, {}.'.format(owner if type(owner) == str else owner.mention, user.mention)
        else:
            if not groupType:
                groupType = GroupType
            groups = self.TTGroup.getGroups(groupType=groupType, options=groupOptions)

        if owner:
            newMsg = '__**{}{}{}** in **{}** in **{}** *({}{}{} players)*__'.format(
                ' '.join([option.name for option in group.options]),
                ' ' if group.options else '',
                group.type.name,
                group.location.name,
                group.district,
                group.members.getPlayerCount(),
                '/' if group.type.maxPlayers else '',
                group.type.maxPlayers if group.type.maxPlayers else ''
            )

            for member in group.members.memberObjs:
                company = member.company - 1
                newMsg += '\n\t{}{}'.format(member.user if group.toonHQ else member.user.mention, ' *(with {} other{})*'.format(company, 's' if company > 1 else '') if company > 1 else '')
                readyToSend = True
        else:
            newMsg = '__***Here\'s what I found:***__'
            limitedMsg = '__***Here\'s what I found:***__'
            purgedMsg = '__***Here\'s what I found:***__'

            x = 0
            y = 0
            for group in groups:
                grpStr = '\n\t**{}{}{}** group in **{}** owned by **{}** *({}{}{} players)*'.format(
                    ' '.join([option.name for option in group.options]),
                    ' ' if group.options else '',
                    group.type.name,
                    group.district,
                    group.owner if group.toonHQ else group.owner.mention,
                    group.members.getPlayerCount(),
                    '/' if group.type.maxPlayers else '',
                    group.type.maxPlayers if group.type.maxPlayers else ''
                )
                newMsg += grpStr
                if group.members.getPlayerCount() != group.type.maxPlayers:
                    limitedMsg += grpStr
                    x += 1
                    if x <= 20:
                        purgedMsg = limitedMsg
                else:
                    y += 1

                readyToSend = True

        if readyToSend and not owner:
            if x <= 20:
                return limitedMsg + ("\n\n\t**...and {} other full groups**".format(y) if y else "")
            else:
                return purgedMsg + "\n\n\t**...and {} others**".format(x - 20)
        elif owner:
            return newMsg
        else:
            if groupType and groupType != GroupType:
                return 'Sorry {}, I couldn\'t find any **{}{}{}** groups.'.format(user.mention, ' '.join([option.name for option in groupOptions]), ' ' if groupOptions else '', groupType.name)
            elif groupOptions:
                return 'Sorry {}, I couldn\'t find any **{}** groups.'.format(user.mention, ' '.join([option.name for option in groupOptions]))
            else:
                return 'Sorry {}, I couldn\'t find any groups.'.format(user.mention)


class GroupMsgHandler(MessageHandler):
    def handle(module, message):
        CREATE = 'create'
        EDIT = 'edit'
        REMOVE = 'remove'
        FIND = 'find'
        JOIN = 'join'
        LEAVE = 'leave'

        user = message.author
        target = message.channel
        msg = message.content.lower()
        groupRequest = GroupRequest(message, ToonTracker)
        
        mode = None

        # Group owner is still active
        if ToonTracker.groupManager.userOwnsGroup(message.author):
            ToonTracker.groupManager.bumpGroup(message.author)

        # Is this a legit request bro
        if gcmReq.match(msg) or msg.endswith('group') or msg.endswith('groups'):
            if gcmReq.match(msg):
                strMode = gcmReq.match(msg).group(1)
            else:
                strMode = 'find'
            mode = GroupRequest.getGroupMode(strMode, msg)
        else:
            return

        glogger.debug('Verified message to be a group request (msg: {}).'.format(msg))

        groupType = getAttributeFromMatch(groupRequest.typeNameIDs, grpReq.match(msg).group(1)) if grpReq.match(msg) else None
        groupLocation = getAttributeFromMatch(groupRequest.locNameIDs, glcReq.match(msg).group(1)) if glcReq.match(msg) else None
        if groupType and len(groupType.locations) == 1 and groupType.locations[0] not in [GroupLocation, PlaygroundLocation, StreetLocation]:
            groupLocation = groupType.locations[0]
        groupOptions = []
        if gopReq.match(msg):
            for option in gopReq.match(msg).captures(1):
                option = getAttributeFromMatch(groupRequest.optNameIDs, option.strip())
                if groupType == CGCType and option == FrontOption:
                    option = FrontThreeOption
                elif option:
                    groupOptions.append(option)

        district = checkForDistrict(msg)

        company = 1
        if gplReq.match(msg.lower()):
            inAddition = True if gplReq.match(msg.lower()).group(2) else False
            try:
                company = int(gplReq.match(msg.lower()).group(1)) + (1 if inAddition else 0)
            except ValueError:
                company = ['zero', 'one', 'two', 'three', 'four', 'five', 'six'].index(gplReq.match(msg.lower()).group(1)) + (1 if inAddition else 0)

        if mode == GroupManagement.CREATE_MODE:
            return groupRequest.createRequest(user, target, groupType, groupLocation, groupOptions, district, company)
      
        elif mode == GroupManagement.EDIT_MODE:
            return groupRequest.editRequest(user, target, gedReq.match(msg).group(2), gedReq.match(msg).group(3), gedReq.match(msg).group(4),
                groupType=groupType, groupLocation=groupLocation, groupOptions=groupOptions, district=district)

        elif mode == GroupManagement.REMOVE_MODE:
            return groupRequest.removeRequest(user, target)

        elif mode == GroupManagement.JOIN_MODE:
            return groupRequest.joinRequest(user, target, message, company)

        elif mode == GroupManagement.LEAVE_MODE:
            return groupRequest.leaveRequest(user, target)

        elif mode == GroupManagement.FIND_MODE:
            return groupRequest.findRequest(user, target, message, groupType, groupOptions)
