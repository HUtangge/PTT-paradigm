# -*- coding: utf-8 -*-
"""
Created on Thu Jan 30 17:10:26 2020

@author: Ethan

Markers:
    bmi_start

    prepare
    nothing, imagine, or move
    relax

    bmi_end
"""


def bmi_main():
    import numpy as np
    import matplotlib.pyplot as plt
    import time, reiz, liesl
    from reiz.visual import Mural, Background
    canvas = reiz.Canvas()
    canvas.open()

    def countdown(canvas, sek):
        for i in range(0, sek):
            cue = reiz.Cue(canvas, visualstim=[bg, Mural(text=str(sek - i), color=(0.18, 0.18, 0.18))])
            cue.show(duration=1)

    def part2(cuetype, image_lib):
        if "Nothing" in cuetype:
            DispImage = image_lib.Nothing
        elif "Imagine" in cuetype:
            DispImage = image_lib.Imagine
        elif "Open" in cuetype:
            DispImage = image_lib.Open
        elif "Close" in cuetype:
            DispImage = image_lib.Close
        return DispImage

    bg          = Background(color='gray')
    states      = ("Nothing", "Imagine", "Open", "Close")
    image_lib   = reiz.visual.read_folder(r'C:\Users\Messung\Desktop\study-phase-triggered-TMS\phase_triggered_tms\pre_post')
    nBlocks     = 3
    tiles       = np.tile(states, (4))
    block_tiles = np.tile(states, (nBlocks, 4))
    for i in range(nBlocks):
        block_tiles[i, :] = np.random.permutation(tiles)

    canvas.start_run = False
    start_protocol = reiz.Cue(
        canvas, visualstim=[bg, Mural(text='Press F5 to start BMI', color=(0.18, 0.18, 0.18))])
    while not canvas.start_run:
        start_protocol.show(duration=0.1)
    countdown(canvas, 3)


    reiz.Cue(canvas,visualstim=[bg, reiz.visual.Mural("BMI Task:", position=[0, 0.5], fontsize=1.5, color=(0.18, 0.18, 0.18)),
        reiz.visual.Mural("Bitte folgen Sie den Anweisungen", position=[0, -0.25], fontsize=1, color=(0.18, 0.18, 0.18))]).show(duration=5)

    reiz.Cue(canvas,visualstim=[bg, reiz.visual.Mural("Bilder werden angezeigt.", position=[0, 0.4], fontsize=1, color=(0.18, 0.18, 0.18)),
                                reiz.visual.Mural("Bitte 3 Sekunden lang durchführen", position=[0, -0.4], fontsize=1, color=(0.18, 0.18, 0.18))]).show(5)

    reiz.Cue(canvas,visualstim=[bg, image_lib.Open, reiz.visual.Mural("Öffnen Ihre rechte Hand", position=[0, 0.7], fontsize=1, color=(0.18, 0.18, 0.18))]).show(5)
    reiz.Cue(canvas,visualstim=[bg, image_lib.Close, reiz.visual.Mural("Schließe Ihre rechte Hand", position=[0, 0.7], fontsize=1, color=(0.18, 0.18, 0.18))]).show(5)
    reiz.Cue(canvas,visualstim=[bg, image_lib.Imagine,
                                reiz.visual.Mural("Stellen sich vor Ihre rechte Hand zu öffnen", position=[0, 0.7], fontsize=0.7, color=(0.18, 0.18, 0.18))]).show(5)
    reiz.Cue(canvas,visualstim=[bg, image_lib.Nothing,
                                reiz.visual.Mural("Mach nichts", position=[0, 0.7], fontsize=1, color=(0.18, 0.18, 0.18))]).show(10)

    reiz.marker.push('bmi_start')
    for k in range(nBlocks):

        canvas.start_run = False
        start_protocol = reiz.Cue(
            canvas, visualstim=[bg, Mural(text="Press F5 to start block " + str(k + 1), color=(0.18, 0.18, 0.18))])

        while not canvas.start_run:
            start_protocol.show(duration=0.1)
        countdown(canvas, 3)

        for cue in range(np.size(block_tiles, 1)):
            reiz.marker.push("prepare_" + str(k) + '_' + str(cue))
            reiz.Cue(canvas, visualstim=[bg, reiz.visual.Mural("Bereitmachen", position=[0, 0.4], fontsize=1, color=(0.18, 0.18, 0.18))]).show(3)

            reiz.marker.push(str(block_tiles[k,cue]) + '_' + str(k) + '_' + str(cue))
            reiz.Cue(canvas, visualstim=[bg, part2(block_tiles[k,cue], image_lib)]).show(3)

            reiz.marker.push("relax_" + str(k) + '_' + str(cue))
            reiz.Cue(canvas, visualstim=[bg, reiz.visual.Mural("Entspannen", position=[0, -0.4], fontsize=1, color=(0.18, 0.18, 0.18))]).show(5)

    reiz.marker.push('bmi_end')
    canvas.close()