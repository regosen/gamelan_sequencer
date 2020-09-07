import os, random, json

try:
  from itertools import zip_longest
except ImportError:
  # This is Python 2
  from itertools import izip_longest as zip_longest

from .tempo import TempoSliced
from .section import Section, Sequence

##### AMPLITUDE AND TIMING IS SLIGHTLY VARIED FOR MORE NATURAL-SOUNDING OUTPUT

MAX_RANDOM_GAIN_RANGE_DB = 0.3
MAX_RANDOM_TIME_OFFSET_MS_BY_TEMPO = 2.0 * 120 # max 2ms for 120 tempo
START_SILENCE_MS = 100
FLOAT_TO_16BIT = pow(2, 15)

class GamelanScore(object):
    def __init__(self, gamelan):
      self.gamelan = gamelan
      self.offset = int(gamelan.wave_manager.frames_per_sec * START_SILENCE_MS / 1000)
      self.outputs = {}
      self.load_errors = 0

    def humanize_offset(self, offset, tempo):
      max_random_time_range_ms = MAX_RANDOM_TIME_OFFSET_MS_BY_TEMPO / tempo
      max_random_time_range_samples = int(max_random_time_range_ms * self.gamelan.wave_manager.frames_per_sec / 1000)
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

    def load_notes(self, samples, output, notes, tempo):
      cur_note = self.gamelan.continuation_note
      cur_length = 0
      cur_pos = self.offset
      fade_length = self.gamelan.wave_manager.frames_per_sec // 100 # 10ms
      for idx, val in enumerate(notes):
        cur_tempo = tempo.get_value(float(idx) / float(len(notes)))
        beat_length = int(self.gamelan.wave_manager.frames_per_sec * 60 / cur_tempo)
        if val == self.gamelan.continuation_note:
          cur_length += 1
        else:
          if cur_note in samples:
            self.paste_mix(samples[cur_note].get_data(), output, cur_pos, beat_length * cur_length, fade_length, cur_tempo)
          cur_pos += beat_length * cur_length
          cur_note = val
          cur_length = 1
      if cur_note in samples:
        # play what's left, extending a little further into the next sequence
        self.paste_mix(samples[cur_note].get_data(), output, cur_pos, beat_length * cur_length, beat_length, cur_tempo)
        cur_pos += beat_length * cur_length
      return self.offset + (beat_length * len(notes))

    def output_for_track(self, track):
      if not track.channel_name in self.outputs:
        self.outputs[track.channel_name] = []
      return self.outputs[track.channel_name]

    def instrument_for_track(self, track):
      return self.gamelan.instruments[track.instrument]

    def load_sequence(self, sequence, filter, tempo):
      cur_pos = 0
      for track in sequence.tracks:
        if filter.track_allowed(track):
          notes = filter.get_notes(track)
          instrument = self.instrument_for_track(track)
          cur_pos = self.load_notes(instrument.samples, self.output_for_track(track), notes, tempo)
          if instrument.detuned_samples:
            self.load_notes(instrument.detuned_samples, self.output_for_track(track), notes, tempo)
      self.offset = cur_pos

    def load_sections(self, sections):
      for index, section_json in enumerate(sections):
        if "structure" in section_json:
          count = section_json.get("count", 1)
          for i in range(count):
            self.load_sections(section_json["structure"])
        else:
          section = Section(section_json, self.sequences, self.gamelan)
          sequence = section.sequence
          sequence_tempo = sequence.tempo.get_override(self.score_tempo)
          section_tempo = section.tempo.get_override(sequence_tempo)
          print("Loading %d: %s" % (index, section.sequence_name))

          if section.tempo.timeline:
            # the section is overriding the tempo start and end 
            section_tempo.offset = 0.0
            section_tempo.span = 1.0 / section.count
            for i in range(section.count):
              self.load_sequence(sequence, section.filter, section_tempo)
              section_tempo.offset += section_tempo.span
          else:
            # use the sequence's default tempo(s)
            for i in range(section.count):
              self.load_sequence(sequence, section.filter, sequence_tempo)

    def load_score(self, score_file): 
      data = json.loads(open(score_file,"r").read())
      self.score_tempo = TempoSliced(data)
      self.sequences = {}
      if "sequences" in data:
        for name, sequence_json in data["sequences"].items():
          sequence = Sequence(sequence_json, self.gamelan)
          self.load_errors += sequence.errors
          self.sequences[name] = sequence

      if self.load_errors == 0:
        self.load_sections(data["structure"])

    def write_output(self, output_file, output_data):
        print("Normalizing + converting data for %s" % output_file)
        maxval = max(max(output_data), abs(min(output_data)))
        scale = (FLOAT_TO_16BIT-1) / maxval
        normalized = [int(float(val) * scale) for val in output_data]
        self.gamelan.wave_manager.write_wave(output_file, normalized)

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

