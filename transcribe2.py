#%pylab inline
#pylab.rcParams['figure.figsize'] = 26, 5
import numpy as np

import pylab
import os, subprocess

from pyknon.genmidi import Midi
from pyknon.music import NoteSeq, Note

import librosa

n_bins = 80
n_classes = 70
fmin = librosa.midi_to_hz(36) #C2
out_tempo = 645 #11 Herz, 8 frames per 1 midi-time


"""
def mkt(notes):
  "create freq samples"
  midi = Midi(1, tempo=out_tempo)
  for i in notes: midi.seq_notes([i], time=notes[i])
  midi.write("temp.mid")
  subprocess.call("timidity temp.mid -Ow -o temp.wav".split(), stdout=subprocess.PIPE)
  return read_mp3("temp.wav")

piano_periods = [12,19,24,28, 31, 34]
first6_periods = [7, 12, 16, 19, 22]

f = read_mp3('sixoctaves.wav')
period_vol = np.zeros([n_classes, len(piano_periods)])
for n in range(6):
  i = f[n+6][143*n:143*(n+1)].argmax()+143*n
  peak = f[i, n+6]
  for p in range(len(first6_periods)):
    period_vol[n][p] = f[i][n+6+first6_periods[p]]/peak
    f[i][n+6+first6_periods[p]] = -100

for n in range(6,n_classes-6):
  i = f[n-6][143*n:143*(n+1)].argmax()+143*n
  peak = f[i, n-6]
  for p in range(len(piano_periods)):
    if n-6+piano_periods[p] < n_bins:
      period_vol[n][p] = f[i][n-6+piano_periods[p]]/peak
      f[i][n-6+piano_periods[p]] = -100

p = lambda g: librosa.display.specshow(g,sr=44100, fmin=fmin, cmap='spectral') and librosa.display.plt.show()
"""
"""
here is my idea for this algorithm. something like this:
if there is some time > min_time(pitch)
and all(f[i] > f[i].mean() during time)?? 
and f[i-1][time].mean() > f[i-1].mean()
and f[i+1][time].mean() > f[i+1].mean()
and f[i+1][time].mean() < f[i][time].mean()??
and f[i+1][time].mean() < f[i][time].mean()??
=> there is a note[i] played during time

+ f[i][time] usually descending...
abs(f[i-1] - f[i+1])[time].mean() < something

TODO rule for period

#librosa.display.specshow(g,sr=44100, x_axis='time', y_axis='cqt_note', fmin=fmin, cmap='spectral');librosa.display.plt.show()
"""
def read_mp3(filename):
    if filename.endswith('.mp3'):
      rc=1
      if rc: rc = os.system('mpg123 -w temp.wav '+filename)
      if rc: rc = os.system('ffmpeg -i '+filename+' -vn -acodec pcm_s16le -ac 1 -ar 44100 -f wav temp.wav')
      if rc: rc = os.system('avconv -i '+filename+' -vn -acodec pcm_s16le -ac 1 -ar 44100 -f wav temp.wav')
      if rc: rc = os.system('mpg321 -w temp.wav '+filename)
      if rc: exit('unable to convert mp3 to wav. install either ffmpeg or avconv or mpg123 or mpg321.')
      filename = "temp.wav"
    x,fs = librosa.load(filename, sr=44100)
    return librosa.logamplitude(librosa.cqt(x, sr=fs, fmin=fmin, n_bins=n_bins))

f = read_mp3('giovanni_allevi-pensieri_nascosti.mp3')

def find_time(f, i, min_time=80, th=10):
  mask = (f[i]>th) & (f[i-1]>th) & (f[i+1]>th)
  
  mask = np.cumsum(mask)
  mask[min_time:] = mask[min_time:] - mask[:-min_time]
  mask = mask==min_time
  mask = np.cumsum(mask)
  mask[min_time:] = mask[min_time:] - mask[:-min_time]
  mask = np.roll(mask > 0, -min_time)
  #f[i][mask] = -100
  return np.argwhere(mask^np.roll(mask,1)).reshape(-1,2)

midi = Midi(1, tempo=out_tempo)
for i in range(1, n_classes):
  for start, end in find_time(f, i, 30):
    midi.seq_notes([Note(i-24, dur=float(end-start)/8/4)], time=start/8)

midi.write("output.mid")
os.system("timidity output.mid")
