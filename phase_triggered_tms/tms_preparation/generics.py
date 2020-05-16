# -*- coding: utf-8 -*-
"""
Created on Mon May 20 17:40:27 2019

@author: AGNPT-M-001
"""


import matplotlib.pyplot as plt
import time
import random
import reiz
from reiz.audio import Message
from collections import defaultdict
from localite.api import Coil
from typing import NewType, Union
from liesl import RingBuffer
from liesl.buffers.response import Response
from pylsl import StreamInlet, FOREVER
from socket import timeout as TimeOutException
DataRingBuffer = NewType("DataRingBuffer", RingBuffer)
MarkerStreamInlet = NewType("MarkerStreamInlet", StreamInlet)
Seconds = Union[int,float]
import logging
import json
from scipy import stats
logger = logging.getLogger(name='__file__')

# %%
def auto_trigger(coil:Coil,
                 lucky,
                 marker:MarkerStreamInlet,
                 buffer:DataRingBuffer,
                 timeout:Seconds=1):
    """Expect the TMS to be triggered manually
    We wait a certain time for the  response to arrive. If this time has passed,
    we trigger again, assuming that somehow the TCP-IP command was lost in
    transition.
    """
    print('auto trigger')
    marker.pull_chunk() #flush the buffer to be sure we catch the latest sample
    # lucky.trigger_now() #trigger the coil
    lucky.trigger()
    _, onset_in_ms = marker.pull_sample()
    try:
        response = wait_for_trigger(coil, marker, buffer, onset_in_ms,  timeout) #wait for the response
        print('auto trigger finished')
    except TimeOutException:
        logger.warning("Timeout,. repeating command to stimulate")
        response = auto_trigger(coil, lucky, marker, buffer, timeout)
    return response

def manual_trigger(coil:Coil,
                 marker:MarkerStreamInlet,
                 buffer:DataRingBuffer):
    """Expect the TMS to be triggered manually

    We therefore also wait forever for the  response to arrive. If examiner
    becomes inpatient as the trigger was swallowed, a manual repetition is
    necessary
    """
    print('manual trigger')
    marker.pull_chunk() #flush the buffer to be sure we catch the latest sample
    while True:
        marker.pull_chunk()
        didt_catch, onset_in_ms = marker.pull_sample()
        if didt_catch[0][9:13] == 'didt':
           break
    # wait  forever for the response, because
    response = wait_for_trigger(coil, marker, buffer, onset_in_ms, timeout=FOREVER)
    return response

def wait_for_trigger(coil:Coil,
                    marker:MarkerStreamInlet,
                    buffer:DataRingBuffer,
                    onset_in_ms,
                    timeout:Seconds=1):
    print('wait for triger')
    # pull the timestamp of the TMS pulse
    # pull_sample is blocking, so this waits until a trigger was received
    if onset_in_ms is None:
        raise TimeOutException(f"Waited {timeout} seconds for TMS pulse to arrive")
    chunk, tstamps = buffer.get()

    # wait a little bit longer to catch enough data around the TMS pulse
    print('[', end='')
    while tstamps[-1] < onset_in_ms +.25:
        print('.', end='')
        chunk, tstamps = buffer.get()
        time.sleep(0.05)
    print(']')
    chunk = chunk*1e6
    # create and return the response
    response = Response(chunk=chunk,
                        tstamps=tstamps,
                        fs=buffer.fs,
                        onset_in_ms=onset_in_ms,
                        post_in_ms = 100)
    return response

def create_marker(response, coil, emg_labels, labels, amplitude):
    position = coil.position
    Vpp= {}
    for idx, lbl in enumerate(emg_labels):
        vpp = response.get_vpp(channel_idx=63+idx)
        Vpp[lbl] = vpp

    if position is None:
        response_marker = {'amplitude':amplitude, 'x':None, 'y': None, 'z':None, **Vpp}
    else:
        response_marker = {'amplitude':amplitude, **position, **Vpp}

    return response_marker

def find_highest(collection, channel='EDC_L'):
    vals = [r[channel] for r in collection]
    shuffler = list(reversed(sorted(range(len(vals)),key=vals.__getitem__)))
    amps = [vals[s] for s in shuffler]
    pos = [(collection[s]['x'], collection[s]['y'], collection[s]['z']) for s in shuffler]
    return amps, pos, shuffler

