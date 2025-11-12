
import os 
from copy import deepcopy
import dataclasses as dc
from time import sleep
import random
import turtle
import math
from typing import Dict,Tuple,List,Optional
ccdone = 0
vowels = {"a","e","i","o","u","A","E","I","O","U"}
pclasses = ["Mage","Warrior","Archer","Spellblade"]
reqrooms = 0
#roomids = {}
global validroomlocs
invalidroomlocs = set({})
validroomlocs = set({})
dorkondict = {"north":"south",
            "south":"north",
            "east":"west",
            "west":"east"}
devmode = None
mapcomplexity = 2
roomthemes = ["castle","cave","ruin"]
perimiterrooms = []
roombuffer = []
specialroomlocs = [(0,0)]
roomcolors = {"ruin":(0,102,0),"castle":(192,192,192)}
@dc.dataclass
class Attack:
    Name:str = "Unnamed Attack"             #Name of Attack
    Hits:int = 0                            #Number of Hits
    Damage:int = 0                          #Damage per Hit
    Desc:str = "Attack Missing Description" #Attack Description
    CD:int = 1                              #Cooldown
    Healing:int = 0                         #Healing (Optional)
    DtypeOVRW:str = None                    #Damage Type Overwride (Optional)
    ImbueReq:Optional[list[bool,str]]       #True or False if it needs an imbuement to show up, followed by either "Ice" or "Fire" as the imbuement it needs (Optional)

@dc.dataclass
class WeaponType:
    Name:str
    Attacks:list[Attack]
    Desc:str = "Weapon Missing Description"
    DamageType:str = "Normal"
NBWeapon = WeaponType("",[])
@dc.dataclass
class ClassType:
    Name:str = ""
    Weapons:list[WeaponType] = None
    HPmult:int = 1
    MPmult:int = 1
    Desc:str = "Class Missing Description"
NBClass = ClassType()
@dc.dataclass
class Player:
    Name:str = ""                                #Players name, should not be modified EVER
    Class:ClassType = None                       #Players class, should not be modified EVER
    Weapon:WeaponType = None                     #Players weapon, can be changed throughout the game by picking up weapons from chests
    Skills:list = dc.field(default_factory=list) #Players skills, should not be modified EVER
    MHP:int = 100                                #Players Max Health Points, may be modified with Addition and Multiplication operations positively or negatively
    MMP:int = 100                                #Players Max Mana Points, may be modified with Addition and Multiplication operations positively or negatively
    HP:int = 100                                 #Players current Health Points, regens fully when outside battle, game over when drops to 0
    MP:int = 100                                 #Players current Mana Points, regens fully outside battle, can't cast magic when drops to 0
    Luck:int = 1                                 #Players Luck modifier, should ONLY be modified using Multiplication operations to increase or reduce it  
    Imbue:Optional[str]                          #Players current Imbuement, can only be given by Equiptment and may unlock new attacks with players weapon
    DMGmult:Optional[float]                      #Players Damage Multiplier, can only be modified by weapons and equpitment, should only be modified using multiplication
player = Player("",NBClass,NBWeapon)

@dc.dataclass
class Equiptment:
    #Type of Equiptment (Ring, Necklace, Crown)
    Type:str
    #Name of this item, (Ring of..., Necklace of... Crown of...)
    Name:str
    #stat name, math operation, number eg, (health,add,50) or (health,mult,0.90) or (luck,mult,1.1), if first string in the list for any stat is "NONE" then that stat is ignored, if there are any Stats, there must be a good and a bad stat modifier, the third can be left blank or either good or bad, some stats may only be modified in specific ways, look at the player dataclass for specific restrictions
    Stat1:Optional[list[str,str,float]] # if a stat here exists then stat2 must also exist, and must be of opposite type (if this is a positive stat boost, then stat2 must reduce a different stat and vice versa)
    Stat2:Optional[list[str,str,float]] # only exists if stat 1 exists
    Stat3:Optional[list[str,str,float]] # can have its first string set to NONE to skip it, or can include either a good or bad trait, independant of stat1 and stat2
    #Either Fire or Ice, only one imbuement source allowed at a time, should only be used if the equiptment provides an attack of similar kind (fire imbue for fireball for example) or if the stats increase damage in any way (stat1 increasing damage by x1.1 for example )
    Imbue:Optional[str]
    #Value in coins, calculated by seeing how positive and negative stats are affected 
    Value:Optional[float]
    #True or False, most spell rings are consumeable, maybe a few are not 
    Consumeable:Optional[bool]
    #How many uses before it breaks
    Uses:Optional[int]
    #GIVE,HEAL,REGEN, Heal/regen amount (ignored if Give), Attack that it gives access to  
    Action:Optional[list[str,int,Optional[Attack]]]




