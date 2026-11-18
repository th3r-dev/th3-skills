#!/usr/bin/env python3
# Rolls a starting point from outside the model's own taste when a creative request is thin.
# From mankidev/antialgorithm@8706a2d scripts/seed.py, unchanged below this header.
# MIT License, Copyright (c) 2026 mankidev:
# https://github.com/mankidev/antialgorithm/blob/8706a2d49511954d0d092f732eb5853497ad25fc/LICENSE
# Usage: python3 seed.py [visual|text|idea] [--only <axis>]
import argparse
import random
import sys

rng = random.SystemRandom()

METHOD_FAMILIES = {
    "hand and print": [
        "woodcut", "screen print", "rubber stamp", "spray stencil", "cut paper collage",
        "photocopy zine", "gouache", "ink brush", "ballpoint sketch", "marker on cardboard",
        "embroidery", "hand painted shop sign", "children's crayon drawing", "spray paint graffiti",
        "chalk on pavement",
    ],
    "screen and machine": [
        "LED dot matrix", "old CRT screen", "thermal receipt printer", "brutalist web page",
        "early 3D video game", "phone screenshot", "spreadsheet chart", "vector icon set",
        "glitched video frame", "airport departure board", "arcade cabinet art", "e-ink display",
        "low poly render", "CAD wireframe", "pixel font on a car dashboard",
    ],
    "camera and science": [
        "flash film photo", "long exposure photo", "infrared photo", "x-ray image",
        "thermal camera image", "satellite image", "microscope image", "security camera still",
        "night vision footage", "macro photo", "drone photo from straight above", "sonar scan",
        "weather radar map", "motion blur photo", "underwater photo",
    ],
    "material and light": [
        "neon tubes", "stained glass", "mosaic tiles", "glazed ceramic", "glossy 3D render",
        "chrome and glass render", "holographic foil", "clay model photo", "inflatable plastic",
        "folded paper", "string and pins", "carved wood relief", "light painting",
        "shadow puppets", "frosted acrylic with backlight",
    ],
}

VISUAL = {
    "color": [
        "one ink only", "black and white with one accent", "two colors that clash",
        "colors taken from the subject's material", "full color with one hue in charge",
        "very pale and high key", "very dark and low key", "fluorescent", "only earth colors",
        "metallic", "colors of a place at a set hour", "gray with one warm spot",
        "cold colors only", "warm colors only", "the colors of a machine screen", "colors of food",
    ],
    "layout": [
        "subject huge and cropped by the edges", "subject tiny in a large empty field",
        "seen from straight above", "seen from far below", "one detail very close",
        "one thing repeated many times", "split into two halves", "the text is the image",
        "strong diagonal", "low and off center", "deep layers from front to back",
        "a crowd of small parts", "a single line across the frame", "framed by something in front",
        "upside down or turned", "one big shape and nothing else",
    ],
    "type": [
        "hand lettered", "cut out letters", "stencil letters", "tall condensed", "very wide",
        "old style serif", "typewriter", "flowing script", "stacked words", "type on a curve",
        "only small type", "one giant word", "letters built from the subject", "mixed found letters",
        "no type at all if allowed", "type set vertically",
    ],
}

TEXT = {
    "voice": [
        "a witness in first person", "instructions in second person", "a plain list",
        "a short letter", "overheard dialogue", "one long sentence", "short fragments",
        "question and answer", "a note left for someone", "a review by someone tired",
        "a child explaining it", "someone who disagrees", "a voice from the future looking back",
        "a rumor passed on",
    ],
    "entry": [
        "a sound", "a smell", "a single object", "a mistake", "a rule", "a place",
        "the ending", "a body feeling", "a thing that is missing", "a complaint", "a habit",
        "a misunderstanding", "a gesture", "a question nobody answers",
    ],
    "register": [
        "plain", "formal", "dry", "warm", "blunt", "playful", "terse", "careful", "nervous", "proud",
    ],
}

IDEA = {
    "verb": [
        "trade", "hide", "build", "repair", "sort", "follow", "trap", "grow", "deliver", "swap",
        "borrow", "steal", "listen", "stack", "balance", "burn", "wash", "guess", "herd", "queue",
        "bargain", "cook", "dig", "signal", "wait", "measure", "lose", "rescue", "copy", "share",
    ],
    "constraint": [
        "only one try", "it gets worse when you wait", "you cannot see it directly",
        "someone else controls half of it", "all of it is borrowed and must go back",
        "it only works in one place", "two rules that fight", "the tool wears out with use",
        "the crowd decides", "you are too small for it", "nobody speaks the same language",
        "the reward is also the cost", "it must be done in silence", "it happens to many at once",
    ],
    "scale": [
        "one person", "a family", "a street", "a whole town", "a crowd of strangers",
        "a machine", "an animal", "a single room", "two rivals", "a team that does not get along",
    ],
    "pressure": [
        "a deadline", "a rival", "a debt", "weather", "a rule that changes", "noise", "hunger",
        "a promise", "a rumor", "running out of space", "a guest who will not leave", "fatigue",
    ],
}

