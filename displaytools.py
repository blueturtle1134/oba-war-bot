BAR_PARTIAL = ["·", "+", "X"]
BAR_FULL = "#"


def charge_bar(x):
    full = int(x)
    result = "".join([BAR_FULL] * full)
    if full != x:
        result += BAR_PARTIAL[int((full - x) * len(BAR_PARTIAL))]