@dc.dataclass
class Poi:
    Type:str
    Contents:list[Equiptment]


@dc.dataclass
class Room:
    Theme:str = "Unassigned"
    Size:str = "medium"
    Desc:str = "Description Not Generated"
    Diff:int = 0
    Pois:list[Poi] = None
    Connections:dict = None


roomids: Dict[Tuple[int, int], Room] = {}
@dc.dataclass
#roomids[(0,0)] = ["cave",'large',"Spawn Room",0,[],{"north":(0,1),"east":(1,0),"south":(0,-1),"west":(-1,0)}]
class RIDS:
    Theme:int = 0
    Size:int = 1
    Desc:int = 2
    Diff:int = 3
    POIS:int = 4
    Doors:int = 5
Rids =RIDS()

def Librarysetup():
    ##attack setups
    ##format is (name,number of hits,damage per hit,description of the attack, cooldown in turns, healing given to the player if any, damage type overwride if needed) last two are optional and should only be used on attacks that have lifesteal or magic damage types, the ASK damage overwride asks the player what damage type to deal, while the PLAYER damage type uses the players chosen magic type (ice or fire)
    QSlash =Attack("Quick Slash",2,3,"",2)
    HSlash =Attack("Heavy Slash",1,8,"",2)
    Thrust =Attack("Thrust",1,4,"",1 )

    Reap =Attack("Reap",1,10,"Steal your enemies lifeforce",5,5) #Scythe Only
    Whirlwind =Attack("Whirlwind",4,2,"Imbue your Scythe and spin rapidly, hitting multiple times",5,0,"ASK") #Scythe Only

    GreatSlam =Attack("Sword Slam",1,12,"Slam the flat of your blade into your enemy",3,0,"Blunt") #Greatsword Only
    Cleave =Attack("Cleaving Strike",1,20,"Put all your might into one massive attack",10,-5) #Greatsword Only

    EldrichBlast =Attack("Otherworldly Bang",3,5,"Fires blasts of legally distinct magic at your foes",4,0,"PLAYER") #Rapier Only

    #Weapon types
    Fire =WeaponType("Flame Magic",[],"Fire","Use the power of fire to burn your enemies to a crisp") #focuses on piling on stacks of fire, burning the enemy over time 
    Ice =WeaponType("Ice Magic",[],"Ice","Use the power of ice to freeze your enemies in place") #focuses on piling on stacks of frost, freezing the enemy over time
    Greatsword =WeaponType("Greatsword",[HSlash,Cleave,GreatSlam],"") # focuses on large, single hit attacks
    Shortsword =WeaponType("Shortsword",[QSlash,HSlash,Thrust],"") # focuses on smaller, multi hit attacks
    Longbow =WeaponType("Longbow",[],"") # focuses on large, single hit attacks
    Shortbow =WeaponType("Shortbow",[],"")# focuses on smaller, multi hit attacks
    Scythe =WeaponType("Scythe",[Reap,Whirlwind],"") # has many life steal attacks but most attacks have a high cooldown
    Rapier =WeaponType("Rapier",[EldrichBlast,Thrust],"")# has many magic imbued attacks, and focuses on quick, multi target strikes

    Mage = ClassType("Mage",[Fire,Ice],0.5,1.5,"Ranged Caster, Higher MP but low HP - Pure Magic damage, and lots of it")
    Warrior = ClassType("Warrior",[Greatsword,Shortsword],1.5,0.5,"Melee Fighter, Higher HP but low MP - Pure Melee damage, and lots of it")
    Archer = ClassType("Archer",[Longbow,Shortbow],1.25,0.75,"")
    Spellblade = ClassType("Spellblade",[Scythe,Rapier],0.75,1.25)

    #Chest = Poi()



    global class_list,weapon_list
    class_list = {
            "Mage":Mage,
            "Warrior":Warrior,
            "Archer":Archer,
            "Spellblade":Spellblade
              }
    weapon_list = {
            "ice magic":Ice,
            "flame magic":Fire,
            "greatsword":Greatsword,
            "shortsword":Shortsword,
            "longbow":Longbow,
            "shortbow":Shortbow,
            "scythe":Scythe,
            "rapier":Rapier

              }

