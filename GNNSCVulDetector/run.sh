#!/usr/bin/env bash
## Train
python3 ./GNNSCModel.py --random_seed 9930 --thresholds 0.352 | tee logs/reentrancy/threshold/SVDetector.log
## Test

