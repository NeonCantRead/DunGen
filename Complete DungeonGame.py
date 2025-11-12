import os 
from copy import deepcopy
import dataclasses as dc
from time import sleep
import random
import turtle
import math
from typing import Dict, Tuple, List, Optional

# Global variables
ccdone = False
vowels = {"a", "e", "i", "o", "u", "A", "E", "I", "O", "U"}
pclasses = ["Mage", "Warrior", "Archer", "Spellblade"]
reqrooms = 0
invalidroomlocs = set()
validroomlocs = set()
dorkondict = {"north": "south", "south": "north", "east": "west", "west": "east"}
devmode = None
mapcomplexity = 2
roomthemes = ["castle", "cave", "ruin"]
perimiterrooms = []
roombuffer = []
specialroomlocs = [(0, 0)]
roomcolors = {"ruin": (0, 102, 0), "castle": (192, 192, 192), "cave": (102, 0, 51)}
devt = None
devmap = None

# Dataclasses
@dc.dataclass
class Attack:
    Name: str = "Unnamed Attack"
    Hits: int = 0
    Damage: int = 0
    Desc: str = "Attack Missing Description"
    CD: int = 1
    Healing: int = 0
    DtypeOVRW: str = None
    ImbueReq: Optional[List] = None
    MPCost: int = 0

@dc.dataclass
class WeaponType:
    Name: str
    Attacks: list[Attack]
    Desc: str = "Weapon Missing Description"
    DamageType: str = "Normal"

NBWeapon = WeaponType("", [])

@dc.dataclass
class ClassType:
    Name: str = ""
    Weapons: list[WeaponType] = None
    HPmult: float = 1
    MPmult: float = 1
    Desc: str = "Class Missing Description"

NBClass = ClassType()

@dc.dataclass
class Player:
    Name: str = ""
    Class: ClassType = None
    Weapon: WeaponType = None
    Skills: list = dc.field(default_factory=list)
    MHP: int = 100
    MMP: int = 100
    HP: int = 100
    MP: int = 100
    Luck: float = 1.0
    Imbue: Optional[str] = None
    DMGmult: float = 1.0
    Coins: int = 0
    Inventory: list = dc.field(default_factory=list)
    EquippedRing: Optional['Equipment'] = None
    EquippedNecklace: Optional['Equipment'] = None
    EquippedCrown: Optional['Equipment'] = None
    AttackCooldowns: dict = dc.field(default_factory=dict)
    CurrentRoom: Tuple[int, int] = (0, 0)

player = Player("", NBClass, NBWeapon)

@dc.dataclass
class Equipment:
    Type: str
    Name: str
    Stat1: Optional[List] = None
    Stat2: Optional[List] = None
    Stat3: Optional[List] = None
    Imbue: Optional[str] = None
    Value: int = 0
    Consumable: bool = False
    Uses: Optional[int] = None
    Action: Optional[List] = None
    Description: str = ""

@dc.dataclass
class Enemy:
    Name: str
    HP: int
    MaxHP: int
    Damage: int
    Defense: int
    Attacks: List[Attack]
    Desc: str = ""
    Loot: List[Equipment] = dc.field(default_factory=list)
    CoinDrop: int = 0

@dc.dataclass
class Poi:
    Type: str
    Name: str
    Contents: list
    Revealed: bool = True
    Locked: bool = False
    Trapped: bool = False
    Interacted: bool = False
    Description: str = ""

@dc.dataclass
class Room:
    Theme: str = "Unassigned"
    Size: str = "medium"
    Desc: str = "Description Not Generated"
    Diff: int = 0
    Pois: list[Poi] = dc.field(default_factory=list)
    Connections: dict = dc.field(default_factory=dict)
    Enemies: list[Enemy] = dc.field(default_factory=list)
    Visited: bool = False
    Cleared: bool = False

roomids: Dict[Tuple[int, int], Room] = {}

