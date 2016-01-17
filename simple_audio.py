import numpy as np
import pyaudio

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100


def record(seconds):
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("* recording")

    frames = []

    for i in range(0, int(RATE / CHUNK * seconds)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()

    return np.hstack([
        np.fromstring(f, dtype=np.int16).astype(np.float32)
        / np.iinfo(np.int16).max
        for f in frames])


def play(data):
    p = pyaudio.PyAudio()

    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        output=True)

    data = np.iinfo(np.int16).max * data
    data = data
    frames = [
        f.astype(np.int16).tostring()
        for f in data.reshape(-1, CHUNK)]

    for f in frames:
        stream.write(f)

    stream.stop_stream()
    stream.close()

    p.terminate()


if __name__ == "__main__":
    import matplotlib.pyplot as pt
    data = record(3)
    pt.plot(data[::10])
    pt.show()

    play(data)

    np.save("cs450", data)