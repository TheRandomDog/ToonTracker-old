# This is a horrible file which contains nothing but unnecessary classes
# that have no reason to exist but to waste space and time.

TTR_ICON = 'https://b.thumbs.redditmedia.com/PDyRp4J5SnEd03ZG24TN3CDirUjHX8Lv9_TAut-u0ec.png'

class CogType:
    name = ''
    def __str__(self): return self.name if self.name else repr(self)

class BossbotType(CogType):
    name = 'Bossbot'

class CashbotType(CogType):
    name = 'Cashbot'

class LawbotType(CogType):
    name = 'Lawbot'

class SellbotType(CogType):
    name = 'Sellbot'

class Cog:
    name = ''
    type = CogType
    def plural(self): 
        if self.name:
            if self.isSkelecog:
                return self.name + 's (Skelecogs)'
            else:
                return str(self) + 's'
    def __init__(self, isV2=False, isSkelecog=False):
        self.isV2 = isV2
        self.isSkelecog = isSkelecog
    def __str__(self):
        v = 'Version 2.0 ' if self.isV2 else ''
        s = ' (Skelecog)' if self.isSkelecog else ''
        return v + self.name + s if self.name else repr(self)
    def __eq__(self, other): 
        if isinstance(other, Cog): 
            return self.name == other.name and self.isV2 == other.isV2 and self.isSkelecog == other.isSkelecog
        else:
            return self is other

class ColdCallerCog(Cog):
    name = 'Cold Caller'
    type = SellbotType

class TelemarketerCog(Cog):
    name = 'Telemarketer'
    type = SellbotType

class NameDropperCog(Cog):
    name = 'Name Dropper'
    type = SellbotType

class GladHanderCog(Cog):
    name = 'Glad Hander'
    type = SellbotType

class MoverShakerCog(Cog):
    name = 'Mover & Shaker'
    type = SellbotType
    @classmethod
    def plural(cls): return 'Movers & Shakers'

class TwoFaceCog(Cog):
    name = 'Two-Face'
    type = SellbotType

class TheMinglerCog(Cog):
    name = 'The Mingler'
    type = SellbotType

class MrHollywoodCog(Cog):
    name = 'Mr. Hollywood'
    type = SellbotType

class ShortChangeCog(Cog):
    name = 'Short Change'
    type = CashbotType

class PennyPincherCog(Cog):
    name = 'Penny Pincher'
    type = CashbotType

class TightwadCog(Cog):
    name = 'Tightwad'
    type = CashbotType

class BeanCounterCog(Cog):
    name = 'Bean Counter'
    type = CashbotType

class NumberCruncherCog(Cog):
    name = 'Number Cruncher'
    type = CashbotType

class MoneyBagsCog(Cog):
    name = 'Money Bags'
    type = CashbotType
    @classmethod
    def plural(cls): return 'Money Bags'

class LoanSharkCog(Cog):
    name = 'Loan Shark'
    type = CashbotType

class RobberBaronCog(Cog):
    name = 'Robber Baron'
    type = CashbotType

class BottomFeederCog(Cog):
    name = 'Bottom Feeder'
    type = LawbotType

class BloodsuckerCog(Cog):
    name = 'Bloodsucker'
    type = LawbotType

class DoubleTalkerCog(Cog):
    name = 'Double Talker'
    type = LawbotType

class AmbulanceChaserCog(Cog):
    name = 'Ambulance Chaser'
    type = LawbotType

class BackstabberCog(Cog):
    name = 'Back Stabber'
    type = LawbotType

class SpinDoctorCog(Cog):
    name = 'Spin Doctor'
    type = LawbotType

class LegalEagleCog(Cog):
    name = 'Legal Eagle'
    type = LawbotType

class BigWigCog(Cog):
    name = 'Big Wig'
    type = LawbotType

class FlunkyCog(Cog):
    name = 'Flunky'
    type = BossbotType
    @classmethod
    def plural(cls): return 'Flunkies'

class PencilPusherCog(Cog):
    name = 'Pencil Pusher'
    type = BossbotType

class YesmanCog(Cog):
    name = 'Yesman'
    type = BossbotType
    @classmethod
    def plural(cls): return 'Yesmen'

class MicromanagerCog(Cog):
    name = 'Micromanager'
    type = BossbotType

class DownsizerCog(Cog):
    name = 'Downsizer'
    type = BossbotType

class HeadHunterCog(Cog):
    name = 'Head Hunter'
    type = BossbotType

class CorporateRaiderCog(Cog):
    name = 'Corporate Raider'
    type = BossbotType

class TheBigCheeseCog(Cog):
    name = 'The Big Cheese'
    type = BossbotType


