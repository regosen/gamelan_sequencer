import os, wave, struct, random, json, math, argparse
try:
  from itertools import zip_longest
  from urllib.request import Request, urlopen, HTTPError
except ImportError:
  # This is Python 2
  from itertools import izip_longest as zip_longest
  from urllib2 import Request, urlopen, HTTPError

##### AMPLITUDE AND TIMING IS SLIGHTLY VARIED FOR MORE NATURAL-SOUNDING OUTPUT

MAX_RANDOM_GAIN_RANGE_DB = 0.3
MAX_RANDOM_TIME_OFFSET_MS_BY_TEMPO = 2.0 * 120 # max 2ms for 120 tempo
START_SILENCE_MS = 100

##### UTILITIES

FLOAT_TO_16BIT = pow(2, 15)

class WaveManager(object):
  def __init__(self):
    self.initialized = False

  # seed wave constants with a wave file
  # we use this data for calculating fade lengths, etc.
  def setup(self, input_file):
    wav = wave.open(input_file)
    self.framerate = wav.getframerate()
    self.nchannels = wav.getnchannels()
    self.sampwidth = wav.getsampwidth()
    self.reference_file = input_file
    self.frames_per_sec = self.framerate * self.nchannels
    self.initialized = True

  # make sure all wave files have the same framerate/channels/bit depth
  def validate(self, wav, filename):
    if not self.initialized:
        raise RuntimeError("validate called before setup")
    if self.framerate != wav.getframerate():
      raise RuntimeError("Wave files don't have the same frame rate (%s: %d, %s: %d)" % (self.reference_file, self.framerate, filename, wav.getframerate()))
    if self.nchannels != wav.getnchannels():
      raise RuntimeError("Wave files don't have the same num channels (%s: %d, %s: %d)" % (self.reference_file, self.nchannels, filename, wav.getnchannels()))
    if self.sampwidth != wav.getsampwidth():
      raise RuntimeError("Wave files don't have the same bit depth (%s: %d, %s: %d)" % (self.reference_file, self.sampwidth, filename, wav.getsampwidth()))

  def read_wave(self, input_file):
    print("Reading " + input_file)
    w = wave.open(input_file)
    self.validate(w, input_file)
    astr = w.readframes(w.getnframes())
    # convert binary chunks to short, then to float
    return list(struct.unpack("%ih" % (w.getnframes() * w.getnchannels()), astr))

  def write_wave(self, output_file, data):
    print("Writing " + output_file)
    frames = bytearray(struct.pack("%ih" % len(data), *data))
    w = wave.open(output_file, "wb")
    w.setframerate(self.framerate)
    w.setnchannels(self.nchannels)
    w.setsampwidth(self.sampwidth)
    w.writeframes(frames)
    w.close()

wave_manager = WaveManager()

##### CLASSES FOR GAMELAN DATA (includes loading/detuning samples)

class Sample(object):
    def __init__(self, input_file, detune_rate = 0.0):
      self.input_file = input_file
      self.detune_scale_factor = 1.0 + (0.00154 * detune_rate)
      self.pitched_input_file = input_file.replace(".wav",".detuned.%g.wav" % detune_rate)
      self.data = []
      if not wave_manager.initialized:
        wave_manager.setup(input_file)

    def detune_data(self, orig):
      print("Detuning " + self.input_file)
      from scipy.signal import resample # scipy is a 3rd-party library and we don't always need it
      resampled = resample(orig, int(self.detune_scale_factor * len(orig)))
      return list(map(int, resampled)) # Python 2 could just return resampled
      
    def get_data(self):
      # lazy loading
      if not self.data:
        orig = wave_manager.read_wave(self.input_file)
        if self.detune_scale_factor != 1.0:
          if os.path.isfile(self.pitched_input_file):
            pitch_adjusted = wave_manager.read_wave(self.pitched_input_file)
          else:
            pitch_adjusted = self.detune_data(orig)
            wave_manager.write_wave(self.pitched_input_file, pitch_adjusted)
          self.data = [float(a) / FLOAT_TO_16BIT for a in pitch_adjusted]
        else:
          self.data = [float(a) / FLOAT_TO_16BIT for a in orig]

      return self.data

class Instrument(object):
    def __init__(self, data, detune_rate, remote_folder, cache_folder):
      unpaired = "unpaired" in data and data["unpaired"].lower() == "true"
      self.samples = {}
      self.detuned_samples = {}
      for (note, wave_file) in data["samples"].items():
        local_file = os.path.join(cache_folder, wave_file)
        if not os.path.isfile(local_file):
          if not remote_folder:
            raise RuntimeError("'samples_host' is empty and the referenced file ('%s') does not exist locally!" % wave_file)
          remote_file = os.path.join(remote_folder, wave_file)
          self.download_from_remote(remote_file, local_file)
        self.samples[note] = Sample(local_file)
        if not unpaired and detune_rate != 0:
          self.detuned_samples[note] = Sample(local_file, detune_rate)

    def download_from_remote(self, remote_file, local_file):
      print("Downloading %s -> %s" % (remote_file, local_file))
      try:
        url = urlopen(Request(remote_file))
        local_data = url.read()
        open(local_file, "wb").write(local_data)
      except HTTPError as e:
        e.msg = "failed to download wave file from URL \"" + remote_file + "\""
        raise e

