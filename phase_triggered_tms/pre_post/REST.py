# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 15:17:54 2020

@author: Ethan

TODO: add audio cues
"""

from reiz.visual import Background, Mural
import reiz
import time

#%%
def start(canvas, trials=5, verbose = True):
    bg = Background(color='gray')
    def countdown(canvas, sek):
        for i in range(0, sek):
            cue = reiz.Cue(canvas, visualstim=[bg, Mural(text=str(sek - i), color=(0.18, 0.18, 0.18))])
            cue.show(duration=1)

    pre = reiz.Cue(canvas, visualstim=[bg, reiz.visual.library.pre])
    post = reiz.Cue(canvas, visualstim=[bg, reiz.visual.library.post])
    f5 = reiz.Cue(canvas, visualstim=[bg, reiz.visual.Mural('Press F5 to start')])
    augen_auf = reiz.Cue(canvas,
                         audiostim=reiz.audio.AudioFile(r'C:\tools\pyreiz\reiz\data\hint.wav'),
                         visualstim=[bg,
                               reiz.visual.library.fixation],
                         markerstr='augen_auf')

    augen_zu = reiz.Cue(canvas,
                         audiostim=reiz.audio.AudioFile(r'C:\tools\pyreiz\reiz\data\relax.wav'),
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

if __name__ == '__main__':
    verbose = True
