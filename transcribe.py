#%pylab inline
#pylab.rcParams['figure.figsize'] = 26, 5
from scipy.io import wavfile
from scipy.fftpack import fft
import numpy as np

import pylab
import os, subprocess
import random

from pyknon.genmidi import Midi
from pyknon.music import NoteSeq, Note

#learning
classes = np.arange(-30, 40)
n_classes = len(classes)
tempo = 180
part_length = 44100/6#7344
input_length = 600
suppress_noise = 10000

#testing
poly = 2
n_samples = 50

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
  return channel_freqs(data.T[0])[:sample_size*10:10].astype(int) / suppress_noise
  
notes_start = clean_freq(np.arange(n_classes).reshape([n_classes,1]))

answers = random_samples(n_samples)
g = clean_freq(answers)
k=0

for t in range(n_samples):
  notes = []
  vol_orig = g[t].mean()
  while g[t].mean() > 0:
    note_probs = np.dot(notes_start, g[t])
    i = note_probs.argmax()
    #how measure volume?
    #fr = notes_start[i].argmax()
    #vol = float(g[t][fr]) / notes_start[i][fr]
    #vol = float(note_probs[i]) / np.dot(notes_start[i],notes_start[i])
    #vol = (g[t]/notes_start[i]).
    best_match = (g[t]*notes_start[i]).argmax()
    vol = float(g[t][best_match]) / notes_start[i][best_match]
    if vol < 1e-2: break #if int(100*vol)
    if len(set(notes))<poly: #vol * g[t].mean() / vol_orig > 0.2:
      notes.append(i)
    #print i,vol
    g[t] -= (vol*notes_start[i]).astype(int)
  
  if set(notes) != set(answers[t]):
    k+=1
    print t, notes, answers[t]

print k*2, '%  error'

def test_output(notes):
  midi = Midi(1, tempo=360)
  for i in notes: midi.seq_notes([i], time=i.time)
  midi.write("output.mid")
  os.system("timidity output.mid")

#f[fi].argsort()[-3:]
g = channel_freqs(read_mp3('giovanni_allevi-pensieri_nascosti.mp3')[1].T[0]).astype(int) / suppress_noise

active = {}
notes = []
for t in range(len(g)):
  chord = {}
  vol_orig = g[t].mean()
  while g[t].mean() > 0:
    note_probs = np.dot(notes_start, g[t])
    i = note_probs.argmax()
    best_match = (g[t]*notes_start[i]).argmax()
    vol = float(g[t][best_match]) / notes_start[i][best_match]
    if vol < 1e-2: break #if int(100*vol)
    if vol * g[t].mean() / vol_orig > 0.2:
      chord[i] = chord.get(i,0) + vol
    #print i,vol
    g[t] -= (vol*notes_start[i]).astype(int)
  
  for i in chord:
    if active.get(i) and chord[i] > active[i].volume:
      notes.append(active[i])
        
    if active.get(i) and chord[i] < active[i].volume:
      active[i].dur += 0.25
    
    else:
      active[i] = Note(classes[i])
      active[i].time = t
      active[i].volume = 70#max(int(min(100*chord[i], 100)),10)
  for i in set(active) - set(chord): # + those new
    notes.append(active[i])
    del active[i]    

test_output(notes)