# Library Setup
def Librarysetup():
    global class_list, weapon_list, equipment_library, enemy_templates
    
    # Default attacks available to all weapons (zero cooldown, always available)
    BasicStrike = Attack("Basic Strike", 1, 5, "A simple attack", 0, 0, None, None, 0)
    
    # Attacks
    QSlash = Attack("Quick Slash", 2, 3, "Two quick slashes", 2, 0, None, None, 0)
    HSlash = Attack("Heavy Slash", 1, 8, "One powerful strike", 2, 0, None, None, 0)
    Thrust = Attack("Thrust", 1, 4, "A piercing thrust", 1, 0, None, None, 0)
    
    Reap = Attack("Reap", 1, 10, "Steal your enemies lifeforce", 5, 5, None, None, 5)
    Whirlwind = Attack("Whirlwind", 4, 2, "Spin rapidly hitting multiple times", 5, 0, "ASK", None, 10)
    
    GreatSlam = Attack("Sword Slam", 1, 12, "Slam the flat of your blade", 3, 0, "Blunt", None, 0)
    Cleave = Attack("Cleaving Strike", 1, 20, "One massive attack", 10, -5, None, None, 0)
    
    EldrichBlast = Attack("Otherworldly Bang", 3, 5, "Fires magical blasts", 4, 0, "PLAYER", None, 15)
    
    Fireball = Attack("Fireball", 1, 15, "Launch a ball of fire", 3, 0, "Fire", None, 20)
    Frostbolt = Attack("Frostbolt", 1, 12, "Freeze your enemy", 3, 0, "Ice", None, 20)
    BurningHands = Attack("Burning Hands", 2, 7, "Burn with both hands", 4, 0, "Fire", None, 15)
    IceShard = Attack("Ice Shard", 3, 5, "Multiple ice shards", 2, 0, "Ice", None, 12)
    
    QuickShot = Attack("Quick Shot", 2, 4, "Two quick arrows", 1, 0, None, None, 0)
    PowerShot = Attack("Power Shot", 1, 16, "One powerful arrow", 4, 0, None, None, 0)
    MultiShot = Attack("Multi Shot", 4, 3, "Multiple arrows", 5, 0, None, None, 0)
    
    # Magic basic attacks (always available)
    MinorFirebolt = Attack("Minor Firebolt", 1, 6, "A small fire projectile", 0, 0, "Fire", None, 5)
    MinorFrostbolt = Attack("Minor Frostbolt", 1, 6, "A small ice projectile", 0, 0, "Ice", None, 5)
    
    # Weapons (all include BasicStrike or similar as first attack with 0 cooldown)
    Fire = WeaponType("Flame Magic", [MinorFirebolt, Fireball, BurningHands], "Use fire to burn enemies", "Fire")
    Ice = WeaponType("Ice Magic", [MinorFrostbolt, Frostbolt, IceShard], "Use ice to freeze enemies", "Ice")
    Greatsword = WeaponType("Greatsword", [BasicStrike, HSlash, Cleave, GreatSlam], "Large powerful sword", "Normal")
    Shortsword = WeaponType("Shortsword", [BasicStrike, QSlash, HSlash, Thrust], "Quick versatile blade", "Normal")
    Longbow = WeaponType("Longbow", [QuickShot, PowerShot, MultiShot], "Powerful ranged weapon", "Normal")
    Shortbow = WeaponType("Shortbow", [QuickShot, MultiShot], "Fast ranged weapon", "Normal")
    Scythe = WeaponType("Scythe", [BasicStrike, Reap, Whirlwind], "Life-stealing weapon", "Normal")
    Rapier = WeaponType("Rapier", [BasicStrike, EldrichBlast, Thrust], "Magical quick blade", "Normal")
    
    # Classes
    Mage = ClassType("Mage", [Fire, Ice], 0.5, 1.5, "Ranged Caster, Higher MP but low HP")
    Warrior = ClassType("Warrior", [Greatsword, Shortsword], 1.5, 0.5, "Melee Fighter, Higher HP but low MP")
    Archer = ClassType("Archer", [Longbow, Shortbow], 1.25, 0.75, "Ranged physical damage dealer")
    Spellblade = ClassType("Spellblade", [Scythe, Rapier], 0.75, 1.25, "Hybrid magic and melee")
    
    class_list = {
        "Mage": Mage,
        "Warrior": Warrior,
        "Archer": Archer,
        "Spellblade": Spellblade
    }
    
    weapon_list = {
        "ice magic": Ice,
        "flame magic": Fire,
        "greatsword": Greatsword,
        "shortsword": Shortsword,
        "longbow": Longbow,
        "shortbow": Shortbow,
        "scythe": Scythe,
        "rapier": Rapier
    }
    
    # Equipment Library
    equipment_library = {
        "rings": [
            Equipment("Ring", "Ring of Strength", ["DMGmult", "mult", 1.2], ["MP", "mult", 0.9], None, None, 50, False, None, None, "Increases damage but reduces mana"),
            Equipment("Ring", "Ring of Vitality", ["MHP", "add", 50], ["DMGmult", "mult", 0.9], None, None, 50, False, None, None, "Increases health but reduces damage"),
            Equipment("Ring", "Ring of Fire", ["DMGmult", "mult", 1.1], None, None, "Fire", 75, False, None, None, "Grants fire imbue"),
            Equipment("Ring", "Ring of Ice", ["DMGmult", "mult", 1.1], None, None, "Ice", 75, False, None, None, "Grants ice imbue"),
            Equipment("Ring", "Ring of Fortune", ["Luck", "mult", 1.5], ["MHP", "mult", 0.95], None, None, 60, False, None, None, "Increases luck"),
        ],
        "necklaces": [
            Equipment("Necklace", "Necklace of Mana", ["MMP", "add", 50], ["MHP", "mult", 0.9], None, None, 50, False, None, None, "Increases mana but reduces health"),
            Equipment("Necklace", "Necklace of Protection", ["MHP", "mult", 1.2], ["DMGmult", "mult", 0.85], None, None, 60, False, None, None, "Increases health but reduces damage"),
            Equipment("Necklace", "Necklace of Power", ["DMGmult", "mult", 1.3], ["MHP", "mult", 0.8], None, None, 70, False, None, None, "Greatly increases damage but reduces health"),
        ],
        "crowns": [
            Equipment("Crown", "Crown of the Wise", ["MMP", "mult", 1.3], ["MHP", "mult", 0.85], None, None, 100, False, None, None, "Greatly increases mana"),
            Equipment("Crown", "Crown of the Warrior", ["MHP", "mult", 1.3], ["MMP", "mult", 0.85], None, None, 100, False, None, None, "Greatly increases health"),
            Equipment("Crown", "Crown of Balance", ["MHP", "mult", 1.1], ["MMP", "mult", 1.1], ["DMGmult", "mult", 1.1], None, 150, False, None, None, "Balanced stat increases"),
        ],
        "consumables": [
            Equipment("Potion", "Health Potion", None, None, None, None, 20, True, 1, ["HEAL", 50, None], "Restores 50 HP"),
            Equipment("Potion", "Mana Potion", None, None, None, None, 20, True, 1, ["MANA", 50, None], "Restores 50 MP"),
            Equipment("Potion", "Full Restore", None, None, None, None, 100, True, 1, ["FULLHEAL", 0, None], "Fully restores HP and MP"),
        ]
    }
    
    # Enemy Templates
    enemy_templates = {
        "castle": [
            {"name": "Castle Guard", "hp": 40, "damage": 8, "defense": 3, "coins": 15},
            {"name": "Royal Knight", "hp": 60, "damage": 12, "defense": 5, "coins": 25},
            {"name": "Castle Wizard", "hp": 30, "damage": 15, "defense": 2, "coins": 20},
        ],
        "cave": [
            {"name": "Cave Bat", "hp": 20, "damage": 5, "defense": 1, "coins": 5},
            {"name": "Rock Golem", "hp": 80, "damage": 10, "defense": 8, "coins": 30},
            {"name": "Cave Troll", "hp": 100, "damage": 15, "defense": 4, "coins": 35},
        ],
        "ruin": [
            {"name": "Skeleton Warrior", "hp": 35, "damage": 9, "defense": 2, "coins": 12},
            {"name": "Ruined Specter", "hp": 45, "damage": 13, "defense": 1, "coins": 18},
            {"name": "Ancient Guardian", "hp": 70, "damage": 14, "defense": 6, "coins": 40},
        ]
    }

skill_library = {
    "Foolproof-proof": "Disarm a trapped object without chance of failure",
    "Lockpicking lawyer": "Pick a lock without consuming a lockpick",
    "Third eye": "Check the room for hidden objects quickly",
    "Combat medic": "Heal for double the amount when using potions",
    "Lucky shot": "Critical hits deal double damage",
}

# Utility Functions
def Clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def devprint(*x):
    if devmode == True:
        print(''.join(map(str, x)))

def confirm(x):
    pin = input("Take this " + str(x) + "? Y/N: ").lower()
    return pin in ["y", "yes"]

