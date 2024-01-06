"""
Read SC code from the large CSV version of 
https://huggingface.co/datasets/mwritescode/slither-audited-smart-contracts/
and convert to opcodes for Peculiar
"""
import os
import sys
import json
import pandas as pd
from tqdm.auto import tqdm


def write_to_jsonl(fd, row):
    fd.write(row.to_json() + '\n')


if __name__ == '__main__':
    try:
        # You need to combine Parquet files to a large CSV with 'source_code', 'vulnerable', 'contracts' first
        contracts = pd.read_csv(sys.argv[1])
        destination_dir = sys.argv[2].rstrip('/')
    except LookupError:
        print('Usage: resnet_to_peculiar.py 100k_contracts.csv output_dataset_dir')
        exit(0)
    print(f'Loaded {len(contracts)} contracts from {sys.argv[1]}, will write to {destination_dir}/')
    contracts = contracts[contracts['source_code'].notnull()]
    print(f'Selected {len(contracts)} non-empty contracts')

    contracts['idx'] = contracts.index.astype(str)
    contracts.rename(
        columns={'contracts': 'address', 'source_code': 'contract'}, 
        inplace=True
    )

    os.makedirs(destination_dir, exist_ok=True)
    contracts.to_csv(f'{destination_dir}/test.txt', columns=['idx', 'vulnerable'], index=False, header=False, sep=' ')

    jsonl_contracts = contracts[['address', 'idx', 'contract']]
    tqdm.pandas(desc="converting resnet to peculiar jsonl")
    with open(f'{destination_dir}/data.jsonl', 'w') as f:
        writer = lambda x: write_to_jsonl(f, x)
        jsonl_contracts.progress_apply(writer, axis=1)
