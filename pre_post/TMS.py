# -*- coding: utf-8 -*-
'''
Created on Thu Feb  6 08:51:45 2020

@author: Ethan

Turn on MagStim and and open Localite
Start Localite Flow on control computer

Setting Single, SICI, or ICF:
    Select N, press Recall
    Select S, press Recall, press Timing, select External Trigger
    Select F, press Recall, press Timing, select External Trigger

Markers:
    tms_start
    'sici_start'
    sici_triggered_RMT
    'sici_end'

    'icf_start'
    icf_triggered_RMT
    'icf_end'

    'cse_100_start'
    cse_100_triggered_RMT
    cse_100_triggered_RMTx1.2
    'cse_100_end'

    'cse_120_start'
    cse_120_triggered_RMT
    cse_120_triggered_RMTx1.2
    'cse_120_end'

    tms_end

'''
import liesl
import time
import reiz
from reiz.visual import Mural, Background
from reiz.marker import push
from matplotlib import pyplot as plt
import numpy as np
from scipy import stats

def plotter():
    fig, axes = plt.plot()
    fig, axes = plt.subplots()
#    fig.canvas.manager.window.move(-1280, 20)
    fig.canvas.manager.window.resize(1280, 1024)
    return fig, axes

def mep_plot(axes, data, edc_r, sequence):
    axes.cla()
    data    = stats.zscore(data)
    peakpos = [data.argmin(), data.argmax()]
    val     = [data.min(), data.max()]
    vpp     = val[1] - val[0]
    wndw    = [np.min(peakpos) - 50, np.max(peakpos) + 50]
    timey   = np.arange(0, len(data), 1)

    axes.plot(timey[wndw[0] : wndw[1]], data[wndw[0] : wndw[1]])
    axes.vlines(
        [timey[peakpos[0]]], val[0], np.mean(data), color="red", linestyle="dashed")
    axes.vlines(
        [timey[peakpos[1]]], val[1], np.mean(data), color="red", linestyle="dashed")
    axes.set_title(str(sequence) + " MEP")

    textstr = "Vpp = {0:3.2f}".format(vpp)
    props   = dict(boxstyle="round", facecolor="wheat", alpha=0.5)

    axes.text(
        0.05,
        0.95,
        textstr,
        transform=axes.transAxes,
        fontsize=14,
        verticalalignment="top",
        bbox=props)
    plt.pause(0.05)

def countdown(canvas, sek):
    for i in range(0, sek):
        cue = reiz.Cue(canvas, visualstim=Mural(text=str(sek - i), color=(0.18, 0.18, 0.18)))
        cue.show(duration=1)

def tms_protocol(canvas, bg, coil, trials, tms_cue, sleep_duration, sequence, rmt, buffer, edc_r):
    fig, axes = plotter()
    push(str(sequence) + '_start_' + str(rmt))
    time.sleep(0.01)
    reiz.Cue(canvas, visualstim=[bg, reiz.visual.Mural(str(sequence) + ': ' + tms_cue , fontsize=1)]).show(10)
    canvas.start_run = False
    start_protocol = reiz.Cue(
        canvas, visualstim=[bg, Mural(text='Activate coil', position=[0, 0.25]), Mural(text='Press F5 to start: ' + str(sequence))])
    while not canvas.start_run:
        start_protocol.show(duration=0.1)
    countdown(canvas, 5)
    coil.amplitude = rmt
    time.sleep(0.01)

    for trial_ind in range(trials):
        if trial_ind > 0:
            time.sleep(sleep_duration)
        push(str(sequence) + '_' + str(trial_ind))
        coil.trigger()
        time.sleep(0.2)
        data = buffer.get_data()[:, edc_r]
        mep_plot(axes, data, edc_r, sequence)

    push(str(sequence) + '_end')

def tms_sequence(canvas, coil, cfg, sequence='sici'):

    rmt            = int(cfg['TMS']['rmt'])
    trials         = 10
    sleep_duration = 4
    bg             = Background(color='gray')
    edc_r          = int(cfg['H_reflex']['edc_r'])
    duration       = 0.5
    sinfo          = liesl.get_streaminfos_matching(type="EEG")[0]
    buffer         = liesl.RingBuffer(sinfo, duration_in_ms=duration * 1000)
    buffer.start()

    if sequence == 'sici':
        tms_cue = ' S>Recall>Timing>Ext Trig'
        tms_protocol(canvas, bg, coil, trials, tms_cue, sleep_duration, sequence, rmt, buffer, edc_r)
    elif sequence == 'icf':
        tms_cue = ' F>Recall>Timing>Ext Trig'
        tms_protocol(canvas, bg, coil, trials, tms_cue, sleep_duration, sequence, rmt, buffer, edc_r)
    elif sequence == 'cse_100':
        tms_cue = ' N>Recall'
        tms_protocol(canvas, bg, coil, trials, tms_cue, sleep_duration, sequence, rmt, buffer, edc_r)
    elif sequence == 'cse_120':
        tms_cue = ' N>Recall'
        rmt = rmt*1.2
        tms_protocol(canvas, bg, coil, trials, tms_cue, sleep_duration, sequence, rmt, buffer, edc_r)
