def statsheet(*clear):
    if clear:
        Clear()
    print("=" * 50)
    print(f"Name: {player.Name}")
    if ccdone or player.Class.Name:
        article = "an" if player.Class.Name[0].lower() in vowels else "a"
        print(f"Class: {article} {player.Class.Name}")
    if ccdone or player.Weapon.Name:
        if " " in player.Weapon.Name:
            print(f"Weapon: {player.Weapon.Name}")
        else:
            article = "an" if player.Weapon.Name[0].lower() in vowels else "a"
            print(f"Weapon: {article} {player.Weapon.Name}")
    if ccdone or len(player.Skills) >= 2:
        print(f"Skills: {player.Skills[0]} and {player.Skills[-1]}")
    print(f"HP: {player.HP}/{player.MHP}")
    print(f"MP: {player.MP}/{player.MMP}")
    print(f"Coins: {player.Coins}")
    print(f"Damage Multiplier: x{player.DMGmult:.2f}")
    print(f"Luck: x{player.Luck:.2f}")
    if player.Imbue:
        print(f"Imbue: {player.Imbue}")
    print("=" * 50)

def TurtleSetup():
    global devt, devmap
    devmap = turtle.Screen()
    devmap.bgcolor("black")
    devmap.title("Dev Map")
    devt = turtle.Turtle()
    devt.pencolor("white")
    devmap.colormode(255)
    devt.speed(0)
    devt.hideturtle()

def Randomcolortuple():
    return (random.randint(10, 255), random.randint(10, 255), random.randint(10, 255))

def RoomLocValidator(room):
    rx, ry = room
    for pos in [(rx - 1, ry), (rx + 1, ry), (rx, ry - 1), (rx, ry + 1)]:
        devprint("testing position ", pos, " for room ", room)
        if abs(pos[0]) <= 7 and abs(pos[1]) <= 5:
            devprint(pos, " within valid bounds")
            if pos not in roomids and pos not in invalidroomlocs:
                devprint(pos, " does not contain a room and has not already been invalidated")
                lx, ly = pos
                adjrooms = 0
                for loc in [(lx - 1, ly), (lx + 1, ly), (lx, ly - 1), (lx, ly + 1)]:
                    devprint("testing adjacent location", loc, "for position", pos, "for room ", room)
                    if abs(loc[0]) <= 7 and abs(loc[1]) <= 5:
                        devprint("location ", loc, " within bounds")
                        if loc in roomids:
                            devprint("room found next to ", pos)
                            validroomlocs.discard(loc)
                            invalidroomlocs.add(loc)
                            adjrooms += 1
                if adjrooms >= mapcomplexity:
                    devprint("too many adjacent rooms for ", pos)
                    validroomlocs.discard(pos)
                    invalidroomlocs.add(pos)
                else:
                    devprint(pos, "appears valid")
                    if pos != (0, 0):
                        validroomlocs.add(pos)
            else:
                devprint(pos, " already contains a room or has been previously invalidated")
        else:
            devprint(pos, " out of bounds")

# Equipment Functions
def ApplyEquipment(equipment: Equipment):
    """Apply equipment stats to player"""
    if equipment.Stat1 and equipment.Stat1[0] != "NONE":
        ApplyStat(equipment.Stat1)
    if equipment.Stat2 and equipment.Stat2[0] != "NONE":
        ApplyStat(equipment.Stat2)
    if equipment.Stat3 and equipment.Stat3[0] != "NONE":
        ApplyStat(equipment.Stat3)
    if equipment.Imbue:
        player.Imbue = equipment.Imbue

def RemoveEquipment(equipment: Equipment):
    """Remove equipment stats from player"""
    if equipment.Stat1 and equipment.Stat1[0] != "NONE":
        ReverseStat(equipment.Stat1)
    if equipment.Stat2 and equipment.Stat2[0] != "NONE":
        ReverseStat(equipment.Stat2)
    if equipment.Stat3 and equipment.Stat3[0] != "NONE":
        ReverseStat(equipment.Stat3)
    if equipment.Imbue and player.Imbue == equipment.Imbue:
        player.Imbue = None

def ApplyStat(stat):
    stat_name, operation, value = stat
    if stat_name == "MHP":
        if operation == "add":
            player.MHP += int(value)
        elif operation == "mult":
            player.MHP = int(player.MHP * value)
    elif stat_name == "MMP":
        if operation == "add":
            player.MMP += int(value)
        elif operation == "mult":
            player.MMP = int(player.MMP * value)
    elif stat_name == "DMGmult":
        if operation == "mult":
            player.DMGmult *= value
    elif stat_name == "Luck":
        if operation == "mult":
            player.Luck *= value
    elif stat_name == "HP":
        if operation == "add":
            player.HP = min(player.HP + int(value), player.MHP)
    elif stat_name == "MP":
        if operation == "add":
            player.MP = min(player.MP + int(value), player.MMP)

def ReverseStat(stat):
    stat_name, operation, value = stat
    if stat_name == "MHP":
        if operation == "add":
            player.MHP -= int(value)
            player.HP = min(player.HP, player.MHP)
        elif operation == "mult":
            player.MHP = int(player.MHP / value)
            player.HP = min(player.HP, player.MHP)
    elif stat_name == "MMP":
        if operation == "add":
            player.MMP -= int(value)
            player.MP = min(player.MP, player.MMP)
        elif operation == "mult":
            player.MMP = int(player.MMP / value)
            player.MP = min(player.MP, player.MMP)
    elif stat_name == "DMGmult":
        if operation == "mult":
            player.DMGmult /= value
    elif stat_name == "Luck":
        if operation == "mult":
            player.Luck /= value

def EquipItem(equipment: Equipment):
    """Equip an item to player"""
    if equipment.Type == "Ring":
        if player.EquippedRing:
            RemoveEquipment(player.EquippedRing)
            player.Inventory.append(player.EquippedRing)
        player.EquippedRing = equipment
        ApplyEquipment(equipment)
        print(f"Equipped {equipment.Name}")
    elif equipment.Type == "Necklace":
        if player.EquippedNecklace:
            RemoveEquipment(player.EquippedNecklace)
            player.Inventory.append(player.EquippedNecklace)
        player.EquippedNecklace = equipment
        ApplyEquipment(equipment)
        print(f"Equipped {equipment.Name}")
    elif equipment.Type == "Crown":
        if player.EquippedCrown:
            RemoveEquipment(player.EquippedCrown)
            player.Inventory.append(player.EquippedCrown)
        player.EquippedCrown = equipment
        ApplyEquipment(equipment)
        print(f"Equipped {equipment.Name}")
    elif equipment.Type == "Potion":
        player.Inventory.append(equipment)
        print(f"Added {equipment.Name} to inventory")

