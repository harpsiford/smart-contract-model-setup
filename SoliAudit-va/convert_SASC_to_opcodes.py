"""
Read SC code from SASC (large CSV version)
and convert to opcodes for SoliAudit
"""
import re
import sys
import json
import solcx
import semantic_version
import pandas as pd
from tqdm.auto import tqdm
from asm_parser import AsmParser
from utils import find_seq, rfind_seq


SOLC_RE = re.compile('pragma solidity( [^;]+)*;', re.M)
CONTRACT_NAME_RE = re.compile(r'^\s*(?:contract|library)\s+([\w\d$_]+)', re.M)
POSSIBLE_SOLIDITY_VERSIONS = [
    # these versions are not supported by py-solc-x
    # "0.0.2", "0.0.3", "0.1.2", "0.1.3", "0.1.4", "0.1.5", "0.1.6", "0.1.7", "0.2.0", "0.2.1", "0.2.2", "0.3.0", "0.3.1", "0.3.2", "0.3.3", "0.3.4", "0.3.5", "0.3.6", "0.4.0", "0.4.1", "0.4.2", "0.4.3", "0.4.4", "0.4.5", "0.4.6", "0.4.7", "0.4.8", "0.4.9", "0.4.10", 
    
    "0.4.11", "0.4.12", "0.4.13", "0.4.14", "0.4.15", "0.4.16", "0.4.17", "0.4.18", "0.4.19", "0.4.20", "0.4.21", "0.4.22", "0.4.23", "0.4.24", "0.4.25", "0.4.26", "0.5.0", "0.5.1", "0.5.2", "0.5.3", "0.5.4", "0.5.5", "0.5.6", "0.5.7", "0.5.8", "0.5.9", "0.5.10", "0.5.11", "0.5.12", "0.5.13", "0.5.14", "0.5.15", "0.5.16", "0.5.17", "0.6.0", "0.6.1", "0.6.2", "0.6.3", "0.6.4", "0.6.5", "0.6.6", "0.6.7", "0.6.8", "0.6.9", "0.6.10", "0.6.11", "0.6.12", "0.7.0", "0.7.1", "0.7.2", "0.7.3", "0.7.4", "0.7.5", "0.7.6", "0.8.0", "0.8.1", "0.8.2", "0.8.3", "0.8.4", "0.8.5", "0.8.6", "0.8.7", "0.8.8", "0.8.9", "0.8.10", "0.8.11", "0.8.12", "0.8.13", "0.8.14", "0.8.15", "0.8.16", "0.8.17", "0.8.18", "0.8.19", "0.8.20", "0.8.21", "0.8.22"]
POSSIBLE_SOLIDITY_VERSIONS = [semantic_version.Version(v) for v in POSSIBLE_SOLIDITY_VERSIONS]


def print_asm_lines(opcodes, begin_line_no=0):
    def is_opcode(op):
        return op['name'].isupper()

    i_width = len(str(len(opcodes) + begin_line_no))
    type_width = max([len(op['name']) for op in opcodes])

    def to_type(op):
        return '[{:^{}}]'.format(op['name'], type_width) if is_opcode(op) else \
               '|{:^{}}|'.format(op['name'], type_width)

    for i, op in enumerate(opcodes):
        print("{:<{}} {} {}:{} {}".format(i+begin_line_no, i_width, to_type(op), op['begin'], op['end'], op.get('value', '')))

def skip_till(str, matched):
    idx = str.find(matched)
    if idx > 0:
        return str[idx+len(matched):]
    return str

class AsmParser:
    @property
    def solfile(self):
        return self.__solfile

    @property
    def solbytes(self):
        if self.__solbytes is None:
            with open(self.__solfile, 'rb') as f:
                self.__solbytes = f.read()
        return self.__solbytes

    def __init__(self, solfile=None, solbytes=None):
        assert solfile or solbytes
        self.__solfile = solfile
        self.__solbytes = solbytes

        asm = self.__get_asm(self.solbytes)
        self.opcodes = self.__to_opcodes(asm)

    def __get_asm(self, source_code):
        prefix = 'EVM assembly:'
        next_sec = '======='
        content, _, _, _ = solcx.wrapper.solc_wrapper(solc_binary=solcx.install.get_executable(), stdin=source_code, asm_json=True)

        asm = []

        pos = 0
        while pos < len(content):
            begin = content.find(prefix, pos)
            if begin < 0:
                break

            begin += len(prefix)
            end = content.find(next_sec, begin)
            if end < 0:
                end = len(content)

            pos = end

            sec = json.loads(content[begin:end])
            if sec is not None:
                asm.append(sec)

        return asm

    def __to_opcodes(self, asm):
        opcodes = []
        for sec in asm:
            #opcodes += sec['.code']
            opcodes += sec['.data']['0']['.code']

        # remove tag and INVLAID (because evm does not disasm out the op)
        opcodes = [ op for op in opcodes if op['name'] not in ('tag', 'INVALID')]

        # normalize opname
        for op in opcodes:
            #op['name] = op['name'].upper()
            if op['name']  == 'PUSH [tag]':
                op['name'] = 'PUSH2'
            elif op['name']  == 'PUSH' or op['name'].startswith('PUSH '):
                op['name'] = 'PUSH%d' % self.__hex_to_nbytes(op['value'])
            elif op['name'] == 'KECCAK256':
                op['name'] = 'SHA3'

        return opcodes

    def __hex_to_nbytes(self, hexstr):
        if hexstr.startswith('0x'):
            hexstr = hexstr[2:]
        nbytes = (len(hexstr) + 1) // 2
        return nbytes
        
    def find(self, subseq, begin=0, end=None, reversed=False, op_eql=None, to_skip=None):
        assert isinstance(subseq, list) or isinstance(subseq, tuple) 

        def op_eql_(op_item, op):
            if op_eql is None:
                return op_item['name'] == op.upper()
            else:
                return op_eql(op_item['name'], op.upper())

        find = rfind_seq if reversed else find_seq
        return find(self.opcodes, subseq, is_eql=op_eql_, begin=begin, end=end)

    def get_ops(self, begin, end):
        return [ op_item['name'] for op_item in self.opcodes[begin:end] ]


