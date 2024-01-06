# GNNSCVulDetector

In order to validate the model we had to modify `GNNSCVulDetector.py` and `BasicModel.py`, but you still need their initial versions to train the model. That is why we store their modified copies. To validate the trained model, replace those files with our versions and then run `model_validation/validate.sh`

As you can see, `contracts_v1.json` only has 2710 lines, even though there are about 100k contracts in SASC. This is due to the fact that the original parser generates empty graph edges for most contracts in SASC:

```bash
grep -v '"graph": \[\]' contracts_v0.json | wc -l
    2710
```

The trained model expects the `graph` colums to be non-empty, so in `contracts_v1.json` we only include rows with graph edges.
