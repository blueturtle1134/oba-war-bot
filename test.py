import discord

from common import *
from secret import TOKEN

client = discord.Client()


@client.event
async def on_ready():
    channel = client.get_channel(LOBBY)
    current_level, next_time = scheduled_level()
    await channel.send(f"Current level: {current_level}\nHours until next level: {next_time / 3600:.1f}")


if __name__ == "__main__":
    client.run(TOKEN)