class District:
    name = ''
    def __init__(self, name): self.name = name
    def __str__(self): return self.name


cogs = (
    ColdCallerCog,
    TelemarketerCog,
    NameDropperCog,
    GladHanderCog,
    MoverShakerCog,
    TwoFaceCog,
    TheMinglerCog,
    MrHollywoodCog,
    ShortChangeCog,
    PennyPincherCog,
    TightwadCog,
    BeanCounterCog,
    NumberCruncherCog,
    MoneyBagsCog,
    LoanSharkCog,
    RobberBaronCog,
    BottomFeederCog,
    BloodsuckerCog,
    DoubleTalkerCog,
    AmbulanceChaserCog,
    BackstabberCog,
    SpinDoctorCog,
    LegalEagleCog,
    BigWigCog,
    FlunkyCog,
    PencilPusherCog,
    YesmanCog,
    MicromanagerCog,
    DownsizerCog,
    HeadHunterCog,
    CorporateRaiderCog,
    TheBigCheeseCog
)
cogsStr = [cog.name for cog in cogs]

districts = [
    District("Acrylic Acres"),
    District("Avant Gardens"),
    District("Baroque Bluffs"),
    District("Bliss Bayou"),
    District("Brush Bay"),
    District("Colorful Canvas"),
    District("Eraser Oasis"),
    District("Graphite Gulch"),
    District("Paintbrush Field"),
    District("Pastel Plains"),
    District("Pianissimo Plateau"),
    District("Pigment Point"),
    District("Renaissance River"),
    District("Stencil Steppe"),
    District("Vibrant Valley"),
    District("Watercolor Woods")
]
districtsStr = [district.name for district in districts]

def populateDistricts(district):
    districts.append(District(district))
    districtsStr.append(district)

def checkForDistrict(msg):
    return
    #for district in districtsStr:
    #    for word in msg.split(" "):
    #        if didyoumean.didYouMean(word, district.lower().split(' ')):
    #            return district

departments = (
    BossbotType,
    LawbotType,
    CashbotType,
    SellbotType
)
departmentsStr = [dep.name for dep in departments]

companyLimit = 100

class GroupOption:
    id = None
    name = ''

class OneStoryOption(GroupOption):
    id = 1
    name = 'One Story'

class TwoStoryOption(GroupOption):
    id = 2
    name = 'Two Story'

class ThreeStoryOption(GroupOption):
    id = 3
    name = 'Three Story'

class FourStoryOption(GroupOption):
    id = 4
    name = 'Four Story'

class FiveStoryOption(GroupOption):
    id = 5
    name = 'Five Story'

class SellbotOption(GroupOption):
    id = 6
    name = 'Sellbot'

class CashbotOption(GroupOption):
    id = 7
    name = 'Cashbot'

class LawbotOption(GroupOption):
    id = 8
    name = 'Lawbot'

class BossbotOption(GroupOption):
    id = 9
    name = 'Bossbot'

class ShortOption(GroupOption):
    id = 10
    name = 'Short'

class LongOption(GroupOption):
    id = 11
    name = 'Long'

class FrontOption(GroupOption):
    id = 12
    name = 'Front'

class SideOption(GroupOption):
    id = 13
    name = 'Side'

class SoundOption(GroupOption):
    id = 14  # and 21
    name = 'Sound'

class SoundlessOption(GroupOption):
    id = 15  # and 22
    name = 'Soundless'

class NoShopOption(GroupOption):
    id = 16
    name = 'No Shopping'

class ShopOption(GroupOption):
    id = 17
    name = 'Shopping'

class CoinOption(GroupOption):
    id = 18
    name = 'Coin'

class DollarOption(GroupOption):
    id = 19
    name = 'Dollar'

class BullionOption(GroupOption):
    id = 20
    name = 'Bullion'

class AOption(GroupOption):
    id = 23
    name = 'A'

class BOption(GroupOption):
    id = 24
    name = 'B'

class COption(GroupOption):
    id = 25
    name = 'C'

class DOption(GroupOption):
    id = 26
    name = 'D'

class FrontThreeOption(GroupOption):
    id = 27
    name = 'Front Three'

class MiddleSixOption(GroupOption):
    id = 28
    name = 'Middle Six'

class BackNineOption(GroupOption):
    id = 29
    name = 'Back Nine'

class ToonUpOption(GroupOption):
    id = 30
    name = 'Toon-Up'

class TrapOption(GroupOption):
    id = 31
    name = 'Trap'

class LureOption(GroupOption):
    id = 32
    name = 'Lure'

class SoundOption(GroupOption):
    id = 33
    name = 'Sound'

class ThrowOption(GroupOption):
    id = 34
    name = 'Throw'

