# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 08:40:27 2020

@author: Ethan

"""
import re
import time
import reiz
import configparser
from localite.coil import Coil
from phase_triggered_tms.pre_post import REST, BMI
from phase_triggered_tms.study_protocol import start_intervention
import liesl
from liesl.streams import localhostname
from liesl.files.session import Recorder, Session
from slalom.slalom_class import Slalom
#import sys
#sys.path.append(r'C:\Users\Messung\Desktop\study-phase-triggered-TMS\TMS_experiment_preparation')
from phase_triggered_tms.tms_preparation.configure import Environment
from luckyloop.client import LuckyClient
import arduino.onebnc

#%%
env = Environment()
env.coil = Coil(0)
env.marker = liesl.get_streams_matching(name="localite_marker")[0]
env.bvr = liesl.get_streaminfos_matching(name="eego")[0]
env.lucky = LuckyClient('134.2.117.144')
env.buffer = liesl.RingBuffer(env.bvr, duration_in_ms=2000)
env.channel_of_interest = 'chan_1'
env.setup()
env.emg_labels = env.emg_labels[:9]

#%%
from phase_triggered_tms.tms_preparation.generics import search_hotspot, find_highest
from phase_triggered_tms.tms_preparation.generics import measure_rmt
from phase_triggered_tms.tms_preparation.generics import free_mode

#%%

canvas = reiz.Canvas()
canvas.open()
time.sleep(0.01)

reiz.marker.start()

cfg = configparser.ConfigParser()
cfg.read(r'C:\tools\study-breathing_intervention\prana\cfg.ini')
subject_token = cfg['study_info']['subject_token']
with open(r'C:\tools\study-breathing_intervention\prana\cfg.ini', "w") as configfile:
    cfg.write(configfile)

#streamargs = [{'name':"eego"}, {'name':'reiz-marker'}, {'name':'GDX-RB'}, {'name':'localite_marker'}, {'name':'pupil_capture'}]
#session    = Session(prefix=subject_token, streamargs=streamargs)
sl = Slalom(cfgpath = r'C:\projects\pranayama\prana\cfg.ini')



#TODO: currently, the Slalom class assumes that the cfg.ini is in the current working directory, and it will be
#written to it. Also, we will have to specify an outdir, where results will be saved.

#push slalom results to marker server?
#%% preparation for the recording




#%% Resting
with session("resting_state_pre"):
	REST.start(canvas, trials=5)

#%% SLALOM CALIBRATION ----------------------------------------------------------------------
with session("slalom_cal_pre"):
    sl.calibrate()

    '''
    calibrate for post as well?
    '''

#%% SLALOM TEST----------------------------------------------------------------------
with session("slalom_test_pre"):
    sl.test()

#%% SLALOM TASK----------------------------------------------------------------------
with session("slalom_pre"):
    sl.run()

#%% BEHA ------------------------------------------------------------------------------------
with session("bmi_pre"):
    BMI.bmi_main(canvas)

#%% PHYS ------------------------------------------------------------------------------------

with session('hotspot_search'):
    # hotspot search

with session('rmt'):
    # rmt


#%% TMS
coil = Coil(coil=0, address=('127.0.0.1', 6667))
time.sleep(0.01)

'''
randomize
'''

cfg.read(r'C:\projects\pranayama\prana\cfg.ini')

with session("sici_pre"):
    TMS.tms_sequence(canvas, coil, cfg, sequence='sici')

with session("icf_pre"):
    TMS.tms_sequence(canvas, coil, cfg, sequence='icf')

with session("cse_100_pre"):
    TMS.tms_sequence(canvas, coil, cfg, sequence='cse_100')

with session("cse_120_pre"):
    TMS.tms_sequence(canvas, coil, cfg, sequence='cse_120')

#%% Calibrate FES
fes = calibrate_FES.FES()
with session("calibrate"):
    fes.calibrate_fes()
    # NOTE: enter 21 to break calibration loop

# Intervention practice session
breath_FES.practice_breathing_FES(canvas,cfg)

#%% Intervention ----------------------------------------------------------------------------

breath_FES.breathing_FES_main(canvas, cfg)

#%% PHYS ------------------------------------------------------------------------------------

with session("resting_state_post"):
	REST.start()

#%% TMS
coil = coil.Coil(coil=0, address=('127.0.0.1', 6667))
time.sleep(0.01)

with session("sici_post"):
	TMS.tms_sequence(canvas, coil, cfg, sequence='sici')

with session("icf_post"):
	TMS.tms_sequence(canvas, coil, cfg, sequence='icf')

with session("cse_100_post"):
	TMS.tms_sequence(canvas, coil, cfg, sequence='cse_100')

with session("cse_120_post"):
	TMS.tms_sequence(canvas, coil, cfg, sequence='cse_120')

#%% SLALOM CALIBRATION ----------------------------------------------------------------------
with session("slalom_cal_pre"):
    sl.calibrate()

#%% BEHA ------------------------------------------------------------------------------------

with session("slalom_post"):

with session("bmi_post"):
    BMI.bmi_main(canvas)

#%% TMS ------------------------------------------------------------------------------------
coil = coil.Coil(coil=0, address=('127.0.0.1', 6667))

with session("sici_post_2"):
	TMS.tms_sequence(canvas, coil, cfg, sequence='sici')

with session("icf_post_2"):
	TMS.tms_sequence(canvas, coil, cfg, sequence='icf')

with session("cse_100_post_2"):
	TMS.tms_sequence(canvas, coil, cfg, sequence='cse_100')

with session("cse_120_post_2"):
	TMS.tms_sequence(canvas, coil, cfg, sequence='cse_120')
    
    
if __name__ == '__main__':
    
    
    