import collections

class Tempo(object):
    def __init__(self, data):
      self.timeline = collections.OrderedDict()
      if "tempo" in data:
        self.timeline[0.0] = int(data["tempo"])
      elif "tempos" in data:
        for offset, tempo in sorted(data["tempos"].items(), key=lambda t: float(t[0])):
          self.timeline[float(offset)/100.0] = tempo

    def get_override(self, root_tempo):
      return self if self.timeline else root_tempo

    def get_value(self, percent_offset):
      first_point = list(self.timeline.items())[0]
      if (len(self.timeline) == 1) or (percent_offset <= first_point[0]):
        return first_point[1]

      last_point = list(self.timeline.items())[-1]
      if percent_offset >= last_point[0]:
        return last_point[1]

      start_offset, start_tempo = (-1.0, 0.0)
      end_offset, end_tempo = (-1.0, 0.0)

      # iterate through timeline to find the start/end segment that our offset is between
      # TODO: this could be more efficient with binary search, but in practice there's few timeline points
      for cur_offset, cur_tempo in self.timeline.items():
        if cur_offset > percent_offset:
          end_offset, end_tempo = (cur_offset, cur_tempo)
          break
        else:
          start_offset, start_tempo = (cur_offset, cur_tempo)

      offset_scale = (percent_offset - start_offset) / (end_offset - start_offset)
      offset_tempo =  start_tempo + ((end_tempo - start_tempo) * offset_scale)
      return offset_tempo

# when a tempo's timeline applies across multiple sequences, then a given sequence's tempo 
# should only come from a subset of the timeline
class TempoSliced(Tempo):
    def __init__(self, data):
      Tempo.__init__(self, data)
      self.offset = 0.0
      self.span = 1.0

    def get_value(self, percent_offset):
      actual_offset = self.offset + (percent_offset * self.span)
      return super(TempoSliced, self).get_value(actual_offset)
