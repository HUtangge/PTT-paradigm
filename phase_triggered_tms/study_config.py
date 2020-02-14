#!/usr/bin/env python

conditions = [{'index': 0,
               'percent_RMT':100,
               'frequency': 10,
               'phase_in_deg': -90,
               'sham': False},
              {'index': 1,
               'percent_RMT':100,
               'frequency': 10,
               'phase_in_deg': 90,
               'sham': False},
              {'index': 2,
               'percent_RMT':100,
               'frequency': 20,
               'phase_in_deg': -90,
               'sham': False},
              {'index': 3,
               'percent_RMT':100,
               'frequency': 20,
               'phase_in_deg': 90,
               'sham': False},
              {'index': 4,
               'percent_RMT':100,
               'frequency': 10,
               'phase_in_deg': 0,
               'sham': True},
              {'index': 5,
               'percent_RMT':120,
               'frequency': 10,
               'phase_in_deg': -90,
               'sham': False},
              {'index': 6,
               'percent_RMT':120,
               'frequency': 10,
               'phase_in_deg': 90,
               'sham': False},
              {'index': 7,
               'percent_RMT':120,
               'frequency': 20,
               'phase_in_deg': -90,
               'sham': False},
              {'index': 8,
               'percent_RMT':120,
               'frequency': 20,
               'phase_in_deg': 90,
               'sham': False},
              {'index': 9,
               'percent_RMT':120,
               'frequency': 20,
               'phase_in_deg': 0,
               'sham': True}]

recordings_path = 'C:\\recordings\\TG_NK_TMS_study\\'

number_of_PVT = 60
number_of_TMS = 300

run_length = 100

verbose = True