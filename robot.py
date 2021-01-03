import json
import os
import pickle
import random
import time
from io import BytesIO
from random import Random

# 0 = space
# 1 = wall
# 2, 3, 4, 5 = balls
# 6, 7, 8, 9 = goals
import discord
from PIL import Image, ImageDraw, ImageFont

from common import TEAM_NAMES, TEAM_COLORS

SOLID = [False, True, True, True, True, True, False, False, False, False]
MOBILE = [False, False, True, True, True, True, False, False, False, False]

DIRECTIONS = [(0, 1), (1, 0), (0, -1), (-1, 0)]
SQUARE_SIZE = 50
COMMAND_NAME = ["SOUTH", "EAST", "NORTH", "WEST", "MAGNET"]
COMMAND_ALIAS = {
    "south": 0,
    "east": 1,
    "north": 2,
    "west": 3,
    "magnet": 4,
    "down": 0,
    "right": 1,
    "up": 2,
    "left": 3
}


class State:
    def __init__(self, board, robot_pos, magnet=False, stack=None, points=None):
        if points is None:
            points = [0, 0, 0, 0, 0]
        if stack is None:
            stack = list()
        self.board = board
        self.robot_pos = robot_pos
        self.magnet = magnet
        self.rng = Random()
        self.stack = stack
        self.points = points

    def valid_coordinates(self, x, y):
        return 0 <= x < len(self.board[0]) and 0 <= y < len(self.board)

    def make_move(self, direction):
        x, y = self.robot_pos
        dx, dy = DIRECTIONS[direction]
        x1, y1 = x + dx, y + dy
        adjacent = ((x, y), (x - dx, y - dy), (x + dy, y + dx), (x - dy, y - dx))
        if self.valid_coordinates(x1, y1):
            self.try_pull((x1, y1), direction)
            destination = self.board[y1][x1]
            if not SOLID[destination]:
                self.robot_pos = x1, y1
                if self.magnet:
                    for p in adjacent:
                        self.try_pull(p, direction)

    def flip_magnet(self):
        self.magnet = not self.magnet

    def try_pull(self, pos, direction):
        x, y = pos
        dx, dy = DIRECTIONS[direction]
        x1, y1 = x + dx, y + dy
        if self.valid_coordinates(x, y) and self.valid_coordinates(x1, y1) and MOBILE[self.board[y][x]]:
            here = self.board[y][x]
            destination = self.board[y1][x1]
            if destination == 0:
                self.board[y1][x1] = self.board[y][x]
                self.board[y][x] = destination
            if 6 <= destination <= 9 and 2 <= here <= 5:
                t1, t2 = here - 2, destination - 6
                self.points[t1] += 1
                if t1 != t2:
                    self.points[t2] += 1
                self.board[y][x] = 0
                self.board[y1][x1] = 0
                x2, y2 = self.pick_random()
                self.board[y2][x2] = here
                x2, y2 = self.pick_random()
                self.board[y2][x2] = destination

    def pick_random(self):
        width, height = len(self.board[0]), len(self.board)
        valid = False
        x, y = None, None
        while not valid:
            x, y = int(width * self.rng.random()), int(height * self.rng.random())
            if self.board[y][x] == 0 and (x, y) != self.robot_pos:
                to_check = ((x + x1, y + y1) for x1, y1 in DIRECTIONS)
                valid = all((not self.valid_coordinates(x1, y1))
                            or ((not 2 <= self.board[y1][x1] <= 9) and (x1, y1) != self.robot_pos) for x1, y1 in
                            to_check)
        return x, y

    def draw(self):
        image = Image.new("RGB", (SQUARE_SIZE * len(self.board[0]) + 150, SQUARE_SIZE * len(self.board) + 1),
                          (255, 255, 255))
        d = ImageDraw.Draw(image)
        for j, row in enumerate(self.board):
            for i, tile in enumerate(row):
                x, y, x1, y1 = i * SQUARE_SIZE, j * SQUARE_SIZE, (i + 1) * SQUARE_SIZE, (j + 1) * SQUARE_SIZE
                p = (x, y), (x1, y1)
                d.rectangle(p, outline=(0, 0, 0))
                if tile == 1:
                    d.rectangle(p, fill=(50, 50, 50))
                if 2 <= tile <= 5:
                    d.ellipse(((x + 5, y + 5), (x1 - 5, y1 - 5)), fill=TEAM_COLORS[tile - 2])
                if 6 <= tile <= 9:
                    d.rectangle(p, fill=TEAM_COLORS[tile - 6], outline=(0, 0, 0))
                    d.ellipse(((x + 5, y + 5), (x1 - 5, y1 - 5)), fill=(255, 255, 255))
        x, y = self.robot_pos
        x, y = (x + 0.5) * SQUARE_SIZE, (y + 0.5) * SQUARE_SIZE
        d.polygon(
            [x, y - 0.4 * SQUARE_SIZE, x - 0.4 * SQUARE_SIZE, y, x, y + 0.4 * SQUARE_SIZE, x + 0.4 * SQUARE_SIZE, y],
            fill=(150, 150, 150))
        d.text((SQUARE_SIZE * len(self.board[0]) + 10, 10),
               "\n".join(f"{TEAM_NAMES[i]}: {self.points[i]}" for i in range(5))
               + "\n\nMAGNET: " + ("ON" if self.magnet else "OFF")
               + f"\nNEXT TICK: {(3600 - time.time() % 3600) / 60:.0f} min"
               + "\nSTACK:\n"
               + "\n".join(f"{i + 1}. {COMMAND_NAME[x]}" for i, x in enumerate(reversed(self.stack)))
               , fill=(0, 0, 0))
        return image

    def execute_stack(self):
        if len(self.stack) > 0:
            command = self.stack.pop()
            if 0 <= command <= 3:
                self.make_move(command)
            elif command == 4:
                self.flip_magnet()
            return COMMAND_NAME[command]
        return None

    def add_command(self, text):
        text = text.strip().lower()
        if text in COMMAND_ALIAS:
            self.stack.append(COMMAND_ALIAS[text])
            return True
        return False

    def load_board(self, file):
        header = file.readline().split(" ")
        width, height = tuple(int(x) for x in header[0].split("x"))
        self.board = [[int(y) for y in file.readline().split(" ")] for _ in range(height)]
        self.robot_pos = tuple(int(x) for x in header[1].split(","))
        num_goals = int(header[2])
        placement_order = [0, 1, 2, 3]
        random.shuffle(placement_order)
        for _ in range(num_goals):
            for team in placement_order:
                x, y = self.pick_random()
                self.board[y][x] = team + 2
            for team in reversed(placement_order):
                x, y = self.pick_random()
                self.board[y][x] = team + 6
        self.magnet = False
        self.stack = list()

    async def send_state(self, channel, caption=None):
        with BytesIO() as image_binary:
            self.draw().save(image_binary, 'PNG')
            image_binary.seek(0)
            await channel.send(content=caption, file=discord.File(fp=image_binary, filename='robot.png'))


def dump(state):
    if not os.path.isdir("data"):
        os.mkdir("data")
    with open("data/robot.json", 'w+') as file:
        json.dump(dict(
            board=state.board,
            pos=state.robot_pos,
            magnet=state.magnet,
            stack=state.stack,
            points=state.points
        ), file)
    with open("data/rng.pkl", 'wb+') as file:
        pickle.dump(state.rng.getstate(), file)


def load():
    with open("data/robot.json", 'r') as file:
        data = json.load(file)
        result = State(data['board'], tuple(data['pos']), data['magnet'], data['stack'], data['points'])
    with open("data/rng.pkl", 'rb') as file:
        result.rng.setstate(pickle.load(file))
    return result


def main():
    state = State([[]], (0, 0))
    with open("levels/robot/1.txt", 'r') as file:
        state.load_board(file)
    state.draw().show()
    dump(state)


if __name__ == '__main__':
    main()  # Use this to reset state to 1
