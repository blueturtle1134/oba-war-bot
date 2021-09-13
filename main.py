import asyncio

import discord
import hangman
from common import *
from secret import TOKEN

client = discord.Client()

DEBUG = False
# POINTS_FILE = "data/points.txt"
# with open(POINTS_FILE, 'r') as f:
#     points = [float(x) for x in f.readline().split(" ")]
# last_graph = 0
# timer = action_timer.Timer("data/timer.json")
# posts_timer = action_timer.Timer("data/posts_timer.json")
# with open("data/dragon.json", 'r') as file:
#     dragon_state = jsons.load(json.load(file), dragon.Game)
# willpower = [0,0,0,0]
# MAX_TIME = 300


# async def repeat_task():
#     while True:
#         await on_tick()
#         await asyncio.sleep(life.TICK_PERIOD)


@client.event
async def on_ready():
    channel = client.get_channel(LOG)
    # client.loop.create_task(repeat_task())
    # await update_points()
    await channel.send("Bot ready")
    channel = client.get_channel(ANSWER)
    await channel.send(hangman.display_word())
    if DEBUG:
        await channel.send("Debugging.")


@client.event
async def on_message(message):
    # global last_graph
    if message.author.bot:
        return
    channel_id = message.channel.id
    content = message.content.strip()
    # user_time = COOLDOWN - timer.last_action(message.author.id)
    if channel_id == ANSWER:
        team = team_from_member(message.author)
        user = message.author.id
        result, show_image = hangman.guess(content, user, team)
        if show_image:
            await message.channel.send(result, file=discord.File(hangman.get_hang_image(team)))
        else:
            await message.channel.send(result)
        if hangman.check_grand_thonk():
            await message.channel.send("No team has guesses remaining. Grand Thonk gets a point!")
        await message.channel.send(hangman.display_word())
    # elif channel_id == TOWER:
    #     if user_time > 0:
    #         timer.deduct_last(message.author.id, 300)
    #         if timer.last_action(message.author.id) > COOLDOWN:
    #             await message.add_reaction("⏲️")
    # elif content.lower() == "team":
    #     await message.channel.send(f"You are on team {TEAM_NAMES[team_from_member(message.author)]}")
    elif content.lower() == "check":
        team = team_from_member(message.author)
        user = message.author.id
        await message.channel.send(hangman.check(user, team))
    # elif content.lower() == "time":
    #     if user_time < 0:
    #         await message.channel.send("You may act right now!")
    #     else:
    #         await message.channel.send(f"{user_time / 60:.1f} min until you may act again")
    #     return
    # if content.lower() == "graph" and (message.author.id == BLUE or message.author.id == RYU):
    #     await message.channel.send("Generating graph...")
    #     data = graphing.load("logs/mao_log.txt")
    #     graphing.graph(data).write_image("images/maolog.png")
    #     await message.channel.send(file=discord.File('images/maolog.png'))


# async def on_tick():
#     await life.on_tick()


# async def update_points():
#     channel = client.get_channel(ANNOUNCEMENTS)
#     message = await channel.fetch_message(772553436029386762)
#     await message.edit(
#         content=f""
#     )
#     if not DEBUG:
#         with open("data/willpower.txt", "w") as file:
#             file.write(" ".join([str(x) for x in willpower]))
#         with open("logs/mao_log.txt", "a+") as file:
#             file.write(",".join([str(time.time())] + [str(x) for x in willpower]))
#             file.write("\n")


if __name__ == "__main__":
    # print(scheduled_level())
    client.run(TOKEN)
