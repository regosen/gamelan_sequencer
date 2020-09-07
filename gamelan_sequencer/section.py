from .tempo import TempoSliced

##### CLASSES FOR COMPOSITION DATA

class Track(object):
    def __init__(self, data, gamelan):
      self.instrument = data["instrument"]
      self.name = data.get("track_name", "")
      self.notes = data["notes"]
      self.channel_name = self.instrument
      if self.name:
        self.channel_name += "_" + self.name

class Sequence(object):
    def __init__(self, data, gamelan):
      self.tempo = TempoSliced(data)
      self.tracks = [Track(track_json, gamelan) for track_json in data["tracks"]]
      self.errors = 0
      missing_notes_by_insrument = gamelan.find_missing_notes(self.tracks)
      for instrument_name, missing_notes in missing_notes_by_insrument.items():
        if missing_notes:
          self.errors += 1
          missing_notes_list = sorted(set(missing_notes))
          print("ERROR in %s: gamelan is missing the following notes: %s" % (instrument_name, ",".join(missing_notes_list)))


class Filter(object):
    def __init__(self, data):
      self.instruments = data.get("instruments", [])
      self.tracks = data.get("tracks", [])
      self.start = data.get("start", 0)
      self.end = data.get("end", -1)

    def track_allowed(self, track):
      if self.instruments and not track.instrument in self.instruments:
        return False
      if self.tracks and not track.name in self.tracks:
        return False
      return True

    def get_notes(self, track):
      if self.end == -1:
        return track.notes
      else:
        return track.notes[self.start:self.end]

class Section(object):
    def __init__(self, data, sequences, gamelan):
      sequence_data = data["sequence"]
      if isinstance(sequence_data, dict):
        self.sequence_name = "(unnamed)"
        self.sequence = Sequence(sequence_data, gamelan)
      else:
        self.sequence_name = sequence_data
        self.sequence = sequences[sequence_data]
      self.filter = Filter(data.get("filter", {}))
      self.count = data.get("count", 1)
      self.tempo = TempoSliced(data)

