# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 08:40:27 2020

@author: Ethan

"""
"""set up the trial information, after running it , Please common it"""
import configparser
from phase_triggered_tms import study_protocol as study
cfg = configparser.ConfigParser()
cfg.read(r"C:\Users\Messung\Desktop\study-phase-triggered-TMS\phase_triggered_tms\cfg.ini")
condition, _ = study.get_condition(cfg)
cfg['general']['condition'] = str([condition])
with open(r"C:\Users\Messung\Desktop\study-phase-triggered-TMS\phase_triggered_tms\cfg.ini", "w",) as configfile:
    cfg.write(configfile)
print('Today is going to measure condition ' + str(condition['index']) + ' for subject ' + cfg['general']['subject_token'])
del cfg, condition

#%%
import re
import time
import reiz
import configparser
from ast import literal_eval
from localite.coil import Coil
from phase_triggered_tms.pre_post import REST, BMI
from phase_triggered_tms.study_protocol import *
import liesl
from liesl.streams import localhostname
from liesl.files.session import Recorder, Session
from slalom.slalom_class import Slalom
#import sys
#sys.path.append(r'C:\Users\Messung\Desktop\study-phase-triggered-TMS\TMS_experiment_preparation')
from phase_triggered_tms.tms_preparation.configure import Environment
from phase_triggered_tms import study_protocol as study
from luckyloop.client import LuckyClient
import arduino.onebnc

# Preparation for the recording
cfg = configparser.ConfigParser()
cfg.read(r"C:\Users\Messung\Desktop\study-phase-triggered-TMS\phase_triggered_tms\cfg.ini")
condition = literal_eval(cfg['general']['condition'])[0]
print(condition)

streamargs = [{'name':"localite_marker"},   # comments: make a real list
              {'name':"reiz-marker"},
              {'name':"eego"},
              #{'name':"LuckyLoop"},
              #{'name':"pupil_capture"},
              #{'name':"GDX-RB_0K2002A1"}
              ]

session = Session(prefix=cfg['general']['subject_token'] + '\\condition_' + str(condition['index']),
                      streamargs=streamargs,
                      mainfolder = cfg['main']['recordings_path'])

#%%

#TODO: currently, the Slalom class assumes that the cfg.ini is in the current working directory, and it will be
#written to it. Also, we will have to specify an outdir, where results will be saved.

#push slalom results to marker server?
#%%
"""
Pre behaviral measurements (around 1 hour)
"""
#%% Resting state (Pre-measurement)
with session("resting_state_pre"):
	REST.start(trials=5)

#%% Slalom calibration (Pre-measurement)
sl = Slalom(cfgpath = r"C:\Users\Messung\Desktop\study-phase-triggered-TMS\phase_triggered_tms\cfg.ini", outdir = cfg['main']['recordings_path'] + '/' + cfg['general']['subject_token'])
with session("slalom_cal_pre"):
    sl.calibrate()

#%% Slalom test (Pre-measurement)
sl = Slalom(cfgpath = r"C:\Users\Messung\Desktop\study-phase-triggered-TMS\phase_triggered_tms\cfg.ini", outdir = cfg['main']['recordings_path'] + '/' + cfg['general']['subject_token'])
with session("slalom_test_pre"):
    sl.test()

#%% Slalom test (Pre-measurement)
sl = Slalom(cfgpath = r"C:\Users\Messung\Desktop\study-phase-triggered-TMS\phase_triggered_tms\cfg.ini", outdir = cfg['main']['recordings_path'] + '/' + cfg['general']['subject_token'])
with session("slalom_pre"):
    sl.run()
    
#%% Brain machine interface (Pre-measurement)
with session("bmi_pre"):
    BMI.bmi_main()

#%%
"""
TMS related physiological measurements preparation
"""
#%% TMS enviroment setup (each time we use TMS, we should restart this part)
env = Environment()
env.coil = Coil(0)
env.marker = liesl.get_streams_matching(name="localite_marker")[0]
env.bvr = liesl.get_streaminfos_matching(name="eego")[0]
env.lucky = arduino.onebnc.Arduino()
# env.lucky = LuckyClient('134.2.117.144')
env.buffer = liesl.RingBuffer(env.bvr, duration_in_ms=2000)
env.channel_of_interest = 'chan_13'
env.setup()
env.emg_labels = env.emg_labels[12:16]

from phase_triggered_tms.tms_preparation.generics import search_hotspot, find_highest
from phase_triggered_tms.tms_preparation.generics import measure_rmt
from phase_triggered_tms.tms_preparation.generics import free_mode

#%% hotspot detection
with session("hotspot-detection"):
    collection = search_hotspot(trials=40, env=env, run_automatic=True)

try:
    amp, pos, sorter  = find_highest(collection, channel=env.channel_of_interest)
    for ix in reversed(sorter):
        print('At the {0}. stimulus the response is {1}'.format(ix+1, collection[ix][env.channel_of_interest]))
except IndexError as e: #aborted run
    raise IndexError('Not enough runs for evaluation' + str(e))

#%% hotspot iteration
with session("hotspot-iteration"):
    collection = []
    for candidate in range(0,3,1):
        candidate_collection = search_hotspot(trials=3, task_description='Change target', env=env)
        collection.extend(candidate_collection)

try:
    amp, pos, sorter  = find_highest(collection, channel=env.channel_of_interest)
    for ix,_ in enumerate(collection):
        print('At the {0}. stimulus the response is {1}'.format(ix+1, collection[ix][env.channel_of_interest]))
except IndexError as e: #aborted run
    raise IndexError('Not enough runs for evaluation' + str(e))

#%% Resting motor threshold
with session("measure-rmt"):
    results = measure_rmt(channel = env.channel_of_interest,  threshold_in_uv=50,
                          max_trials_per_amplitude=10, env=env)

#%%
"""
Pre physiological measurements
"""
#%% SICI (Pre-measurement)
with session('SICI_pre'):
    SICI_collections = search_hotspot(trials=10, task_description='SICI measurement', env=env, run_automatic=True)

#%% ICF (Pre-measurement)
with session('ICF_pre'):
    ICF_collections = search_hotspot(trials=10, task_description='ICF measurement', env=env, run_automatic=True)

#%% CSE_100 (Pre-measurement)
with session('CSE_100_pre'):
    SICI_collections = search_hotspot(trials=10, task_description='CSE measurement', env=env, run_automatic=True)

#%% CSE_120 (Pre-measurement)
with session('CSE_120_pre'):
    SICI_collections = search_hotspot(trials=10, task_description='CSE measurement', env=env, run_automatic=True)

#%%
"""
Main intervention (around 45 minutes)
"""
#%% Intervention (main study)
condition, stim_number = study.get_condition(cfg)
if condition['index'] != literal_eval(cfg['general']['condition'])[0]['index']:
    print('Are you sure? Please re-run')
    protocol_file_name = "protocol.list"
    subject_token = cfg['general']['subject_token']
    subject_folder = f"{cfg['main']['recordings_path']}\\{cfg['general']['subject_token']}\\"
    protocol_path = f"{subject_folder}{protocol_file_name}"
    protocol = load_list(protocol_path)
    protocol.remove(protocol[-1])
    save_list(protocol_path, protocol)
else:
    start_intervention(cfg, condition, stim_number, verbose = True)

#%%
"""
First post physiological measurements
"""
#%% Resting state (Post-measurement)
with session("resting_state_post"):
	REST.start(trials=5)

#%% SICI (Post-measurement)
with session('SICI_post_first'):
    SICI_collections = search_hotspot(trials=10, task_description='SICI measurement', env=env, run_automatic=True)

#%% ICF (Post-measurement)
with session('ICF_post_first'):
    ICF_collections = search_hotspot(trials=10, task_description='ICF measurement', env=env, run_automatic=True)

#%% CSE_100 (Post-measurement)
with session('CSE_100_post_first'):
    SICI_collections = search_hotspot(trials=10, task_description='CSE measurement', env=env, run_automatic=True)

#%% CSE_120 (Post-measurement)
with session('CSE_120_post_first'):
    SICI_collections = search_hotspot(trials=10, task_description='CSE measurement', env=env, run_automatic=True)

#%%
"""
Post behaviral measurements (around 1 hour)
"""
#%% Slalom calibration (Post-measurement)
sl = Slalom(cfgpath = r"C:\Users\Messung\Desktop\study-phase-triggered-TMS\phase_triggered_tms\cfg.ini", outdir = cfg['main']['recordings_path'] + '/' + cfg['general']['subject_token'])
with session("slalom_cal_post"):
    sl.calibrate()

#%% Slalom test (Post-measurement)
sl = Slalom(cfgpath = r"C:\Users\Messung\Desktop\study-phase-triggered-TMS\phase_triggered_tms\cfg.ini", outdir = cfg['main']['recordings_path'] + '/' + cfg['general']['subject_token'])
with session("slalom_post"):
    sl.run()
    
#%% Brain machine interface (Post-measurement)
with session("bmi_post"):
    BMI.bmi_main()

#%%
"""
Second post physiological measurements
"""
#%% SICI (Post-measurement)
with session('SICI_post_second'):
    SICI_collections = search_hotspot(trials=10, task_description='SICI measurement', env=env, run_automatic=True)

#%% ICF (Post-measurement)
with session('ICF_post_second'):
    ICF_collections = search_hotspot(trials=10, task_description='ICF measurement', env=env, run_automatic=True)

#%% CSE_100 (Post-measurement)
with session('CSE_100_post_second'):
    SICI_collections = search_hotspot(trials=10, task_description='CSE measurement', env=env, run_automatic=True)

#%% CSE_120 (Post-measurement)
with session('CSE_120_post_second'):
    SICI_collections = search_hotspot(trials=10, task_description='CSE measurement', env=env, run_automatic=True)

"""
Experiment ended
"""

