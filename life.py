import asyncio
import copy
import datetime
import json
import os
import random
import time

import discord

import grids
from common import TEAM_NAMES, team_from_member, get_notification, TEAM_ROLES, team_from_string, get_team_name, \
    ANSWER, TOWER, CATEGORY_ID, LOG
from grids import stringify_grid, COORDINATE_REGEX
from secret import TOKEN, SEED

DATA_PATH = "data/life.json"

DISPLAY = {
    (0, 0, 0): "·",
    (1, 0, 0): "C",
    (0, 1, 0): "I",
    (0, 0, 1): "E",
    (1, 1, 0): "$",
    (0, 1, 1): "&",
    (1, 0, 1): "#",
    (1, 1, 1): "X"
}

DIRECTIONS = [
    (1, 1),
    (1, -1),
    (-1, 1),
    (-1, -1),
    (1, 0),
    (-1, 0),
    (0, 1),
    (0, -1),
]

TICK_PERIOD = 120
ACTION_PERIOD = 200
TOWER_GAIN = 10

current_grid = [[(0, 0, 0) for i in range(18)] for _ in range(18)]
last_action = dict()
last_update = None
tick_count = 0
last_tick = time.time()

random.seed(SEED)
next_measurement = 0
measurement_num = 0

client = discord.Client()


def save():
    with open(DATA_PATH, 'w') as file:
        json.dump(dict(
            current_grid=current_grid,
            last_action=last_action,
            tick_count=tick_count
        ), file)


def load():
    with open(DATA_PATH, 'r') as file:
        data = json.load(file)
    global current_grid, last_action, last_update, tick_count, next_measurement, measurement_num
    current_grid = [[tuple(x) for x in row] for row in data["current_grid"]]
    last_action = data["last_action"]
    tick_count = data["tick_count"]
    measurement_num = 0
    while next_measurement < tick_count:
        next_measurement += generate_measurement_interval(measurement_num)
        measurement_num += 1
    print(next_measurement)


def show_key(cell_display=None):
    if cell_display is None:
        cell_display = DISPLAY
    return "\n".join([
        (", ".join([TEAM_NAMES[i] for i, x in enumerate(state) if x == 1]) if state != (0, 0, 0) and state != (1, 1, 1)
         else "Dead" if state == (0, 0, 0) else "Unaligned") + ": " + DISPLAY[state]
        for state in cell_display
    ])


def compute_cell(current, neighbors):
    live = [cell for cell in neighbors if cell != (0, 0, 0)]
    if current != (0, 0, 0):
        if len(live) < 2 or len(live) > 3:
            return 0, 0, 0
        else:
            return current
    else:
        if len(live) != 3:
            return 0, 0, 0
        else:
            counts = [sum(x) for x in zip(*neighbors)]
            highest = max(counts)
            if highest == 3:
                return tuple([1 if x == highest else 0 for x in counts])
            else:
                return tuple([1 if x > 0 else 0 for x in counts])


def compute_tick(grid):
    height, width = len(grid), len(grid[0])
    return [
        [compute_cell(cell, [grid[(y + a) % height][(x + b) % width] for a, b in DIRECTIONS])
         for x, cell in enumerate(row)] for y, row in enumerate(grid)]


def score_grid(grid):
    return tuple([sum(x) for x in zip(*[cell for row in grid for cell in row])]), \
           len([cell for row in grid for cell in row if cell != (0, 0, 0)])


def validate_position(position, team):
    x, y = position
    if team is None:
        return True
    if team == 0:
        return x < 9
    elif team == 1:
        return 5 < x < 15
    elif team == 2:
        return not 2 < x < 12
    return True


def flip_cell(text, member):
    team = team_from_member(member)
    cell_state = [1, 1, 1]
    x, y = cell = grids.parse_coords(text.split(" ", 1)[0])
    if x < 0 or x > 17 or y < 0 or y > 17:
        return "Location is out of bounds!"
    if not validate_position(cell, team):
        return "Your team does not have control over that cell!"
    member_id = str(member.id)
    actions_available, time_to_next = get_actions_available(member_id)
    if actions_available < 1:
        return f"You may act again in {time_to_next} ticks"
    if team is not None and 0 <= team <= 2:
        cell_state = [1 if team == i else 0 for i in range(3)]
    terms = text.split(" ")
    for term in terms[1:]:
        team_parsed = team_from_string(term)
        if team_parsed is not None:
            cell_state[team_parsed] = 1
    cell_state = cell_state[0], cell_state[1], cell_state[2]
    if current_grid[y][x] == (0, 0, 0):
        current_grid[y][x] = cell_state
        last_action[member_id] = int((last_action[member_id] + tick_count) / 2)
        return "Cell placed!"
    else:
        return "There is already a cell there."


def display_current():
    scores, count = score_grid(current_grid)
    return "\n```\n".join((f"Tick {tick_count} (last update {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
                           stringify_grid(current_grid, DISPLAY),
                           display_scores(scores, count)))


def display_scores(scores, count):
    return "\n".join([f"{TEAM_NAMES[i]}: {scores[i]}" for i in range(3)]) + f"\nLive cells: {count}"


def get_actions_available(member_id):
    if member_id not in last_action:
        last_action[member_id] = -ACTION_PERIOD
    i, t = 0, tick_count - last_action[member_id]
    while ACTION_PERIOD * 2 ** i < t:
        i += 1
    return i, ACTION_PERIOD * 2 ** i - t