# %% init messages
entamp = Message('Enter an amplitude and confirm')
ready = Message('ready')
run_ended = Message('run ended')
auto_start_reminder = Message('Run will started after 5 seconds')

#%%
def search_hotspot(trials=40, isi=(3.5,4.5),
                   task_description='Start Hotspot Search',
                   env=None,
                   run_automatic:bool=False):
    print(__file__)
    labels = env.labels
    emg_labels = env.emg_labels
    coil, marker, buffer, lucky = env.coil, env.marker, env.buffer, env.lucky
    task = Message(task_description)
    time.sleep(0.1)


    plt.close('all')
    def create_hotspot_canvas(emg_labels):
        nr, nc = 2, len(emg_labels)//2
        if len(emg_labels)%2: #uneven
            nc += 1
        fig, axes = plt.subplots(nrows=nr, ncols = nc, sharex=True, sharey=True)
        fig.canvas.manager.window.move(-1280, 20)
        fig.canvas.manager.window.resize(1280, 1024)
        fig.tight_layout()
        return fig, axes

    fig, axes = create_hotspot_canvas(emg_labels)
    def show(response, axes, emg_labels, labels):
        xticks, xticklabels, xlim = response.get_xaxis(stepsize=25)
        for ax, lbl in zip(axes.flatten(), emg_labels):
            ax.cla()
            trace = response.get_trace(channel_idx=labels.index(lbl))
            vpp = response.get_vpp(channel_idx=labels.index(lbl))
            ax.plot(trace)
            for pos, val in zip(response.peakpos_in_ms, response.peakval):
                ax.plot([pos, pos],[0, val], color='red', linestyle=':')
            #TG: for test temporary change scale to [-1 1]
            ax.axvline(x = response.pre_in_ms, color = 'red')
            textstr = 'Vpp = {0:3.2f}'.format(vpp)
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
                    verticalalignment='top', bbox=props)
            ax.set_title(lbl)
            ax.set_xticks(xticks)
            ax.set_xlim(xlim)
            ax.set_xticklabels(xticklabels)
        plt.show()
    task.play_blocking()

    if coil.amplitude == 0:
        entamp.play_blocking()
        response = manual_trigger(coil, marker, buffer)
        #coil.amplitude = amplitude
        amplitude = coil.amplitude
        amplitude = coil.amplitude
    else:
        amplitude = coil.amplitude
        amplitude = coil.amplitude

    counter = 0
    collection = []
    automatic = False
    has_started = False
    while counter < trials:
        if run_automatic or automatic:
            print('Automatic trigger')
            if counter == 0:
                coil.amplitude = 0
                manual_trigger(coil, marker, buffer)
                coil.amplitude = amplitude
            time.sleep(isi[0]+ (random.random()*(isi[1]-isi[0])))
            response = auto_trigger(coil, lucky, marker, buffer)
            print('go to next auto trigger')
        else:
            print('Waiting for manual trigger')
            if not has_started:
                ready.play_blocking()
                has_started = True
            response = manual_trigger(coil, marker, buffer)
            if run_automatic:
                automatic = True

        response_marker = create_marker(response, coil, emg_labels, labels, amplitude)
        coil_message = json.loads(response.as_json(channel_idx=labels.index(env.channel_of_interest)))
        print('before push')
        coil.set_response(mepmaxtime = coil_message['mepmaxtime'],
                          mepamplitude = coil_message['mepamplitude'],
                          mepmin = coil_message['mepmin'],
                          mepmax = coil_message['mepmax'])
        coil.push_marker(json.dumps(response_marker))
        show(response, axes, emg_labels, labels)
        props = dict(boxstyle='round', facecolor='white', alpha=1)
        counter  += 1
        print(f'this is the {counter} trial')
        ax = axes[0,0]
        ax.text(-.15, 1.05, f'{counter} of {trials}', transform=ax.transAxes, fontsize=14,
                verticalalignment='top', bbox=props)
        collection.append(response_marker)
        plt.pause(0.05)

    run_ended.play_blocking()
    time.sleep(2)
    return collection
