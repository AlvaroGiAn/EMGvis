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
        self.canvas.setYRange(-11, 11, padding=0)
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


        else:
            self.traces[name] = self.canvas.plot(pen='y', fillLevel=20.0, fillOutline=True, name="EMG Biceps")


# Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    p = Plot2D()
#    i = 0
#    f = np.zeros((1,270),dtype=float)
#    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#    s.setblocking(0)
    dev = pytrigno.TrignoEMG(channel_range=(0, 0), samples_per_read=300, host='localhost', units='mV')
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



    def update():
        global p, l, f, s

        
        t = np.arange(0,300,1)
#        fp = f
#        fd = np.full(len(t), 10.0)
#        p.trace("Fd", t, fd)
#        f, address = s.recvfrom(1024)
        f = dev.read()
        assert f.shape == (1, 300)
#        f = struct.unpack('d', f)
        
#        print(f)
#        c = np.full(len(t), f)
        f = f.T
        s = f.reshape(300,)
        p.trace("EMG", t, s)

        l = LE(s, 20, 50, 6, 4, 2000)
        p.trace("LE", t, l)
 #       if i == 100:
 #           p.trace("Fd", t, fd)
 #           p.trace("F", t, c)
 #           i = 0

#        i += 1

    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start()
    p.start()