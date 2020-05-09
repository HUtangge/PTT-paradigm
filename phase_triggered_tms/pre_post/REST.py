# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 15:17:54 2020

@author: Ethan

TODO: add audio cues
"""

from reiz.visual import Background, Mural
import reiz
import time
from reiz.audio import Message


def start(trials=5):
    canvas = reiz.Canvas()
    canvas.open()

    bg = Background(color='red')
    def countdown(canvas, sek):
        for i in range(0, sek):
            cue = reiz.Cue(canvas, visualstim=[bg, Mural(text=str(sek - i), color=(0.18, 0.18, 0.18))])
            cue.show(duration=1)

    pre = reiz.Cue(canvas, visualstim=[bg, reiz.visual.library.pre])
    post = reiz.Cue(canvas, visualstim=[bg, reiz.visual.library.post])
    f5 = reiz.Cue(canvas, visualstim=[bg, reiz.visual.Mural('Press F5 to start')])
    open_eyes = Message('Open eyes')
    close_eyes = Message('Close eyes')
    augen_auf = reiz.Cue(canvas,
                         audiostim=reiz.audio.library.beep,
                         visualstim=[bg,
                               reiz.visual.library.fixation],
                         markerstr='augen_auf')

    augen_zu = reiz.Cue(canvas,
                         audiostim=reiz.audio.library.beep,
                         visualstim=[bg,
                               reiz.visual.library.fixation],
                         markerstr='augen_zu')

    while not canvas.start_run:
        f5.show(duration = 1)

    pre.show(duration = 3)

    for trl_num in range(trials):
        augen_auf.show(duration = 30)
        augen_zu.show(duration = 30)
    post.show(duration = 3)

    canvas.close()
