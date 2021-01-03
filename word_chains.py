import os
import random
from os import path
from string import ascii_lowercase
import plotly.graph_objects as go

import requests

WORDS_URL = "http://www.mit.edu/~ecprice/wordlist.10000"
# WORDS_URL = "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
WORDS_PATH = "data/words.txt"


def load_words(length_requirement=1):
    # if not path.exists(WORDS_PATH):
    #     if not path.isdir("data"):
    #         os.mkdir("data")
    #     r = requests.get(WORDS_URL)
    #     with open(WORDS_PATH, 'wb+') as file:
    #         file.write(r.content)
    if not path.isdir("data"):
        os.mkdir("data")
    r = requests.get(WORDS_URL)
    with open(WORDS_PATH, 'wb+') as file:
        file.write(r.content)
    with open(WORDS_PATH, 'r') as file:
        words = set(x.strip() for x in file.readlines() if len(x) >= length_requirement)
    return words


def generate_adjacents(word):
    return (set(word[:i] + x + word[i + 1:] for x in ascii_lowercase for i in range(len(word)))
            | set(word[:i] + word[i + 1:] for i in range(len(word)))
            | set(word + x for x in ascii_lowercase)
            | set(word[:i] + x + word[i:] for x in ascii_lowercase for i in range(len(word)))) \
           - {word, ""}


def generate_inward_adjacents(word):
    return (set(word[:i] + y + word[i + 1:] for y in ascii_lowercase for i, x in enumerate(word))
            | set(word[:i] + word[i + 1:] for i in range(1, len(word) - 1))
            | set(word + x for x in ascii_lowercase)
            | set(x + word for x in ascii_lowercase)) \
           - {word, ""}


def generate_outward_adjacents(word):
    return (set(word[:i] + y + word[i + 1:] for y in ascii_lowercase for i, x in enumerate(word))
            | set(word[:i] + x + word[i:] for x in ascii_lowercase for i in range(1, len(word) - 1))
            | {word[1:], word[:-1]}) \
           - {word, ""}


def generate_forward_adjacents(word):
    return (set(word[:i] + y + word[i + 1:] for y in ascii_lowercase for i, x in enumerate(word))
            | set(x + word for x in ascii_lowercase)
            | {word[:-1]}) \
           - {word, ""}


def generate_backward_adjacents(word):
    return (set(word[:i] + y + word[i + 1:] for y in ascii_lowercase for i, x in enumerate(word))
            | set(word + x for x in ascii_lowercase)
            | {word[1:]}) \
           - {word, ""}


def super_adjacents(word, n=2):
    result = {word}
    for _ in range(n):
        result = {x for y in result for x in generate_adjacents(y)}
    return result


def sample_function(function, k=50000):
    words = load_words()
    test = random.choices(list(words), k=k)
    summed = 0
    zero = 0
    link_counts = list()
    for word in test:
        links = len([x for x in function(word) if x in words])
        link_counts.append(links)
        summed += links
        if links == 0:
            zero += 1
        # print(word, [x for x in function(word) if x in words])
    print(f"Average links: {summed / k:.2f}\nNo links: {zero / k:.0%}")
    # fig = go.Figure(data=[go.Histogram(x=link_counts)])
    # fig.show()


def main():
    load_words(3)
    print("Original:")
    sample_function(generate_adjacents)
    print()
    print("Inward:")
    sample_function(generate_inward_adjacents)
    print()
    print("Outward:")
    sample_function(generate_outward_adjacents)
    print()
    print("Forward:")
    sample_function(generate_forward_adjacents)
    print()
    print("Backward:")
    sample_function(generate_backward_adjacents)


if __name__ == '__main__':
    main()
