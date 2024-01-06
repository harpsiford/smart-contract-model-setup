"""
Read SC code from https://huggingface.co/datasets/mwritescode/slither-audited-smart-contracts/
and convert to opcodes for SoliAudit
"""
import sys
import json
import pandas as pd


def is_reentrant(slither_results):
    slither_results = json.loads(slither_results)['results'].get('detectors', [])
    slither_results = [d['check'] for d in slither_results]
    slither_result = 'reentrancy-no-eth' in slither_results or 'reentrancy-eth' in slither_results
    return str(int(slither_result))


if __name__ == '__main__':
    try:
        contracts = pd.read_parquet(sys.argv[1], engine='fastparquet')
        destination_csv = sys.argv[2]
    except KeyError:
        print('Usage: convert_SASC_to_csv.py contractsN.parquet outputN.csv')
        exit(0)
    print(f'Loaded {len(contracts)} contracts from {sys.argv[1]}, will write to {destination_csv}')
    contracts = contracts[contracts['source_code'].notnull()]
    print(f'Selected {len(contracts)} non-empty contracts')

    csv_contracts = pd.DataFrame()

    csv_contracts['vulnerable'] = contracts['results'].apply(is_reentrant)
    csv_contracts['contracts'] = contracts['contracts']
    csv_contracts['source_code'] = contracts['source_code']
    csv_contracts = csv_contracts.dropna()

    
    csv_contracts.to_csv(destination_csv, index=False, header=False)
