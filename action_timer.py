import json
import os
import time


class Timer:
    def __init__(self, save_file):
        self.save_file = save_file
        self.times = dict()
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

    def last_action(self, user_id):
        user_id = str(user_id)
        if user_id in self.times:
            return time.time() - self.times[user_id]
        else:
            return time.time() - 1599318686

    def reset_last(self, user_id):
        user_id = str(user_id)
        self.times[user_id] = time.time()
        self.save()

    def deduct_last(self, user_id, amount):
        user_id = str(user_id)
        if user_id in self.times:
            self.times[user_id] = self.times[user_id] - amount
            self.save()