skill_library = {
    "Foolproof-proof":"Disarm a trapped object without chance of failure",
    #"Brace":"Brace your body for a blow, reduces the damage of the next attack that hits you",
    "Lockpicking lawyer":"Pick a lock without consuming a lockpick",
    "Third eye":"Check the room for hidden objects quickly",
}

def statsheet(*clear):
    if clear:
        Clear()
    print("Your name is " + player.Name)
    if ccdone == 1 or player.Class.Name:
        if player.Class.Name[0].lower() in vowels:
            print("You are an " + player.Class.Name)
        else:
            print("You are a " + player.Class.Name)
    if ccdone == 1 or player.Weapon.Name:
        if " " in player.Weapon.Name:
            print("Your weapon is " + player.Weapon.Name)

        elif player.Weapon.Name[0].lower() in vowels:
             print("Your weapon is an " + player.Weapon.Name)
        else:
             print("Your weapon is a " + player.Weapon.Name)
    if ccdone == 1 or len(player.Skills) >= 2:
        print("Your skills are: " + player.Skills[0] + " and " + player.Skills[-1] )

def confirm(x):
    pin = input("Take this " + str(x) + "? Y/N: ").lower()
    if pin == "y" or pin == "yes":
        return True
    else:
        return False

def Clear():
    os.system('cls' if os.name == 'nt' else 'clear')
def devprint(*x):
    if devmode == True:
        print(''.join(map(str,x)))
def TurtleSetup():
    global devt,devmap
    devmap = turtle.Screen()
    devmap.bgcolor("black")
    devmap.title("Dev Map")
    devt = turtle.Turtle()
    devt.pencolor("white")
    devmap.colormode(255)
    devt.speed(0)
    devt.hideturtle()

def Randomcolortuple():
    return((random.randint(10,255),random.randint(10,255),random.randint(10,255)))
def Getadjacentrooms(origin): # this is not used in RoomLocValidator because I wrote it after and am afraid of changing it
    rx,ry = origin
    return list((rx-1,ry),(rx+1,ry),(rx,ry-1),(rx,ry+1))

def RoomLocValidator(room):
    rx, ry = room
    for pos in [(rx - 1, ry), (rx + 1, ry), (rx, ry - 1), (rx, ry + 1)]:  # Check adjacent spaces of existing rooms
        devprint("testing position ", pos, " for room ", room)
        if abs(pos[0]) <= 7 and abs(pos[1]) <= 5:  # Check if space is within bounds
            devprint(pos, " within valid bounds")
            if pos not in roomids and pos not in invalidroomlocs:  # Check if the room already exists or is already illegal
                devprint(pos, " does not contain a room and has not already been invalidated")
                lx, ly = pos
                adjrooms = 0
                for loc in [(lx - 1, ly), (lx + 1, ly), (lx, ly - 1), (lx, ly + 1)]:  # Check the adjacent spaces of available room locs
                    devprint("testing adjacent location", loc, "for position", pos, "for room ", room)
                    if abs(loc[0]) <= 7 and abs(loc[1]) <= 5:  # Check if the loc is within bounds
                        devprint("location ", loc, " within bounds")
                        if loc in roomids:  # If a room exists at that location
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
                    if pos == (0, 0):
                        # Handle the special case for the room at (0, 0)
                        print("doing something to 0,0")
                    else:
                        # Assign a new room at the current position with default or random properties
                        validroomlocs.add(pos)
            else:
                devprint(pos, " already contains a room or has been previously invalidated")
        else:
            devprint(pos, " out of bounds")





        

