import re
import time

import discord

from secret import TOKEN

client = discord.Client()
last_hail = 0

RE_HAIL = re.compile(r"(\W|^)hail(\W|$)", re.IGNORECASE)


@client.event
async def on_message(message):
    global last_hail
    if message.author.bot:
        return
    if RE_HAIL.search(message.content) and time.time() - last_hail > 5:
        last_hail = time.time()
        await message.channel.send(file=discord.File("hail.jpg"))


if __name__ == "__main__":
    # print(scheduled_level())
    client.run(TOKEN)
