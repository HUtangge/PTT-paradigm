# -*- coding: utf-8 -*-
"""
Created on Tue Mar 10 09:28:37 2020

@author: Ethan
"""
from liesl.files.session import Session
from stg.api import STG4000
from PyQt5 import QtWidgets
from phase_triggered_tms.pre_post.hwave import test_stimulation
import sys
from functools import partial
from reiz.marker import push
import time
from scipy import stats
import numpy as np
import liesl
import configparser
import matplotlib
from matplotlib.backends.qt_compat import is_pyqt5
from liesl.buffers.response import Response

#%%
if is_pyqt5():
    from matplotlib.backends.backend_qt5agg import (
        FigureCanvas,
        NavigationToolbar2QT as NavigationToolbar,
    )
else:
    from matplotlib.backends.backend_qt4agg import (
        FigureCanvas,
        NavigationToolbar2QT as NavigationToolbar,
    )

# Ensure using PyQt5 backend
matplotlib.use("QT5Agg")

def on_close():
   print("Shutting down")

def create_stimulation_signal(intensity):
    amplitudes_in_mA = [intensity / 1000]
    durations_in_ms = [float("1")]
    return amplitudes_in_mA, durations_in_ms

class Ui(QtWidgets.QMainWindow, test_stimulation.Ui_MainWindow):
    def __init__(self, parent=None):
        super(Ui, self).__init__(parent)
        self.setupUi(self)
        self.show()

        self.FDS_R = int(cfg["H_reflex"]["fds_r"])
        sinfo = liesl.get_streaminfos_matching(type="EEG")[0]
        self.buffer = liesl.RingBuffer(sinfo, duration_in_ms=500)
        self.buffer.start()
        self.buffer.await_running()
        time.sleep(1)

        self.addToolBar(NavigationToolbar(self.MplWidget.canvas, self))

        self.download()
        self.intensity_minus_1000.clicked.connect(
            partial(self.decrease_intensity, 1000))
        self.intensity_plus_1000.clicked.connect(partial(self.increase_intensity, 1000))
        self.intensity_minus_100.clicked.connect(partial(self.decrease_intensity, 100))
        self.intensity_plus_100.clicked.connect(partial(self.increase_intensity, 100))
        self.trigger.clicked.connect(self.start_stimulation)
        push("hreflex_start")

    def plot_hreflex(self, onset_in_ms: int):
        chunk, tstamps = self.buffer.get()[:, self.FDS_R]
        response = Response(chunk = chunk,
                    tstamps = tstamps,
                    fs = self.buffer.fs,
                    onset_in_ms = onset_in_ms,
                    post_in_ms = 250)
        xticks, xticklabels, xlim = response.get_xaxis(stepsize=25)
        trace = response.get_trace(channel_idx = self.FDS_R, baseline_correction = True)
        vpp = response.get_vpp(channel_idx = self.FDS_R)

        # discards the old graph
        self.MplWidget.canvas.axes.clear()

        # plot data
        self.MplWidget.canvas.axes.plot(trace)

        for pos, val in zip(response.peakpos_in_ms, response.peakval):            
            self.MplWidget.canvas.axes.vlines(
                [pos], val, 0, color="red", linestyle="dashed")
        
        self.MplWidget.canvas.axes.vlines([onset_in_ms], 0, 1,                                           transform=self.MplWidget.canvas.axes.get_xaxis_transform(), colors='r')
        textstr = 'Vpp = {0:3.2f}'.format(vpp)
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)        
        self.MplWidget.canvas.axes.text(
            0.05,
            0.95,
            textstr,
            transform=self.MplWidget.canvas.axes.transAxes,
            fontsize=14,
            verticalalignment="top",
            bbox=props)
        self.MplWidget.canvas.axes.set_title('H_reflex')
        self.MplWidget.canvas.axes.set_xticks(xticks)
        self.MplWidget.canvas.axes.set_xlim(xlim)
        self.MplWidget.canvas.axes.set_xticklabels(xticklabels)
        time.sleep(0.01)
        # refresh canvas
        self.MplWidget.canvas.draw()
        
    def download(self):
        self.cur = int(self.intensity_label.text())
        amplitudes_in_mA, durations_in_ms = create_stimulation_signal(self.cur)
        self.mcs.download(0, amplitudes_in_mA, durations_in_ms)

    def increase_intensity(self, factor=20):
        cur = int(self.intensity_label.text())
        cur += factor
        if cur > 16000:
            cur = 0
        self.intensity_label.setText(str(cur))
        self.download()

    def decrease_intensity(self, factor=20):
        cur = int(self.intensity_label.text())
        cur -= factor
        if cur < 0:
            cur = 16000
        self.intensity_label.setText(str(cur))
        self.download()

    def start_stimulation(self):
        push("h_reflex_stim_" + str(self.cur / 1000))
        self.mcs.start_stimulation()
        time.sleep(0.25)
        self.plot_hreflex()

    @property
    def mcs(self):
        if not hasattr(self, "_mcs"):
            mcs = None
            while mcs is None:
                try:
                    mcs = STG4000()
                except IndexError:  # no STG connected
                    self.error_missing_stg()
            self._mcs = mcs
            self.setWindowTitle("Selected " + str(self.mcs))
        return self._mcs

    def execute_right_click(self):
        try:
            amount = int(self.rc_amount.text())
        except ValueError:
            amount = 1000
        if self.rc_dec.isChecked():
            self.decrease_intensity(amount)
        elif self.rc_inc.isChecked():
            self.increase_intensity(amount)

    def mousePressEvent(self, QMouseEvent):
        button = ["left", "right"][QMouseEvent.button() - 1]
        if button == "right":
            self.execute_right_click()

    def closeEvent(self, event):
        push("hreflex_end")
        session.stop_recording()
        app.aboutToQuit.connect(on_close)

# %%
import reiz
reiz.marker.start()
        
if __name__ == "__main__":
    cfg = configparser.ConfigParser()
    cfg.read("/Users/getang/study-phase-triggered-TMS/cfg.ini")
    with open("/Users/getang/study-phase-triggered-TMS/cfg.ini", "w",) as configfile:
        cfg.write(configfile)
    streamargs = [{'name':"eego"}, 
                  {'name':'reiz-marker'}, 
                  {'name':'GDX-RB_0K2002A1'}, 
                  {'name':'localite_marker'}, 
                  {'name':'pupil_capture'}]
    session = Session(prefix=cfg['general']['subject_token'], 
                      streamargs=streamargs)
    time.sleep(0.01)

    with session('h_reflex'):
        app = QtWidgets.QApplication(sys.argv)
        window = Ui()
        window.show()
        app.exec_()
