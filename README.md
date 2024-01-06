# smart-contract-model-setup

This repository hosts Dockerfiles and data processing scripts for the ML models we tested in our work, "Evaluation of State-of-the-Art Machine Learning Smart Contract Vulnerability Detection Methods". We used a new dataset, Slither Audited Smart Contracts (SASC), to evaluate the performance of several available vulnerability detectors.

To use any Dockerfile, just copy it to the target repository together with the accompanying files. For example, to use AMEVulDetector.Dockerfile, copy the contents of AMEVulDetector into a cloned version of the repository.

Some scripts use the CSV version of SASC. The conversion script is in the root folder of this repository. Apply it to all the SASC Parquet files available at [HuggingFace](https://huggingface.co/datasets/mwritescode/slither-audited-smart-contracts), then combine them into a one and prepend the header line: `vulnerable,addr,source_code`.

Repositories:
- [AMEVulDetector](https://github.com/Messi-Q/AMEVulDetector), commit `f68cd4e0fd98b7fbacb775373fc0ca77e7df5fa9`
- [GNNSCVulDetector](https://github.com/Messi-Q/GNNSCVulDetector), commit `314fb16cc2e4da501b46d8ff23671bdb6fe96c2f`
- [Peculiar](https://github.com/wuhongjun15/Peculiar), commit `eaeaf600a3ee796d59db07034d0e8e6254d9c5f9`
- [SoliAudit](https://github.com/jianwei76/SoliAudit), commit `50e5c0f9c1d9524e93ea0bf1bd46623b1adc101b`, use the `va/` folder inside the original repo
