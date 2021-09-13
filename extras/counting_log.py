import re
from datetime import datetime

import discord

from secret import TOKEN
import plotly.express as px
import pandas as pd

client = discord.Client()


@client.event
async def on_ready():
    # await count_tower()
    await count_counting()


async def count_counting():
    channel = client.get_channel(586777485023379467)
    counts = list()
    last = 0
    async for message in channel.history(limit=1000000):
        number_part = re.search(r"^-?\d+", message.content.strip())
        if number_part is None:
            print(message.content.strip())
        else:
            number = int(number_part[0])
            if (not (1 >= number-last >= -1)) and (1 >= -number-last >= -1):
                number *= -1
            user = message.author.name
            timestamp = message.created_at
            counts.append((timestamp, user, number))
            last = number
    data = pd.DataFrame(counts, columns=["time", "user", "number"])
    fig = px.line(data, x="time", y="number", title="#counting")
    # fig.add_vline(x=datetime(year=2019, month=12, day=12).timestamp(), line_dash="dash", annotation_text="Ryu calls for a crusade to +100", annotation_position="top left")
    # fig.add_vline(x=datetime(year=2020, month=2, day=12).timestamp(), line_dash="dash", annotation_text="Cryusade reaches +100", annotation_position="top left")
    # fig.add_vline(x=datetime(year=2021, month=7, day=26).timestamp(), line_dash="dash", annotation_text="Blue issues counting challenge", annotation_position="top left")
    fig.add_hline(y=42, line_dash="dash", annotation_text="+42", annotation_position="top left")
    fig.add_hline(y=69, line_dash="dash", annotation_text="+69", annotation_position="top left")
    # fig.add_vrect(x0="2019-12-12", x1="2020-02-12",
    #               annotation_text="Cryusade", annotation_position="top left",
    #               fillcolor="green", opacity=0.25, line_width=0)
    fig.show()


async def count_tower():
    channel = client.get_channel(401200182525558785)
    counts = list()
    async for message in channel.history(limit=1000000):
        number_part = re.search(r"(?:^\W*[a-zA-z]*\W*|.*floor )(\d+)\**(?:[:;].*|\s*[a-zA-z])", message.content.strip().lower())
        if number_part is None:
            if message.content.strip().lower().startswith("floor"):
                number = None
            else:
                print(message.content.strip())
                continue
        else:
            number = int(number_part[1])
        user = message.author.name
        timestamp = message.created_at
        counts.append((timestamp, user, number))
    data = pd.DataFrame(counts, columns=["time", "user", "number"]).sort_values(by="time", ignore_index=True)
    fig = px.line(data, x="time", y="number", title="Tower floor v.s. time")
    # fig.add_vrect(x0=datetime(year=2020, month=9, day=9).timestamp(),
    #               x1=datetime(year=2020, month=9, day=13).timestamp(),
    #               annotation_text="Tower War event", annotation_position="top left",
    #               fillcolor="blue", opacity=0.25, line_width=0)
    # fig.add_vrect(x0=datetime(year=2020, month=9, day=21).timestamp(),
    #               x1=datetime(year=2020, month=10, day=1).timestamp(),
    #               annotation_text="Ryukan's Towerfight", annotation_position="top left",
    #               fillcolor="green", opacity=0.25, line_width=0)
    fig.show()
    fig2 = px.line(data, x=data.index, y="number", title="Tower floor v.s. message number")
    fig2.show()


if __name__ == "__main__":
    client.run(TOKEN)
