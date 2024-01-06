#!/bin/bash
## Train & test on native dataset
python3 detect.py dev
## Test on SASC
python3 detect.py validate_sasc