# Enemy Functions
def CreateEnemy(theme: str, difficulty: int) -> Enemy:
    """Create an enemy based on theme and difficulty"""
    template = random.choice(enemy_templates[theme])
    
    # Scale stats based on difficulty
    hp = int(template["hp"] * (1 + difficulty * 0.3))
    damage = int(template["damage"] * (1 + difficulty * 0.2))
    defense = int(template["defense"] * (1 + difficulty * 0.15))
    coins = int(template["coins"] * (1 + difficulty * 0.25))
    
    # Create basic attack for enemy
    basic_attack = Attack(
        Name=f"{template['name']} Attack",
        Hits=1,
        Damage=damage,
        Desc=f"{template['name']} attacks!",
        CD=1
    )
    
    # Generate loot
    loot = []
    if random.random() < 0.3 * player.Luck:  # 30% chance for equipment
        equipment_type = random.choice(["rings", "necklaces", "consumables"])
        loot.append(deepcopy(random.choice(equipment_library[equipment_type])))
    
    return Enemy(
        Name=template["name"],
        HP=hp,
        MaxHP=hp,
        Damage=damage,
        Defense=defense,
        Attacks=[basic_attack],
        Desc=f"A dangerous {template['name']}",
        Loot=loot,
        CoinDrop=coins
    )

# POI Functions
def CreatePOI(poi_type: str, theme: str, difficulty: int) -> Poi:
    """Create a point of interest"""
    if poi_type == "chest":
        contents = GenerateLoot(theme, difficulty)
        return Poi(
            Type="chest",
            Name="Treasure Chest",
            Contents=contents,
            Revealed=True,
            Locked=random.random() < 0.3,
            Trapped=random.random() < 0.2,
            Description="A wooden chest sits here, perhaps containing treasure."
        )
    elif poi_type == "decorative":
        decorations = {
            "castle": ["A suit of armor stands guard", "Tapestries hang on the walls", "A grand chandelier hangs overhead"],
            "cave": ["Stalactites hang from the ceiling", "A pool of water reflects the dim light", "Ancient cave paintings cover the walls"],
            "ruin": ["Crumbling statues line the walls", "Overgrown vines cover everything", "Ancient runes glow faintly"]
        }
        desc = random.choice(decorations.get(theme, ["Something decorative is here"]))
        return Poi(
            Type="decorative",
            Name="Decoration",
            Contents=[],
            Description=desc
        )
    elif poi_type == "secret":
        contents = GenerateLoot(theme, difficulty + 1)
        return Poi(
            Type="secret",
            Name="Hidden Cache",
            Contents=contents,
            Revealed=False,
            Description="A hidden stash, if you can find it."
        )
    elif poi_type == "trap":
        return Poi(
            Type="trap",
            Name="Trap",
            Contents=[],
            Revealed=True,
            Trapped=True,
            Description="A suspicious mechanism is visible here."
        )
    else:
        return Poi(
            Type="empty",
            Name="Nothing",
            Contents=[],
            Description="Nothing of interest here."
        )

def GenerateLoot(theme: str, difficulty: int) -> List[Equipment]:
    """Generate loot for chests"""
    loot = []
    num_items = random.randint(1, 3)
    
    for _ in range(num_items):
        roll = random.random() * player.Luck
        if roll < 0.4:  # Consumables
            loot.append(deepcopy(random.choice(equipment_library["consumables"])))
        elif roll < 0.7:  # Rings
            loot.append(deepcopy(random.choice(equipment_library["rings"])))
        elif roll < 0.9:  # Necklaces
            loot.append(deepcopy(random.choice(equipment_library["necklaces"])))
        else:  # Crowns (rare)
            loot.append(deepcopy(random.choice(equipment_library["crowns"])))
    
    # Add coins
    coins = random.randint(5, 20) * (1 + difficulty)
    coin_equipment = Equipment("Coins", f"{int(coins)} Coins", None, None, None, None, int(coins), True, 1, ["COINS", int(coins), None], f"A pile of {int(coins)} coins")
    loot.append(coin_equipment)
    
    return loot

def PopulateRoom(room: Room, position: Tuple[int, int]):
    """Populate a room with POIs and enemies"""
    if position == (0, 0):  # Spawn room - no enemies
        return
    
    if room.Desc in ["Boss Room", "Key Room"]:  # Special rooms handled separately
        return
    
    # Determine number of POIs based on size
    poi_counts = {"small": (1, 3), "medium": (2, 4), "large": (3, 7)}
    min_poi, max_poi = poi_counts.get(room.Size, (2, 4))
    num_pois = random.randint(min_poi, max_poi)
    
    # Add POIs
    for _ in range(num_pois):
        poi_type = random.choices(
            ["chest", "decorative", "secret", "trap", "empty"],
            weights=[0.3, 0.3, 0.1, 0.15, 0.15]
        )[0]
        room.Pois.append(CreatePOI(poi_type, room.Theme, room.Diff))
    
    # Add enemies based on size
    enemy_counts = {"small": 0, "medium": 1, "large": 2}
    if random.random() < 0.7:  # 70% chance for enemies
        num_enemies = enemy_counts.get(room.Size, 1)
        for _ in range(num_enemies):
            room.Enemies.append(CreateEnemy(room.Theme, room.Diff))

def GenerateRoomDescription(room: Room) -> str:
    """Generate a description for a room"""
    theme_descriptions = {
        "castle": [
            "You stand in a grand stone hall with high vaulted ceilings.",
            "This appears to be a castle chamber with stone walls and torch sconces.",
            "A well-maintained castle room stretches before you.",
        ],
        "cave": [
            "You enter a dark cave with rough stone walls.",
            "The cave opens up before you, damp and echoing.",
            "A natural cave formation surrounds you with stalactites overhead.",
        ],
        "ruin": [
            "Ancient ruins crumble around you, covered in moss and vines.",
            "You step into what was once a grand structure, now in ruins.",
            "Weathered stones and broken pillars mark this ruined area.",
        ]
    }
    
    base_desc = random.choice(theme_descriptions.get(room.Theme, ["You enter a room."]))
    
    # Add size context
    size_desc = {
        "small": " The space is cramped and confined.",
        "medium": " The room is of moderate size.",
        "large": " The chamber is vast and imposing."
    }
    base_desc += size_desc.get(room.Size, "")
    
    # Mention visible POIs
    visible_pois = [poi for poi in room.Pois if poi.Revealed and poi.Type != "decorative"]
    if visible_pois:
        poi_count = len(visible_pois)
        object_word = "object" if poi_count == 1 else "objects"
        base_desc += f" You notice {poi_count} interesting {object_word} here."
    
    # Mention enemies
    if room.Enemies:
        enemy_count = len(room.Enemies)
        creature_word = "creature" if enemy_count == 1 else "creatures"
        verb = "is" if enemy_count == 1 else "are"
        base_desc += f" {enemy_count} hostile {creature_word} {verb} present!"
    
    # Mention exits
    exits = [direction for direction, pos in room.Connections.items() if pos in roomids]
    if exits:
        base_desc += f" Exits lead: {', '.join(exits)}."
    
    return base_desc

