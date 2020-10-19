import asyncio
import math
import time

import discord

import graphing
from common import *
from action_timer import Timer

client = discord.Client()

DEBUG = False

SPECIES = [
    ("Fly", ":mosquito:", "🦟"),
    ("Butterfly", ":butterfly:", "🦋"),
    ("Cricket", ":cricket:", "🦗"),
    ("Bee", ":bee:", "🐝")
]

# def warships_command(message):
#     command_text = message.content.strip().lower()
#     sender_ship = warships.ship_from_member(message.author)
#     channel = client.get_channel(CHANNEL_ID)
#     member_id = str(message.author.id)
#     if command_text.startswith("check") or command_text.startswith("stat"):
#         if sender_ship and not command_text.endswith("all"):
#             await channel.send(sender_ship.description())
#         else:
#             await channel.send("\n\n".join([ship.description() for ship in warships.ships]))
#     if ("bad" in command_text and "bot" in command_text) or ("bod" in command_text and "bat" in command_text) \
#             or command_text.startswith("bad"):
#         if member_id in warships.last_action:
#             warships.last_action[member_id] += 60 * 5
#             await channel.send("Five minutes have been added to your time until you can act.")
#     elif sender_ship:
#         result = warships.process_command(command_text, sender_ship, member_id)
#         if result:
#             await channel.send(result)


# def life_command(message):
#     message_content = message.content.strip().lower()
#     if message.author.bot:
#         return
#     if message.channel.id == CHANNEL_ID:
#         text = message.content.strip()
#         channel = client.get_channel(CHANNEL_ID)
#         if text.lower().startswith("time"):
#             await channel.send(life.get_time_stats(message.author))
#         if COORDINATE_REGEX.match(text.split(" ", 1)[0]):
#             await channel.send(life.flip_cell(text, message.author))
#         await life.update_status(channel)
#     elif message.channel.id == 401200182525558785:
#         author_id = str(message.author.id)
#         if author_id in life.last_action and life.get_action_timer(author_id) > 0:
#             life.last_action[author_id] -= 10
#             if life.get_action_timer(author_id) < 0:
#                 await message.add_reaction("⏲️")
#     elif message.channel.category_id == CATEGORY_ID:
#         if message_content.startswith("target") or message_content.startswith("preview"):
#             parts = message_content.split(" ")
#             if len(parts) > 1 and COORDINATE_REGEX.match(parts[1]):
#                 await message.channel.send(life.display_targeting(parts[1]))
#         elif message_content.startswith("forecast") or message_content.startswith("predict"):
#             parts = message_content.split(" ")
#             if len(parts) > 1 and parts[1].isdigit():
#                 if len(parts) > 2 and grids.COORDINATE_REGEX.match(parts[2]):
#                     if len(parts) > 3:
#                         await message.channel.send(life.forecast(int(parts[1]), parts[2], team_from_string(parts[3])))
#                     else:
#                         await message.channel.send(life.forecast(int(parts[1]), parts[2],
#                         team_from_member(message.author)))
#                 else:
#                     await message.channel.send(life.forecast(int(parts[1])))
#             else:
#                 await message.channel.send(life.forecast())


flies = dict()
points = [0.0, 0.0, 0.0, 0.0, 0.0]
freq_boost = 0
fly_timer = Timer("fly_timer.json")
last_graph = 0


async def repeat_task():
    while True:
        await on_tick()
        await asyncio.sleep(1)


@client.event
async def on_ready():
    channel = client.get_channel(LOG)
    client.loop.create_task(repeat_task())
    global points, freq_boost
    with open("fly.txt", 'r') as file:
        points = [float(i) for i in file.readline().strip().split(" ")]
        freq_boost = int(file.readline().strip())
    await update_points()
    await channel.send("Bot ready")
    if DEBUG:
        await channel.send("Debugging.")
    # await client.get_channel(LOG).send("Applying a bee to remedy mistake...")
    # for i in range(len(points)):
    #     points[i] = (1 - bee_drop()) * points[i]
    # await update_points()
    # await client.get_channel(LOG).send(f"Points reduced by {bee_drop():.1%}.")