class Gamelan(object):
    def __init__(self, config_file):
      config = json.loads(open(config_file,"r").read())
      remote_folder = config["samples_host"] if "samples_host" in config else ""
      cache_folder = config["samples_cache"] if "samples_host" in config else "samples_cache"
      if not os.path.isdir(cache_folder):
        os.makedirs(cache_folder)
      self.paired_detune_rate = 0.0
      if "detune_rate_between_pairs" in config:
        self.paired_detune_rate = float(config["detune_rate_between_pairs"])
      self.continuation_note = config["continuation_note"] if "continuation_note" in config else "."
      self.instruments = {}
      for instrument_name, instrument_data in config["instruments"].items():
        self.instruments[instrument_name] = Instrument(instrument_data, self.paired_detune_rate, remote_folder, cache_folder)


##### CLASSES FOR COMPOSITION DATA

def parse_tempo_json(data):
      tempo_start = float(data["tempo"]) if "tempo" in data else 0.0
      tempo_end = float(data["tempo_end"]) if "tempo_end" in data else tempo_start
      if tempo_end and not tempo_start:
        raise ValueError("'tempo_end' (%d) must be accompanied with starting 'tempo'." % int(tempo_end))
      return (tempo_start, tempo_end) if (tempo_start and tempo_end) else ()

class Track(object):
    def __init__(self, data, continuation_note):
      self.instrument = data["instrument"]
      self.name = data["track_name"] if "track_name" in data else ""
      self.notes = data["notes"]
      # ignore spaces unless user specified them as continuation notes
      if continuation_note != " ":
        self.notes.replace(" ","")

class Sequence(object):
    def __init__(self, data, continuation_note):
      self.tempos = parse_tempo_json(data)
      self.tracks = [Track(track_json, continuation_note) for track_json in data["tracks"]]

class Section(object):
    def __init__(self, data, sequences):
      sequence_name = data["sequence"]
      self.sequence = sequences[sequence_name]
      self.tracks = data["tracks"] if "tracks" in data else []
      self.count = int(data["count"]) if "count" in data else 1
      self.tempos = parse_tempo_json(data)

##### COMPOSITION METHODS

