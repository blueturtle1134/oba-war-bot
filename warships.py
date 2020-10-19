import json
import random
import time
from common import *

ARMOR_HP = 15
BASE_HP = 50
SAVE_FILE = "ships.json"

TIME_THRESHOLD = 6 * 60 * 60


class Building:
    def __init__(self, name, cost, onetime):
        self.name = name
        self.cost = cost
        self.onetime = onetime


BUILDINGS = {
    "engi": Building("Engineering Bay", lambda n: 3 * 2 ** n, False),
    "repair": Building("Repair Bay", lambda n: n + 4, False),
    "armor": Building("Hull Plating", lambda n: 2 * n + 3, False),
    "light": Building("Light Turret", lambda n: 2, False),
    "medium": Building("Medium Turret", lambda n: 5, False),
    "heavy": Building("Heavy Turret", lambda n: 12, False),
    "shield": Building("Shield Generator", lambda n: 4, False),
    # "missile": Building("Missile", lambda n: 10, False),
    "targeting": Building("Targeting System", lambda n: 12, True),
    "munitions": Building("Munitions Depot", lambda n: 15, True),
    "bridge": Building("Bridge", lambda n: 20, True),
    "recharge": Building("Recharge Array", lambda n: 15 * 2 ** n, True)
}


def calculate_build(amount, cost, current, progress, target):
    if amount + progress < target:
        return current, amount + progress, target
    else:
        amount -= target - progress
        current += 1
        while cost(current) <= amount:
            amount -= cost(current)
            current += 1
        return current, amount, cost(current)


class Ship:

    def __init__(self, name=None, source=None):
        if source is None:
            self.buildings = {x: (0, 0, y.cost(0)) for (x, y) in BUILDINGS.items()}
            self.hp = 50
            self.shield_time = time.time()
            self.shield_charge = 1.0
            self.sunk = False
        else:
            self.name = source["name"]
            self.hp = source["hp"]
            self.buildings = {x: tuple(source["buildings"][x] if x in source["buildings"] else (0, 0, 0))
                              for x in BUILDINGS}
            self.shield_time = source["shield_time"]
            self.shield_charge = source["shield_charge"]
            self.sunk = source["sunk"]
        if name:
            self.name = name

    def max_hp(self):
        return BASE_HP + self.buildings["armor"][0] * ARMOR_HP

    def max_shield(self):
        return self.buildings["shield"][0] * 10

    def build_speed(self):
        return self.buildings["engi"][0] + 1

    def repair_speed(self):
        return self.buildings["repair"][0] * 12

    def shield_speed(self):
        return 2 ** self.buildings["recharge"][0] / (8 * 60 * 60)

    def damage_output(self):
        return (self.buildings["light"][0] * 3 + self.buildings["medium"][0] * 10 + self.buildings["heavy"][0] * 30) \
               * (2 if self.buildings["munitions"][0] > 0 else 1)

    def targeting_power(self):
        return self.buildings["targeting"][0]

    def action_delay(self):
        return TIME_THRESHOLD * (0.5 if self.buildings["bridge"][0] > 0 else 1)

    def get_shield_percent(self):
        return min(self.shield_charge + (time.time() - self.shield_time) * self.shield_speed(), 1.0)

    def recalc_shield(self):
        self.shield_charge = self.get_shield_percent()
        self.shield_time = time.time()

    def take_damage(self, damage, targeting=0):
        shield = self.get_shield_percent() * self.max_shield()
        if damage == 0:
            return 0, None
        if damage > shield:
            if shield > 0:
                self.shield_time = time.time()
                self.shield_charge = 0.0
            damage -= shield
            self.hp -= damage
            if self.hp <= 0:
                self.sunk = True
            pierce_prob = damage / (shield + damage)
            if targeting > 0 and random.random() < pierce_prob:
                built = [x for x in self.buildings.keys() if self.buildings[x][0] > 0]
                if len(built) > 0:
                    targeted = random.choice(built)
                    built, progress, target = self.buildings[targeted]
                    for _ in range(targeting):
                        if progress == 0:
                            if built == 0:
                                break
                            else:
                                built -= 1
                                target = BUILDINGS[targeted].cost(built)
                                progress = target - 1
                        else:
                            progress -= 1
                    self.buildings[targeted] = built, progress, target
                    return damage, targeted
            return damage, None
        else:
            self.shield_charge -= damage / self.max_shield()
            self.shield_time = time.time()
            return 0, None

    def construct(self, building):
        previous = self.buildings[building][0]
        self.buildings[building] = calculate_build(self.build_speed(), BUILDINGS[building].cost,
                                                   *self.buildings[building])
        if building == "recharge" and self.buildings[building][0] > previous:
            self.recalc_shield()
        return self.buildings[building][0] > previous

    def repair(self, amount):
        old = self.hp
        self.hp = min(self.hp + amount, self.max_hp())
        return self.hp - old

    def fire(self, target):
        return target.take_damage(self.damage_output(), self.targeting_power())

    def description(self):
        if self.sunk:
            return f"**__{self.name}__**\n" \
                   f"SUNK!"
        return f"**__{self.name}__**\n" \
               f"**HP**: {self.hp:.1f}/{self.max_hp():.1f}\n" \
               f"**Shield**: {self.get_shield_percent() * self.max_shield():.1f}/{self.max_shield():.1f} " \
               f"({self.get_shield_percent():.1%})\n" \
               f"**Damage**: {self.damage_output():.1f}\n" \
               f"**Targeting**: {self.targeting_power()}\n" \
               f"**Build**: {self.build_speed()}\n" \
               f"**Repair**: {self.repair_speed()}\n" \
               f"**Buildings**:\n" + \
               "\n".join(
                   [f" - {building.name}: {self.buildings[name][0]} "
                    f"({self.buildings[name][1]}/{self.buildings[name][2]})" for name, building in BUILDINGS.items()
                    if name in self.buildings and (self.buildings[name][0] > 0 or self.buildings[name][1] > 0)])


