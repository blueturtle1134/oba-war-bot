# Everybody Admins Bot v1.1
# By blueturtle1134
# 8/17/2020
# To use: Run it.

import asyncio
import discord
from discord.utils import get

TOKEN = "NzQ1MDg3NjgwNTA4OTg1NDUw.Xzsq-g.A64W8wVnmIhIR_19DdegMv59pJ0"
GUILD_ID = 591322364462104716
ROLE_ID = 591323718660259845

client = discord.Client()


@client.event
async def on_ready():
    print("Bot ready!")
    client.loop.create_task(repeat_task())


async def everybody_is_admin():
    server = client.get_guild(GUILD_ID)
    role = get(server.roles, id=ROLE_ID)
    for member in server.members:
        if role not in member.roles:
            await member.add_roles(role)
            print(f"Made {member} admin.")


async def repeat_task():
    while True:
        await everybody_is_admin()
        await asyncio.sleep(1)

if __name__ == "__main__":
    client.run(TOKEN)
