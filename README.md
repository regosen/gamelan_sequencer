# Gamelan Sequencer

**Python Sequencer for Gamelan Music**

## Introduction

PROBLEM: Western scores and MIDI files aren't well suited for composing and playing pieces for a gamelan ensemble.

SOLUTION: Gamelan Sequencer uses a gamelan-friendly Kepatihan-inspired score format.  When provided with instrument samples and a score, the provided Python script generates a recording of the music.

I was fortunate to find online samples of the UC Davis Gamelan Ensemble, recorded for ketuk-ketik.com by Elisa Hough, and with permission I'm using said samples to seed this system.

## Demo

Clone this repository and run the following (assuming you have Python installed):

`python -m gamelan_sequencer scores/simple_score.json --mixdown=simple_score.wav`

Output should be a simple musical piece.

`python -m gamelan_sequencer scores/kotekan_sonatina.json --mixdown=kotekan_sonatina.wav`

Output should sound something like this: https://youtu.be/6_ZQaYkq0q0

_Note: The recording in the above video used the `--separates` option instead of `--mixdown`, which allowed me to make a custom mixdown from the individual tracks._

## Requirements

- Python 2.6+ or any version of Python 3
- (only if you set detune_rate > 0) scipy library: `pip install scipy`

## Usage

### From the Command Line
 
`python -m gamelan_sequencer SCORE_FILE [--mixdown=MIXDOWN_FILE] [--separates=SEPARATES_FOLDER] [--samples=SAMPLES_FILE]`

- SCORE_FILE: path to a JSON-formatted score
   - see [scores](scores) folder for examples
- Either (or both) of the following parameters:
  - MIXDOWN_FILE: record to a single file
  - SEPARATES_FOLDER: record to a folder of multiple files
- SAMPLES_FILE (optional): path to gamelan JSON file
  - defaults to provided [javanese_gamelan.json](gamelan_sequencer/samples/javanese_gamelan.json)
  - all sounds referenced by this JSON must be WAV format and have the same framerate / bits-per-sample / num-channels.

### From the Python Environment
```
from gamelan_sequencer import Gamelan

gamelan = Gamelan()
score = gamelan.load_score(SCORE_FILE)
if score.load_errors == 0:
   score.write_mixdown(MIXDOWN_FILE)
   -and/or-
   score.write_separates(SEPARATES_FOLDER)
```

## Output

Outputs will be WAV files with the same framerate / bits-per-sample / num-channels as your sample files.

If you provide a filename for `--mixdown`, the entire recording will be mixed down to a WAV file.

If you provide a folder path for `--separates`, you will get a separate WAV file for each unique instrument/name pair. 

## Score Format
See [scores](scores) folder for examples.

Gamelan music has different variations of scale notations, but typically they're represented as numbers within an octave, with a dot above or below the number to represent a lower or higher octave, respectively.

For convenience I used alphanumeric values in the provided example:

```
                       .....
Kepatihan: 12356 12356 12356
           ·····

My format: 12356 ABCDE FGHIJ
```

You can specify any character mapping (even unicode) you choose in your samples JSON file, and then use the mapping in your corresponding score JSON files.

For example, in the default samples file [javanese_gamelan.json](gamelan_sequencer/samples/javanese_gamelan.json) we have these jenglong samples:
```
    "jenglong": { 
      "samples": {
      "1": "jenglong5lo.wav", 
      "2": "jenglong4.wav", 
      "3": "jenglong3.wav", 
      "5": "jenglong2.wav", 
      "6": "jenglong1.wav",
      "A": "jenglong5hi.wav"
      }
    }
```

And so, in our score we can reference these notes in a track like this:
```
{ "instrument": "jenglong", "notes": "5...6...A.6.5...6...A.6.5..." }
```

### How Separates are split up

For example, if you have a sequence like this:
```
{ "instrument": "gong",                            "notes": "1..." },
{ "instrument": "bonang", "track_name": "polos",   "notes": "56.5" },
{ "instrument": "bonang", "track_name": "sangsih", "notes": "32.3" }
```
Then the notes will be recorded into the following files, respectively: 
- gong.wav
- bonang_polos.wav
- bonang_sangsih.wav

They will all be in sync, so you can drag them into an audio application of your choice for mixing.


## License

Licensed under the MIT License.

NOTE: samples from ketuk-ketik.com are not covered by this license.  Please refer to http://elisahough.com/sounds/sampler.html regarding those online samples.

