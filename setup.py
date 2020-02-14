# -*- coding: utf-8 -*-
from distutils.core import setup

setup(
    name="Study Phase Triggered TMS",
    version="0.0.1",
    description="This is a study aims at explore the neuroplasticity after EEG-triggered TMS.",
    long_description="This is a study aims at explore the neuroplasticity after EEG-triggered TMS. The study included ten different conditions. They are the combination of two intensities (100% RMT and 120% RMT), two frequencies (10 Hz and 20 Hz) and two phases (peak and trough). In addition with two sham conditions. Each participant experinece the ten conditions with a random order.",
    author="Julian-Samuel Gebuehr, Ge Tang, Nelli Keksel",
    author_email="julian-samuel@gebuehr.net",
    url="https://github.com/translationalneurosurgery/study-phase-triggered-TMS",
    download_url="https://github.com/translationalneurosurgery/study-phase-triggered-TMS",
    license="MIT",
    packages=["phase_triggered_tms"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "Topic :: Software Development :: Libraries",
    ],
)