def CharCreator():
    print("Starting Charactor Creator")
    player.Name = input("Name your character: ")
    if Player.Name == "e":
        devmode = True
    statsheet(1)
    while True != False:
        statsheet(1)
        print("Available classes: " + ', '.join(class_list.keys()))
        pin = str(input("Choose your class:"))
        if pin.lower() not in (x.lower() for x in class_list.keys()): 
            print("That is not a valid class, try again")
        else:
            print("You have chosen: " + str(pin.capitalize()))
            print("Description: " + class_list[pin.capitalize()].Desc)
            if confirm("class"):
                player.Class = class_list[str(pin.capitalize())]
                player.MHP *= player.Class.HPmult
                player.HP = player.MHP
                player.MMP *= player.Class.MPmult
                player.MP = player.MMP
                break
    while True != False:
        statsheet(1)
        print("Available weapons for your class: " + ', '.join(x.Name for x in player.Class.Weapons))
        pin = str(input("Choose your weapon: "))
        if pin.lower() not in (x.Name.lower() for x in player.Class.Weapons):
            print("That is not a valid weapon, try again")
        else:
            print("You have chosen: " + str(pin.capitalize()))
            print("Description: " + weapon_list[pin.lower()].Desc)
            bruh = (weapon_list[pin.lower()].Attacks)
            bruh2 = [x.Name.lower() for x in bruh]
            print("Attacks: " + ', '.join([x.Name for x in weapon_list[pin.lower()].Attacks]))
            if confirm("weapon"):
                player.Weapon = weapon_list[str(pin.lower())]
                break
    while True != False:
        statsheet(1)
        print("Available skills: " + ( ', '.join(set(skill_library.keys()).difference(player.Skills))))
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
    ccdone = 1