@client.event
async def on_message(message):
    channel = client.get_channel(LOG)
    if message.author.bot:
        return
    global flies, freq_boost, last_graph
    channel_id = message.channel.id
    content = message.content.strip(" .!*_").lower()
    if content == "team":
        await message.channel.send(f"You are on team {TEAM_NAMES[team_from_member(message.author)]}")
    if content == "check":
        await on_tick()
        await message.delete()
    if content == "time":
        usertime = 3600 - fly_timer.last_action(message.author.id)
        if usertime < 0:
            sent_message = await message.channel.send("You may smack right now!")
        else:
            sent_message = await message.channel.send(f"{usertime/60:.1f} min until you may smack again")
        await message.delete(delay=10)
        await sent_message.delete(delay=10)
    if content == "graph" and (message.author.id == BLUE or message.author.id == RYU):
        if message.author.id == RYU:
            if last_graph > time.time() - 60:
                await message.channel.send("Too many graphs. A point will be removed from Cryusade as punishment.")
                points[3] -= 1
                await update_points()
                return
            else:
                last_graph = time.time()
        await message.channel.send("Generating graph...")
        data = graphing.load("fly_log.txt")
        graphing.graph(data).write_image("images/flylog.png")
        await message.channel.send(file=discord.File('images/flylog.png'))
    if channel_id == FORUM or channel_id == 371423137574813697 or channel_id in ALLOWED_CHANNELS:
        if content == "fly":
            await message.channel.send("Flies spawn in this channel.")
        elif content == "smack":
            await on_tick()
            if channel_id in flies:
                if fly_timer.last_action(message.author.id) > 3600:
                    last_message, spawn_time, insect = flies[channel_id]
                    smacked = await message.channel.fetch_message(last_message)
                    del flies[channel_id]
                    fly_timer.reset_last(message.author.id)
                    team = team_from_member(message.author)
                    if insect == 3:
                        points[team] -= 1
                        await client.get_channel(LOG).send(f"{TEAM_NAMES[team]} loses a point!")
                    elif insect == 2:
                        cricket = 1.81648 * math.log(time.time() - spawn_time + 4.08639) - 3.557
                        points[team] += cricket
                        await client.get_channel(LOG).send(f"{TEAM_NAMES[team]} gets {cricket:.2f} points!")
                    else:
                        points[team] += 1
                        if insect == 1:
                            await client.get_channel(LOG).send(f"Butterfly smacked.")
                        await client.get_channel(LOG).send(f"{TEAM_NAMES[team]} gets a point!")
                    await message.add_reaction("💥")
                    await update_points()
                    if smacked is not None:
                        await smacked.delete()
                else:
                    await message.add_reaction("⏱️")
            else:
                await message.add_reaction("💨")
            await message.delete(delay=60)
        else:
            if message.author.id != RYU and channel_id not in flies:
                fly_timer.deduct_last(message.author.id, 120)
                r_num = random.random()
                print(r_num)
                if r_num < fly_prob():
                    r_num = random.random()
                    if DEBUG:
                        species = 2
                    elif r_num < 0.1:
                        species = 1
                    elif r_num < 0.2:
                        species = 2
                    elif r_num < 0.3:
                        species = 3
                    else:
                        species = 0
                    name, emoji, react = SPECIES[species]
                    last_message = await message.channel.send(emoji)
                    spawn_time = time.time()
                    flies[channel_id] = last_message.id, spawn_time, species
                    log = f"> {message.content.strip()}\n{name} in {message.channel.name}"
                    print(log)
                    await channel.send(log)


def fly_prob():
    if DEBUG:
        return 1 - 0.5 ** (1 + freq_boost)
    return 1 - 0.99**(1 + freq_boost / 3.0)


def bee_drop():
    return 0.5 * 0.75 ** (freq_boost / 5.0)


async def on_tick():
    global freq_boost, points
    to_del = set()
    for channel_id, value in flies.items():
        last_message_id, spawn_time, insect = value
        channel = client.get_channel(channel_id)
        last_message = await channel.fetch_message(last_message_id)
        if time.time() - spawn_time > 60:
            if insect == 1:
                freq_boost += 1
                await update_points()
                await client.get_channel(LOG).send("Spawn rate boosted!")
            elif insect == 3:
                print("Bee going...")
                for i in range(len(points)):
                    points[i] = (1-bee_drop()) * points[i]
                await update_points()
                await client.get_channel(LOG).send(f"Points reduced by {bee_drop():.1%}.")
            else:
                points[4] += 1
                if freq_boost > 0 and insect == 2:
                    freq_boost -= 1
                await update_points()
                await client.get_channel(LOG).send("Grand Thonk gets a point!")
            to_del.add(channel_id)
            if last_message is not None:
                await last_message.add_reaction("💨")
    for channel_id in to_del:
        del flies[channel_id]


async def update_points():
    channel = client.get_channel(ANNOUNCEMENTS)
    message = await channel.fetch_message(764006519447879681)
    await message.edit(
        content=f"**Current scores**\n" + "\n".join([f"{TEAM_NAMES[i]}: {x:.2f}" for i, x in enumerate(points)]) +
                f"\n\nCurrent frequency: {fly_prob():.2%}" +
                f"\nBee reduction amount: {bee_drop():.1%}" +
                ("**\nDEBUG MODE ON - SCORES WILL BE REVERTED**" if DEBUG else ""))
    if not DEBUG:
        with open("fly.txt", "w") as file:
            file.write(" ".join([str(x) for x in points]))
            file.write("\n" + str(freq_boost))
        with open("fly_log.txt", "a") as file:
            file.write(",".join([str(time.time())] + [str(x) for x in points]))
            file.write("\n")
    fly_timer.save()


if __name__ == "__main__":
    client.run(TOKEN)
