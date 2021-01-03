import json
import time
from math import sqrt, dist
from scipy.spatial import ConvexHull, QhullError
from matplotlib import Path

TIME_FACTOR = 600  # Seconds to fly one unit
FUEL_FACTOR = 1  # Fuel to fly one unit
TANK_SIZE = 10  # Maximum fueling level

planes = list()
fuels = dict()
visited = [set() for _ in range(5)]
hulls = [None for _ in range(5)]


def record(id_num, timestamp, fuel):
    print(id_num, timestamp, fuel)


def save():
    with open("data/planes.json", 'w+') as file:
        json.dump(dict(planes=[plane.save() for plane in planes], fuels=list(fuels.items())), file)


def load():
    global planes, fuels, visited, hulls
    with open("data/planes.json", 'r') as file:
        data = json.load(file)
        planes = [Airplane(**plane) for plane in data["planes"]]
        fuels = {tuple(x[0]): x[1] for x in data["fuels"]}
        visited = {tuple(x[0]): x[1] for x in data["visited"]}
        hulls = [ConvexHull(list(filter(lambda x: visited[x][i], visited.keys())), incremental=True) for i in range(5)]


def dist_to_land(dest):
    return dist(dest, (0, 0)) * 0.1


def course_consumptions(source, dest, landing=False):
    distance = dist(source, dest)
    total_time = distance * TIME_FACTOR
    landing_time = total_time + (dist_to_land(dest) * TIME_FACTOR if landing else 0)
    fuel_use = distance * FUEL_FACTOR
    return distance, total_time, landing_time, fuel_use


def visit(point, team):
    if point not in visited[team]:
        visited[team].add(point)
        if hulls[team] is None:
            if len(visited[team]) >= 3:
                try:
                    hulls[team] = ConvexHull(list(visited[team]), incremental=True)
                except QhullError:
                    hulls[team] = None
        else:
            hulls[team].add_point(point)


def within_visited(point):
    if hulls[4] is None:
        return False
    else:
        hull_path = Path(hulls[4].points[hulls[4].vertices])
        hull_path.contains_point((1, 2))
        return


class Airplane:
    def __init__(self, owner, team, source, dest, launch_time, launch_fuel, landing):
        self.owner = owner
        self.team = team
        self.source = tuple(source)
        self.dest = tuple(dest)
        self.launch_time = launch_time
        self.fuel = launch_fuel
        self.landing = landing

    def save(self):
        return dict(
            owner=self.owner,
            team=self.team,
            source=self.source,
            dest=self.dest,
            launch_time=self.launch_time,
            launch_fuel=self.fuel,
            landing=self.landing
        )

    def current(self, now=None):  # position, fuel, in flight
        if now is None:
            now = time.time()
        if self.launch_time == -1:
            return self.dest, self.fuel, False
        else:
            distance, total_time, landing_time, fuel_use = course_consumptions(self.source, self.dest, self.landing)
            if now > landing_time + self.launch_time:
                # We've landed.
                arrival = self.launch_time + landing_time
                self.fuel -= fuel_use
                record(self.owner, arrival, self.fuel)
                self.launch_time = -1
                visit(self.dest, self.team)

                return self.dest, self.fuel, False
            else:
                ratio = min((now - self.launch_time) / total_time, 1)
                return (self.source[0] * (1 - ratio) + self.dest[0] * ratio,
                        self.source[1] * (1 - ratio) + self.dest[1] * ratio), \
                       self.fuel - fuel_use * ratio, True

    def command_dump(self, amount):
        position, fuel, in_flight = self.current()
        if not in_flight:
            return False, "Not landed."
        new_fuel = fuel + amount
        if new_fuel < 0:
            return False, f"You have only {fuel:.1f} units of fuel"
        self.fuel = new_fuel
        if position not in fuels:
            fuels[position] = [0, 0, 0, 0, 0]
        fuels[position][self.team] += amount

    def command_load(self, amount):
        position, fuel, in_flight = self.current()
        if not in_flight:
            return False, "Not landed."
        if position not in fuels:
            return False, "No fuel at this location"
        fuel_available = fuels[position][self.team] + fuels[position][4]
        if amount > fuel_available:
            return False, f"This location has only {fuel_available:.1f} units of fuel"
        if fuel + amount > TANK_SIZE:
            return False, f"You have only {TANK_SIZE - self.fuel:.1f} units of space"
        self.fuel += amount
        fuels[position][4] -= max(0, amount - fuels[position][self.team])
        fuels[position][self.team] = max(0, fuels[position][self.team] - amount)
        return True, f"Loaded {amount:.1f} units of fuel ({self.fuel:.f} total)"

    def course_stats(self, dest):
        position, fuel, in_flight = self.current()
        distance, travel_time, time_usage, fuel_usage = course_consumptions(position, dest)
        possible = fuel_usage <= fuel
        return distance, travel_time, time_usage, fuel_usage, possible

    # def set_course(self):


def main():
    # planes.append(Airplane(0, (0, 0), (0, 1), time.time(), 10, False))
    # save()
    # load()
    # print(planes[0].current())


if __name__ == "__main__":
    main()
