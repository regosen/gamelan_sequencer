import wave, struct

class WaveManager(object):
  def __init__(self):
    self.seeded = False

  # seed wave constants with a wave file
  # we use this data for calculating fade lengths, etc.
  def seed(self, input_file):
    if self.seeded:
      raise RuntimeError("seed previously called on wave manager")
    wav = wave.open(input_file)
    self.framerate = wav.getframerate()
    self.nchannels = wav.getnchannels()
    self.sampwidth = wav.getsampwidth()
    self.reference_file = input_file
    self.frames_per_sec = self.framerate * self.nchannels
    self.seeded = True

  # make sure all wave files have the same framerate/channels/bit depth
  def validate(self, wav, filename):
    if not self.seeded:
      raise RuntimeError("validate called before seeding wave manager")
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