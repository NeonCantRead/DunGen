import dataclasses as dc
import random
from pyparsing import Optional 
dc.dataclass(frozen=True)
class Attack:
    Name:str
    #AtkType:str # Melee, Projectile, Spell, Wave, Embue, Bomb
    Range:str # e.g. "Close", "Ranged", "AoE" (Area of Effect)
    Splash:bool = False # If true, the attack can hit multiple targets in an area
    Damage:int
    DamageType:str # e.g. "Physical", "Fire", "Ice", etc. SPECIAL VALUE "Inherit" if the damage type is inherited from the weapon
    ManaCost:int = 0
    SpecialEffect:tuple[str,int] = ("", 0) # Effect name and duration in turns, e.g. ("Burn", 3) for a burn effect that lasts 3 turns
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

dc.dataclass
class Equipment:
    Name:str 
    Archetype:str # e.g. "Weapon", "Armor", "Accessory"
    Type:str # e.g. "Sword", "Shield", "Ring", etc.
    SpecialAttr:list[str] = dc.field(default_factory=list) # Anything about the item that could be used in a special way (eg, an iron weapon would be good against fae enemies, so it would note down "Iron")
    ProvAtks:list[Attack] = dc.field(default_factory=list) # List of attacks that are given to the play while they have this item equipped
    ProvAbil:list[str] = dc.field(default_factory=list) # List of abilities that are given to the player while they have this item equipped
@dc.dataclass 
class Player:
    Name:str
    Health:int
    MaxHealth:int
    Mana:int
    MaxMana:int
    Loadout:list[Equipment] = dc.field(default_factory=list)
    StatusEffects:list[tuple[str,int]] = dc.field(default_factory=list) # List of status effects currently affecting the player, with their remaining duration in turns, e.g. [("Burn", 2), ("Poison", 3)]
    def heal(self, amount:int):
        self.Health = min(self.Health + amount, self.MaxHealth)
    def hurt(self, amount:int):
        self.Health = max(self.Health - amount, 0)
        if self.Health == 0:
            print(f"{self.Name} has been defeated!")
            #put death handler here
    def StatusTick(self):
        for i in range(len(self.StatusEffects)-1, -1, -1):
            effect, duration = self.StatusEffects[i]
            if effect == "Burn":
                self.hurt(5) # Burn does 5 damage per turn
            elif effect == "Poison":
                self.hurt(3) # Poison does 3 damage per turn
            # Add more status effects as needed
            self.StatusEffects[i] = (effect, duration - 1)
            if self.StatusEffects[i][1] <= 0:
                print(f"{self.Name} is no longer affected by {effect}.")
                del self.StatusEffects[i]

@dc.dataclass
class Enemy:
    Name:str
    Health:int
    MaxHealth:int
    Mana:int
    MaxMana:int

    def __post_init__(self):
        self.Health = self.MaxHealth
        self.Mana = self.MaxMana
    