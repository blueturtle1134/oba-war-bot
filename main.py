import asyncio
import os
import time

import discord

import action_timer
import robot
from common import *
from robot import scheduled_level
from secret import TOKEN

client = discord.Client()

DEBUG = False
# POINTS_FILE = "data/points.txt"
# with open(POINTS_FILE, 'r') as f:
#     points = [float(x) for x in f.readline().split(" ")]
last_graph = 0
timer = action_timer.Timer("data/timer.json")
robot_state = robot.load()
last_tick = 0

level = scheduled_level()


async def repeat_task():
    while True:
        await on_tick()
        await asyncio.sleep(60)


@client.event
async def on_ready():
    global robot_state
    channel = client.get_channel(LOG)
    client.loop.create_task(repeat_task())
    # await update_points()
    await channel.send("Bot ready")
    channel = client.get_channel(ANSWER)
    await robot_state.send_state(channel)
    if DEBUG:
        await channel.send("Debugging.")


@client.event
async def on_message(message):
    global last_graph
    if message.author.bot:
        return
    channel_id = message.channel.id
    content = message.content.strip()
    user_time = 10800 - timer.last_action(message.author.id)
    if channel_id == ANSWER:
        if user_time > 0:
            await message.channel.send(f"{user_time / 60:.1f} min until you may act again")
        elif robot_state.add_command(message.content.strip()):
            timer.reset_last(message.author.id)
            robot.dump(robot_state)
        else:
            await message.channel.send("Invalid command, try again")
        await robot_state.send_state(message.channel)
    elif channel_id == TOWER:
        if user_time > 0:
            timer.deduct_last(message.author.id, 300)
            if timer.last_action(message.author.id) > 10800:
                await message.add_reaction("⏲️")
    elif content.lower() == "team":
        await message.channel.send(f"You are on team {TEAM_NAMES[team_from_member(message.author)]}")
    elif content.lower() == "time":
        if user_time < 0:
            await message.channel.send("You may act right now!")
        else:
            await message.channel.send(f"{user_time / 60:.1f} min until you may act again")
        return
    elif content.lower() == "forecast":
        await robot_state.send_forecast(message.channel)
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
    if now % 1800 < last_tick % 1800:
        # On the half hour!
        stack_result = robot_state.execute_stack()
        if stack_result is not None:
            await robot_state.send_state(channel, f"`Executed: {stack_result}`")
        robot.dump(robot_state)
        with open("logs/robot_log.txt", "a+") as file:
            file.write(",".join([str(time.time())] + [str(x) for x in robot_state.points]))
            file.write("\n")
        if robot_state.dead:
            path = f"levels/robot/{level}.txt"
            if os.path.isfile(path):
                robot_state.points[4] += scheduled_level()
                with open(path, 'r') as file:
                    robot_state.load_board(file)
                await channel.send(f"Reloading board {level}")
                await robot_state.send_state(channel)
            robot.dump(robot_state)
    if scheduled_level() > level:
        # Time to change levels
        path = f"levels/robot/{scheduled_level()}.txt"
        if os.path.isfile(path):
            with open(path, 'r') as file:
                robot_state.load_board(file)
            level = scheduled_level()
            await channel.send(f"Changing to board {level}")
            await robot_state.send_state(channel)
        robot.dump(robot_state)
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