# Combat Functions
def Combat(enemies: List[Enemy]) -> bool:
    """Run a combat encounter. Returns True if player wins."""
    print("\n" + "=" * 50)
    print("COMBAT BEGINS!")
    print("=" * 50)
    
    # Reset cooldowns at start of combat
    player.AttackCooldowns = {}
    
    while enemies and player.HP > 0:
        # Player turn
        print(f"\n{player.Name}'s Turn")
        print(f"HP: {player.HP}/{player.MHP} | MP: {player.MP}/{player.MMP}")
        print("\nEnemies:")
        for i, enemy in enumerate(enemies, 1):
            print(f"  {i}. {enemy.Name} - HP: {enemy.HP}/{enemy.MaxHP}")
        
        print("\nActions:")
        print("1. Attack")
        print("2. Use Item")
        print("3. Run (50% chance)")
        
        choice = input("Choose action: ").strip()
        
        if choice == "1":
            # Select attack
            available_attacks = [atk for atk in player.Weapon.Attacks 
                                if player.AttackCooldowns.get(atk.Name, 0) == 0 and atk.MPCost <= player.MP]
            
            if not available_attacks:
                print("All attacks on cooldown or not enough MP!")
                input("Press Enter to continue...")
                continue
            
            print("\nAvailable Attacks:")
            for i, attack in enumerate(available_attacks, 1):
                mp_cost = f" (MP: {attack.MPCost})" if attack.MPCost > 0 else ""
                print(f"  {i}. {attack.Name} - {attack.Hits}x{attack.Damage} dmg{mp_cost} (CD: {attack.CD})")
            
            # Show attacks on cooldown for reference
            cooldown_attacks = [(atk, player.AttackCooldowns.get(atk.Name, 0)) 
                               for atk in player.Weapon.Attacks 
                               if player.AttackCooldowns.get(atk.Name, 0) > 0]
            if cooldown_attacks:
                print("\nOn Cooldown:")
                for atk, cd in cooldown_attacks:
                    print(f"  - {atk.Name} (ready in {cd} turn{'s' if cd > 1 else ''})")
            
            # Show attacks that need more MP
            no_mp_attacks = [atk for atk in player.Weapon.Attacks 
                           if player.AttackCooldowns.get(atk.Name, 0) == 0 and atk.MPCost > player.MP]
            if no_mp_attacks:
                print("\nNot Enough MP:")
                for atk in no_mp_attacks:
                    print(f"  - {atk.Name} (needs {atk.MPCost} MP)")
            
            atk_choice = input("\nChoose attack (or 'back'): ").strip()
            if atk_choice.lower() == "back":
                continue
            
            try:
                atk_idx = int(atk_choice) - 1
                if 0 <= atk_idx < len(available_attacks):
                    attack = available_attacks[atk_idx]
                    
                    # Check MP
                    if attack.MPCost > player.MP:
                        print("Not enough MP!")
                        continue
                    
                    # Select target
                    print("Select target:")
                    for i, enemy in enumerate(enemies, 1):
                        print(f"  {i}. {enemy.Name}")
                    
                    target_choice = input("Target: ").strip()
                    try:
                        target_idx = int(target_choice) - 1
                        if 0 <= target_idx < len(enemies):
                            target = enemies[target_idx]
                            
                            # Execute attack
                            player.MP -= attack.MPCost
                            total_damage = 0
                            for hit in range(attack.Hits):
                                damage = int(attack.Damage * player.DMGmult)
                                # Check for lucky critical
                                if "Lucky shot" in player.Skills and random.random() < (0.1 * player.Luck):
                                    damage *= 2
                                    print("CRITICAL HIT!")
                                total_damage += max(1, damage - target.Defense)
                            
                            target.HP -= total_damage
                            print(f"\n{player.Name} uses {attack.Name}!")
                            print(f"Dealt {total_damage} damage to {target.Name}!")
                            
                            if attack.Healing > 0:
                                heal = attack.Healing
                                if "Combat medic" in player.Skills:
                                    heal *= 2
                                player.HP = min(player.HP + heal, player.MHP)
                                print(f"Healed {heal} HP!")
                            
                            # Set cooldown
                            player.AttackCooldowns[attack.Name] = attack.CD
                            
                            # Remove dead enemy
                            if target.HP <= 0:
                                print(f"{target.Name} defeated!")
                                # Drop loot
                                for item in target.Loot:
                                    print(f"  Dropped: {item.Name}")
                                    player.Inventory.append(item)
                                player.Coins += target.CoinDrop
                                print(f"  Gained {target.CoinDrop} coins!")
                                enemies.remove(target)
                        else:
                            print("Invalid target!")
                            continue
                    except ValueError:
                        print("Invalid input!")
                        continue
                else:
                    print("Invalid attack!")
                    continue
            except ValueError:
                print("Invalid input!")
                continue
                
        elif choice == "2":
            # Use item
            usable_items = [item for item in player.Inventory if item.Consumable]
            if not usable_items:
                print("No usable items!")
                continue
            
            print("\nItems:")
            for i, item in enumerate(usable_items, 1):
                print(f"  {i}. {item.Name} - {item.Description}")
            
            item_choice = input("Choose item (or 'back'): ").strip()
            if item_choice.lower() == "back":
                continue
            
            try:
                item_idx = int(item_choice) - 1
                if 0 <= item_idx < len(usable_items):
                    item = usable_items[item_idx]
                    UseItem(item)
                    player.Inventory.remove(item)
                else:
                    print("Invalid item!")
                    continue
            except ValueError:
                print("Invalid input!")
                continue
                
        elif choice == "3":
            # Run
            if random.random() < 0.5:
                print("You successfully fled!")
                return False
            else:
                print("Failed to escape!")
        
        else:
            print("Invalid choice!")
            continue
        
        # Reduce cooldowns
        for attack_name in list(player.AttackCooldowns.keys()):
            player.AttackCooldowns[attack_name] = max(0, player.AttackCooldowns[attack_name] - 1)
        
        # Enemy turn
        if enemies:
            print("\n--- Enemy Turn ---")
            for enemy in enemies:
                if enemy.Attacks:
                    attack = random.choice(enemy.Attacks)
                    damage = max(1, attack.Damage - int(player.DMGmult * 2))  # Player defense
                    player.HP -= damage
                    print(f"{enemy.Name} uses {attack.Name}! Dealt {damage} damage!")
                    
                    if player.HP <= 0:
                        print("\n" + "=" * 50)
                        print("YOU DIED!")
                        print("=" * 50)
                        return False
        
        input("\nPress Enter to continue...")
    
    if player.HP > 0:
        print("\n" + "=" * 50)
        print("VICTORY!")
        print("=" * 50)
        # Restore some HP/MP after combat
        player.HP = min(player.HP + 20, player.MHP)
        player.MP = min(player.MP + 20, player.MMP)
        return True
    
    return False