def get_time_stats(member):
    member_id = str(member.id)
    tick_string = f"\nIt is currently tick {tick_count}" \
                  f"\nNext tick in approximately {TICK_PERIOD + last_tick - time.time():.1f} seconds."
    actions_available, time_to_next = get_actions_available(member_id)
    return f"You have {actions_available} actions available, next in {time_to_next}" + tick_string


def get_measurement():
    scores, count = score_grid(current_grid)
    max_score = max(scores)
    if max_score == 0:
        return "**Measurement!**\nWinner(s): **Grand Thonk**\n" + get_notification(TEAM_ROLES)
    winners = ", ".join([TEAM_NAMES[i] for i in range(3) if scores[i] == max_score or scores[i] >= count / 2])
    return f"**Measurement!**\n" \
           f"Winner(s): **{winners}**\n" \
           f"{get_notification(TEAM_ROLES)}"


def log_stats():
    scores = score_grid(current_grid)
    with open("logs/life_log.txt", "a") as file:
        file.write("\n")
        file.write(" ".join([str(tick_count)] + [str(x) for x in scores]))
    with open("logs/life_record.txt", "a") as file:
        file.write("\n")
        file.write(str(tick_count) + " ")
        file.write("".join([DISPLAY[x] for row in current_grid for x in row]))


async def on_tick():
    global current_grid, tick_count, last_tick
    last_tick = time.time()
    tick_count += 1
    current_grid = compute_tick(current_grid)
    save()
    log_stats()
    channel = client.get_channel(ANSWER)
    await update_status(channel)
    # if should_measure():
    #    await channel.send(get_measurement())


async def update_status(channel):
    channel_last = channel.last_message_id
    global last_update
    if last_update is not None and channel_last == last_update:
        message = await channel.fetch_message(channel_last)
        await message.edit(content=display_current())
    else:
        sent_message = await channel.send(display_current())
        last_update = sent_message.id


def should_measure():
    global next_measurement, measurement_num
    if measurement_num >= 20:
        return False
    if next_measurement <= tick_count:
        next_measurement += generate_measurement_interval(measurement_num)
        measurement_num += 1
        return True
    else:
        return False


def generate_measurement_interval(i):
    return random.randint(500 - i * 15, 900 - i * 25)


def forecast(n=1, move_text=None, team=None):
    if n > 200:
        return "Not letting you forecast that much."
    next_grid = copy.deepcopy(current_grid)
    move = None
    if move_text is not None and grids.COORDINATE_REGEX.match(move_text):
        move = grids.parse_coords(move_text)
        if team is not None:
            cell_state = tuple([1 if team == i else 0 for i in range(3)])
        else:
            cell_state = (1, 1, 1)
        next_grid[move[1]][move[0]] = cell_state
    for _ in range(n):
        next_grid = compute_tick(next_grid)
    header = f"Tick {tick_count + n} if {get_team_name(team)} places {move_text.upper()} on {tick_count}:" if move \
        else f"Forecast for tick {tick_count + n}:"
    return f"{header}\n" \
           f"```\n{stringify_grid(next_grid, DISPLAY)}\n```\n" \
           f"{display_scores(*score_grid(next_grid))}"


def display_targeting(string):
    return f"Previewing {string.upper()}\n" \
           f"```{grids.stringify_grid(current_grid, DISPLAY, *grids.parse_coords(string))}```"


def load_from_string(string):
    reverse_display = {y: x for x, y in DISPLAY.items()}
    for i in range(18):
        for j in range(18):
            current_grid[i][j] = reverse_display[string[i * 18 + j]]


async def repeat_task():
    while True:
        await on_tick()
        await asyncio.sleep(TICK_PERIOD)


@client.event
async def on_ready():
    channel = client.get_channel(LOG)
    client.loop.create_task(repeat_task())
    await channel.send("Bot ready")


@client.event
async def on_message(message):
    message_content = message.content.strip().lower()
    if message.author.bot:
        return
    if message.channel.id == ANSWER:
        channel = client.get_channel(ANSWER)
        if COORDINATE_REGEX.match(message_content.split(" ", 1)[0]):
            await channel.send(flip_cell(message_content, message.author))
        await update_status(channel)
    elif message.channel.id == TOWER:
        author_id = str(message.author.id)
        actions_available, time_to_next = get_actions_available(author_id)
        if author_id not in last_action:
            last_action[author_id] = -ACTION_PERIOD
        last_action[author_id] -= TOWER_GAIN
        if time_to_next <= TOWER_GAIN:
            await message.add_reaction("⏲️")
    elif message.channel.category_id == CATEGORY_ID:
        if message_content.startswith("time"):
            await message.channel.send(get_time_stats(message.author))
        if message_content.startswith("target") or message_content.startswith("preview"):
            parts = message_content.split(" ")
            if len(parts) > 1 and COORDINATE_REGEX.match(parts[1]):
                await message.channel.send(display_targeting(parts[1]))
        elif message_content.startswith("forecast") or message_content.startswith("predict"):
            parts = message_content.split(" ")
            if len(parts) > 1 and parts[1].isdigit():
                if len(parts) > 2 and grids.COORDINATE_REGEX.match(parts[2]):
                    if len(parts) > 3:
                        await message.channel.send(forecast(int(parts[1]), parts[2], team_from_string(parts[3])))
                    else:
                        await message.channel.send(forecast(int(parts[1]), parts[2],
                                                            team_from_member(message.author)))
                else:
                    await message.channel.send(forecast(int(parts[1])))
            else:
                await message.channel.send(forecast())


def main():
    if os.path.exists(DATA_PATH):
        load()
    client.run(TOKEN)


if __name__ == "__main__":
    main()
