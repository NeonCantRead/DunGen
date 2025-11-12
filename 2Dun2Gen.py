import dataclasses as dc
import random
import warnings
from pyparsing import Optional 
from enum import Enum

class Dtype(Enum):
    """Valid Damage Types"""
    #None Type, for when something has no inherent weakness
    NONE = "none"
    #Buff Tyypes, for beneficial effects
    HEAL = "heal"
    STRBUFF = "str buff"
    MANBUFF = "man buff"
    #Melee Damage types
    SLASH = "slash"   #good against unarmored
    BLUNT = "blunt"   #good against heavy armored
    PIERCE = "pierce" #good against light armored
    # The following types are just assigned as weaknesses at the devs disgretion
    FIRE = "fire"
    ICE = "ice"
    DARK = "dark"
    LIGHT = "light"
    # The following types are for shits and giggles
    SIGMA = "sigma"
    AURA = "aura"
    CRINGE = "cringe"
    BASED = "based"
    @classmethod
    def Buffs(cls) -> list['Dtype']:
        """Returns all buff types"""
        members = list(cls)
        none_idx = members.index(cls.NONE)
        slash_idx = members.index(cls.SLASH)
        return members[none_idx + 1:slash_idx]

@dc.dataclass
class Effect:
    Name:str = "ERROR"
    DamageType:Dtype = Dtype.NONE
    Duration:int = -1
    RemainingDuration:int = -1
    Damage:int = -1
    def refresh(self):
        self.RemainingDuration = self.Duration
    def decrement(self):
        """Decreases the effect timer by 1 tick, returns True if the timer has reached 0"""
        self.RemainingDuration -= 1
        if self.RemainingDuration == 0:
            return True
        return False
    def __post_init__(self):
        if self.Name == "ERROR":
            raise ValueError("Effect must have a name")
        if self.Duration < 0:
            raise ValueError("Effect must have a non-negative duration")
        if self.DamageType == Dtype.NONE:
            raise ValueError("Effect must have a damage type")
        if self.Damage < 0:
            raise ValueError("Effect must have a non-negative damage value")
        if self.RemainingDuration == -1:
            self.RemainingDuration = self.Duration
            warnings.warn("RemainingDuration not set, defaulting to Duration")
    def __hash__(self):
        return hash((self.Name, self.DamageType))

class Etype(Enum):
    """Valid Effect Types"""
    BURN = Effect(Name="Burn", DamageType=Dtype.FIRE, Duration=3, Damage=5)
    FREEZE = Effect(Name="Freeze", DamageType=Dtype.ICE, Duration=2, Damage=3)
    POISON = Effect(Name="Poison", DamageType=Dtype.DARK, Duration=4, Damage=2)
    HEALING = Effect(Name="Healing", DamageType=Dtype.HEAL, Duration=3, Damage=-5)
    MAGICBUFF = Effect(Name="Magic Buff", DamageType=Dtype.MANBUFF, Duration=3, Damage=2)
    PHYSICALBUFF = Effect(Name="Physical Buff", DamageType=Dtype.STRBUFF, Duration=3, Damage=2)
    NONE = Effect(Name="None", DamageType=Dtype.NONE, Duration=0, Damage=0)
    
@dc.dataclass(frozen=True)
class Attack:
    Name:str
    #AtkType:str # Melee, Projectile, Spell, Wave, Embue, Bomb
    Range:str # e.g. "Close", "Ranged", "AoE" (Area of Effect)
    Splash:bool = False # If true, the attack can hit multiple targets in an area
    Damage:int
    DamageType:str # e.g. "Physical", "Fire", "Ice", etc. SPECIAL VALUE "Inherit" if the damage type is inherited from the weapon
    ManaCost:int = 0
    SpecialEffect:Etype = Etype.NONE # Effect name and duration in turns, e.g. ("Burn", 3) for a burn effect that lasts 3 turns
    def __post_init__(self):
        if self.Range and self.ManaCost and self.DamageType: #AtkType Definition
            if self.Range == "Close":
                if self.ManaCost > 0: # Having a melee attack with mana cost indicates an imbued attack
                    if self.DamageType == "Physical":
                        raise ValueError("Cannot have Physical Embuement")
                    else:
                        self.AtkType = "Embue"
                else:
                    self.AtkType = "Melee"
            elif self.Range == "Ranged":
                if self.ManaCost > 0: # Having a ranged attack with mana cost indicates a spell
                    if self.DamageType == "Physical":
                        raise ValueError("Cannot have Physical Spell")
                    else:
                        self.AtkType = "Spell"
                else:
                    self.AtkType = "Projectile"
            elif self.Range == "AoE":
                if self.ManaCost > 0: # Having an AoE attack with mana cost indicates a wave
                    if self.DamageType == "Physical":
                        raise ValueError("Cannot have Physical Wave")
                    else:
                        self.AtkType = "Wave"
                else:
                    self.AtkType = "Bomb"          

@dc.dataclass
class Equipment:
    Name:str 
    Archetype:str # e.g. "Weapon", "Armor", "Accessory"
    Type:str # e.g. "Sword", "Shield", "Ring", etc.
    SpecialAttr:list[str] = dc.field(default_factory=list) # Anything about the item that could be used in a special way (eg, an iron weapon would be good against fae enemies, so it would note down "Iron")
    ProvAtks:list[Attack] = dc.field(default_factory=list) # List of attacks that are given to the play while they have this item equipped
    ProvAbil:list[str] = dc.field(default_factory=list) # List of abilities that are given to the player while they have this item equipped


@dc.dataclass
class Entity:
    Name:str
    Health:int
    MaxHealth:int
    Mana:int
    MaxMana:int
    Loadout:list[Equipment] = dc.field(default_factory=list)
    StatusEffects:list[Effect] = dc.field(default_factory=list) # List of status effects currently affecting the entity
    Buffs:dict[Dtype, Effect] = dc.field(default_factory=dict) # Active buffs on the entity, mapped by their damage type
    Weakness:list[Dtype] = dc.field(default_factory=lambda: [Dtype.NONE])  # Fixed: Use default_factory to avoid shared mutable default
    def heal(self, amount:int):
        self.Health = min(self.Health + amount, self.MaxHealth)
    def hurt(self, amount:int, dtype:Dtype):
        self.Health = max(self.Health - (amount * 2 if dtype in self.Weakness else amount) , 0)
        if self.Health == 0:
            print(f"{self.Name} has been defeated!")
            #put death handler here
    def StatusTick(self):
        self.Buffs = {}
        for effect in reversed(self.StatusEffects): # first we check if any buffs should be applied
            if effect.DamageType in Dtype.Buffs():
                if effect.decrement():
                    print(f"{self.Name}'s {effect.Name} has worn off.")
                    self.StatusEffects.remove(effect)
                    continue
                if self.Buffs.get(effect.DamageType) is None:
                    self.Buffs[effect.DamageType] = effect
                else:
                    self.Buffs[effect.DamageType].refresh() # Refresh the buff duration if it's already active


        for effect in reversed(self.StatusEffects):
            # name, type, duration, damage
            if effect.DamageType in Dtype.Buffs():
                continue # Buffs are applied at the start, so we skip them here
            self.hurt(effect.Damage, effect.DamageType)
            if effect.decrement():
                print(f"{self.Name} is no longer affected by {effect.Name}.")
                self.StatusEffects.remove(effect)


            