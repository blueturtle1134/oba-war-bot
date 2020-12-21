import random
import re

REGEX_FILE = "mao_rules.txt"
SAVE_FILE = "data/mao.txt"

REGEXES = list()
enacted = list()


def load():
    global REGEXES, enacted
    with open(REGEX_FILE, 'r') as file:
        REGEXES = [re.compile(line.strip(), re.IGNORECASE) if i < 10 else re.compile(line.strip()) for i, line
                   in enumerate(file.readlines())]
    with open(SAVE_FILE, 'r') as file:
        enacted = [x == "Y" for x in file.readline().strip()]
        enacted += [False] * (len(REGEXES) - len(enacted))
        to_ban = file.readline().strip()
        return to_ban


def save(to_ban=""):
    with open(SAVE_FILE, 'w') as file:
        file.write("".join("Y" if x else "N" for x in enacted))
        file.write("\n")
        file.write(to_ban)


def ban(text):
    save()
    load()
    bannable = list()
    for i, r in enumerate(REGEXES):
        if not enacted[i] and not r.match(text):
            bannable.append(i)
    if len(bannable) > 0:
        enact = random.choice(bannable)
        print("Enacting " + str(enact))
        enacted[enact] = True
        save()
        return True
    else:
        save(text)
        return False


def check(text):
    violated = list()
    for i, r in enumerate(REGEXES):
        if enacted[i] and not r.match(text):
            violated.append(i+1)
    return violated


def points(text):
    return 3.77964 * pow(count(), 1.5) / float(len(text))


def count():
    return sum(1 if x else 0 for x in enacted)


def search(num):
    pass
