import random

from common import TEAM_NAMES, TEAM_LETTER
from grids import neighbors, stringify_grid, move, NORTH, coords_to_str
import jsons

KNIGHT_STEPS = dict(
    nnw=(-1, -2),
    nww=(-2, -1),
    ssw=(-1, 2),
    sww=(-2, 1),
    nne=(1, -2),
    nee=(2, -1),
    sse=(1, 2),
    see=(2, 1),
)

Position = tuple[int, int]


class Dragon:

    def __init__(self, game, pos: Position, direction, length, history: list[Position], team):
        self.pos = pos
        self.direction = direction
        self.length = length
        self.history = history
        self.team = team
        self.__game = game

    def move(self):
        self.history.append(self.pos)
        self.pos = move(self.pos, self.direction, height=len(self.__game.ownership),
                        width=len(self.__game.ownership[0]))
        knight = self.__game.has_knight(self.pos)
        if (knight != -1 and knight != self.team) or self.__game.has_dragon_body(self.pos) != -1:
            self.kill()
        else:
            self.__game.attack(self.pos, self.team)

    def update_tail(self):
        while len(self.history) > self.length:
            self.history.pop(0)

    def kill(self):
        self.pos = self.__game.hubs[self.team]
        self.direction = NORTH
        self.length = 5
        self.history = list()
        self.__game.scores[self.team][3] += 1

    def set_game(self, game):
        self.__game = game


class Knight:

    def __init__(self, game, pos: Position, team, owner):
        self.__game: Game = game
        self.pos = pos
        self.team = team
        self.owner = owner

    def set_game(self, game):
        self.__game = game

    def kill(self):
        self.pos = self.__game.hubs[self.team]
        self.__game.scores[self.team][2] += 1


class Game:

    def __init__(self, ownership=None, dragons: list[Dragon] = None, hubs: list[Position] = None,
                 knights: list[Knight] = None, scores=None):
        if ownership is None:
            ownership = [[-1] * 24 for _ in range(24)]
        if hubs is None:
            x, y = int(24 * random.random()), int(24 * random.random())
            dy = 8 if random.random() > 0.5 else -8
            hubs = [(x, y), ((x + 8) % 24, (y + dy) % 24), ((x + 16) % 24, (y + 2 * dy) % 24)]
            random.shuffle(hubs)
            for i, hub in enumerate(hubs):
                x, y = hub
                ownership[y][x] = i
        if dragons is None:
            dragons = [Dragon(self, hubs[i], NORTH, 5, list(), i) for i in range(3)]
        if knights is None:
            knights = dict()
        if scores is None:
            scores = [[0] * 5 for _ in range(3)]  # Scores: Tiles, knight deaths, dragon deaths, tower captures
        for dragon in dragons:
            dragon.set_game(self)
        for knight in knights:
            knight.set_game(self)
        self.ownership = ownership
        self.dragons = dragons
        self.hubs = hubs
        self.knights = knights
        self.scores = scores

    def get_ownership(self, pos):
        return self.ownership[pos[1]][pos[0]]

    def expand(self, team):
        possibles = dict()
        for i, row in enumerate(self.ownership):
            for j, x in enumerate(row):
                if x == team:
                    for point, y in neighbors((j, i), self.ownership):
                        if y == -1:
                            if point not in possibles:
                                possibles[point] = 1
                            else:
                                possibles[point] += 1
        possibles_list = list(possibles.keys())
        if len(possibles_list) == 0:
            return False
        target = random.choices(possibles_list, weights=[possibles[x] for x in possibles_list])[0]
        self.ownership[target[1]][target[0]] = team

    def has_dragon_head(self, pos):
        for i, dragon in enumerate(self.dragons):
            if dragon.pos == pos:
                return i
        return -1

    def has_dragon_body(self, pos):
        for i, dragon in enumerate(self.dragons):
            if pos in dragon.history:
                return i
        return -1

    def has_knight(self, pos):
        for i, knights in enumerate(self.knights.values()):
            if knights.pos == pos:
                return i
        return -1

    def attack(self, pos, team):
        if self.ownership[pos[1]][pos[0]] != team:
            self.ownership[pos[1]][pos[0]] = -1

    def draw(self, territory=True, dragons=True, knights=True, powerups=True):
        display = [[("·" if a == -1 else (
            "+" if all(b[1] == a for b in neighbors((x, y), self.ownership)) else TEAM_NAMES[a][0].lower())) for x, a in
                    enumerate(row)] for y, row in enumerate(self.ownership)] if territory else \
            [["·" for _ in range(len(self.ownership[0]))] for _ in range(len(self.ownership))]
        for i, hub in enumerate(self.hubs):
            x, y = hub
            display[y][x] = TEAM_LETTER[i].upper()
        if dragons:
            for dragon in self.dragons:
                x, y = dragon.pos
                display[y][x] = TEAM_LETTER[dragon.team].upper()
                for x, y in dragon.history:
                    display[y][x] = "o"
        if knights:
            for knight in self.knights.values():
                x, y = knight.pos
                display[y][x] = TEAM_LETTER[knight.team].upper()
        return stringify_grid(display)

    def tick(self):
        for i in random.sample([0, 1, 2], 3):
            self.expand(i)
        for dragon in self.dragons:
            dragon.move()
        for dragon in self.dragons:
            dragon.update_tail()

    def command_dragon(self, team, direction):
        self.dragons[team].direction = direction

    def command_knight(self, user, team, movement):
        if user not in self.knights:
            self.knights[user] = Knight(game=self, pos=self.hubs[team], team=team, owner=user)
        self.knights[user].team = team
        if movement.lower() in KNIGHT_STEPS:
            dx, dy = KNIGHT_STEPS[movement.lower()]
            x, y = self.knights[user].pos
            dest = (x + dx) % 24, (y + dy) % 24
            knight_landed = self.has_knight(dest)
            if self.has_dragon_body(dest) != -1:
                return False, "You cannot jump on a dragon!"
            if knight_landed != -1 and knight_landed != team:
                # Conflict!
                for knight in self.knights.values():
                    if knight.pos == dest and knight.team != self.get_ownership(dest):
                        knight.kill()
                if self.knights[user].team != self.get_ownership(dest):
                    self.knights[user].kill()
                    return True, "You die!"
            self.knights[user].pos = dest
            dragon_hit = self.has_dragon_head(self.knights[user].pos)
            if dragon_hit != -1 and dragon_hit != self.knights[user].team:
                self.dragons[dragon_hit].length -= 1
                if self.dragons[dragon_hit].length < 2:
                    self.dragons[dragon_hit].kill()
                    return True, "You have slain the dragon!"
                else:
                    return True, "You hit the dragon!"
            return True, f"You have moved to {coords_to_str(dest)}."
        else:
            return False, "That movement is invalid!"


def main():
    game = Game()
    for _ in range(100):
        game.tick()
    print(game.draw())
    saved = jsons.dump(game, strip_privates=True)
    print(saved)
    game = jsons.load(saved, Game)
    for _ in range(100):
        game.tick()
    print(game.draw())


if __name__ == '__main__':
    main()
