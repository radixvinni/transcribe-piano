The 2 programs solve the system of linear equations for parts of FFT spectrogram of an mp3 or wav file: 

* transcibe.py uses rough approximation given by scalar multiplication of compared spectograms;
* transcribe2.py uses an approximate solution of an overdetermined system using ordinary least squares method. It is a bit slower.

Make sure you have timidity and mpg123 installed:

    sudo apt-get install timidity mpg123
    sudo pip install -r requirements.txt