def UseItem(item: Equipment):
    """Use a consumable item"""
    if item.Action:
        action_type = item.Action[0]
        if action_type == "HEAL":
            heal = item.Action[1]
            if "Combat medic" in player.Skills:
                heal *= 2
            player.HP = min(player.HP + heal, player.MHP)
            print(f"Healed {heal} HP!")
        elif action_type == "MANA":
            mana = item.Action[1]
            player.MP = min(player.MP + mana, player.MMP)
            print(f"Restored {mana} MP!")
        elif action_type == "FULLHEAL":
            player.HP = player.MHP
            player.MP = player.MMP
            print("Fully restored HP and MP!")
        elif action_type == "COINS":
            coins = item.Action[1]
            player.Coins += coins
            print(f"Gained {coins} coins!")

# Room Interaction Functions
def InteractWithRoom(room: Room):
    """Handle room interactions"""
    while True:
        Clear()
        print(GenerateRoomDescription(room))
        print("\n" + "=" * 50)
        statsheet()
        
        if not room.Cleared and room.Enemies:
            print("\nYou must defeat the enemies before exploring!")
            input("Press Enter to fight...")
            if Combat(room.Enemies):
                room.Cleared = True
                print("Room cleared!")
                input("Press Enter to continue...")
            else:
                return False  # Player died or fled
            continue
        
        print("\nActions:")
        print("1. Examine POIs")
        print("2. Search for secrets (requires 'Third eye' skill)")
        print("3. Move to another room")
        print("4. View Inventory")
        print("5. Rest (restore HP/MP)")
        
        choice = input("\nChoose action: ").strip()
        
        if choice == "1":
            ExaminePOIs(room)
        elif choice == "2":
            if "Third eye" in player.Skills:
                SearchSecrets(room)
            else:
                print("You don't have the 'Third eye' skill!")
                input("Press Enter...")
        elif choice == "3":
            return True  # Move to another room
        elif choice == "4":
            ViewInventory()
        elif choice == "5":
            player.HP = player.MHP
            player.MP = player.MMP
            print("You rest and restore your HP and MP.")
            input("Press Enter...")
        else:
            print("Invalid choice!")

def ExaminePOIs(room: Room):
    """Examine points of interest in the room"""
    visible_pois = [poi for poi in room.Pois if poi.Revealed and poi.Type != "empty"]
    
    if not visible_pois:
        print("\nThere's nothing interesting to examine here.")
        input("Press Enter...")
        return
    
    while True:
        Clear()
        print("Points of Interest:")
        for i, poi in enumerate(visible_pois, 1):
            status = " (interacted)" if poi.Interacted else ""
            locked = " [LOCKED]" if poi.Locked else ""
            trapped = " [TRAPPED]" if poi.Trapped else ""
            print(f"  {i}. {poi.Name}{locked}{trapped}{status}")
        print("  0. Back")
        
        choice = input("\nExamine which POI? ").strip()
        
        if choice == "0":
            return
        
        try:
            poi_idx = int(choice) - 1
            if 0 <= poi_idx < len(visible_pois):
                poi = visible_pois[poi_idx]
                InteractWithPOI(poi)
            else:
                print("Invalid choice!")
                input("Press Enter...")
        except ValueError:
            print("Invalid input!")
            input("Press Enter...")

def InteractWithPOI(poi: Poi):
    """Interact with a specific POI"""
    Clear()
    print(poi.Description)
    
    if poi.Interacted:
        print("\nYou've already interacted with this.")
        input("Press Enter...")
        return
    
    if poi.Locked:
        print("\nThis is locked!")
        if "Lockpicking lawyer" in player.Skills:
            print("You use your lockpicking skills to open it!")
            poi.Locked = False
        else:
            print("You need the 'Lockpicking lawyer' skill to open this.")
            input("Press Enter...")
            return
    
    if poi.Trapped and not poi.Interacted:
        print("\nThis is trapped!")
        if "Foolproof-proof" in player.Skills:
            print("You safely disarm the trap!")
            poi.Trapped = False
        else:
            if random.random() < 0.5:
                damage = random.randint(10, 30)
                player.HP -= damage
                print(f"The trap springs! You take {damage} damage!")
                if player.HP <= 0:
                    print("You died!")
                    return
            else:
                print("You carefully avoid the trap!")
            poi.Trapped = False
    
    if poi.Contents:
        print("\nYou found:")
        for item in poi.Contents:
            print(f"  - {item.Name}")
            if item.Type == "Coins":
                UseItem(item)
            else:
                player.Inventory.append(item)
        poi.Contents = []
    
    poi.Interacted = True
    input("\nPress Enter...")

def SearchSecrets(room: Room):
    """Search for hidden POIs"""
    hidden_pois = [poi for poi in room.Pois if not poi.Revealed]
    
    if not hidden_pois:
        print("\nYou don't find anything hidden.")
        input("Press Enter...")
        return
    
    # Use luck to find secrets
    if random.random() < (0.5 * player.Luck):
        poi = hidden_pois[0]
        poi.Revealed = True
        print(f"\nYou found a hidden {poi.Name}!")
        input("Press Enter...")
    else:
        print("\nYou don't find anything hidden.")
        input("Press Enter...")

