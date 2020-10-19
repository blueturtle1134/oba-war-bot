import discord

from common import ANNOUNCEMENTS, TOKEN

client = discord.Client()


@client.event
async def on_ready():
    channel = client.get_channel(ANNOUNCEMENTS)
    await channel.send("Reserved.")


if __name__ == "__main__":
    client.run(TOKEN)
