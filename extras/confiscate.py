import asyncio
import json
import random
import re
import discord

from secret import TOKEN

client = discord.Client()


def confiscate(string):
    if not valid_words(string):
        return string
    while True:
        i = random.randrange(len(string))
        if string[i].isalpha() and i > 0 and string[i - 1].isalpha():
            removed = remove(string, i)
            if valid_words(removed[0]):
                return removed


def remove(string, i):
    return string[0:i] + string[i + 1:], string[i]


VOWELS = set('aeiou')


def valid_words(string):
    for word in re.split(r'\W', string.lower()):
        if set(word).isdisjoint(VOWELS):
            return False
    return True


def get_channels():
    oba = client.get_guild(270763719619772416)
    channels = oba.channels
    return {channel.id: channel.name for channel in channels}


async def apply_channels(channels):
    for channel_id in channels:
        await asyncio.sleep(1)
        channel = client.get_channel(int(channel_id))
        try:
            print("Applying", channels[channel_id])
            await channel.edit(name=channels[channel_id])
        except discord.Forbidden:
            print(f"Could not edit {channel.name}")


@client.event
async def on_ready():
    # channels = get_channels()
    # with open("correct_channels.json", "w+") as file:
    #     json.dump(channels, file)
    with open("correct_channels.json", "r") as file:
        correct_channels = json.load(file)
        correct_channels = {int(x): correct_channels[x] for x in correct_channels}
    # for x in correct_channels:
    #     if correct_channels[x] != channels[x]:
    #         del channels[x]
    # new_channels = {x: confiscate(channels[x]) for x in channels}
    # removed_letters = [new_channels[x][1] for x in new_channels]
    # new_channels = {x: new_channels[x][0] for x in new_channels}
    # print(new_channels)
    # await apply_channels(new_channels)
    # print("".join(sorted(removed_letters)))

    await apply_channels(correct_channels)

    print("Done.")


if __name__ == "__main__":
    client.run(TOKEN)
