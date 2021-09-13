import json
import os
import time


class Timer:
    def __init__(self, save_file, start_time=1599318686):
        self.save_file = save_file
        self.times = dict()
        self.start_time = start_time
        if os.path.isfile(save_file):
            self.load()
        else:
            self.save()

    def save(self):
        with open(self.save_file, 'w+') as file:
            file.write(json.dumps(dict(times=self.times), indent=4))

    def load(self):
        with open(self.save_file, 'r') as file:
            state = json.load(file)
        self.times = state["times"]

    def create_if_not(self, user_id):
        if user_id not in self.times:
            self.times[user_id] = self.start_time

    def last_action(self, user_id):
        user_id = str(user_id)
        self.create_if_not(user_id)
        return time.time() - self.times[user_id]

    def reset_last(self, user_id):
        user_id = str(user_id)
        self.times[user_id] = time.time()
        self.save()

    def deduct_last(self, user_id, amount):
        user_id = str(user_id)
        self.create_if_not(user_id)
        self.times[user_id] = self.times[user_id] - amount
        self.save()

    def reset_all(self):
        self.times = dict()


class BankedTimer(Timer):
    def __init__(self, save_file, cost_function, start_time):
        super().__init__(save_file, start_time)
        self.start_time = start_time
        self.cost_function = cost_function

    def actions_available(self, user_id):
        since_last = self.last_action(user_id)
        i, t = 0, 0
        while t < since_last:
            t += self.cost_function(i)
        return i, t - since_last

    def deduct_last(self, user_id, amount):
        _, t = self.actions_available(user_id)
        super().deduct_last(user_id, amount)
        return amount > t

    def spend_action(self, user_id):
        i, _ = self.actions_available(user_id)
        self.times[user_id] += self.cost_function(i)
        self.save()
