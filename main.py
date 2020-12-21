import asyncio
import sys
import time

import discord

import action_timer
import graphing
import mao
from common import *
from secret import TOKEN

client = discord.Client()

DEBUG = False
POINTS_FILE = "data/points.txt"
with open(POINTS_FILE, 'r') as f:
    points = [float(x) for x in f.readline().split(" ")]
last_graph = 0
timer = action_timer.Timer("data/timer.json")


async def repeat_task():
    while True:
        await on_tick()
        await asyncio.sleep(1)


@client.event
async def on_ready():
    channel = client.get_channel(LOG)
    client.loop.create_task(repeat_task())
    to_ban = mao.load()
    if len(to_ban) > 0:
        await try_ban(to_ban)
    await update_points()
    await channel.send("Bot ready")
    if DEBUG:
        await channel.send("Debugging.")


@client.event
async def on_message(message):
    global last_graph
    if message.author.bot:
        return
    channel_id = message.channel.id
    content = message.content.strip()
    if content.lower() == "team":
        await message.channel.send(f"You are on team {TEAM_NAMES[team_from_member(message.author)]}")
    # if content == "check":
    #     await on_tick()
    #     await message.delete()
    usertime = 3600 - timer.last_action(message.author.id)
    if content.lower() == "time":
        if usertime < 0:
            await message.channel.send("You may act right now!")
        else:
            await message.channel.send(f"{usertime / 60:.1f} min until you may act again")
    if content.lower() == "graph" and (message.author.id == BLUE or message.author.id == RYU):
        if message.author.id == RYU:
            if last_graph > time.time() - 10:
                await message.channel.send("Too many graphs. A point will be removed from Cryusade as punishment.")
                points[3] -= 1
                await update_points()
                return
            else:
                last_graph = time.time()
        await message.channel.send("Generating graph...")
        data = graphing.load("logs/mao_log.txt")
        graphing.graph(data).write_image("images/maolog.png")
        await message.channel.send(file=discord.File('images/maolog.png'))
    if channel_id == ANSWER:
        if usertime > 0:
            await message.channel.send(f"{usertime / 60:.1f} min until you may act again")
            return
        violated = mao.check(content)
        if len(violated) != 0:
            if len(violated) > 1:
                await message.channel.send(f":no_entry: Violates multiple rules {*violated,}")
            else:
                await message.channel.send(f":no_entry: Violates rule {violated[0]}")
        else:
            reward = mao.points(content)
            team = team_from_member(message.author)
            await message.channel.send(f":white_check_mark: {reward:.2f} points to {TEAM_NAMES[team]}")
            points[team] += reward
            await update_points()
        with open("logs/mao_record.txt", "a+") as file:
            file.write(f"{str(message.author.id)} {str(violated)} {content}")
            file.write("\n")
        mao.save()
        timer.reset_last(message.author.id)
        timer.save()
        if len(violated) == 0:
            await try_ban(content)
            await update_points()


async def on_tick():
    pass


async def update_points():
    channel = client.get_channel(ANNOUNCEMENTS)
    message = await channel.fetch_message(772553436029386762)
    await message.edit(
        content=f"**Current scores**\n" + "\n".join([f"{TEAM_NAMES[i]}: {x:.2f}" for i, x in enumerate(points)]) +
                f"\nEnacted rules: {mao.count()}/{len(mao.REGEXES)}")
    if not DEBUG:
        with open("data/points.txt", "w") as file:
            file.write(" ".join([str(x) for x in points]))
        with open("logs/mao_log.txt", "a+") as file:
            file.write(",".join([str(time.time())] + [str(x) for x in points]))
            file.write("\n")


async def try_ban(text):
    channel = client.get_channel(ANSWER)
    success = mao.ban(text)
    if success:
        await channel.send("An additional rule has been enacted!")
    else:
        await channel.send("Wait for Blue to write more rules. (do not post until the bot posts again)")
        sys.exit()


if __name__ == "__main__":
    client.run(TOKEN)