ships = list()
overrides = dict()


def save():
    with open(SAVE_FILE, 'w') as file:
        file.write(json.dumps(dict(ships=[ship.__dict__ for ship in ships],
                                   last_action=last_action,
                                   overrides=overrides),
                              indent=4))


def load():
    global ships, last_action, overrides
    with open(SAVE_FILE, 'r') as file:
        data = json.load(file)
    ships = [Ship(source=x) for x in data["ships"]]
    last_action = data["last_action"]
    overrides = data["overrides"]


def ship_from_member(member):
    if member.id == 322467362857025538:
        return None
    elif str(member.id) in overrides:
        return ship_from_string(overrides[str(member.id)])
    else:
        for role in member.roles:
            if role.id == CHRONSPIRACY:
                return ships[0]
            if role.id == IMPPERIUM:
                return ships[1]
            if role.id == ERISTOCRACY:
                return ships[2]
        return None


def ship_from_string(string):
    if string == "chronspiracy":
        return ships[0]
    elif string == "impperium":
        return ships[1]
    elif string == "eristocracy":
        return ships[2]
    return None


def building_from_string(string):
    for building in BUILDINGS:
        if string.startswith(building):
            return building
    return None


def repair_command(body, sender_ship):
    target = ship_from_string(body)
    if not target:
        target = sender_ship
    repaired = target.repair(sender_ship.repair_speed())
    return f"Repaired {repaired:.1f} damage", target


def fire_command(body, sender_ship):
    target = ship_from_string(body)
    if target:
        if target == sender_ship:
            return f"You may not fire on yourself!\nYour timer has been set as punishment."
        damage, module = sender_ship.fire(target)
        if module:
            return f"Dealt {damage:.1f} damage; hit {BUILDINGS[module].name}!", target
        elif damage > 0:
            return f"Dealt {damage:.1f} to {target.name}.", target
        else:
            return f"{target.name} shields at {target.get_shield_percent():.1%}.", target
    else:
        return None


def build_command(body, sender_ship):
    building = building_from_string(body)
    if building:
        if sender_ship.construct(building):
            return f"Completed {BUILDINGS[building].name}", sender_ship
        else:
            return f"Building {BUILDINGS[building].name}:" \
                   f" ({sender_ship.buildings[building][1]}/{sender_ship.buildings[building][2]})", sender_ship
    else:
        return None


COMMANDS = {
    "build": build_command,
    "construct": build_command,
    "repair": repair_command,
    "fire": fire_command,
    "attack": fire_command
}


def show_time(seconds):
    return f"{seconds / 60:.1f} min"


last_action = dict()


def process_command(string, sender_ship, member_id):
    string = string.lower()
    split = string.split(" ", 1)
    if len(split) == 1:
        split.append("")
    command, body = tuple(split)
    if sender_ship is None:
        return None
    if command == "jump" and sender_ship.sunk:
        if ship_from_string(body):
            overrides[member_id] = body
            last_action[member_id] = 0
            save()
            return f"Jumped ship to {ship_from_string(body).name}, reset action timer"
    if sender_ship.sunk:
        return None
    threshold = sender_ship.action_delay()
    if member_id in last_action:
        time_since_last = time.time() - last_action[member_id]
    else:
        time_since_last = time.time()
    if command == "time":
        if time_since_last > threshold:
            return "You can act right now!"
        else:
            return "You can act again in " + show_time(threshold - time_since_last)
    if command in COMMANDS:
        if time_since_last > threshold:
            print(f"{sender_ship.name}: {command} {body}")
            result = COMMANDS[command](body, sender_ship)
            if result:
                last_action[member_id] = time.time()
                response, ship = result
                save()
                return f"`{response}`\n{ship.description()}"
            else:
                return f"Command unsuccessful - check spelling and try again"
        else:
            return "You can act again in " + show_time(threshold - time_since_last)


def main():
    global ships
    ships = [Ship("Chronspiracy"), Ship("IMPPerium"), Ship("Eristocracy")]
    save()
    # load()
    # while True:
    #     for ship in ships:
    #         print(ship.description())
    #     target = ships[int(input("Which ship to test: "))]
    #     process_command(input("Command to test: "), target)
    #     save()


if __name__ == "__main__":
    main()
