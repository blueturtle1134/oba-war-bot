import discord

import robot
from common import LOG
from secret import TOKEN

client = discord.Client()


@client.event
async def on_ready():
    channel = client.get_channel(LOG)
    await robot.load().send_state(channel)


if __name__ == "__main__":
    client.run(TOKEN)
