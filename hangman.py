import os
import random

import dictionary
import common
from action_timer import Timer

ACTION_TIME = 2 * 60 * 60
FAIL_MAX = 6

SAVE_PATH = "data/hangman.txt"
IMAGE_PATH = "resources/hangmen/"

game_num = 0
word = None
guessed_letters = set()
fails = [0] * 4
points = [0] * 5
timer = Timer("data/hangman_timer.json")


def save():
    with open(SAVE_PATH, 'w+') as savefile:
        savefile.write(str(game_num) + "\n")
        savefile.write(word + "\n")
        savefile.write("".join(guessed_letters) + "\n")
        savefile.write(",".join(map(str, fails)) + "\n")
        savefile.write(",".join(map(str, points)) + "\n")


def choose_word():
    global game_num, word, guessed_letters, fails
    game_num += 1
    length = int(game_num / 3) + 4
    while length not in dictionary.by_length:
        length -= 1
    word = random.choice(dictionary.by_length[length]).upper()
    guessed_letters = set()
    fails = [0] * 4
    save()


def display_word():
    shown_word = "".join([x if x in guessed_letters else "_" for x in word])
    unused_letters = ", ".join(list(guessed_letters - set(word)))
    return f"```\n{shown_word}\nIncorrect guesses: {unused_letters}\n```"


def get_hang_image(team):
    return f"resources/hangmen/{fails[team]}.png"


def check_grand_thonk():
    if fails[0] == FAIL_MAX and fails[1] == FAIL_MAX and fails[2] == FAIL_MAX:
        choose_word()
        return True
    return False


def guess(x, user, team):
    x = x.strip().upper()
    if timer.last_action(user) < ACTION_TIME:
        return f"You can only guess once every two hours!", False
    if len(x) == 1:
        if fails[team] == 6:
            return f"Your team is out!", False
        if x in guessed_letters:
            return f"{x} has already been guessed.", False
        correct = x in word
        guessed_letters.add(x)
        timer.reset_last(user)
        if not correct:
            fails[team] += 1
            save()
            return f"No {x}.", True
        else:
            if set(word).issubset(guessed_letters):
                choose_word()
                points[team] += 1
                save()
                return f"There is a {x}. **Word complete!** {common.get_team_name(team)} gets a point." \
                       f"\n__Current points__\n{common.print_points(points)}", False
            else:
                save()
                return f"There is a {x}.", False
    elif len(x) == len(word):
        if fails[team] == 6:
            return f"Your team is out!", False
        timer.reset_last(user)
        if x == word:
            choose_word()
            points[team] += 1
            save()
            return f"**{x}** is **correct!** {common.get_team_name(team)} gets a point." \
                   f"\n__Current points__\n{common.print_points(points)}", False
        else:
            save()
            fails[team] += 1
            return f"**{x}** is **incorrect!**", True
    else:
        return f"Incorrect length. Guess either a single letter or a solution of length {len(word)}.", False


def check(user, team):
    time = timer.last_action(user)
    if time > ACTION_TIME:
        result = "You may guess right now!"
    else:
        result = f"You may guess again in **{(ACTION_TIME - time) / 60:.2f}** minutes"
    result += f"\nYour team ({common.TEAM_NAMES[team]}) has guessed wrong **{fails[team]}** time(s)."
    return result


if os.path.isfile("data/hangman.txt"):
    with open("data/hangman.txt", 'r') as file:
        game_num = int(file.readline())
        word = file.readline().strip()
        guessed_letters = set(file.readline().strip())
        fails = [int(x) for x in file.readline().split(",")]
        points = [int(x) for x in file.readline().split(",")]
else:
    choose_word()
    save()

# if __name__ == '__main__':
#     # guess("t", 0)
#     save()