ANCHOR = [
    "ladder", "bicycle", "glove", "mirror", "bread", "magnet", "compass", "hinge", "fog", "bee",
    "copper", "thread", "lamp", "drum", "sponge", "scissors", "ice", "cactus", "radio", "bridge",
    "key", "feather", "brick", "orange", "train", "coin", "bone", "cloud", "button", "mushroom",
    "wire", "fan", "tooth", "bell", "window", "kite", "ash", "honey", "nail", "moth", "paint",
    "tent", "elevator", "umbrella", "cassette", "dice", "spoon", "candle", "lock", "stairs",
    "battery", "garden hose", "skateboard", "laundry", "traffic cone", "ticket", "alarm clock",
    "snail", "cable", "balloon", "ring", "knot", "crane", "pump", "mask", "barcode", "tire",
    "zip", "comb", "fork", "parachute", "chair", "puddle", "smoke", "chili", "rice", "sand",
    "escalator", "satellite dish", "lemon", "goat", "camel", "bamboo", "lantern", "scooter",
    "vending machine", "pigeon", "ceiling fan", "water tank", "mango", "plastic chair", "antenna",
    "glass bottle", "sunflower", "cardboard box", "headphones", "rug", "tea glass", "bus",
]

SETTING = [
    "a desert town at noon", "a mountain village above the clouds", "a rooftop in a huge city",
    "a parking lot after closing", "a tropical market in the rain", "a frozen lake", "a rice terrace",
    "a highway service station", "a night bus", "a dense housing block courtyard", "a jungle river",
    "a shopping mall basement", "a steppe under a big sky", "an industrial suburb",
    "a cable car station", "a salt flat", "a volcanic island", "a pine forest in snow",
    "a stadium after the match", "a subway platform", "a hot spring town", "an orchard in bloom",
    "a border crossing", "a canyon", "a university dorm", "a wind farm", "a crowded old bazaar",
    "a new town still being built", "a ski lift", "a tea plantation", "an airport at night",
    "a car wash", "a hilltop monastery", "a laundromat", "a savanna road", "a glass office tower",
    "a village wedding tent", "a server room", "a hospital corridor", "a school gym",
    "a gas station in the mountains", "a food court", "a construction crane cab",
]

REGION = [
    "Georgia (the country)", "northern Chile", "Kerala", "Hokkaido", "the Scottish Highlands",
    "Anatolia", "Sicily", "Ghana", "Mongolia", "Quebec", "Java", "the Faroe Islands", "Oaxaca",
    "Morocco", "Finnish Lapland", "the Philippines", "Patagonia", "Kenya", "Vietnam", "Iceland",
    "Bavaria", "Poland", "Sri Lanka", "the Andes of Peru", "Portugal", "Nigeria", "Korea",
    "Brazil's northeast", "Ukraine", "Ethiopia", "Wales", "Nepal", "Senegal", "Sardinia",
    "Kazakhstan", "the Basque Country", "Tasmania", "Cuba", "Bangladesh", "the American Midwest",
    "Iran", "Croatia", "Colombia", "Taiwan", "Egypt", "Norway", "Bolivia", "Uzbekistan",
]
NO_ANCHOR = [
    "no single object, build it from a pattern of the place",
    "no single object, only type",
    "no single object, a crowd of people",
    "no single object, numbers or data from the subject",
    "no single object, a field of light or color",
    "no single object, the surface of the place up close",
]


def method():
    family = rng.choice(list(METHOD_FAMILIES))
    return rng.choice(METHOD_FAMILIES[family])


def pools(kind):
    if kind == "visual":
        return {"method": None, **VISUAL}
    if kind == "text":
        return dict(TEXT)
    return dict(IDEA)


def roll(kind):
    out = {}
    for name, items in pools(kind).items():
        out[name] = method() if items is None else rng.choice(items)
    if kind == "visual":
        out["verb"] = rng.choice(IDEA["verb"])
        out["scale"] = rng.choice(IDEA["scale"])
    out["setting"] = rng.choice(SETTING)
    out["region"] = rng.choice(REGION)
    if kind == "visual" and rng.random() < 0.5:
        out["anchor"] = rng.choice(NO_ANCHOR)
    else:
        out["anchor"] = rng.choice(ANCHOR)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", nargs="?", default="visual", choices=["visual", "text", "idea"])
    ap.add_argument("--only", help="roll one axis again, for example --only method")
    args = ap.parse_args()
    seed = roll(args.kind)
    if args.only:
        if args.only not in seed:
            sys.exit(f"no axis '{args.only}' for {args.kind}; axes: {', '.join(seed)}")
        seed = {args.only: seed[args.only]}
    for k, v in seed.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
