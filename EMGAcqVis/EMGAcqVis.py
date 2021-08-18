import sys
import pytrigno

import errno

import numpy as np
from numpy import arange
import PyQt5
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import sys
import socket
import struct
import math 
from scipy import signal
from scipy.integrate import odeint
import os


class Plot2D():
    def __init__(self):
        self.traces = dict()

        #QtGui.QApplication.setGraphicsSystem('raster')
        self.app = QtGui.QApplication([])
        #mw = QtGui.QMainWindow()
        #mw.resize(800,800)

        self.win = pg.GraphicsWindow(title="Basic plotting examples")
        self.win.resize(1000, 600)
        self.win.setWindowTitle('EMG')

        # Enable antialiasing for prettier plots
        pg.setConfigOptions(antialias=True)

        self.canvas = self.win.addPlot(title="EMG")
        self.canvas.setYRange(-5, 5, padding=0)
        self.canvas.addLegend(offset=(20, 20))
        self.canvas.setLabel('left', 'mV')
        self.canvas.hideAxis('bottom')



    def start(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()

    def trace(self, name, dataset_x, dataset_y):
        if name in self.traces:
            self.traces[name].setData(dataset_x,dataset_y)

        elif name == "LE":
            self.traces[name] = self.canvas.plot(pen='r', name="Linear Envelope")

        elif name == "A":
            self.traces[name] = self.canvas.plot(pen='b', name="Normalised Activation")

        elif name == "V":
            self.traces[name] = self.canvas.plot(pen='g', name="Fatigue")

        else:
            self.traces[name] = self.canvas.plot(pen='y', fillLevel=20.0, fillOutline=True, name="EMG Biceps")


# Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':

    file = open(r"C:\Users\Alvaro\source\repos\CalibExp\calibparam.txt", "r")
    lines = file.readlines()

    MVC = float(lines[0])
    Tend = float(lines[1])
    Cf = -(0.3*MVC*Tend)/(math.log((1-0.993), 10))
    Ath = 0.4
    timestep = 0
    samples = 50
    emgrate=1500
    file.close()

    # UDP CONNECTION CONSTANTS
    KUKA_IP = "192.180.1.5"
    KUKA_PORT = 54002
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)



   

    vo = 0
    p = Plot2D()
#    i = 0
#    f = np.zeros((1,270),dtype=float)
#    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#    s.setblocking(0)
    dev = pytrigno.TrignoEMG(channel_range=(0, 0), samples_per_read=samples, host='localhost', units='mV')
    dev.rate = emgrate
    dev.start()
#    if s.bind(("127.0.0.1", 5555)) == -1:
#        print("The binding did not work")

    def LE(f, hpf, lpf, hpn, lpn, fs):
        """
        This function will calculate the linear envelope of the EMG signal. 
        For this, only butterworth filters are used.

        Parameters: 
        f: EMG signal
        hpf: Cutoff frequency in Hz for the high pass filter
        lpf: Cutoff frequency in Hz for the low pass filter
        hpn: order of the high pass butterworth filter
        lpn: order of the low pass butterworth filter
        fs: sampling frequency of the signal

        Output: 
        
        sle: linear envelope of the EMG signal. With the same shape as the 
        """

        global a, b, c, d

        nyq = fs/2
        hpfn = hpf/nyq
        lpfn = lpf/nyq

        b, a = signal.butter(hpn, hpfn, btype='highpass', analog=False, output='ba' )
        f = signal.filtfilt(b, a, f)

        f = np.absolute(f)

        d, c = signal.butter(lpn, lpfn, btype='lowpass', analog=False, output='ba' )
        sle = signal.filtfilt(d, c, f)

        return sle

    def fatigue(v, t):

        global Cf, norm

        return (1-v)*(norm.max()/Cf)


    def recov(v, t):

        global Cf

        R = 0.5
        return -v*(R/Cf)


    def update():
        global p, l, f, s, norm, v, MVC, vo, Ath, timestep, samples, emgrate, KUKA_IP, KUKA_PORT

        
        t = np.arange(0,((samples*(1/emgrate))) , 1/emgrate)
#        timestep = t[len(t)-1] + (1/emgrate)
        
#        fp = f
#        fd = np.full(len(t), 10.0)
#        p.trace("Fd", t, fd)
#        f, address = s.recvfrom(1024)
        f = dev.read()
        assert f.shape == (1, samples)
#        f = struct.unpack('d', f)
        
#        print(f)
#        c = np.full(len(t), f)
        f = f.T
        s = f.reshape(samples,)
        p.trace("EMG", t, s)

        l = LE(s, 20, 50, 6, 4, emgrate)
        p.trace("LE", t, l)
 
        norm = l/MVC
        p.trace("A", t, norm)

        if(norm.max()>= Ath):
            v = odeint(fatigue,vo,t)
            v = v.reshape(samples,)
            p.trace("V", t, v)
            vo = v[len(v)-1]
        elif(norm.max()<Ath):
            v = odeint(recov,vo,t)
            v = v.reshape(samples,)
            p.trace("V", t, v)
            vo = v[len(v)-1]
        fat = np.sum(v)/samples;
        sfat = str(fat)
        sock.sendto(sfat.encode('ascii'), (KUKA_IP, KUKA_PORT))
        
        


       
        
        

    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start()
    p.start()
    
