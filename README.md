# gamelan_sequencer

**Python sequencer for Gamelan music**

## Introduction

PROBLEM: western scores and MIDI files aren't well suited for composing and playing pieces for a Gamelan ensemble.

SOLUTION: I decided to write my own format inspired by Kepatihan, as well as a corresponding sequencer script in Python.  When provided with instrument samples, the script turns a score into a recording.

I was fortunate to find online samples of the UC Davis Gamelan Ensemble, recorded for ketuk-ketik.com by Elisa Hough, and with permission I'm using said samples to seed this system.


## Requirements

1. Python 2.6 or greater
2. scipy library (only if you use a gamelan with detuning): `pip install scipy`
3. a Gamelan JSON file: a listing of gamelan samples in JSON format
   - see javanese_gamelan.json for example
4. a Score JSON file: a score that utilizes said instruments, also in JSON format
   - see kotekan_sonatina.json for example

## Usage

`python gamelan.py [GAMELAN_FILE] [SCORE_FILE] --mixdown=MIXDOWN_FILE --separates=SEPARATES_FOLDER`

- GAMELAN_FILE (required): path to Gamelan JSON file (described above)
- SCORE_FILE (required): path to Score JSON file (described above)
- MIXDOWN_FILE: if provided, the recording will be mixed down to a mono WAV file at this path
- SEPARATES_FOLDER: if provided, for each unique instrument/track name combination, you will get a WAV file in this directory
  - Example: if a sequence track has "instrument": "bonang", "name": "polos1", the track will be recorded onto a file called "bonang_polos1.wav"
  - Example: if a sequence track has "instrument": "bonang" but no "name" provided, the track will be recorded onto a file called "bonang.wav"

You must provide either a MIXDOWN_FILE or SEPARATES_FOLDER (or both)

## Example

Using the provided JSON files in this repository:

`python gamelan.py javanese_gamelan.json kotekan_sonatina.json --mixdown=mixdown.wav`

Output should sound something like this: https://youtu.be/6_ZQaYkq0q0

(Note: The recording in the above video has `detune_rate_between_pairs` set to 5 and uses the --separates option to output tracks as separate WAV files, which I then panned and added reverb, etc.)

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

