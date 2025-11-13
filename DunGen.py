import dataclasses as dc
import random




devmode:bool = True
def Devprint(msg:str):
    if devmode:
        print(f"[DEV]: {msg}")
@dc.dataclass(frozen=True)
class Equipment:
    Name:str = "ERROR"
    Slot:str = "ERROR"  # "Head"
    Desc:str = "ERROR"  # e.g., "A sturdy iron helmet."
    DropChance:int = 0 # What % chance this item has to drop as loot
@dc.dataclass
class Entity: # Base class for all living entities in the game
    Name:str = "ERROR"
    MaxHP:int = -1
    CurrentHP:int = -1
    MaxMP:int = -1
    CurrentMP:int = -1
    Speed:int = -1
    Loadout:dict[str, list[Equipment]] = dc.field(default_factory=lambda: {"Head":[], "Chest":[], "Legs":[],"Boots":[], "Weapon":[], "Ring":[], "Neck":[]})
    def __post_init__(self):
        # Handle CurrentHP and CurrentMP defaults
        if self.CurrentHP == -1:
            object.__setattr__(self, 'CurrentHP', self.MaxHP)
            Devprint(f"{self.Name}'s CurrentHP set to MaxHP ({self.MaxHP})")
        if self.CurrentMP == -1:
            object.__setattr__(self, 'CurrentMP', self.MaxMP)
            Devprint(f"{self.Name}'s CurrentMP set to MaxMP ({self.MaxMP})")
        
        # Validate required fields and ranges
        error = (
               (self.Name == "ERROR" and "Entity must have a name")
            or (self.MaxHP == -1 and "Entity must have MaxHP set")
            or (self.MaxHP < 1 and f"{self.Name} must have a positive MaxHP")
            or (self.CurrentHP > self.MaxHP and f"{self.Name}'s CurrentHP must be between 0 and MaxHP")
            or (self.MaxMP == -1 and f"{self.Name} must have MaxMP set")
            or (self.MaxMP < 0 and f"{self.Name} must have a non-negative MaxMP")
            or (self.CurrentMP > self.MaxMP and f"{self.Name}'s CurrentMP must be between 0 and MaxMP")
            or (self.Speed == -1 and f"{self.Name} must have Speed set")
            or (self.Speed < 1 and f"{self.Name} must have a positive Speed")
        )
        if error:
            raise ValueError(error)
@dc.dataclass
class Player(Entity):
    Inventory:list = dc.field(default_factory=list)
    LuckModifier:float = 1.0 # Multiplier affecting loot drop chances and gold loot amounts
    pass
    def CheckLoadoutAddition(self, item:Equipment):
        """Checks if there is space to add the given item to the player's loadout.
        
        Returns True if the item can be added, False otherwise.
        Raises ValueError if the item is not an Equipment instance.
        """
        #safety check to make sure item is actually an Equipment
        if not isinstance(item, Equipment):
            raise ValueError("item must be an instance of Equipment")
        # Check based on item slot
        if item.Slot == "Ring":
            if len(self.Loadout["Ring"]) >= 5:
                return False # max of 5 rings, return false
        else:
            if len(self.Loadout[item.Slot]) >= 1:
                return False # only 1 of other equipment types, return false
        return True
    def Equip(self, item:Equipment):
        if self.CheckLoadoutAddition(item):
            self.Loadout[item.Slot].append(item)
            print(f"{item.Name} equipped to {item.Slot} slot.")
        else:
            if item.Slot == "Ring":
                print(f"Maximum number of Rings reached, pick a ring to replace, or cancel")
                for idx, ring in enumerate(self.Loadout["Ring"]):
                    print(f"{idx + 1}: {ring.Name} - {ring.Desc}")
                while True:
                    choice = input("Enter the number of the ring to replace, or 'c' to cancel: ")
                    if choice.lower() == 'c':
                        print("Equip cancelled.")
                        return
                    else:
                        choice_idx = int(choice) - 1
                        if 0 <= choice_idx < len(self.Loadout["Ring"]):
                            replaced_ring = self.Loadout["Ring"][choice_idx]
                            self.Inventory.append(replaced_ring)
                            self.Loadout["Ring"][choice_idx] = item
                            self.Inventory.remove(item)
                            
                            print(f"Replaced {replaced_ring.Name} with {item.Name}.")
                            break
                        else:
                            print("Invalid choice, try again.")
            else:
                print(f"Slot {item.Slot} already contains {self.Loadout[item.Slot][0].Name}, replace this item?")
                while True:
                    choice = input("Enter 'y' to replace, 'n' to cancel: ")
                    if choice.lower() == 'y':
                        replaced_item = self.Loadout[item.Slot][0]
                        self.Inventory.append(replaced_item)
                        self.Loadout[item.Slot][0] = item
                        self.Inventory.remove(item)
                        
                        print(f"Replaced {replaced_item.Name} with {item.Name}.")
                        break
                    elif choice.lower() == 'n':
                        print("Equip cancelled.")
                        break
                    else:
                        print("Invalid choice, try again.")

player = Player(Name="DEFAULT", MaxHP=1, MaxMP=1, Speed=1)
@dc.dataclass
class Monster(Entity):
    drops:int = -1
    pass

def GenerateDropTable(EquipmentDrops:list[Equipment]):
    for item in EquipmentDrops:
        if random.randint(1, 100) <= item.DropChance * player.LuckModifier :
            pass


def setup():
    pass
