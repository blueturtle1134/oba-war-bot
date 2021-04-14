import asyncio
import json

import discord
import jsons

import action_timer
import dragon
from common import *
from secret import TOKEN

TICK_TIME = 1800

COOLDOWN = 10800

client = discord.Client()

DEBUG = False
# POINTS_FILE = "data/points.txt"
# with open(POINTS_FILE, 'r') as f:
#     points = [float(x) for x in f.readline().split(" ")]
last_graph = 0
timer = action_timer.Timer("data/timer.json")
with open("data/dragon.json", 'r') as file:
    dragon_state = jsons.load(json.load(file), dragon.Game)
last_tick = 0

level = scheduled_level()[0]


async def repeat_task():
    while True:
        await on_tick()
        await asyncio.sleep(3)


@client.event
async def on_ready():
    channel = client.get_channel(LOG)
    client.loop.create_task(repeat_task())
    # await update_points()
    await channel.send("Bot ready")
    channel = client.get_channel(ANSWER)
    if DEBUG:
        await channel.send("Debugging.")


@client.event
async def on_message(message):
    global last_graph
    if message.author.bot:
        return
    channel_id = message.channel.id
    content = message.content.strip()
    user_time = COOLDOWN - timer.last_action(message.author.id)
    if channel_id == ANSWER:
        if user_time > 0:
            await message.channel.send(f"{user_time / 60:.1f} min until you may act again")
        else:
            command = message.content.lower().split(" ")
            if command[0] == "dragon":
                pass
            elif command[0] == "knight":
                pass
    elif channel_id == TOWER:
        if user_time > 0:
            timer.deduct_last(message.author.id, 300)
            if timer.last_action(message.author.id) > COOLDOWN:
                await message.add_reaction("⏲️")
    elif content.lower() == "team":
        await message.channel.send(f"You are on team {TEAM_NAMES[team_from_member(message.author)]}")
    elif content.lower() == "time":
        if user_time < 0:
            await message.channel.send("You may act right now!")
        else:
            await message.channel.send(f"{user_time / 60:.1f} min until you may act again")
        return
    # if content.lower() == "graph" and (message.author.id == BLUE or message.author.id == RYU):
    #     await message.channel.send("Generating graph...")
    #     data = graphing.load("logs/mao_log.txt")
    #     graphing.graph(data).write_image("images/maolog.png")
    #     await message.channel.send(file=discord.File('images/maolog.png'))


async def on_tick():
    global last_tick, level
    now = time.time()
    channel = client.get_channel(ANSWER)
    if now % TICK_TIME < last_tick % TICK_TIME:
        # On the half hour!
        pass
    last_tick = now


# async def update_points():
#     channel = client.get_channel(ANNOUNCEMENTS)
#     message = await channel.fetch_message(772553436029386762)
#     await message.edit(
#         content=f"**Current scores**\n" + "\n".join([f"{TEAM_NAMES[i]}: {x:.2f}" for i, x in enumerate(points)]) +
#                 f"\nEnacted rules: {mao.count()}/{len(mao.REGEXES)}")
#     if not DEBUG:
#         with open("data/points.txt", "w") as file:
#             file.write(" ".join([str(x) for x in points]))
#         with open("logs/mao_log.txt", "a+") as file:
#             file.write(",".join([str(time.time())] + [str(x) for x in points]))
#             file.write("\n")


if __name__ == "__main__":
    # print(scheduled_level())
    client.run(TOKEN)
