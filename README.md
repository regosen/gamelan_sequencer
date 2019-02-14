# gamelan_sequencer

**Python sequencer for Gamelan music**

## Introduction

PROBLEM: western scores and MIDI files aren't well suited for composing and playing pieces for a Gamelan ensemble.

SOLUTION: I decided to write my own format inspired by Kepatihan, as well as a corresponding sequencer script in Python.  When provided with instrument samples, the script turns a score into a recording.

I was fortunate to find online samples of the UC Davis Gamelan Ensemble, recorded for ketuk-ketik.com by Elisa Hough, and with permission I'm using said samples to seed this system.

## Demo

Clone this repository and run the following (assuming you have Python installed):

`python gamelan.py javanese_gamelan.json kotekan_sonatina.json --mixdown=mixdown.wav`

Output should sound something like this: https://youtu.be/6_ZQaYkq0q0

_Note: The recording in the above video used the `--separates` option instead of `--mixdown`, which allowed me to make a custom mixdown from the individual tracks._


## Requirements

1. Python 2.6 or greater
2. scipy library (only if you use a gamelan with detuning): `pip install scipy`
3. a Gamelan JSON file: a listing of gamelan samples in JSON format
   - see javanese_gamelan.json for example
   - all sounds referenced by this JSON must be WAV format and have the same framerate / bits-per-sample / num-channels.
4. a Score JSON file: a score that utilizes said instruments, also in JSON format
   - see kotekan_sonatina.json for example

## Usage

`python gamelan.py [GAMELAN_FILE] [SCORE_FILE] --mixdown=MIXDOWN_FILE --separates=SEPARATES_FOLDER`

- GAMELAN_FILE: path to Gamelan JSON file (described above)
- SCORE_FILE: path to Score JSON file (described above)
- Either (or both) of the following parameters:
  - MIXDOWN_FILE: record to a single file
  - SEPARATES_FOLDER: record to a folder of multiple files   

## Output

Outputs will be mono WAV files, with the same framerate / bits-per-sample / num-channels as your sample files.

If you provide a filename for `--mixdown`, the entire recording will be mixed down to a mono WAV file.

If you provide a folder path for `--separates`, you will get a separate mono WAV file for each unique instrument/name pair. 

### How Separates are split up

For example, if you have a sequence like this:
```
{ "instrument": "gong",                            "notes": "1..." },
{ "instrument": "bonang", "track_name": "polos",   "notes": "45.4" },
{ "instrument": "bonang", "track_name": "sangsih", "notes": "32.3" }
```
Then the notes will be recorded into the following files, respectively: 
- gong.wav
- bonang_polos.wav
- bonang_sangsih.wav

They will all be in sync, so you can drag them into the audio application of your choice for mixing.


## Score Format

Gamelan music has different variations of scale notations, but typically they're represented as numbers within an octave, with a dot above or below the number to represent a lower or higher octave, respectively.

For convenience I used alphanumberic values in the provided example:

```
                       .....
Kepatihan: 12345 12345 12345
           ^^^^^

My format: 12345 ABCDE FGHIJ
```

You can specify any character mapping (even unicode) you choose in your Gamelan file, and then use the mapping in your corresponding Score files.

You can also specify what character to denote for continuation of the previous note ("." by default).  It also ignores spaces (unless you specify a space as your continuation character).

## License

Licensed under the MIT License.

NOTE: samples from ketuk-ketik.com are not covered by this license.  Please refer to http://elisahough.com/sounds/sampler.html regarding those online samples.

