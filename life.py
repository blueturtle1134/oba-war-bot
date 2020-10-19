import copy
import datetime
import json
import random
import time

import grids
from common import TEAM_NAMES, team_from_member, get_notification, TEAM_ROLES, team_from_string, get_team_name
from grids import stringify_grid

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
ACTION_PERIOD = 100

current_grid = [[(0, 0, 0) for i in range(18)] for _ in range(18)]
last_action = dict()
last_update = None
tick_count = 0
last_tick = time.time()

random.seed(15275)
next_measurement = 0


def save():
    with open("life.json", 'w') as file:
        json.dump(dict(
            current_grid=current_grid,
            last_action=last_action,
            tick_count=tick_count
        ), file)


def load():
    with open("life.json", 'r') as file:
        data = json.load(file)
    global current_grid, last_action, last_update, tick_count, next_measurement
    current_grid = [[tuple(x) for x in row] for row in data["current_grid"]]
    last_action = data["last_action"]
    tick_count = data["tick_count"]
    while next_measurement < tick_count:
        next_measurement += generate_measurement_interval()
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
            return tuple([1 if x == highest else 0 for x in counts])


def compute_tick(grid):
    height, width = len(grid), len(grid[0])
    return [
        [compute_cell(cell, [grid[(y + a) % height][(x + b) % width] for a, b in DIRECTIONS])
         for x, cell in enumerate(row)] for y, row in enumerate(grid)]


def score_grid(grid):
    return tuple([sum(x) for x in zip(*[cell for row in grid for cell in row])])


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
    if member_id in last_action and get_action_timer(member_id) > 0:
        return f"You may act again in {get_action_timer(member_id)} ticks"
    if team is not None:
        cell_state = [1 if team == i else 0 for i in range(3)]
    terms = text.split(" ")
    for term in terms[1:]:
        team_parsed = team_from_string(term)
        if team_parsed is not None:
            cell_state[team_parsed] = 1
    cell_state = cell_state[0], cell_state[1], cell_state[2]
    if current_grid[y][x] == (0, 0, 0):
        current_grid[y][x] = cell_state
        last_action[member_id] = tick_count
        return "Cell placed!"
    else:
        return "There is already a cell there."


def display_current():
    scores = score_grid(current_grid)
    return "\n```\n".join((f"Tick {tick_count} (last update {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})",
                           stringify_grid(current_grid, DISPLAY),
                           display_scores(scores)))


def display_scores(scores):
    return "\n".join([f"{TEAM_NAMES[i]}: {scores[i]}" for i in range(3)])


def get_action_timer(member_id):
    return ACTION_PERIOD - tick_count + last_action[member_id]


def get_time_stats(member):
    member_id = str(member.id)
    tick_string = f"\nIt is currently tick {tick_count}" \
                  f"\nNext tick in approximately {TICK_PERIOD + last_tick - time.time():.1f} seconds."
    if member_id in last_action and get_action_timer(member_id) > 0:
        return f"You may act again in {get_action_timer(member_id)} ticks" + tick_string
    else:
        return "You may act right now!" + tick_string


def get_measurement():
    scores = score_grid(current_grid)
    max_score = max(scores)
    if max_score == 0:
        winners = "Grand Thonk"
    else:
        winners = ", ".join([TEAM_NAMES[i] for i in range(3) if scores[i] == max_score])
    return f"**Measurement!**\n" \
           f"{display_scores(scores)}\n" \
           f"Winner(s): **{winners}**\n" \
           f"{get_notification(TEAM_ROLES)}"


def log_stats():
    scores = score_grid(current_grid)
    with open("life_log.txt", "a") as file:
        file.write("\n")
        file.write(" ".join([str(tick_count)] + [str(x) for x in scores]))
    with open("life_record.txt", "a") as file:
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
    global next_measurement
    if next_measurement <= tick_count:
        next_measurement += generate_measurement_interval()
        return True
    else:
        return False


def generate_measurement_interval():
    return random.randint(500, 750)


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
           f"{display_scores(score_grid(next_grid))}"


def display_targeting(string):
    return f"Previewing {string.upper()}\n" \
           f"```{grids.stringify_grid(current_grid, DISPLAY, *grids.parse_coords(string))}```"


def load_from_string(string):
    reverse_display = {y: x for x, y in DISPLAY.items()}
    for i in range(18):
        for j in range(18):
            current_grid[i][j] = reverse_display[string[i * 18 + j]]


def main():
    load()
    print(stringify_grid(current_grid, DISPLAY, 5, 6))


if __name__ == "__main__":
    main()