def ViewInventory():
    """View and manage inventory"""
    while True:
        Clear()
        print("=" * 50)
        print("INVENTORY")
        print("=" * 50)
        print(f"Coins: {player.Coins}")
        print(f"\nEquipped:")
        print(f"  Ring: {player.EquippedRing.Name if player.EquippedRing else 'None'}")
        print(f"  Necklace: {player.EquippedNecklace.Name if player.EquippedNecklace else 'None'}")
        print(f"  Crown: {player.EquippedCrown.Name if player.EquippedCrown else 'None'}")
        
        if player.Inventory:
            print(f"\nInventory ({len(player.Inventory)} items):")
            for i, item in enumerate(player.Inventory, 1):
                print(f"  {i}. {item.Name} ({item.Type})")
        else:
            print("\nInventory is empty.")
        
        print("\n0. Back")
        choice = input("\nSelect item to use/equip (or 0 to go back): ").strip()
        
        if choice == "0":
            return
        
        try:
            item_idx = int(choice) - 1
            if 0 <= item_idx < len(player.Inventory):
                item = player.Inventory[item_idx]
                print(f"\n{item.Name}")
                print(item.Description)
                
                if item.Consumable:
                    if confirm("use this item"):
                        player.Inventory.remove(item)
                        UseItem(item)
                        input("Press Enter...")
                elif item.Type in ["Ring", "Necklace", "Crown"]:
                    if confirm("equip this item"):
                        player.Inventory.remove(item)
                        EquipItem(item)
                        input("Press Enter...")
            else:
                print("Invalid choice!")
                input("Press Enter...")
        except ValueError:
            print("Invalid input!")
            input("Press Enter...")

def MoveToRoom():
    """Move to an adjacent room"""
    current_room = roomids[player.CurrentRoom]
    available_exits = [(direction, pos) for direction, pos in current_room.Connections.items() if pos in roomids]
    
    if not available_exits:
        print("No exits available!")
        input("Press Enter...")
        return
    
    Clear()
    print("Available exits:")
    for i, (direction, pos) in enumerate(available_exits, 1):
        visited = " (visited)" if roomids[pos].Visited else " (unexplored)"
        print(f"  {i}. {direction.capitalize()}{visited}")
    print("  0. Stay here")
    
    choice = input("\nWhere do you want to go? ").strip()
    
    if choice == "0":
        return
    
    try:
        exit_idx = int(choice) - 1
        if 0 <= exit_idx < len(available_exits):
            direction, new_pos = available_exits[exit_idx]
            player.CurrentRoom = new_pos
            roomids[new_pos].Visited = True
            print(f"\nYou move {direction}...")
            sleep(1)
        else:
            print("Invalid choice!")
            input("Press Enter...")
    except ValueError:
        print("Invalid input!")
        input("Press Enter...")

# Character Creation
def CharCreator():
    global ccdone, devmode
    print("Starting Character Creator")
    player.Name = input("Name your character: ")
    if player.Name == "e":
        devmode = True
    
    statsheet(1)
    
    # Choose class
    while True:
        statsheet(1)
        print("Available classes: " + ', '.join(class_list.keys()))
        pin = str(input("Choose your class: "))
        if pin.lower() not in (x.lower() for x in class_list.keys()):
            print("That is not a valid class, try again")
        else:
            print("You have chosen: " + str(pin.capitalize()))
            print("Description: " + class_list[pin.capitalize()].Desc)
            if confirm("class"):
                player.Class = class_list[str(pin.capitalize())]
                player.MHP = int(player.MHP * player.Class.HPmult)
                player.HP = player.MHP
                player.MMP = int(player.MMP * player.Class.MPmult)
                player.MP = player.MMP
                break
    
    # Choose weapon
    while True:
        statsheet(1)
        print("Available weapons for your class: " + ', '.join(x.Name for x in player.Class.Weapons))
        pin = str(input("Choose your weapon: "))
        if pin.lower() not in (x.Name.lower() for x in player.Class.Weapons):
            print("That is not a valid weapon, try again")
        else:
            print("You have chosen: " + str(pin.capitalize()))
            print("Description: " + weapon_list[pin.lower()].Desc)
            print("Attacks: " + ', '.join([x.Name for x in weapon_list[pin.lower()].Attacks]))
            if confirm("weapon"):
                player.Weapon = weapon_list[str(pin.lower())]
                break
    
    # Choose skills
    while True:
        statsheet(1)
        print("Available skills: " + (', '.join(set(skill_library.keys()).difference(player.Skills))))
        pin = str(input("Choose a skill: "))
        if pin.lower() not in [x.lower() for x in ((set(skill_library.keys()).difference(player.Skills)))]:
            print("That is not a valid skill, try again")
            sleep(1)
        else:
            print("You have chosen: " + (pin.capitalize()))
            print("Description: " + skill_library[(pin.capitalize())])
            if confirm("skill"):
                player.Skills.append(pin.capitalize())
            if len(player.Skills) >= 2:
                break
    
    statsheet(1)
    ccdone = True
    input("Press Enter to begin your adventure...")

