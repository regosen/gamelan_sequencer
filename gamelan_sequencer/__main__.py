import argparse

from .gamelan import Gamelan

parser = argparse.ArgumentParser()

parser.add_argument("samples", help="JSON file for gamelan instrument samples")
parser.add_argument("score", help="JSON file containing score to play")
parser.add_argument("--mixdown", help="mixdown tracks to this file", default="")
parser.add_argument("--separates", help="output tracks to this folder", default="")

args = parser.parse_args()

if not (args.samples and args.score and (args.mixdown or args.separates)):
  parser.print_help()
else:
  gamelan = Gamelan(args.samples)
  score = gamelan.load_score(args.score)
  if score.load_errors == 0:
    if args.separates:
      score.write_separates(args.separates)
    if args.mixdown:
      score.write_mixdown(args.mixdown)


