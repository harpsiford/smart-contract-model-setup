# AMEVulDetector

We could not understand the final dataset preprocessing step (see this [issue](https://github.com/Messi-Q/AMEVulDetector/issues/4)), so we did not validate it against SASC. However, you can find some intermediate files here.

The data in `AMEVulDetector/graph_feature/reentrancy/reentrancy_final_train.txt` could have been compressed using MLP, like in `pattern_extractor_example`, but the format is too ambiguous to give a conclusive answer. Even if MLP is used, how are graph nodes and edges combined with author expert patterns before being passed to MLP?

We could not find any answers.