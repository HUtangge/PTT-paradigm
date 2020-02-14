
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 30 16:24:29 2019

@author: Julian-Samuel Gebühr

Modified on Wed Nov 27 16:20:29 2019
by: Tang Ge

"""
import reiz
import random
import time
import os
import numpy as np
import json
from luckyloop.client import LuckyClient
from luckyloop.mock import mock
#from arduino import sandy
from localite.api import Coil
from phase_triggered_tms import study_config as cfg
from reiz.marker import push
from reiz import Canvas
from reiz.visual import Mural, library
from liesl.streams import localhostname
from liesl.files.session import Session, Recorder
from reiz.audio import Message
import re
import pickle

protocol_file_name = "protocol.list"

def countdown(canvas, sek):
    for i in range(0,sek):
        #reiz.audio.library.hint.play_blocking()
        cue = reiz.Cue(canvas, visualstim=Mural(text=str(sek-i)))
        cue.show(duration=1)

def gen_range(start, end, step):
        while start <= end:
            yield start
            start += step

def random_time(min, max):
        rand = random.random()
        random_add = (max-min)*rand
        random_time = min+random_add
        return random_time

def random_condition(conditions):
    """Get a randomized condition"""
    conditions_idx = random.randint(0,len(conditions)-1)
    condition = conditions[conditions_idx]
    return condition

def random_condition2(conditions, subject):
    """Get a randomized condition"""
    conditions_idx = list(range(1, 11, 1))
    sub_list = os.listdir(cfg.recordings_path)
    if ('sub-' + subject) in sub_list:
        condition_list = os.listdir(cfg.recordings_path + "sub-" + subject)
    else:
        condition_list = []
    tested_conditions = []
    for cond in condition_list:
        tested_conditions.append(int(re.findall(r'\d+', cond)[0]))
    untested_conditions = list(set(conditions_idx) - set(tested_conditions))
    condition_idx = random.choice(untested_conditions)
    condition = conditions[condition_idx - 1]
    frequencies_to_stimulate = condition[1]
    phases_to_stimulate = condition[2]
    intensity_to_stimulate = condition[0]
    return condition_idx, frequencies_to_stimulate, phases_to_stimulate, intensity_to_stimulate

def get_subject_token():
    """Get a subject token in format VvNn from user input"""
    while True:
        subject_token = input("Please enter subject token: ")
        if re.match(r'^[A-Z][a-z][A-Z][a-z]$', subject_token):
            break
    return subject_token

def get_RMT(max_percent_RMT:int):
    """Get the RMT from user input"""
    while True:
        try:
            RMT = int(input("Please enter the RMT: "))
            max_stimulation_intensity = RMT*max_percent_RMT/100
            if RMT >=0 and max_stimulation_intensity <= 100:
                break
            else:
                print("The RMT has to be greater 0 and the maximum stimulation intensity has to lower than 100")
        except ValueError:
            print("Please enter a valid number")
    return RMT

def save_dict(path:str, dictionary:dict):
    np_float_32_to_float(dictionary)
    dict_as_json = json.dumps(dictionary)
    f = open(path, "w")
    f.write(dict_as_json)
    f.close()

def load_dict(path:str) -> dict:
    try:
        f = open(path,"r")
        loaded_dict = dict(json.load(f))
        f.close()
        return loaded_dict
    except FileNotFoundError:
        return False

def save_list(path:str, list_to_save:list):
    with open(path, "wb") as fp:
        pickle.dump(list_to_save, fp)

def load_list(path:str) -> list:
    try:
        with open(path, "rb") as fp:
            loaded_list = pickle.load(fp)
            return loaded_list
    except FileNotFoundError:
        return False

def ask_user_yes_no_question(question:str):
    while True:
        answer = input(f"{question}(y/n):")
        if answer == "y":
            return True
        elif answer == "n":
            return False
        else:
            print("Please type a valid answer")

def ask_user_for_stimulation_idx():
    while True:
        try:
            start_index = int(input("Please enter the start_index: "))
            if start_index >=0 and start_index <= cfg.number_of_PVT+cfg.number_of_TMS-1:
                break
            else:
                print("Index out of range!")
        except ValueError:
            print("Please enter a valid index")
    return start_index

def protocol_attempt(condition_idx:int, protocol_path:str, stim_number:int = 0):
    """Protocols an attempt with the stimulated index and stim_number in stim list"""
    condition_dict = {'condition_idx': condition_idx,
                     'stim_number': stim_number,
                     'time': time.time()}
    protocol = load_list(protocol_path)

    if protocol:
        protocol = load_list(protocol_path)
        protocol.append(condition_dict)
    else:
        protocol = [condition_dict]
    save_list(protocol_path, protocol)

def creat_condition_list(condition):
    """Creates a list of stimuli with the given condition. No PVTs in a row"""
    frequency = condition['frequency']
    phase = condition['phase_in_deg']
    stimuli = []
    PVT_stimuli = []
    TMS_stimuli = []
    PVT_stimuli.extend([{'stim_type': 'PVT','frquency': frequency,'phase': phase}]*cfg.number_of_PVT)
    stimuli.extend([{'stim_type': 'TMS','frquency': frequency,'phase': phase}]*cfg.number_of_TMS)
    for PVT_stimulus in PVT_stimuli:
        while True:
            random_index = random.randint(0, len(stimuli)-1)
            """Check if not two PVT follow each other"""
            if not(stimuli[random_index-1]['stim_type'] == 'PVT' or stimuli[random_index]['stim_type'] == 'PVT'):
                stimuli.insert(random_index, PVT_stimulus)
                break
    return stimuli

#%%
def start(verbose:bool = False):
    subject_token = get_subject_token()
    subject_folder = f"{cfg.recordings_path}sub-{subject_token}\\"

    RMT = get_RMT(max_percent_RMT = 120)

    """Check if there are old conditions"""
    protocol_path = f"{subject_folder}{protocol_file_name}"
    protocol = load_list(protocol_path)
    if protocol:
        question = "Do you want to repeat the last condition?"
        if ask_user_yes_no_question(question):
            """Load condition which has been stimulated last"""
            condition_idx = protocol[-1]['condition_idx']
            condition = cfg.conditions[condition_idx]

            """ToDo: Ask operator if they want to continue from a specific stim idx"""
            stim_number = 42
        else:
            """Select condition which as not been stimulated before"""
            already_stimulated_conditions = set([x['condition_idx'] for x in load_list(protocol_path)])
            conditions_idx_not_done = list(set(range(0,len(cfg.conditions)))-already_stimulated_conditions)
            conditions_not_done = [cfg.conditions[condition_idx] for condition_idx in conditions_idx_not_done]
            condition = random_condition(conditions_not_done) # select a condition
            stim_number = 0

    else:
        """Select random condition"""
        create_new_condition = True
        condition = random_condition(cfg.conditions)
        stim_number = 0

    """Protocol that the condition has been stimulated"""
    protocol_attempt(condition['index'], protocol_path, stim_number)

    """If there was previous experiment, ask user if want to repeat"""

    """If want to repeakt ask for stimulation index"""
    => a condition + stimulation index to start

    """Save the condition"""
    condition_order_directory = cfg.recordings_path+"sub-"+subject_token+'\\condition_%s\\config\\' % condition_idx
    condition_order_file_path = condition_order_directory+'config.json'

    """Check if all streams are available"""
    streamargs = [{'name':"localite_marker"},   # comments: make a real list
                  {'name':"reiz-marker"},
                  {'name':"localite_marker"},
                  {'name':"eego"},
                  {'name':"GDX-RB_0K2002A1"}]

    session = Session(prefix=subject_token,
                      streamargs=streamargs)

    # TG: as we have 5 conditions for each intensity, so I randomize two studies (Nelli and me), I can also do it in a separate way.
    condition_idx, frequencies_to_stimulate, phases_to_stimulate, intensity_to_stimulate = random_condition(conditions = cfg.conditions, subject = subject_token)

    """Define stimulation intensity"""
    stimulation_intensity = round(RMT*intensity_to_stimulate)
    print(f"Stimulation intensity {stimulation_intensity}")


#    try:
#        with open(condition_order_file_path) as json_file:
#            stimuli = json.load(json_file)
#        print('Loaded condition file')
#        while True:
#            try:
#                start_index = int(input("Please enter the start_index: "))
#                if start_index >=0 and start_index <= len(stimuli)-1:
#                    break
#            except ValueError:
#                print("Please enter a valid index")
#        stimuli = stimuli[start_index:]
#
#    except:

    if create_new_condition:
        PVT_stimuli = []
        TMS_stimuli = []
        stimuli = []
        stimulus_idx = 0
        for frequency in frequencies_to_stimulate:
            for phase in phases_to_stimulate:
                PVT_stimuli.extend([(('PVT',frequency,phase))]*cfg.number_of_PVT_per_phase)
                TMS_stimuli.extend([(('TMS',frequency,phase))]*cfg.number_of_TMS_per_phase)
        stimuli_list = PVT_stimuli+TMS_stimuli

        # TG: this is for generating a random list, as we do not want to have two PVT trials come together, so we generate random number with the purpose
        # this process takes relative long, I think there is some better way
        stimuli_idx = list(range(0, len(stimuli_list), 1))
        while True:
            PVT_stimuli_idx = random.sample(range(0, len(stimuli_list), 1), cfg.number_of_PVT_per_phase)
            PVT_stimuli_idx = sorted(PVT_stimuli_idx)
            if 1 not in np.diff(PVT_stimuli_idx):
                break
        TMS_stimuli_idx = list(set(stimuli_idx) - set(PVT_stimuli_idx))
        stimuli_idx = PVT_stimuli_idx + TMS_stimuli_idx

        count = -1
        for stimulus_idx in stimuli_idx:
            count += 1
            stimuli_list[count] = (stimulus_idx,)+stimuli_list[count]
        #####################################################################################################

        stimuli = stimuli_list
        stimuli = sorted(stimuli)
        os.makedirs(condition_order_directory)
        with open(condition_order_file_path,'w') as file:
            file.write(json.dumps(stimuli)) #überschreibt immer
        print('Created new condition file')

    break_idx = TMS_stimuli_idx[(cfg.run_length-1):-1:cfg.run_length]
    N = len(stimuli_idx)
    expected_duration = (len(TMS_stimuli_idx)*10) / 60
    print(f'Expected duration is around {expected_duration} min')


    #%%
    """Intit Lucky Client"""
    print("Init lucky")
    #lucky = LuckyClient('134.2.117.144')
    lucky = LuckyClient()

    """Init Coil"""
    print("Init coil")
    coil = Coil(0)
    coil.amplitude = stimulation_intensity

    """Init Sandy"""
    print("Init sandy")
#    sandy_cli = sandy.Arduino(timeout=1.5, version =  'v0.3.1 - StalwartSandy')
#    sandy_cli.reset()
#    sandy_cli.set_threshold(150)
#    sandy_cli.blink(5)
#    #sandy_cli.set_threshold(0)
#    print("Sandy in standby")
#    time.sleep(1)

    """Create the GUI"""
    canvas = Canvas()
    canvas.open()

    labcue= reiz.Cue(canvas, visualstim=reiz.visual.library.logo)
    labcue.show(duration=2)

    #%%
    with session("TMS_intervention"):
        print("Started recording")
        canvas.window.start_run = False
        start_protocol = reiz.Cue(canvas, visualstim=Mural(text='Start protocol with F5'))
        print("Waiting for user to start in GUI")
        while not canvas.window.start_run:
            start_protocol.show(duration=1)
        countdown(canvas, 5)
        labcue.show()

        t0  = time.time()

        last_frequency = 0
        reaction_times = []
        break_counter = 0

        for (stimulus_idx, stim_type, frequency,phase) in stimuli:
            print(f"Stimulation index {stimulus_idx}")
            time.sleep(0.5)
            time_setup_trial = time.time()

            # sends current setup as marker
            time_push = time.time()
            push(json.dumps({'stimulus_idx':str(stimulus_idx),
                             'stim_type':stim_type,
                             'freq':str(frequency),
                             'phase':str(phase)}),sanitize=False)
            print("\n push time: " + str(time.time()-time_push ))
            print('Stimulation index: '+str(stimulus_idx))
            if verbose:
                print("Start "+stim_type+" for frequency " + str(frequency)+' and phase ' + str(phase))

            # set patrick according to parameters of this trial
            time_setup = time.time()

            lucky.phase = phase
            if frequency != last_frequency:
                lucky.frequency = frequency
                last_frequency = frequency
            print("\n lucky time: " + str(time.time()-time_setup ))

            # conditional of stimtype, setup TMS and Arduino this trial
            if stim_type == 'TMS':
                coil.amplitude = stimulation_intensity
                t1 = time.time()
                trial_time = t1-t0
                if verbose:
                    print("\n Trial time: "+ str(trial_time))
                # TG: wait and trigger phase and frequency dependent, if next stimuli is TMS, then wait 10s, else wait 5s
                if stimulus_idx < (N-1) and stimuli[stimulus_idx+1][1] == 'TMS':
                    sleep_time= random_time(min=9.5-trial_time,max=10.5-trial_time)
                else:
                    sleep_time= random_time(min=4.5-trial_time,max=5.5-trial_time)

            if stim_type == 'PVT':
                coil.amplitude = 0
                # wait and trigger phase and frequency dependent
                t1 = time.time()
                trial_time = t1-t0
                if verbose:
                    print("\n Trial time: "+ str(trial_time))
                sleep_time= random_time(min=4.5-trial_time,max=5.5-trial_time)
                try:
                    # sandy_cli.await_blink()
                    if verbose:
                        print('Sandy is waiting for blink')
                except:
                    raise ConnectionError('Sandy in unclear state')
            print(f"\n Setup: {(time.time()-time_setup_trial):.2f}s")

            if sleep_time < 0.75:
                sleep_time = 0.75
            if True or verbose:
                print(f"\n Sleep_time = {sleep_time:.2f}s")
                print(f"\n ISI = {sleep_time+trial_time:.2f}s\n")
            labcue.show(duration=sleep_time)
            t0 = time.time()
            # conditional on stimtype, wait for keypress
            if stim_type == 'PVT':
                event_list = []
                # sandy_cli.receive()
                blink_wait_start = time.time()
                while not(event_list) or len(event_list) == 0:
                    if time.time()-blink_wait_start > 30:
                        raise ConnectionError(f"Sandy could not be triggered for 1.5 seconds. Stimulus idx: {stimulus_idx}")
                    print(f"Wait for blink trigger. Stim: {stimulus_idx}")
                    lucky.trigger()
                    # event_list = sandy_cli.receive()
                    print(f"Event list: {event_list}")
                for event in event_list:
                    if event['state-change'] == 'blink-started':
                        time_trigger = int(event['timestamp'])
                time_wait_for_press = time.time()
                print("Waiting for button pressed")
                while time.time()-time_wait_for_press < 1.25:
                    atleast_one_button_pressed = False
                    time_reaction = False
                    # response = sandy_cli.receive()
                    if response:
                        event_list.extend(response)
                    if event_list:
                        print("Found response")
                        for event in event_list:
                            if event:
                                print(event)
                                button_1_pressed = event['state-change'] == 'button-1-pressed'
                                button_2_pressed = event['state-change'] == 'button-2-pressed'
                                both_buttons_pressed = event['state-change'] == 'both-buttons-pressed'
                                atleast_one_button_pressed = button_1_pressed or button_2_pressed or both_buttons_pressed
                                if atleast_one_button_pressed:
                                    time_reaction = int(event['timestamp'])
                                    break
                    if atleast_one_button_pressed:
                        break
                if verbose:
                        print(f"Trigger timestamp= {time_trigger}")

                if  time_trigger is not None: # led was turned on
                    if verbose:
                        print("Reaction timestamp= "+str(time_reaction))
                    if not(time_reaction) or time_reaction-time_trigger<0 or time_reaction-time_trigger>1000:
                        reaction_time = "No reaction"
                        rt = reiz.Cue(canvas,
                              visualstim=Mural(text=reaction_time))
                    else:
                        reaction_time = time_reaction-time_trigger
                        reaction_times.append(reaction_time)
                        rt = reiz.Cue(canvas,
                              visualstim=Mural(text='{0:3.1f} ms'.format(
                                      reaction_time)))
                    if verbose:
                        print('Reaction time: '+ str(reaction_time))

                    push(json.dumps({'reaction_time':str(reaction_time)}),
                         sanitize=False)
                    rt.show(duration=1)
            else: # when TMS stimulus
                # TG:for test
                print('hello')
                lucky.trigger()

            try:
                if stimuli[stimulus_idx+1][1] == "PVT":
                    coil.amplitude = 0
            except IndexError:
                print("Index error")

            if stimulus_idx in break_idx and (stimulus_idx<stimuli[-1][0]): #make a break after cfg.run_length stimuli if experiment is not over
                break_counter += 1
                if break_counter == 1:
                    mean_run_reaction_time = np.mean(reaction_times[:stimulus_idx])
                else:
                    mean_run_reaction_time = np.mean(reaction_times[break_idx[break_counter-2]+1:stimulus_idx])
                mean_overall_reaction_time = np.mean(reaction_times)
                #displays run reaction time
                v_run_reaction_time = reiz.Cue(canvas,
                                  visualstim=Mural(text='Run reaction time = '+'{0:3.1f} ms'.format(mean_run_reaction_time)))
                v_run_reaction_time.show(duration=2)

                #displays overall reaction time
                v_overall_reaction_time = reiz.Cue(canvas,
                                  visualstim=Mural(text='Overall reaction time = '+'{0:3.1f} ms'.format(mean_overall_reaction_time)))
                v_overall_reaction_time.show(duration=2)

                #calculates and shows the expected duration of the intervention that is  left
                expected_duration_left = expected_duration - (cfg.run_length * 10 * break_counter) / 60
                print(f'Expected duration is around {expected_duration} min')
                v_expected_duration_left = reiz.Cue(canvas,
                                  visualstim=Mural(text='Expected duration left = '+'{0:3.1f} min'.format(expected_duration_left)))
                v_expected_duration_left.show(duration=4)

                canvas.window.start_run = False
                nextrun = reiz.Cue(canvas, visualstim=Mural(text='Continue with F5'))
                while not canvas.window.start_run:
                    nextrun.show(duration=1)
                countdown(canvas, 5)
            labcue.show()

    v_intervention_finished = reiz.Cue(canvas,
                              visualstim=Mural(text='Intervention is finished. Please stop the recording'))
    v_intervention_finished.show(duration=1)


if __name__ == '__main__':
    start(verbose = True)

