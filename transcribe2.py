#%pylab inline
#pylab.rcParams['figure.figsize'] = 26, 5
from scipy.io import wavfile
from scipy.fftpack import fft
from scipy.optimize import lsq_linear
import numpy as np

import pylab
import sys, os, subprocess
import random

from pyknon.genmidi import Midi
from pyknon.music import NoteSeq, Note

#learning
classes = np.arange(-30, 40) #notes from F#2 to E8
n_classes = len(classes)
tempo = 180 #tempo of file for sample notes.  fps / tempo gives how much of the sample we analyze
fps = 6 #frequency of the chords we recognize
part_length = 44100 / fps #size of a part we analyze
input_length = 600 #number of amplitudes of spectrogram we analyze
suppress_noise = 10000 # for nice printing

timespan = 60 * 5 * fps / tempo 
out_tempo = fps * 60

minimal_volume = 0.01 # output volume threshold 

#testing
poly = 0 # size of chord to test recognition on
n_samples = 50 # number of tests

#todo: polishing

def read_mp3(filename):
    if filename.endswith('.mp3'):
      rc=1
      if rc: rc = os.system('mpg123 -w temp.wav '+filename)
      if rc: rc = os.system('ffmpeg -i '+filename+' -vn -acodec pcm_s16le -ac 1 -ar 44100 -f wav temp.wav')
      if rc: rc = os.system('avconv -i '+filename+' -vn -acodec pcm_s16le -ac 1 -ar 44100 -f wav temp.wav')
      if rc: rc = os.system('mpg321 -w temp.wav '+filename)
      if rc: exit('unable to convert mp3 to wav. install either ffmpeg or avconv or mpg123 or mpg321.')
      filename = "temp.wav"
    return wavfile.read(filename)

def channel_freqs(channel1, part_length=part_length, input_length=input_length):
  #channel1 = channel1[part_length/2:]
  parts = len(channel1) / part_length
  freqs = np.array([abs(fft(channel1[i*part_length:(i+1)*part_length]))[:input_length] for i in range(parts)])
  pylab.imshow(freqs.T, extent=(0,parts,input_length,0), cmap='spectral')
  #pylab.show()
  
  return freqs

def random_samples(sample_size):
  "get random notes"
  return np.array([random.sample(range(n_classes), random.choice([poly])) for i in range(sample_size)])

def clean_freq(samples):
  "create freq samples"
  sample_size = len(samples)
  chords = [NoteSeq([Note(classes[i]) for i in sample]) for sample in samples]
  midi = Midi(1, tempo=tempo)
  for i in range(sample_size): midi.seq_chords([chords[i]], time=5*i)
  midi.write("temp.mid")

  subprocess.call("timidity temp.mid -Ow -o temp.wav".split(), stdout=subprocess.PIPE)

  rate, data = wavfile.read('temp.wav')
  return channel_freqs(data.T[0])[:sample_size*timespan:timespan].astype(int) / suppress_noise
  
notes_start = clean_freq(np.arange(n_classes).reshape([n_classes,1]))

if poly:
  answers = random_samples(n_samples)
  g = clean_freq(answers)
  k=0
  for t in range(n_samples):
    vol_orig = g[t].mean()
    
    result = lsq_linear(notes_start.T, g[t], (0, np.inf))
    notes = result.x.argsort()[-poly:]
    
    if set(notes) != set(answers[t]):
      k+=1
      print t, 'precision -', set(notes)-set(answers[t]), 'recall +', set(answers[t])-set(notes)

  print k*2, '%  error'

def test_output(x, g):
  midi = Midi(1, tempo=out_tempo)
  for i in range(n_classes):
    dur = 0
    vol = 0
    for t,v in enumerate(x.T[i]):
      min_volume = minimal_volume * g[t] / g.mean()
      if v*v>min_volume:
        if dur:
          vol = (vol / dur + v*v/min_volume ) * (dur+1)
        else:
          vol = v*v/min_volume
        dur += 1
      elif dur:
        midi.seq_notes([Note(classes[i], dur=dur/4., volume=min(100,int(vol)))], time=t)
        dur = 0
        vol = 0
  midi.write("output.mid")
  os.system("timidity output.mid")

#f[fi].argsort()[-3:]
if not sys.argv[1:]: sys.argv.append('giovanni_allevi-pensieri_nascosti.mp3')
g = channel_freqs(read_mp3(sys.argv[1])[1].T[0]).astype(int) / suppress_noise

x = np.zeros([len(g),n_classes])
for i,b in enumerate(g):
  print '{:.1%}'.format(float(i)/len(g))
  result = lsq_linear(notes_start.T, b, (0, np.inf))
  if not result.status:
    print result
  x[i] = result.x
pylab.imshow(x.T, cmap='spectral')
#pylab.show()

test_output(x, g.mean(axis=1))