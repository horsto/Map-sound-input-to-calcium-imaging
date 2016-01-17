#!/usr/bin/python

# open a microphone in pyAudio and listen for taps

import pyaudio
import struct
import math

from collections import deque
import numpy as np
import argparse
import imutils
import cv2
from scipy.interpolate import interp1d
#import colormaps as cm
from matplotlib.pylab import cm

INITIAL_TAP_THRESHOLD = 0.010
FORMAT = pyaudio.paInt16 
SHORT_NORMALIZE = (1.0/32768.0)
CHANNELS = 2
RATE = 44100  
INPUT_BLOCK_TIME = 0.05
INPUT_FRAMES_PER_BLOCK = int(RATE*INPUT_BLOCK_TIME)
# if we get this many noisy blocks in a row, increase the threshold
OVERSENSITIVE = 15.0/INPUT_BLOCK_TIME                    
# if we get this many quiet blocks in a row, decrease the threshold
UNDERSENSITIVE = 120.0/INPUT_BLOCK_TIME 
# if the noise was longer than this many blocks, it's not a 'tap'
MAX_TAP_BLOCKS = 0.35/INPUT_BLOCK_TIME



def get_rms( block ):
    # RMS amplitude is defined as the square root of the 
    # mean over time of the square of the amplitude.
    # so we need to convert this string of bytes into 
    # a string of 16-bit samples...

    # we will get one short out for each 
    # two chars in the string.
    count = len(block)/2
    format = "%dh"%(count)
    shorts = struct.unpack( format, block )

    # iterate over the block.
    sum_squares = 0.0
    for sample in shorts:
        # sample is a signed short in +/- 32768. 
        # normalize it to 1.0
        n = sample * SHORT_NORMALIZE
        sum_squares += n*n

    #print str(math.sqrt(sum_squares / count))
    return math.sqrt( sum_squares / count )

class TapTester(object):
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.stream = self.open_mic_stream()
        self.tap_threshold = INITIAL_TAP_THRESHOLD
        self.noisycount = MAX_TAP_BLOCKS+1 
        self.quietcount = 0 
        self.errorcount = 0

    def stop(self):
        self.stream.close()

    def find_input_device(self):
        device_index = None            
        for i in range( self.pa.get_device_count() ):     
            devinfo = self.pa.get_device_info_by_index(i)   
            print( "Device %d: %s"%(i,devinfo["name"]) )

            for keyword in ["mic","input"]:
                if keyword in devinfo["name"].lower():
                    print( "Found an input: device %d - %s"%(i,devinfo["name"]) )
                    device_index = i
                    return device_index

        if device_index == None:
            print( "No preferred input found; using default input device." )

        return device_index

    def open_mic_stream( self ):
        device_index = self.find_input_device()

        stream = self.pa.open(   format = FORMAT,
                                 channels = CHANNELS,
                                 rate = RATE,
                                 input = True,
                                 input_device_index = device_index,
                                 frames_per_buffer = INPUT_FRAMES_PER_BLOCK)

        return stream

    def tapDetected(self):
        print None

    def listen(self):
        try:
            block = self.stream.read(INPUT_FRAMES_PER_BLOCK)
        except IOError, e:

            # dammit. 
            self.errorcount += 1
            print( "(%d) Error recording: %s"%(self.errorcount,e) )
            amplitude = 0 
            self.noisycount = 1
            return

        amplitude = get_rms( block )
        return amplitude


        if amplitude > self.tap_threshold:
            # noisy block
            self.quietcount = 0
            self.noisycount += 1
            if self.noisycount > OVERSENSITIVE:
                # turn down the sensitivity
                self.tap_threshold *= 1.1
        else:            
            # quiet block.

            if 1 <= self.noisycount <= MAX_TAP_BLOCKS:
                self.tapDetected()
            self.noisycount = 0
            self.quietcount += 1
            if self.quietcount > UNDERSENSITIVE:
                # turn up the sensitivity
                self.tap_threshold *= 0.9



if __name__ == "__main__":
     
    tt = TapTester()

    # load video: 
    neurons = cv2.VideoCapture('Substack2.avi')
    frame_count = int(neurons.get(7))
    print "Total frames: " + str(frame_count)
    rolling_max = deque(maxlen=20)
    

    while True:
        amplitude = tt.listen()
        rolling_max.append(amplitude)
        maximum = np.amax(rolling_max)

        if maximum < 0.001:
            maximum = 0.01


        #print amplitude
        
        interp = interp1d([0,maximum],[20,1])
        frame_no = int(interp(amplitude))
        neurons.set(1,frame_no)


        (grabbed, frame) = neurons.read()
        frame = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
        #frame = cv2.equalizeHist(frame)

        #cm.viridis
        cv2.line(frame,(0,0),(int(amplitude*5000),0),(255,255,255),4,8)
        # cv2.putText(frame, "{0:.{1}f}".format(frame_no,0),
        #     (int(frame.shape[1])-47, 35), cv2.FONT_HERSHEY_PLAIN,
        #     1, (255, 255, 255), 1)  
        colorized = cm.Spectral(frame)
        #colorized = cv2.resize(colorized, (0,0), fx=1.2, fy=1.2) 
        cv2.imshow("Dancing neuron",colorized)


        #cv2.imshow("Cleared Mask",Iclear)
        
        key = cv2.waitKey(1) & 0xFF
        # if the 'q' key is pressed, stop the loop
        if key == ord("q"):
            break


        # input output
        
        # goes to frame 20 

        #print amplitude
    neurons.release()
    cv2.destroyAllWindows()    