class SquirtOption(GroupOption):
    id = 35
    name = 'Squirt'

class DropOption(GroupOption):
    id = 36
    name = 'Drop'

class CheckersOption(GroupOption):
    id = 37
    name = 'Checkers'

class ChineseCheckersOption(GroupOption):
    id = 38
    name = 'Chinese Checkers'

class FindFourOption(GroupOption):
    id = 39
    name = 'Find Four'



class GroupLocation:
    name = ''

    def __init__(self):
        raise NotImplementedError

class PlaygroundLocation(GroupLocation):
    name = ''

class StreetLocation(GroupLocation):
    name = ''

class AltoAvenueLocation(StreetLocation):
    name = 'Alto Avenue'

class BaritoneBoulevardLocation(StreetLocation):
    name = 'Baritone Boulevard'

class BarnacleBoulevardLocation(StreetLocation):
    name = 'Barnacle Boulevard'

class ElmStreetLocation(StreetLocation):
    name = 'Elm Street'

class LighthouseLaneLocation(StreetLocation):
    name = 'Lighthouse Lane'

class LoopyLaneLocation(StreetLocation):
    name = 'Loopy Lane'

class LullabyLaneLocation(StreetLocation):
    name = 'Lullaby Lane'

class MapleStreetLocation(StreetLocation):
    name = 'Maple Street'

class OakStreetLocation(StreetLocation):
    name = 'Oak Street'

class PajamaPlaceLocation(StreetLocation):
    name = 'Pajama Place'

class PolarPlaceLocation(StreetLocation):
    name = 'Polar Place'

class PunchlinePlaceLocation(StreetLocation):
    name = 'Punchline Place'

class SeaweedStreetLocation(StreetLocation):
    name = 'Seaweed Street'

class SillyStreetLocation(StreetLocation):
    name = 'Silly Street'

class SleetStreetLocation(StreetLocation):
    name = 'Sleet Street'

class TenorTerranceLocation(StreetLocation):
    name = 'Tenor Terrance'

class WalrusWayLocation(StreetLocation):
    name = 'Walrus Way'

class SellbotHQLocation(GroupLocation):
    name = 'Sellbot HQ'

class CashbotHQLocation(GroupLocation):
    name = 'Cashbot HQ'

class LawbotHQLocation(GroupLocation):
    name = 'Lawbot HQ'

class BossbotHQLocation(GroupLocation):
    name = 'Bossbot HQ'

class ToontownCentralLocation(PlaygroundLocation):
    name = 'Toontown Central'

class DonaldsDockLocation(PlaygroundLocation):
    name = 'Donald\'s Dock'

class DaisyGardensLocation(PlaygroundLocation):
    name = 'Daisy Gardens'

class MinnieMelodylandLocation(PlaygroundLocation):
    name = 'Minnie\'s Melodyland'

class TheBrrrghLocation(PlaygroundLocation):
    name = 'The Brrrgh'

class DonaldsDreamlandLocation(PlaygroundLocation):
    name = 'Donald\'s Dreamland'

class GoofySpeedwayLocation(GroupLocation):
    name = 'Goofy Speedway'

class AcornAcresLocation(GroupLocation):
    name = 'Acorn Acres'



class GroupType:
    id = None
    options = []
    locations = []
    name = ''
    maxPlayers = 0

    def __init__(self):
        raise NotImplementedError

class BuildingType(GroupType):
    id = 1
    options = [OneStoryOption, TwoStoryOption, ThreeStoryOption, FourStoryOption, FiveStoryOption, SellbotOption, CashbotOption, LawbotOption, BossbotOption]
    locations = [StreetLocation]
    name = 'Building'
    maxPlayers = 4

class FactoryType(GroupType):
    id = 2
    options = [FrontOption, SideOption, SoundOption, SoundlessOption]
    locations = [SellbotHQLocation]
    name = 'Factory'
    maxPlayers = 4

class VPType(GroupType):
    id = 3
    options = [NoShopOption, ShopOption]
    locations = [SellbotHQLocation]
    name = 'VP'
    maxPlayers = 8

class MintType(GroupType):
    id = 4
    options = [CoinOption, DollarOption, BullionOption, SoundOption, SoundlessOption]
    locations = [CashbotHQLocation]
    name = 'Mint'
    maxPlayers = 4

class CFOType(GroupType):
    id = 5
    locations = [CashbotHQLocation]
    name = 'CFO'
    maxPlayers = 8

class DAType(GroupType):
    id = 6
    options = [AOption, BOption, COption, DOption]
    locations = [LawbotHQLocation]
    name = 'DA Office'
    maxPlayers = 4

