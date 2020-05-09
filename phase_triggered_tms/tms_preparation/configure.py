# -*- coding: utf-8 -*-
"""
Created on Mon May 20 18:07:24 2019

@author: AGNPT-M-001
"""

# %%
import liesl
from dataclasses import dataclass
from phase_triggered_tms.tms_preparation.tools import eeg_channels
import localite.api
from luckyloop.client import LuckyClient
import pylsl

@dataclass
class Environment():
    coil = None #:localite.Coil(host="134.2.117.173")
    marker = None #:liesl.open_streams(type='Markers',
               #                 name="BrainVision RDA Markers",
               #                 hostname='Patrick')[0]
    bvr = None #:liesl.open_streams(type='EEG',
              #               name="BrainVision RDA",
              #               hostname='Patrick')[0]
    lucky = None

    buffer = None #:liesl.RingBuffer(bvr, duration_in_ms=2000)

    def setup(self):
        self.buffer.start()
        labels = liesl.get_channel_map(pylsl.StreamInlet(self.bvr))
        self.labels = list(labels.keys())
        self.emg_labels = [l for l in self.labels if l not in eeg_channels()]
        self.eeg_labels = [l for l in self.labels if l in eeg_channels()]