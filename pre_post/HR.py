# -*- coding: utf-8 -*-
"""
Created on Mon Jan 27 09:02:40 2020

@author: Ethan


H-Reflex test for flexors and extensors

please note that currently plotting is not locked to stimulation onset,
but rather the plot grabs the min and max values, shown as vertical red lines,
and gives back a window of -100 and +100 points to display
***This may result in the plotting of m-waves rather than h-waves.

Markers:
    hreflex_start
    radial_search_1.0
    radial_test_
    hreflex_end

"""

import numpy as np
from stg.api import PulseFile, STG4000
import liesl
import time
from matplotlib import pyplot as plt
import reiz
from reiz.visual import Mural, Background
from scipy import stats



def countdown(canvas, sek):
    for i in range(0, sek):
        cue = reiz.Cue(canvas, visualstim=Mural(text=str(sek - i), color=(0.18, 0.18, 0.18)))
        cue.show(duration=1)


def plotter():
    fig, axes = plt.subplots(1, 2, sharex=False)
#    fig.canvas.manager.window.move(-1280, 20)
    fig.canvas.manager.window.resize(1280, 1024)
    fig.tight_layout()
    return fig, axes

def plot_hreflex(axes, buffer, EDC_R):
    axes[0].cla()

    data    = buffer.get_data()[:, EDC_R]
    data    = stats.zscore(data)
    peakpos = [data.argmin(), data.argmax()]
    val     = [data.min(), data.max()]
    vpp     = val[1] - val[0]
    wndw    = [np.min(peakpos) - 200, np.max(peakpos) + 200]
    timey   = np.arange(0, len(data), 1)

    axes[0].plot(timey[wndw[0] : wndw[1]], data[wndw[0] : wndw[1]])
    axes[0].vlines(
        [timey[peakpos[0]]], val[0], np.mean(data), color="red", linestyle="dashed")
    axes[0].vlines(
        [timey[peakpos[1]]], val[1], np.mean(data), color="red", linestyle="dashed")

    textstr = "Vpp = {0:3.2f}".format(vpp)
    props   = dict(boxstyle="round", facecolor="wheat", alpha=0.5)

    axes[0].text(
        0.05,
        0.95,
        textstr,
        transform=axes[0].transAxes,
        fontsize=14,
        verticalalignment="top",
        bbox=props)
    time.sleep(0.1)


def vpp_curve(trial, axes, amp, pamps, vpp, vpp_out):
    vpp = np.append(vpp, vpp_out)
    pamps = np.append(pamps, amp)
    axes[1].plot(amp, vpp, "ro", "-")
    axes[1].set_title("Vpp curve, test: " + str(trial + 1))
    for i, txt in enumerate(pamps):
        axes[1].annotate(txt, (pamps[i], vpp[i]), size="xx-large")


def radial_hs(stg, buffer, canvas, bg, hs_amps, hdurs, EDC_R):

    vpp = []
    pamps = []

    # Radial nerve hotspot search
    canvas.start_run = False
    fig, axes        = plotter()


    vpp_out = h_reflex(stg, axes, buffer, EDC_R, hs_amps, hdurs)
    vpp_curve(axes, hs_amps, pamps, vpp, vpp_out)
    reiz.marker.push("radial_search_ %f" % float(hs_amps[0]))
    plt.pause(0.1)

    endcue = reiz.Cue(canvas, visualstim=[bg, Mural(text="End of radial nerve hotspot search", color=(0.18, 0.18, 0.18))])
    endcue.show(3)
    plt.close()


def radial_test(stg, buffer, canvas, bg, stim_intensities, hdurs, EDC_R):

    vpp   = []
    pamps = []

    canvas.start_run = False
    fig, axes        = plotter()
    start_test       = reiz.Cue(
        canvas, visualstim=[bg, Mural(text="Press F5 to test radial nerve", color=(0.18, 0.18, 0.18))])
    while not canvas.start_run:
        start_test.show(duration=0.1)
    countdown(canvas, 3)

    for trial, amp in enumerate(stim_intensities):

        vpp_out = h_reflex(trial, stg, axes, buffer, EDC_R, [amp], hdurs)
        vpp_curve(trial, axes, [amp], pamps, vpp, vpp_out)
        intensity = "{:.1f}".format(amp)
        reiz.marker.push("radial_test_" + intensity)
        reiz.Cue(canvas, visualstim=[bg, Mural(text="Radial nerve test with: " + intensity + " mA", color=(0.18, 0.18, 0.18))]).show()

        plt.pause(0.1)
        time.sleep(5)

    endcue = reiz.Cue(canvas, visualstim=[bg, Mural(text="End of radial nerve testing", color=(0.18, 0.18, 0.18))])
    endcue.show(3)


def h_reflex_main(canvas, cfg):

    EDC_R      = int(cfg['H_reflex']['edc_r'])
    hs_amps    = [float(cfg['H_reflex']['hs_amps'])]
    stim_range = [float('{:1.2f}'.format(x)) for x in np.arange(0.1, 2.9, 0.3)]
    bg         = Background(color='gray')
    # --------------
    duration = 0.5
    sinfo = liesl.get_streaminfos_matching(type="EEG")[0]
    buffer = liesl.RingBuffer(sinfo, duration_in_ms=duration * 1000)
    buffer.start()
    buffer.await_running()

    stg = STG4000()  # throws error if stimulator is off
    time.sleep(0.01)
    pf = PulseFile(
        intensity_in_mA=stim_range,
        mode="monophasic",
        pulsewidth_in_ms=1,  # durations,
        burstcount=1,
        isi_in_ms=49,)

    hamps, hdurs = pf.compile()

    # ----------------
    # run testing

    reiz.marker.push("hreflex_start")

    radial_hs(buffer, canvas, bg, EDC_R)

    # run test once
    reiz.Cue(canvas, visualstim=[bg, Mural(text="Radial Testing", color=(0.18, 0.18, 0.18))]).show(duration=3)
    radial_test(stg, buffer, canvas, stim_range, hdurs, EDC_R)

    reiz.Cue(canvas, visualstim=[bg, Mural(text="H-Reflex Finished", color=(0.18, 0.18, 0.18))]).show(duration=3)

    reiz.marker.push("hreflex_end")

    def on_close():
        print("Shutting down")

    app.aboutToQuit.connect(on_close)