# %%
def measure_rmt(channel='EDC_L',  threshold_in_uv=50,
                max_trials_per_amplitude=10, isi=(3.5,4.5),
                task_description = 'Start resting motor threshold',
                env=None):

    labels = env.labels
    coil, marker, buffer, lucky = env.coil, env.marker, env.buffer, env.lucky
    task = Message(task_description)

    plt.close('all')
    def create_rmt_canvas():
        fig, axes = plt.subplots(1,1)
        fig.canvas.manager.window.move(-1280, 20)
        fig.canvas.manager.window.resize(1280, 1024)
        fig.tight_layout()
        return fig, axes

    fig, ax = create_rmt_canvas()
    def show(response, labels):
        ax.cla()
        trace = response.get_trace(channel_idx=labels.index(channel))
        vpp = response.get_vpp(channel_idx=labels.index(channel))
        ax.plot(trace)
        #TG: for test temporary change scale to [-1 1]
        ax.plot([response.pre_in_ms, response.pre_in_ms],[-100, 100], color='red')
        for pos, val in zip(response.peakpos_in_ms, response.peakval):
            ax.plot([pos, pos],[0, val], color='red', linestyle=':')
        textstr = 'Vpp = {0:3.2f}'.format(vpp)
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
            verticalalignment='top', bbox=props)
        ax.set_title(channel)
        xticks, xticklabels, xlim = response.get_xaxis()
        ax.set_xticks(xticks)
        ax.set_xlim(xlim)
        ax.set_xticklabels(xticklabels)

    task.play_blocking()

    if coil.amplitude == 0:
        entamp.play_blocking()
        response = manual_trigger(coil, marker, buffer)
        #coil.amplitude = amplitude
        amplitude = coil.amplitude
        amplitude = coil.amplitude
    else:
        amplitude = coil.amplitude
        amplitude = coil.amplitude

    amplitude_response = defaultdict(list)
    automatic = False
    while True:
        if not automatic:
            ready.play_blocking()
            response = manual_trigger(coil, marker, buffer)
            automatic = True
            amplitude_count = True
        else:
            time.sleep(isi[0]+ (random.random()*(isi[1]-isi[0])))
            response = auto_trigger(coil, lucky, marker, buffer)
            amplitude_count = False

        if amplitude_count:
            amplitude = coil.amplitude
            amplitude = coil.amplitude
            trial_amplitude = amplitude
        else:
            amplitude = trial_amplitude

        if amplitude == 0:
            break

        # show and save result
        coil_message = json.loads(response.as_json(channel_idx=labels.index(channel)))
        coil.set_response(mepmaxtime = coil_message['mepmaxtime'],
                          mepamplitude = coil_message['mepamplitude'],
                          mepmin = coil_message['mepmin'],
                          mepmax = coil_message['mepmax'])
        vpp = response.get_vpp(labels.index(channel))
        amplitude_response[amplitude].append(vpp)
        show(response, labels)
        count = len(amplitude_response[amplitude])
        props = dict(boxstyle='round', facecolor='white', alpha=1)
        ax.text(-.025, 1, f'#{count} at {amplitude}%', transform=ax.transAxes, fontsize=14,
                verticalalignment='top', bbox=props)
        # analyse results
        vals = amplitude_response[amplitude]
        above = [v>=threshold_in_uv for v in vals]
        cut_off = (max_trials_per_amplitude//2)
        above_rmt = sum(above) > cut_off
        below_rmt = sum([not a for a in above]) > cut_off

        plt.pause(0.5)
        # when more than max_trials, or any has sufficient counts, the state is reset
        # to start_confirmed, and requires manual setting
        if above_rmt or below_rmt: #also evaluates true if more than max_trials
            percent = sum(above)/len(above)
            perccue = Message('{0} creates {1:2.0f} percent'.format(amplitude, percent*100))
            perccue.play_blocking()
            automatic = False
        elif len(above) == max_trials_per_amplitude: #that means 50/50
            perfcue = Message('{0} is perfect'.format(amplitude))
            perfcue.play_blocking()
            automatic = False
        for key in sorted(amplitude_response.keys()):
            vals = amplitude_response[key]
            print('{0} -> {1:3.2f} ({2})'.format(key, sum(vals)/len(vals), vals))
        coil.amplitude = amplitude

    run_ended.play_blocking()
    time.sleep(2)
    return amplitude_response

#%%
def free_mode(trials=40, isi=(3.5,4.5), channel='chan_13',
              task_description='Start free Modes',
              env=None):

    labels = env.labels
    coil, marker, buffer, lucky = env.coil, env.marker, env.buffer, env.lucky
    task = Message(task_description)

    plt.close('all')
    def create_canvas():
        fig, axes = plt.subplots(1,1)
        fig.canvas.manager.window.move(-1280, 20)
        fig.canvas.manager.window.resize(1280, 1024)
        fig.tight_layout()
        return fig, axes

    fig, ax = create_canvas()
    def show(response, labels):
        ax.cla()
        trace = response.get_trace(channel_idx=labels.index(channel))
        vpp = response.get_vpp(channel_idx=labels.index(channel))
        ax.plot(trace)
        ax.plot([response.pre_in_ms, response.pre_in_ms],[-100, 100], color='red')
        for pos, val in zip(response.peakpos_in_ms, response.peakval):
            ax.plot([pos, pos],[0, val], color='red', linestyle=':')

        textstr = 'Vpp = {0:3.2f}'.format(vpp)
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
        ax.text(0.05, 0.95, textstr, transform=ax.transAxes, fontsize=14,
            verticalalignment='top', bbox=props)
        ax.set_title(channel)
        xticks, xticklabels, xlim = response.get_xaxis()
        ax.set_xticks(xticks)
        ax.set_xlim(xlim)
        ax.set_xticklabels(xticklabels)

    task.play_blocking()

    if coil.amplitude == 0:
        entamp.play_blocking()
        response = manual_trigger(coil, marker, buffer)
        #coil.amplitude = amplitude
        amplitude = coil.amplitude
        amplitude = coil.amplitude
    else:
        amplitude = coil.amplitude
        amplitude = coil.amplitude

    counter = 0
    amplitude_response = defaultdict(list)
    automatic = False
    while counter < trials:
        if not automatic:
            ready.play_blocking()
            response = manual_trigger(coil, marker, buffer)
            automatic = True
            amplitude_count = True
        else:
            time.sleep(isi[0]+ (random.random()*(isi[1]-isi[0])))
            response = auto_trigger(coil, lucky, marker, buffer)
            amplitude_count = False

        if amplitude_count:
            amplitude = coil.amplitude
            amplitude = coil.amplitude
            trial_amplitude = amplitude
        else:
            amplitude = trial_amplitude

        # show and save result
        coil_message = json.loads(response.as_json(channel_idx=labels.index(channel)))
        coil.set_response(mepmaxtime = coil_message['mepmaxtime'],
                          mepamplitude = coil_message['mepamplitude'],
                          mepmin = coil_message['mepmin'],
                          mepmax = coil_message['mepmax'])
        vpp = response.get_vpp(labels.index(channel))
        amplitude_response[amplitude].append(vpp)
        show(response, labels)
        props = dict(boxstyle='round', facecolor='white', alpha=1)
        counter  += 1
        print(f'this is the {counter} trial')
        ax.text(-.025, 1, f'{counter} of {trials}', transform=ax.transAxes, fontsize=14,
                verticalalignment='top', bbox=props)
        plt.pause(0.05)
        coil.amplitude = amplitude
    run_ended.play_blocking()
    time.sleep(2)

#%% TG: test coil trigger
def test():
    import arduino.onebnc
    import time
    from localite.api import Coil
    import reiz
    coil = Coil(0)
    a = arduino.onebnc.Arduino()
    coil = Coil(0)
    coil.amplitude = 50
    delay = []
    delay_coil = []
    for i in range(9):
        print(i)
        start = time.time()
        coil.trigger()
        stop = time.time()
        reiz.marker.push('coil was triggered')
        push_time = time.time()
        time.sleep(4)
        delay_coil.append(push_time - stop)


    for i in range(100):
        print(i)
        time.sleep(1)
        coil.amplitude = amplitude
        amplitude = coil.amplitude
        lucky.trigger()
        print(amplitude)