class Composition(object):
    def __init__(self, gamelan):
      self.gamelan = gamelan
      self.offset = int(wave_manager.frames_per_sec * START_SILENCE_MS / 1000)
      self.outputs = {}

    def humanize_offset(self, offset, tempo):
      max_random_time_range_ms = MAX_RANDOM_TIME_OFFSET_MS_BY_TEMPO / tempo
      max_random_time_range_samples = int(max_random_time_range_ms * wave_manager.frames_per_sec / 1000)
      random_offset = random.randrange(-max_random_time_range_samples, max_random_time_range_samples)
      return max(0, offset + random_offset)

    def humanize_gain(self):
      random_gain_db = random.uniform(-MAX_RANDOM_GAIN_RANGE_DB, MAX_RANDOM_GAIN_RANGE_DB)
      return pow(10, random_gain_db / 20.0)

    def paste_mix(self, input, output, samples_offset, length, fade_length, tempo):
      if not input:
        return
      cur_offset = self.humanize_offset(samples_offset, tempo)

      output_padding = cur_offset + length + fade_length - len(output)
      if output_padding > 0:
        output += [0.0 for i in range(output_padding)]

      input_padding = length + fade_length - len(input)
      if input_padding > 0:
        input += [0.0 for i in range(input_padding)]

      gain = self.humanize_gain()
      for idx in range(length):
        output_index = cur_offset + idx
        output[output_index] += input[idx] * gain
      for fade_idx in range(fade_length):
        idx = length + fade_idx
        output_index = cur_offset + idx
        fade_gain = 1.0 - (float(fade_idx) / fade_length) 
        output[output_index] += input[idx] * gain * fade_gain

    def play_notes(self, samples, output, notes, start_tempo, end_tempo):
      cur_note = self.gamelan.continuation_note
      cur_length = 0
      cur_pos = self.offset
      fade_length = wave_manager.frames_per_sec // 100 # 10ms
      for idx, val in enumerate(notes):
        tempo = int(((float(idx) / len(notes)) * (end_tempo - start_tempo)) + start_tempo)
        beat_length = wave_manager.frames_per_sec * 60 // tempo 
        if val == self.gamelan.continuation_note:
          cur_length += 1
        else:
          if cur_note in samples:
            self.paste_mix(samples[cur_note].get_data(), output, cur_pos, beat_length * cur_length, fade_length, tempo)
          cur_pos += beat_length * cur_length
          cur_note = val
          cur_length = 1
      if cur_note in samples:
        # play what's left, extending a little further into the next sequence
        self.paste_mix(samples[cur_note].get_data(), output, cur_pos, beat_length * cur_length, beat_length, tempo)
        cur_pos += beat_length * cur_length
      return cur_pos

    def play_sequence(self, sequence, filtered_tracks, tempo_start, tempo_end):
      cur_pos = 0
      for track in sequence.tracks:
        if (len(filtered_tracks) == 0) or (track.name in filtered_tracks):
          instrument = self.gamelan.instruments[track.instrument]
          channel_name = track.instrument
          if track.name:
            channel_name += "_" + track.name
          if not channel_name in self.outputs:
            self.outputs[channel_name] = []
          cur_pos = self.play_notes(instrument.samples, self.outputs[channel_name], track.notes, tempo_start, tempo_end)
          if instrument.detuned_samples:
            self.play_notes(instrument.detuned_samples, self.outputs[channel_name], track.notes, tempo_start, tempo_end)
      self.offset = cur_pos

    # checks for errors, i.e. if sequence references any notes missing from the gamelan json
    def validate_sequence(self, sequence, sequence_name):
      missing_notes_by_instrument = {}
      for track in sequence.tracks:
        instrument_name = track.instrument
        if not instrument_name in missing_notes_by_instrument:
          missing_notes_by_instrument[instrument_name] = []
        instrument = self.gamelan.instruments[instrument_name]
        for note in set(track.notes):
          if note == self.gamelan.continuation_note:
            continue
          if note not in instrument.samples:
            missing_notes_by_instrument[instrument_name].append(note)
      num_errors = 0
      for instrument_name, missing_notes in missing_notes_by_instrument.items():
        if missing_notes:
          num_errors += 1
          missing_notes_list = sorted(set(missing_notes))
          print("ERROR in '%s' %s: gamelan is missing the following notes: %s" % (sequence_name, instrument_name, ",".join(missing_notes_list)))
      return num_errors

    def load_score(self, score_file): 
      num_errors = 0
      data = json.loads(open(score_file,"r").read())
      sequences = {}
      for name, sequence_json in data["sequences"].items():
        sequence = Sequence(sequence_json, self.gamelan.continuation_note)
        num_errors += self.validate_sequence(sequence, name)
        sequences[name] = sequence
      if num_errors:
        return num_errors

      for idx, section_json in enumerate(data["structure"]):
        section = Section(section_json, sequences)
        sequence = section.sequence
        print("Playing section %d: %s" % (idx + 1, section_json["sequence"]))

        if section.tempos:
          # the section is overriding the tempo start and end 
          step = (section.tempos[1] - section.tempos[0]) / section.count
          tempo_start = section.tempos[0]
          tempo_end = section.tempos[0] + step
          for i in range(section.count):
            self.play_sequence(sequence, section.tracks, tempo_start, tempo_end)
            tempo_start += step
            tempo_end += step
        else:
          # use the sequence's default tempo(s)
          for i in range(section.count):
            self.play_sequence(sequence, section.tracks, sequence.tempos[0], sequence.tempos[1])
      return num_errors

    def write_output(self, output_file, output_data):
        print("Normalizing + converting data for %s" % output_file)
        maxval = max(max(output_data), abs(min(output_data)))
        scale = (FLOAT_TO_16BIT-1) / maxval
        normalized = [int(float(val) * scale) for val in output_data]
        wave_manager.write_wave(output_file, normalized)

    def write_separates(self, folder):
        if not os.path.isdir(folder):
          os.makedirs(folder)
        for name, output_data in self.outputs.items():
          output_file = os.path.join(folder, "%s.wav" % name)
          self.write_output(output_file, output_data)

    def write_mixdown(self, output_file):
        print("Mixing down tracks...")
        tracks = [data for (name, data) in self.outputs.items()]
        mixdown_data = [sum(x) for x in zip_longest(*tracks, fillvalue=0.0)]
        self.write_output(output_file, mixdown_data)


##### EXECUTION

def main():
  parser = argparse.ArgumentParser()

  parser.add_argument("gamelan", help="JSON file for gamelan instruments")
  parser.add_argument("score", help="JSON file containing score to play")
  parser.add_argument("--mixdown", help="mixdown tracks to this file", default="")
  parser.add_argument("--separates", help="output tracks to this folder", default="")

  args = parser.parse_args()

  if not (args.gamelan and args.score and (args.mixdown or args.separates)):
    parser.print_help()
  else:
    gamelan_samples = Gamelan(args.gamelan)
    composition = Composition(gamelan_samples)
    num_errors = composition.load_score(args.score)

    if not num_errors:
      if args.separates:
        composition.write_separates(args.separates)
      if args.mixdown:
        composition.write_mixdown(args.mixdown)

if __name__ == '__main__':
    main()




