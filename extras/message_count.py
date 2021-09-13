import discord

from secret import TOKEN

client = discord.Client()


async def log(message, log_id):
    print(message)
    await client.get_channel(log_id).send(message)


@client.event
async def on_ready():
    # await count_server(540092734300618753, 540116657654202378)
    forum = client.get_channel(270763719619772416)
    words = list()
    async for message in forum.history(limit=1000):
        content = message.content.strip()
        if "-" in content:
            words.append(content)
    print("\n".join(reversed(words)))


async def count_server(server_id=270763719619772416, log_id=270763719619772416):
    oba = client.get_guild(server_id)
    channels = oba.text_channels
    summed = 0
    users = dict()
    print("Counting messages...")
    for channel in channels:
        try:
            count = 0
            async for message in channel.history(limit=1000000):
                count += 1
                writer = message.author.name
                if writer not in users:
                    users[writer] = 0
                users[writer] += 1
            summed += count
            await log(f"Analyzed {channel.name}: {count} messages.\n"
                      f"{summed} messages so far from {len(users)} unique users", log_id)
        except discord.Forbidden:
            await log(f"Could not analyze {channel.name}", log_id)
    await log(f"Total: {summed}", log_id)
    print("\n".join([f"{x}: {users[x]}" for x in users]))


if __name__ == "__main__":
    client.run(TOKEN)
