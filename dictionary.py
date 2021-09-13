words = list()
with open("resources/google-10000-english-usa-no-swears.txt", 'r') as file:
    for line in file.readlines():
        words.append(line.strip())

by_length = dict()
for word in words:
    length = len(word)
    if length not in by_length:
        by_length[length] = list()
    by_length[length].append(word)