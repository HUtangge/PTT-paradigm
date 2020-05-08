# -*- coding: utf-8 -*-

import sys
sys.path.append(r'C:\Users\Messung\Desktop\study-phase-triggered-TMS\TMS_experiment_preparation')
from configure import Environment
from localite.api import Coil
from luckyloop.client import LuckyClient
import reiz
import liesl
from liesl.streams import localhostname
from liesl.files.session import Recorder, Session


# %%
env = Environment()
env.coil = Coil(0)
env.marker = liesl.get_streams_matching(name="localite_marker")[0]
env.bvr = liesl.get_streaminfos_matching(name="eego")[0]
env.lucky = LuckyClient('134.2.117.144')
env.buffer = liesl.RingBuffer(env.bvr, duration_in_ms=2000)
env.channel_of_interest = 'chan_1'
env.setup()
env.emg_labels = env.emg_labels[:9]

# %%
from generics import search_hotspot, find_highest
from generics import measure_rmt
from generics import free_mode
# %% Make a rough map for the hotspot  detection by applying several stimuli
with session("hotspot-detection"):
    collection = search_hotspot(trials=5, env=env, run_automatic=True)

try:
    amp, pos, sorter  = find_highest(collection, channel=env.channel_of_interest)
    for ix in reversed(sorter):
        print('At the {0}. stimulus the response is {1}'.format(ix+1, collection[ix][env.channel_of_interest]))
except IndexError as e: #aborted run
    raise IndexError('Not enough runs for evaluation' + str(e))

# %% Fine tune the best hotspot by iterating over the best three
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


#%% Bestimme die Ruhemotorschwellen
with session("measure-rmt"):
    results = measure_rmt(channel = env.channel_of_interest,  threshold_in_uv=50,
                          max_trials_per_amplitude=10, env=env)


#%% SICI
with session('pre_measure-SICI'):
    SICI_collections = search_hotspot(trials=3, task_description='SICI measurement', env=env, run_automatic=True)


#%% ICF
with session('pre_measure-ICF'):
    ICF_collections = search_hotspot(trials=5, task_description='ICF measurement', env=env, run_automatic=True)


#%% SICI
with session('post_measure-SICI'):
    SICI_collections = search_hotspot(trials=3, task_description='SICI measurement', env=env, run_automatic=True)


#%% ICF
with session('post_measure-ICF'):
    ICF_collections = search_hotspot(trials=5, task_description='ICF measurement', env=env, run_automatic=True)





