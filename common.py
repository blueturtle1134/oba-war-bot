import random
import time

GUILD_ID = 270763719619772416
ANSWER = 743650853986238525
# ANSWER = 747105016182997073 # test
CATEGORY_ID = 743650031831351336
CHRONSPIRACY = 795117843502333994
IMPPERIUM = 795118009567674370
ERISTOCRACY = 795118078504730624
TEAM_ROLES = CHRONSPIRACY, IMPPERIUM, ERISTOCRACY
TEAM_NAMES = "Chronspiracy", "IMPPerium", "Eristocracy", "Crysuade", "Grand Thonk"
TEAM_COLORS = (229, 208, 128), (214, 36, 0), (52, 152, 219), (102, 2, 60), (17, 128, 106)
TEAM_LETTER = "C", "I", "E", "R", "T"
BLUE = 322467362857025538
FAL = 225241718344122368
RYU = 228162889062678529
FORUM = 270763719619772416
ANNOUNCEMENTS = 743650430810062888
LOG = 763108528553590824
LOBBY = 743650314233839697
TOWER = 401200182525558785
ALLOWED_CHANNELS = {706644963596828693,  # fallacy
                    371423137574813697,  # complaints
                    596120692844658709,  # media
                    761616481967407106,  # neo terra
                    494176816546840576,  # discord games forum
                    753411014334218250,  # generals chat
                    758024681365176561,  # demoko rp
                    753436234868588605,  # 1 10 game
                    762470353271783455}  # battleship discussion
r = random.Random()


def team_from_member(member):
    if member.id == BLUE:
        return 3
    if member.id == FAL:
        return r.choice(range(0, 3))
    for role in member.roles:
        for i, x in enumerate(TEAM_ROLES):
            if role.id == x:
                return i
    return 3


def team_from_string(string):
    string = string.lower().strip()
    if string == "chronspiracy":
        return 0
    elif string == "impperium":
        return 1
    elif string == "eristocracy":
        return 2
    return None


def get_notification(role_ids):
    return " ".join([f"<@&{role}>" for role in role_ids])


def get_team_name(team):
    if 0 <= team < len(TEAM_NAMES):
        return TEAM_NAMES[team]
    else:
        return "Cryusade"


def scheduled_level():
    return int((time.time() - 1609644810) / 259200) + 1, 259200 - ((time.time() - 1609644810) % 259200)


def print_points(point_array):
    return "\n".join([f"{TEAM_NAMES[i]}: **{p}**" for i, p in enumerate(point_array)])