def shithead():
    sleep(1)
    # def DunGen():
    #     Clear()
    #     print("starting DunGen")
    #     roomid["0-0"] = ["stone",'large',"Spawn Room",0,[],{"north":-1,"east":-1,"south":-1,"west":-1}]
        # while True:
        #     print("Easy - Normal - Hard - Hell")
        #     pin = input("Select a difficulty: \n").lower()
        #     if devmode or pin in ["easy","normal","hard","hell"]:
        #         if devmode or input("You have selected: " + pin.capitalize() + ". Proceed?\n").lower() in ["y","yes"]:
        #             if pin == "easy":
        #                 rooms = 10
        #             elif pin == "normal":
        #                 rooms = 15
        #             elif pin == "hard":
        #                 rooms = 20
        #             elif pin == "hell":
        #                 rooms = 30
        #             elif devmode:
        #                 rooms = 31
        #             else:
        #                 print("Difficulty selection failed (somehow), got: " + str(pin) + ", expected easy,normal,hard,hell")
        #             break
        #     else:
        #         print("Not a valid input, try again")
        #         sleep(1)
    #     opencons = {}
    #     room_distribution = [0,0,0]
    #     while len(roomid) < rooms:
    #         opencons = {}
    #         allopen = []
    #         for room in roomid:
    #             # if roomid[room][1] == "large":
    #             #     room_distribution[0] += 1
    #             # elif roomid[room][1] == "medium":
    #             #     room_distribution[1] += 1
    #             # elif room_distribution == "small":
    #             #     room_distribution[2] += 1
    #             for key in roomid[room][5]:
    #                 if roomid[room][5][key] == -1:
    #                     if room not in opencons.keys(): 
    #                         opencons.update({room:[key]})
    #                     else:
    #                         opencons[room].append(key)
    #                     allopen.append(key)
    #         id = len(roomid)
    #         roomid[id] = ["Unassigned",["large","medium","medium","small"][random.randint(0,3)],"Description Not Generated",0,[],{"north":-1,"east":-1,"south":-1,"west":-1}]
    #         target = random.randint(1,len(opencons)) -1  #x1
    #         sideint = random.randint(1,len(opencons[target])) -1 #x2
    #         Clear()
    #         devprint("Attaching RoomID:"+ str(id) + " to RoomID:" + str(target) + " Side: " + opencons[target][sideint])
    #         devprint("Attaching RoomID:"+ str(id) + " to RoomID:" + str(target) + " Side: " + list(roomid[target][5])[sideint])
    #         sidestr = list(roomid[target][5])[sideint] # the side to be modified
    #         roomid[target][5][sidestr] = id
    #         devprint("RoomID:" + str(target) + " Side:" + sidestr +  " Set to:" + str(id))
    #         devprint("Attaching RoomID:"+ str(target) + " to RoomID:" + str(id) + " Side: " + dorkondict[sidestr])
    #         sidestr = dorkondict[sidestr]
    #         roomid[id][5][sidestr] = target
            
    
    #         while False == True:
    #             print("Reciever pre-assignment: " + str(roomid[x1][5][list(roomid[x1][5])[x2]]))
    #             roomid[x1][5][list(roomid[x1][5])[x2]] = id
    #             print("Expected Post-ID:" + str(id))
    #             print("Reciever post-assignment: " + str(roomid[x1][5][list(roomid[x1][5])[x2]]))
    #             print("Sender pre-assignment: " + str(roomid[id][5][dorkondict[list(roomid[x1][5])[x2]]]))
    #             roomid[id][5][dorkondict[list(roomid[x1][5])[x2]]] = x1
    #             print("Expected Post-ID: " + str(x1))
    #             print("Sender post-assignment: " + str(roomid[id][5][dorkondict[list(roomid[x1][5])[x2]]]))
    #             Clear()
                                                                                        
    #     print("Generating rooms")
    #     while len(roomid) < rooms:
    #         print("Working on roomid:" + str(len(roomid) + 1))
    #         #prepare dict entry
    #         id = len(roomid)
    #         roomid[id] = ["Unassigned",["large","medium","medium","small"][random.randint(0,3)],"Description Not Generated",0,[],{"north":-1,"east":-1,"south":-1,"west":-1}]
    #         #assemble dungeon
    #     global opencons,room_distribution
    #     opencons = {}
    #     room_distribution = [0,0,0]
    #     for room in roomid:
    #         if roomid[room][1] == "large":
    #             room_distribution[0] += 1
    #         elif roomid[room][1] == "medium":
    #             room_distribution[1] += 1
    #         else:
    #             room_distribution[2] += 1
            
    #         for key in roomid[room][5]:
    #             if roomid[room][5][key] == -1:
    #                 if room not in opencons.keys(): 
    #                     opencons.update({room:[key]})
    #                 else:
    #                     opencons[room].append(key)
    #                 #basically we want a dictionary pointing to a list, where the key is the room ID, and the value is the list
    #             #print(roomid[0][4][key])
    #     x3 = 0
    #     while x3 < 1000:
    #         x1 = random.randint(1,len(opencons)) -1
    #         x2 = random.randint(1,len(opencons[x1])) -1
    #         print("Roomid: " + str(x1) + " Side: " + opencons[x1][x2])
    #         x3 += 1
        

    # im gonna be real future me, you're probably gonna want to pseudocode the entire thing before making it
    # also what the fuck are we actually doing with the Poi Dataclass, is it meant to be used when accessing the current room data so that we can do len(Room.Pois) and other such bullshittery

    # Room data needed to generate:
    # random room size, small, medium, large. Larger rooms have more POIs
    # Position in the world, this means I need to set ID0 to the spawn room, and then keep track of every available connection point (I think we do a loop that builds a dict of every room with open spaces, and the directions of those spaces, and then just get two random numbers to determine which room ID we are looking in, and which direction we are attaching too



    # Theme to determine adjectives used in descriptions and POIs placed in the room
    # # I think that rooms should have twice the chance to be the same theme as the rooms next to them (A room next to a rocky themed room would have "rocky" appear twice in the theme random table)
    

    # the description generator is gonna need to be a whole thing
