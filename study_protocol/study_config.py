#!/usr/bin/env python

conditions = {0: {'percent_RMT':100,
                  'frequency': 10,
                  'phase_in_deg': -90,
                  'sham': False},
              1: {'percent_RMT':100,
                  'frequency': 10,
                  'phase_in_deg': 90,
                  'sham': False},
              2: {'percent_RMT':100,
                  'frequency': 20,
                  'phase_in_deg': -90,
                  'sham': False},
              3: {'percent_RMT':100,
                  'frequency': 20,
                  'phase_in_deg': 90,
                  'sham': False},
              4: {'percent_RMT':100,
                  'frequency': 10,
                  'phase_in_deg': 0,
                  'sham': True},
              5: {'percent_RMT':120,
                  'frequency': 10,
                  'phase_in_deg': -90,
                  'sham': False},
              6: {'percent_RMT':120,
                  'frequency': 10,
                  'phase_in_deg': 90,
                  'sham': False},
              7: {'percent_RMT':120,
                  'frequency': 20,
                  'phase_in_deg': -90,
                  'sham': False},
              8: {'percent_RMT':120,
                  'frequency': 20,
                  'phase_in_deg': 90,
                  'sham': False},
              9: {'percent_RMT':120,
                  'frequency': 20,
                  'phase_in_deg': 0,
                  'sham': True}}

recordings_path = 'C:\\recordings\\TG_NK_TMS_study\\'

number_of_PVT_per_phase = 60
number_of_TMS_per_phase = 300

run_length = 100

verbose = True