def remove_comments(source_code):
    # source: https://stackoverflow.com/questions/2319019/using-regex-to-remove-comments-from-source-files
    # comment by ishmael
    COMMENT_RE = re.compile(r"(\".*?(?<!\\)\"|\'.*?(?<!\\)\')|(/\*.*?\*/|//[^\r\n]*$)", re.MULTILINE|re.DOTALL)
    def _replacer(match):
        # if the 2nd group (capturing comments) is not None,
        # it means we have captured a non-quoted (real) comment string.
        if match.group(2) is not None:
            return "" # so we will return empty to remove the comment
        else: # otherwise, we will return the 1st group
            return match.group(1) # captured quoted-string
    return COMMENT_RE.sub(_replacer, source_code)


def get_compiler_version(source_code, default='0.4.25'):
    try:
        results = SOLC_RE.findall(source_code)
        compiler_versions_raw = [r.strip(' ').split(' ')[0] for r in results]
        
        # Handle situations like 'pragma solidity >= 0.8.4;',
        # where there is a space between the >= token and the version number
        compiler_versions = []
        for v in compiler_versions_raw:
            try:
                if not any([c in '0123456789' for c in compiler_versions[-1]]):
                    v = compiler_versions[-1] + v
                    compiler_versions.pop()
            except IndexError:
                pass
            compiler_versions.append(v)

        # how do I even handle this?
        # > import pdb; pdb.set_trace()
        # (Pdb) SOLC_RE.findall(source_code)
        # [' ^ 0.4 .9']
        # (Pdb) print(source_code)
        # pragma solidity ^ 0.4 .9;
        # no, seriously, if you ever think of a clean way 
        # to normalize such version strings, by all means open a PR 

        if not compiler_versions:
            return default
        version_spec = semantic_version.SimpleSpec(','.join(compiler_versions))
        compiler_version = str(version_spec.select(POSSIBLE_SOLIDITY_VERSIONS))
        assert compiler_version != 'None'
        return compiler_version
    except Exception as e:
        return default


OPCODE_FILTER = ["ADD","SUB","SHA3","ADDRESS","BALANCE","ORIGIN","CALLER","CALLVALUE",
                 "CALLDATALOAD","CALLDATASIZE","CALLDATACOPY","CODESIZE","CODECOPY",
                 "GASPRICE","EXTCODESIZE","EXTCODECOPY","BLOCKHASH","COINBASE","TIMESTAMP",
                 "NUMBER","DIFFICULTY","GASLIMIT","GAS","CREATE","CALL","CALLCODE","RETURN",
                 "DELEGATECALL","SELFDESTRUCT","REVERT"]


def contract_source_to_opcodes(source_code):    
    try:
        compiler_version = get_compiler_version(source_code)
        solcx.install_solc(version=compiler_version)
        solcx.set_solc_version(compiler_version)
        parser = AsmParser(solbytes=source_code)
        return ' '.join(op['name'] for op in parser.opcodes if op['name'] in OPCODE_FILTER)
    except Exception as e:
        return None


def is_reentrant(slither_results):
    slither_results = json.loads(slither_results)['results'].get('detectors', [])
    slither_results = [d['check'] for d in slither_results]
    slither_result = 'reentrancy-no-eth' in slither_results or 'reentrancy-eth' in slither_results
    return str(int(slither_result))


if __name__ == '__main__':
    contracts = pd.read_csv(sys.argv[1])
    destination_csv = sys.argv[2]
    print(f'Loaded {len(contracts)} contracts from {sys.argv[1]}, will write to {destination_csv}')
    contracts = contracts[contracts['source_code'].notnull()]
    print(f'Selected {len(contracts)} non-empty contracts')

    new_contracts = pd.DataFrame()

    tqdm.pandas(desc="converting contracts to opcodes")
    new_contracts['Vulnerable'] = contracts['vulnerable']
    new_contracts['Addr'] = contracts['contracts']
    new_contracts['Opcodes'] = contracts['source_code'].progress_apply(contract_source_to_opcodes)
    new_contracts = new_contracts.dropna()

    print(f'Successfully converted {len(new_contracts)} out of {len(contracts)}')

    new_contracts.to_csv(destination_csv, index=False)
