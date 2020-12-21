from datetime import datetime

import plotly.graph_objects as go

from common import TEAM_NAMES


def load(filename):
    data = list()
    with open(filename, 'r') as file:
        for line in file.readlines():
            data.append(tuple(float(x) for x in line.strip().split(",")))
    return data


def graph(data):
    sequences = [[row[i] for row in data] for i in range(len(data[0]))]
    sequences[0] = [datetime.fromtimestamp(x) for x in sequences[0]]
    fig = go.Figure()
    for i, col in enumerate(sequences[1:]):
        fig.add_trace(go.Scatter(x=sequences[0], y=col, mode='lines', name=TEAM_NAMES[i], line_shape="hv"))
    return fig


def main():
    data = load("logs/fly_log.txt")
    graph(data).write_image("images/flylog.png")


if __name__ == "__main__":
    main()
