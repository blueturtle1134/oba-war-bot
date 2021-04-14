import discord

from secret import TOKEN

client = discord.Client()


@client.event
async def on_ready():
    vc = await client.get_channel(270763719619772419).connect()
    # audio = discord.FFmpegPCMAudio(r"C:\Users\Daniel Fu\Downloads\hyperrogue113a\FFBatch\hr3-crossroads.mp3")
    # vc.play(audio)
    await vc.disconnect()


if __name__ == "__main__":
    client.run(TOKEN)