class CJType(GroupType):
    id = 7
    locations = [LawbotHQLocation]
    name = 'CJ'
    maxPlayers = 8

class CGCType(GroupType):
    id = 8
    options = [FrontThreeOption, MiddleSixOption, BackNineOption]
    locations = [BossbotHQLocation]
    name = 'CGC'
    maxPlayers = 4

class CEOType(GroupType):
    id = 9
    locations = [BossbotHQLocation]
    name = 'CEO'
    maxPlayers = 8

class BeanfestType(GroupType):
    id = 10
    locations = [GroupLocation]
    name = 'Beanfest'

class TaskType(GroupType):
    id = 11
    locations = [GroupLocation]
    name = 'ToonTask'
    maxPlayers = 8

class TrainingType(GroupType):
    id = 12
    locations = [GroupLocation]
    options = [ToonUpOption, TrapOption, LureOption, SoundOption, ThrowOption, SquirtOption, DropOption]
    name = 'Gag Training'
    maxPlayers = 8

class RacingType(GroupType):
    id = 13
    locations = [GoofySpeedwayLocation]
    name = 'Racing'
    maxPlayers = 4

class GolfType(GroupType):
    id = 14
    locations = [AcornAcresLocation]
    name = 'Golf'
    maxPlayers = 4

class TrolleyType(GroupType):
    id = 15
    locations = [PlaygroundLocation]
    name = 'Trolley'
    maxPlayers = 4

class GameType(GroupType):
    id = 16
    locations = [AcornAcresLocation]
    options = [CheckersOption, ChineseCheckersOption, FindFourOption]
    name = 'Game'

optionIDs = {
    1: OneStoryOption,
    2: TwoStoryOption,
    3: ThreeStoryOption,
    4: FourStoryOption,
    5: FiveStoryOption,
    6: SellbotOption,
    7: CashbotOption,
    8: LawbotOption,
    9: BossbotOption,
    10: ShortOption,
    11: LongOption,
    12: FrontOption,
    13: SideOption,
    14: SoundOption,
    15: SoundlessOption,
    16: NoShopOption,
    17: ShopOption,
    18: CoinOption,
    19: DollarOption,
    20: BullionOption,
    21: SoundOption,
    22: SoundlessOption,
    23: AOption,
    24: BOption,
    25: COption,
    26: DOption,
    27: FrontThreeOption,
    28: MiddleSixOption,
    29: BackNineOption,
    30: ToonUpOption,
    31: TrapOption,
    32: LureOption,
    33: SoundOption,
    34: ThrowOption,
    35: SquirtOption,
    36: DropOption,
    37: CheckersOption,
    38: ChineseCheckersOption,
    39: FindFourOption
}

typeIDs = {
    1: BuildingType,
    2: FactoryType,
    3: VPType,
    4: MintType,
    5: CFOType,
    6: DAType,
    7: CJType,
    8: CGCType,
    9: CEOType,
    10: BeanfestType,
    11: TaskType,
    12: TrainingType,
    13: RacingType,
    14: GolfType,
    15: TrolleyType,
    16: GameType
}

locationNames = {
    'Alto Avenue': AltoAvenueLocation,
    'Baritone Boulevard': BaritoneBoulevardLocation,
    'Barnacle Boulevard': BarnacleBoulevardLocation,
    'Elm Street': ElmStreetLocation,
    'Lighthouse Lane': LighthouseLaneLocation,
    'Loopy Lane': LoopyLaneLocation,
    'Lullaby Lane': LullabyLaneLocation,
    'Maple Street': MapleStreetLocation,
    'Oak Street': OakStreetLocation,
    'Pajama Place': PajamaPlaceLocation,
    'Polar Place': PolarPlaceLocation,
    'Punchline Place': PunchlinePlaceLocation,
    'Seaweed Street': SeaweedStreetLocation,
    'Silly Street': SillyStreetLocation,
    'Sleet Street': SleetStreetLocation,
    'Tenor Terrance': TenorTerranceLocation,
    'Walrus Way': WalrusWayLocation,
    'Sellbot HQ': SellbotHQLocation,
    'Cashbot HQ': CashbotHQLocation,
    'Lawbot HQ': LawbotHQLocation,
    'Bossbot HQ': BossbotHQLocation,
    'Toontown Central': ToontownCentralLocation,
    'Donald\'s Dock': DonaldsDockLocation,
    'Daisy Gardens': DaisyGardensLocation,
    'Minnie\'s Melodyland': MinnieMelodylandLocation,
    'The Brrrgh': TheBrrrghLocation,
    'Donald\'s Dreamland': DonaldsDreamlandLocation,
    'Goofy Speedway': GoofySpeedwayLocation,
    'Acorn Acres': AcornAcresLocation
}