# Dungeon Generation
def DunGen():
    global roomids, validroomlocs, invalidroomlocs
    devprint("Starting dungeon generation")
    
    roomids = {}
    validroomlocs.clear()
    invalidroomlocs.clear()
    
    # Create spawn room
    roomids[(0, 0)] = Room("cave", 'large', "Spawn Room", 0, [], 
                           {"north": (0, 1), "east": (1, 0), "south": (0, -1), "west": (-1, 0)}, 
                           [], True, True)
    
    totalrooms = 1
    
    # Select difficulty
    while True:
        print("Easy - Normal - Hard - Hell")
        pin = input("Select a difficulty: \n").lower()
        
        if devmode:
            if devt:
                devt.clear()
                devt.pencolor("white")
                devt.penup()
                devt.goto(0, 0)
                devt.pendown()
                devt.dot(80, (102, 0, 51))
                devt.pencolor("black")
                devt.write(str(mapcomplexity))
        
        if devmode or pin in ["easy", "normal", "hard", "hell"]:
            if devmode or input("You have selected: " + pin.capitalize() + ". Proceed?\n").lower() in ["y", "yes"]:
                if pin == "easy":
                    reqrooms = 10
                elif pin == "normal":
                    reqrooms = 15
                elif pin == "hard":
                    reqrooms = 20
                elif pin == "hell":
                    reqrooms = 30
                elif devmode:
                    reqrooms = 50
                else:
                    print("Difficulty selection failed")
                break
        else:
            print("Not a valid input, try again")
            sleep(1)
    
    # Generate rooms
    while totalrooms < reqrooms:
        for room in roomids:
            RoomLocValidator(room)
        
        if not validroomlocs:
            break
        
        newroomloc = random.choice(list(validroomlocs))
        if newroomloc in roomids:
            continue
        
        roomids[newroomloc] = Room(
            Theme="Unassigned",
            Size=random.choice(["large", "medium", "medium", "small"]),
            Desc="Description Not Generated",
            Diff=0,
            Pois=[],
            Connections={"north": (newroomloc[0], newroomloc[1] + 1),
                        "east": (newroomloc[0] + 1, newroomloc[1]),
                        "south": (newroomloc[0], newroomloc[1] - 1),
                        "west": (newroomloc[0] - 1, newroomloc[1])},
            Enemies=[],
            Visited=False,
            Cleared=False
        )
        
        totalrooms = len(roomids)
        
        if devmode and devt:
            rx, ry = newroomloc
            devt.penup()
            devt.goto(0 + (100 * rx), 0 + (100 * ry))
            devt.pendown()
            devt.dot(60, tuple(Randomcolortuple()))
            devt.penup()
            devt.goto(0 + (100 * rx) - 12.5, 0 + (100 * ry))
            devt.pendown()
            devt.write(str(newroomloc))
    
    # Find perimeter rooms
    perimiterrooms.clear()
    for room in roomids:
        rx, ry = room
        adjrooms = 0
        for pos in [(rx - 1, ry), (rx + 1, ry), (rx, ry - 1), (rx, ry + 1)]:
            if pos in roomids:
                adjrooms += 1
            if adjrooms > 1:
                break
        if adjrooms == 1:
            perimiterrooms.append(room)
    
    # Find furthest rooms for boss and key
    maxdist = 0
    furthestrooms = [list(roomids.keys())[0], list(roomids.keys())[-1]]
    for room1 in perimiterrooms:
        for room2 in perimiterrooms:
            if room1 != room2:
                dist = math.dist(room1, room2)
                if dist > maxdist:
                    maxdist = dist
                    furthestrooms = [room1, room2]
    
    # Place special rooms
    for x, room in enumerate(furthestrooms):
        for direction, pos in roomids[room].Connections.items():
            if pos in roomids:
                newroomloc = roomids[room].Connections[dorkondict[direction]]
                if x == 0:  # Key room
                    roomids[newroomloc] = Room(
                        Theme="ruin",
                        Size="large",
                        Desc="Key Room",
                        Diff=0,
                        Pois=[],
                        Connections={"north": (newroomloc[0], newroomloc[1] + 1),
                                    "east": (newroomloc[0] + 1, newroomloc[1]),
                                    "south": (newroomloc[0], newroomloc[1] - 1),
                                    "west": (newroomloc[0] - 1, newroomloc[1])},
                        Enemies=[],
                        Visited=False,
                        Cleared=False
                    )
                    specialroomlocs.append(newroomloc)
                    if devmode and devt:
                        rx, ry = newroomloc
                        devt.penup()
                        devt.goto(0 + (100 * rx), 0 + (100 * ry))
                        devt.pendown()
                        devt.dot(80, tuple((0, 102, 0)))
                        devt.penup()
                        devt.goto(0 + (100 * rx) - 12.5, 0 + (100 * ry))
                        devt.pendown()
                        devt.write(str(newroomloc))
                    break
                else:  # Boss room
                    roomids[newroomloc] = Room(
                        Theme="castle",
                        Size="large",
                        Desc="Boss Room",
                        Diff=0,
                        Pois=[],
                        Connections={"north": (newroomloc[0], newroomloc[1] + 1),
                                    "east": (newroomloc[0] + 1, newroomloc[1]),
                                    "south": (newroomloc[0], newroomloc[1] - 1),
                                    "west": (newroomloc[0] - 1, newroomloc[1])},
                        Enemies=[],
                        Visited=False,
                        Cleared=False
                    )
                    specialroomlocs.append(newroomloc)
                    if devmode and devt:
                        rx, ry = newroomloc
                        devt.penup()
                        devt.goto(0 + (100 * rx), 0 + (100 * ry))
                        devt.pendown()
                        devt.dot(80, tuple((192, 192, 192)))
                        devt.penup()
                        devt.goto(0 + (100 * rx) - 12.5, 0 + (100 * ry))
                        devt.pendown()
                        devt.write(str(newroomloc))
                    break
    
    # Cull invalid connections
    culleddict = deepcopy(roomids)
    for room_pos, room in roomids.items():
        for direction in list(room.Connections.keys()):
            connected_pos = room.Connections[direction]
            if connected_pos not in roomids:
                del culleddict[room_pos].Connections[direction]
    roomids = culleddict
    
    # Theme proliferation
    themed = list(specialroomlocs)
    unthemed = [room for room in roomids.keys() if roomids[room].Theme == 'Unassigned']
    
    while len(unthemed) > 0 and themed:
        room = random.choice(themed)
        for direction, adjroom in roomids[room].Connections.items():
            if adjroom in roomids and roomids[adjroom].Theme == 'Unassigned':
                roomids[adjroom].Theme = roomids[room].Theme
                
                if devmode and devt:
                    rx, ry = adjroom
                    devt.penup()
                    devt.goto(0 + (100 * rx), 0 + (100 * ry))
                    devt.pendown()
                    if roomids[room].Theme == 'ruin':
                        devt.dot(60, (0, 102, 0))
                    elif roomids[room].Theme == 'cave':
                        devt.dot(60, (102, 0, 51))
                    elif roomids[room].Theme == 'castle':
                        devt.dot(60, (192, 192, 192))
                    devt.penup()
                    devt.goto(0 + (100 * rx) - 12.5, 0 + (100 * ry))
                    devt.pendown()
                    devt.write(str(adjroom))
                
                unthemed.remove(adjroom)
                themed.append(adjroom)
        themed.remove(room)
    
    # Populate all rooms
    for pos, room in roomids.items():
        PopulateRoom(room, pos)
    
    print("Dungeon generation complete!")
    input("Press Enter to continue...")

# Main Game Loop
def GameLoop():
    """Main gameplay loop"""
    player.CurrentRoom = (0, 0)
    roomids[(0, 0)].Visited = True
    
    while player.HP > 0:
        current_room = roomids[player.CurrentRoom]
        
        if not InteractWithRoom(current_room):
            print("\nGAME OVER")
            return
        
        MoveToRoom()
    
    print("\nGAME OVER")

# Main execution
if __name__ == "__main__":
    Clear()
    Librarysetup()
    
    CharCreator()
    
    # Initialize turtle graphics if devmode is enabled
    if devmode:
        TurtleSetup()
    
    DunGen()
    
    print("\n" + "=" * 50)
    print("Your adventure begins...")
    print("=" * 50)
    input("Press Enter to start...")
    
    GameLoop()
