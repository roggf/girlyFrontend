import re
import json
from vosk import Model, KaldiRecognizer
import pyaudio

model = Model(r'/home/robby/Spracherkennung/vosk-model-small-en-us-0.15')
recognizer = KaldiRecognizer(model, 16000)


cap = pyaudio.PyAudio()
stream = cap.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
stream.start_stream()


while True:
    data = stream.read(4096)

    if recognizer.AcceptWaveform(data):
        print (recognizer.Result())
        jsonfile = json.loads(recognizer.Result())
        text = jsonfile['text']
        if (text == "start Spiel" or text == "stop Spiel"):
            print (text, " wurde erkannt")