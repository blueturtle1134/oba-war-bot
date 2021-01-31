import re
import string

EAST = (1, 0)
SOUTH = (0, 1)
WEST = (-1, 0)
NORTH = (0, -1)
DIRECTIONS = [EAST, SOUTH, WEST, NORTH]


def move(point, direction, height, width):
    if isinstance(direction, int):
        direction = DIRECTIONS[direction]
    x, y = point[0] + direction[0], point[1] + direction[1]
    return x % width, y % height


def neighbors(point, grid):
    height, width = len(grid), len(grid[0])
    for i, direction in enumerate(DIRECTIONS):
        x, y = (point[0] + direction[0]) % width, (point[1] + direction[1]) % height
        yield (x, y), grid[y][x]


def stringify_grid(grid, display_mapping=None, recticle_x=-1, recticle_y=-1):
    if display_mapping is None:
        def display_mapping(x):
            return str(x)
    height, width = len(grid), len(grid[0])
    return "   " + " ".join([x for x in string.ascii_uppercase[0:width]]) + "\n" \
           + "\n".join(
        [str(y + 1).rjust(2) + " " + " ".join([
            ("╬" if x == recticle_x else "═") if y == recticle_y
            else ("║" if x == recticle_x else display_mapping(a))
            for x, a in enumerate(row)]) for y, row in enumerate(grid)])


def parse_coords(coords):
    return ord(coords[0].lower()) - 97, int(coords[1:]) - 1


COORDINATE_REGEX = re.compile(r"\w\d+")
