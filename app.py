# Import necessary libraries
import socket
import time
from urllib import request
import pickle

import socketio
from flask import Flask, render_template, Response, request, url_for
import cv2
import threading
from threading import *
from flask_socketio import SocketIO
import os
import json
from vosk import Model, KaldiRecognizer
import pyaudio
PEOPLE_FOLDER = os.path.join('static', 'Symbols')
"""Variables for Threading"""
POOL_TIME = 5  # Seconds
commonDataStruct = {}
dataLock = threading.Lock()
yourThread = threading.Thread()
thread = None
thread2 = None
thread3 = None
thread_lock = Lock()
""""""
SYMBOL_FOLDER = os.path.join('static/Symbole')
"""Camera-Settings"""
IM_WIDTH = 640
IM_HEIGHT = 480
fps = 30

camera = cv2.VideoCapture(0, cv2.CAP_GSTREAMER)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, IM_WIDTH)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, IM_HEIGHT)
camera.set(cv2.CAP_PROP_FPS, fps)
camera.set(cv2.CAP_PROP_AUTOFOCUS, 0)
camera.set(28, 15)
out_send = cv2.VideoWriter('appsrc ! videoconvert ! x264enc tune=zerolatency,width=640,height=480,  bitrate=500 '
                           'speed-preset=2 ! rtph264pay ! udpsink host=127.0.0.1 port=9800',
                           cv2.CAP_GSTREAMER, 2, 20, (640, 480), True)
""""""

"""FlaskApp and SocketIO"""
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = PEOPLE_FOLDER
sio = SocketIO(app)
""""""

"""Global Variables for Interaction-Handling"""
punkte_user = 0
punkte_ki = 0
got_it = False
send_frame = False
ready = False
i = 0
difficulty = 10
symbol = ""
already_plotted = False
symbol_name = ""
""""""


@app.route("/start_stop_game", methods=['GET', 'POST'])
def start_stop_game():
    global i
    global send_frame
    if i == 0:
        send_frame = True
        i = 1
        return None

    elif i == 1:
        send_frame = False
        i = 0
        return None


@app.route("/gotit", methods=['GET', 'POST'])
def gotit():
    global got_it
    got_it = True


@app.route("/easy", methods=['GET', 'POST'])
def easy():
    global symbol
    global difficulty
    difficulty = 10
    SocketSend(10, 9595)


@app.route("/reset", methods=['GET', 'POST'])
def reset():
    global punkte_ki
    global punkte_user
    print("!!!!!!!!!!!!!!!!!")
    punkte_ki = 0
    punkte_user = 0
    punktestand = [punkte_user, punkte_ki]
    print("vor dem senden")
    handlemsg(punktestand)


@app.route("/hard", methods=['GET', 'POST'])
def hard():
    global difficulty
    difficulty = 5
    SocketSend(5, 9595)


@app.route("/ready", methods=['GET', 'POST'])
def ready():
    global difficulty
    global symbol
    global already_plotted
    already_plotted = False
    symbol = ""
    SocketSend(True, 9696)
    countdown2(difficulty)


def ready_2():
    global difficulty
    global symbol
    global already_plotted
    already_plotted = False
    symbol = ""
    SocketSend(True, 9696)
    countdown2(difficulty)

#    handlemsg(symbol)
#    global send_frame
#    global ready
#    ready = True
#    send_frame = True