def DunGen():
    devprint("starting dungen")
    #roomids = {}
    global roomids
    #roomids[(0,0)] = ["cave",'large',"Spawn Room",0,[],{"north":(0,1),"east":(1,0),"south":(0,-1),"west":(-1,0)}]
    roomids[(0,0)] = Room("cave",'large',"Spawn Room",0,[],{"north":(0,1),"east":(1,0),"south":(0,-1),"west":(-1,0)})
    totalrooms = 1
    while True:
        print("Easy - Normal - Hard - Hell")
        pin = input("Select a difficulty: \n").lower()
        devt.clear()
        devt.pencolor("white")
        devt.penup()
        devt.goto(0,0)
        devt.pendown()
        devt.dot(80,(102,0,51))
        devt.pencolor("black")
        devt.write(str(mapcomplexity))
        if devmode or pin in ["easy","normal","hard","hell"]:
            if devmode or input("You have selected: " + pin.capitalize() + ". Proceed?\n").lower() in ["y","yes"]:
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
                    print("Difficulty selection failed (somehow), got: " + str(pin) + ", expected easy,normal,hard,hell")
                break
        else:
            print("Not a valid input, try again")
            sleep(1)
    validroomlocs.clear()
    invalidroomlocs.clear()
    timesrun = 0
    while totalrooms < reqrooms:
        for room in roomids:
            RoomLocValidator(room)

        while True:
            newroomloc = random.choice(list(validroomlocs))
            if newroomloc not in roomids:
                break
        devprint(newroomloc, "has been selected")
        oldrooms = list(roomids.keys())
        
        # Create a new Room instance using the Room class
        roomids[newroomloc] = Room(
            Theme="Unassigned", 
            Size=["large", "medium", "medium", "small"][random.randint(0, 3)], 
            Desc="Description Not Generated", 
            Diff=0, 
            Pois=[], 
            Connections={"north": (newroomloc[0], newroomloc[1] + 1), 
                        "east": (newroomloc[0] + 1, newroomloc[1]), 
                        "south": (newroomloc[0], newroomloc[1] - 1), 
                        "west": (newroomloc[0] - 1, newroomloc[1])}
        )
        totalrooms = len(roomids)
        timesrun += 1
        if oldrooms == list(roomids.keys()):
            devprint("room overwritten!!!")
        
        if devmode == True:  # Draws the map
            rx, ry = newroomloc
            devt.penup()
            devt.goto(0 + (100 * rx), 0 + (100 * ry))
            devt.pendown()
            devt.dot(60, tuple(Randomcolortuple()))
            devt.penup()
            devt.goto(0 + (100 * rx) - 12.5, 0 + (100 * ry))
            devt.pendown()
            devt.write(str(newroomloc))
            devprint("turtle done")

    # Find perimeter rooms
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

    maxdist = 0
    for room1 in perimiterrooms:  # Find two furthest rooms
        for room2 in perimiterrooms:
            if not room1 == room2:
                dist = math.dist(room1, room2)
                if dist > maxdist:
                    maxdist = dist
                    global furthestrooms
                    furthestrooms = [room1, room2]

    x = 0
    for room in furthestrooms:
        for pos in roomids[room].Connections:  # Use .Connections for accessing doors
            if roomids[room].Connections[pos] in roomids:
                newroomloc = roomids[room].Connections[dorkondict[pos]]
                if x == 0:
                    roomids[roomids[room].Connections[dorkondict[pos]]] = Room(
                        Theme="ruin",
                        Size="large",
                        Desc="Key Room",
                        Diff=0,
                        Pois=[],
                        Connections={"north": (newroomloc[0], newroomloc[1] + 1),
                                    "east": (newroomloc[0] + 1, newroomloc[1]),
                                    "south": (newroomloc[0], newroomloc[1] - 1),
                                    "west": (newroomloc[0] - 1, newroomloc[1])}
                    )
                    rx, ry = newroomloc
                    devt.penup()
                    devt.goto(0 + (100 * rx), 0 + (100 * ry))
                    devt.pendown()
                    devt.dot(80, tuple((0, 102, 0)))
                    devt.penup()
                    devt.goto(0 + (100 * rx) - 12.5, 0 + (100 * ry))
                    devt.pendown()
                    devt.write(str(newroomloc))
                    specialroomlocs.append(list(roomids.keys())[-1])
                    break
                if x == 1:
                    roomids[roomids[room].Connections[dorkondict[pos]]] = Room(
                        Theme="castle",
                        Size="large",
                        Desc="Boss Room",
                        Diff=0,
                        Pois=[],
                        Connections={"north": (newroomloc[0], newroomloc[1] + 1),
                                    "east": (newroomloc[0] + 1, newroomloc[1]),
                                    "south": (newroomloc[0], newroomloc[1] - 1),
                                    "west": (newroomloc[0] - 1, newroomloc[1])}
                    )
                    rx, ry = newroomloc
                    devt.penup()
                    devt.goto(0 + (100 * rx), 0 + (100 * ry))
                    devt.pendown()
                    devt.dot(80, tuple((192, 192, 192)))
                    devt.penup()
                    devt.goto(0 + (100 * rx) - 12.5, 0 + (100 * ry))
                    devt.pendown()
                    devt.write(str(newroomloc))
                    specialroomlocs.append(list(roomids.keys())[-1])
                    break
        x += 1







    culleddict = deepcopy(roomids)  # Create a deep copy of roomids to avoid modifying the original during iteration

    # Check if the room at (0, 0) in roomids and culleddict are the same object
    print(culleddict[(0, 0)] is roomids[(0, 0)])

    # Iterate through all rooms in roomids
    for room_pos, room in roomids.items():
        devprint("culling ", room_pos)
        
        # Iterate over the connections (directions) in the room's Connections attribute
        print(room)
        room.Connections
        for direction, connected_pos in room.Connections.items():
            devprint("culling ", connected_pos, " in ", room_pos)
            
            # Check if the connected position is in roomids
            if connected_pos not in roomids:
                devprint("removing connection from ", room_pos, " to ", connected_pos)
                # If the connected room does not exist, remove the connection from the culled dictionary
                del culleddict[room_pos].Connections[direction]
    roomids = deepcopy(culleddict)
    #Theme proliferation time
    themed = deepcopy(specialroomlocs)
    unthemed = list(roomids.keys())
    for room in themed:
        unthemed.remove(room)

    while len(unthemed) > 0:
        room = random.choice(themed)
        
        # Check the connections (doors) of the selected room
        for existingroom in roomids[room].Connections:  # Use .Connections
            adjroom = roomids[room].Connections[existingroom]  # Get the adjacent room
            
            if roomids[adjroom].Theme == 'Unassigned':  # Check if the room's theme is unassigned
                roomids[adjroom].Theme = roomids[room].Theme  # Set the theme of the adjacent room
                
                rx, ry = adjroom
                devt.penup()
                devt.goto(0 + (100 * rx), 0 + (100 * ry))
                devt.pendown()

                # Draw different dots based on the room's theme
                if roomids[room].Theme == 'ruin':
                    devt.dot(60, (0, 102, 0))  # Green for ruin
                elif roomids[room].Theme == 'cave':
                    devt.dot(60, (102, 0, 51))  # Purple for cave
                elif roomids[room].Theme == 'castle':
                    devt.dot(60, (192, 192, 192))  # Gray for castle
                    
                devt.penup()
                devt.goto(0 + (100 * rx) - 12.5, 0 + (100 * ry))
                devt.pendown()
                devt.write(str(adjroom))
                
                # Remove from unthemed and add to themed
                unthemed.remove(adjroom)
                themed.append(adjroom)
        
        themed.remove(room)  # Remove the current room from themed list

    devprint("theme proliferation complete")


        
## next up is room populating, we want to limit the amount of things in a room based on size, so small things could have at most 1-3 POIs, medium can have an enemy and 2-4 POIs, and large can have 1-2 enemies and 3-7 POIs

## most POIs should just be nothingburger, maybe containing a coin or two (if I have time to implement shopping) (one shop would be near the boss room, another secret shot with better stuff would be hidden somewhere and require the boss room key to get in)
## some POIs should be secret, requiring another POI to be interacted with to reveal (chest hidden until torch pulled kinda thing)
## every large room and medium rooms with enemies should have chests in them, small rooms may rarely have hidden chests
##  chests should be given loot from a loot table, with its stats affected by a general luck roll somehow (eg: necklace that rolled well could have +40 health or + 3 damage )
## loot should have rings, necklaces, rarely new weapons, often coins and heath potions, very rarely free spell casting stuff (if I can figure out how to implement that)
## I want rings to be able to give you magic element infusions so that you can use infused attacks 


    devprint("hehehha")




        
    













            




Clear()
Librarysetup()
TurtleSetup()
#CharCreator()
if Player.Name == "" or player.Name == "e":
    devmode = True
print("Done")
DunGen()
print("DoneGen")


