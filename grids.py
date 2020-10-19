import re
import string


def stringify_grid(grid, display_mapping, recticle_x=-1, recticle_y=-1):
    height, width = len(grid), len(grid[0])
    return "   " + " ".join([x for x in string.ascii_uppercase[0:width]]) + "\n" \
           + "\n".join(
        [str(y + 1).rjust(2) + " " + " ".join([
            ("╬" if x == recticle_x else "═") if y == recticle_y
            else ("║" if x == recticle_x else display_mapping[a])
            for x, a in enumerate(row)]) for y, row in enumerate(grid)])


def parse_coords(coords):
    return ord(coords[0].lower()) - 97, int(coords[1:]) - 1


COORDINATE_REGEX = re.compile(r"\w\d+")
