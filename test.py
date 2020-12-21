import discord

from common import FORUM
from secret import TOKEN

client = discord.Client()


@client.event
async def on_ready():
    channel = client.get_channel(FORUM)
    await channel.send("Test.")


if __name__ == "__main__":
    client.run(TOKEN)
