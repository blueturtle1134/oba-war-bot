import discord

from previous_events import robot
from common import *
from secret import TOKEN

client = discord.Client()


@client.event
async def on_ready():
    channel = client.get_channel(ANSWER)
    state = robot.load()
    await channel.send("Running a tick to make up for bug")
    state.execute_stack()
    robot.dump(state)
    await state.send_state(channel)


if __name__ == "__main__":
    client.run(TOKEN)
