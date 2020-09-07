import os, json
from .wave_manager import WaveManager
from .gamelan_score import GamelanScore

try:
  from urllib.request import Request, urlopen, HTTPError
except ImportError:
  # This is Python 2
  from urllib2 import Request, urlopen, HTTPError

FLOAT_TO_16BIT = pow(2, 15)

##### CLASSES FOR GAMELAN DATA (includes loading/detuning samples)

class Sample(object):
    def __init__(self, input_file, wave_manager, detune_rate = 0.0):
      self.input_file = input_file
      self.detune_scale_factor = 1.0 + (0.00154 * detune_rate)
      self.pitched_input_file = input_file.replace(".wav",".detuned.%g.wav" % detune_rate)
      self.data = []
      self.wave_manager = wave_manager
      if not wave_manager.seeded:
        wave_manager.seed(input_file)
    
    def detune_data(self, orig):
      print("Detuning " + self.input_file)
      from scipy.signal import resample # scipy is a 3rd-party library and we don't always need it
      resampled = resample(orig, int(self.detune_scale_factor * len(orig)))
      return list(map(int, resampled)) # Python 2 could just return resampled
      
    def get_data(self):
      # lazy loading
      if not self.data:
        orig = self.wave_manager.read_wave(self.input_file)
        if self.detune_scale_factor != 1.0:
          if os.path.isfile(self.pitched_input_file):
            pitch_adjusted = self.wave_manager.read_wave(self.pitched_input_file)
          else:
            pitch_adjusted = self.detune_data(orig)
            self.wave_manager.write_wave(self.pitched_input_file, pitch_adjusted)
          self.data = [float(a) / FLOAT_TO_16BIT for a in pitch_adjusted]
        else:
          self.data = [float(a) / FLOAT_TO_16BIT for a in orig]

      return self.data

class Instrument(object):
    def __init__(self, data, detune_rate, remote_folder, cache_folder, wave_manager):
      unpaired = data.get("unpaired", "").lower() == "true"
      self.samples = {}
      self.detuned_samples = {}
      for (note, wave_file) in data["samples"].items():
        local_file = os.path.join(cache_folder, wave_file)
        if not os.path.isfile(local_file):
          if not remote_folder:
            raise RuntimeError("'samples_host' is empty and the referenced file ('%s') does not exist locally!" % wave_file)
          remote_file = os.path.join(remote_folder, wave_file)
          self.download_from_remote(remote_file, local_file)
        self.samples[note] = Sample(local_file, wave_manager)
        if not unpaired and detune_rate != 0:
          self.detuned_samples[note] = Sample(local_file, wave_manager, detune_rate)

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
      remote_folder = config.get("samples_host", "")
      cache_folder = config.get("samples_cache", "samples_cache")
      if not os.path.isdir(cache_folder):
        os.makedirs(cache_folder)
      self.detune_rate = float(config.get("detune_rate",0.0))
      self.continuation_note = config.get("continuation_note", ".")
      self.rest_note = config.get("rest_note", " ")
      self.instruments = {}
      self.wave_manager = WaveManager()
      for instrument_name, instrument_data in config["instruments"].items():
        self.instruments[instrument_name] = Instrument(instrument_data, self.detune_rate, remote_folder, cache_folder, self.wave_manager)

    def load_score(self, score_file):
      score = GamelanScore(self)
      score.load_score(score_file)
      return score

    # if sequence references any notes missing from the gamelan, returns list of notes per instrument
    def find_missing_notes(self, tracks):
      missing_notes_by_instrument = {}
      for track in tracks:
        instrument_name = track.instrument
        if not instrument_name in missing_notes_by_instrument:
          missing_notes_by_instrument[instrument_name] = []
        instrument = self.instruments[instrument_name]
        for note in set(track.notes):
          if note == self.continuation_note:
            continue
          if note == self.rest_note:
            continue
          if note not in instrument.samples:
            missing_notes_by_instrument[instrument_name].append(note)
      return missing_notes_by_instrument