def SocketSend(message, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', port))
    array = [message]
    data_dump = pickle.dumps(array)
    s.sendall(data_dump)
    s.close()
    print("Done sending...")


def interrupt():
    global yourThread
    yourThread.cancel()


def gen_frames():
    global got_it
    global send_frame
    while True:
        success, frame = camera.read()  # read the camera frame
        out_send.write(frame)
        #        if send_frame:
        #            SocketSend(frame, 9090)
        #            send_frame = False
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


def symbol_generator():
    global symbol_name
    while True:
        full_filename = os.path.join(app.config['UPLOAD_FOLDER'], f'{symbol_name}.jpg')
        frame = cv2.imread(full_filename)
        print(frame)
        ret, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()
        print(frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route("/", methods=['GET', 'POST'])
def index():
    global thread
    global thread2
    global thread3
    with thread_lock:
        if thread is None:
            thread = sio.start_background_task(SocketEmpfang)
            thread2 = sio.start_background_task(AudioRecognition)
            thread3 = sio.start_background_task(readySocket2)
    return render_template("index.html")


@app.route("/test", methods=['GET', 'POST'])
def test():
    select = str(request.form.get('Schwierigkeitsgrad'))
    return str(select)  # just to see what select is


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/symbol_feed')
def symbol_feed():
    return Response(symbol_generator(), mimetype='multipart/x-mixed-replace; boundary=frame')


def readySocket2():
    while True:
        p.listen(1)
        s, addr = p.accept()
        data = b""
        while True:
            packet = s.recv(4096)
            if not packet:
                break
            data += packet
        data_arr = pickle.loads(data)
        data = data_arr[0]
        if data == "True":
            time.sleep(4)
            ready_2()


def SocketEmpfang():
    global punkte_ki
    global punkte_user
    global got_it
    global ready
    global symbol_name
    global symbol
    global already_plotted
    while True:
        g.listen(1)
        s, addr = g.accept()
        data = b""
        while True:
            packet = s.recv(4096)
            if not packet:
                break
            data += packet
        #        reset_textfield()
        data_arr = pickle.loads(data)
        symbol = data_arr[0]
        symbol_name = symbol
        path = f"../static/Symbole/{symbol}.JPG"
        handlemsg(path)
#        print(path)
#        img = cv2.imread(, cv2.IMREAD_GRAYSCALE)
#        socketio.emit('my_response',
#                      {'data': 'Server generated event',
#                       'image': img})
#        print(symbol)
        symbol = str(symbol)
        #        handlemsg(symbol)
        winner = data_arr[1]
        if winner == "user":
            punkte_user += 1
            handlemsg(symbol)
            os.system('espeak "{}"'.format(symbol))
            already_plotted = True
        if winner == "ki":
            punkte_ki += 1
            handlemsg(symbol)
            os.system('espeak "{}"'.format(symbol))
        punktestand = [punkte_user, punkte_ki]
        handlemsg(punktestand)

        #        ready = False
        #        countdown()
        #        if got_it:
        #            punkte_user = show_solution_user(symbol, punkte_user)
        #        if not got_it:
        #            punkte_ki = show_solution_ki(symbol, punkte_ki)
        #        time.sleep(2)
        #        punktestand = [punkte_user, punkte_ki]
        #        handlemsg(punktestand)  ## s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ## s.bind(("localhost", 42008))
        #        got_it = False
        #        handlemsg("Bitte neue Karte auflegen!")
        while not ready:
            print("not ready")


def countdown2(schwierigkeit):
    global already_plotted
    global symbol
    for e in reversed(range(schwierigkeit)):
        handlemsg(f"Auflösung in {schwierigkeit}..")
        schwierigkeit -= 1
        time.sleep(1)
        if not already_plotted:
            continue
        else:
            break
    if already_plotted:
        handlemsg(symbol)


def countdown():
    handlemsg("Auflösung in 10..")
    time.sleep(1)
    handlemsg("Auflösung in 9..")
    time.sleep(1)
    handlemsg("Auflösung in 8..")
    time.sleep(1)
    handlemsg("Auflösung in 7..")
    time.sleep(1)
    handlemsg("Auflösung in 6..")
    time.sleep(1)


def show_solution_user(symbol, punkte_u):
    handlemsg("Nutzer hat die Antwort gefunden")
    time.sleep(1)
    handlemsg("Auflösung in 5..")
    time.sleep(1)
    handlemsg("Auflösung in 4..")
    time.sleep(1)
    handlemsg("Auflösung in 3..")
    time.sleep(1)
    handlemsg("Auflösung in 2..")
    time.sleep(1)
    handlemsg("Auflösung in 1..")
    time.sleep(1)
    if not symbol:
        handlemsg("Symbol konnte nicht gefunden werden!")
    else:
        handlemsg(symbol)
        punkte_u += 1
    return punkte_u


def show_solution_ki(symbol, punkte_k):
    time.sleep(1)
    handlemsg("Auflösung in 5..")
    time.sleep(1)
    handlemsg("Auflösung in 4..")
    time.sleep(1)
    handlemsg("Auflösung in 3..")
    time.sleep(1)
    handlemsg("Auflösung in 2..")
    time.sleep(1)
    handlemsg("Auflösung in 1..")
    time.sleep(1)
    if not symbol:
        handlemsg("Symbol konnte nicht gefunden werden!")
    else:
        handlemsg(symbol)
        punkte_k += 1
    return punkte_k


def reset_textfield():
    handlemsg("")


@sio.on('message')
def handlemsg(msg):
    sio.send(msg)


def AudioRecognition():
    model = Model('./vosk-model-small-en-us-0.15')
    recognizer = KaldiRecognizer(model, 16000)
    cap = pyaudio.PyAudio()
    stream = cap.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
    stream.start_stream()
    while True:
        data = stream.read(4096)
        if recognizer.AcceptWaveform(data):
            #print(recognizer.Result())
            jsonfile = json.loads(recognizer.Result())
            text = jsonfile['text']
            if text == "next":
                print(text)
                ready_2()


g = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
g.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
g.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
g.bind(("localhost", 12350))

p = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
p.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
p.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
p.bind(("localhost", 12357))
## s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
## s.bind(("localhost", 42008))

if __name__ == "__main__":
    app.run(debug=True)
