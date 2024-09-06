import sys

nextInsAddr = 0
nextAddr    = 16
variables   = {}
labels      = {}
predefined  = {
    'R0'     : 0,
    'R1'     : 1,
    'R2'     : 2,
    'R3'     : 3,
    'R4'     : 4,
    'R5'     : 5,
    'R6'     : 6,
    'R7'     : 7,
    'R8'     : 8,
    'R9'     : 9,
    'R10'    : 10,
    'R11'    : 11,
    'R12'    : 12,
    'R13'    : 13,
    'R14'    : 14,
    'R15'    : 15,
    'SCREEN' : 16384,
    'KBD'    : 24576,
    'SP'     : 0,
    'LCL'    : 1,
    'ARG'    : 2,
    'THIS'   : 3,
    'THAT'   : 4
}

jmpMap = {
    'JGT' : 1,
    'JEQ' : 2,
    'JGE' : 3,
    'JLT' : 4,
    'JNE' : 5,
    'JLE' : 6,
    'JMP' : 7
}

compMap = {
    '0'   : 0x2A,
    '1'   : 0x3f,
    '-1'  : 0x3A,
    'D'   : 0x0C,
    'A'   : 0x30,
    'M'   : 0x30,
    '!D'  : 0x0D,
    '!A'  : 0x31,
    '!M'  : 0x31,
    '-D'  : 0x0F,
    '-A'  : 0x33,
    '-M'  : 0x33,
    'D+1' : 0x1F,
    'A+1' : 0x37,
    'M+1' : 0x37,
    'D-1' : 0x0E,
    'A-1' : 0x32,
    'M-1' : 0x32,
    'D+A' : 0x02,
    'D+M' : 0x02,
    'D-A' : 0x13,
    'D-M' : 0x13,
    'A-D' : 0x07,
    'M-D' : 0x07,
    'D&A' : 0x00,
    'D&M' : 0x00,
    'D|A' : 0x15,
    'D|M' : 0x15
}

destMap = {
    'M' :  1,
    'D' :  2,
    'DM':  3,
    'MD':  3,
    'A' :  4,
    'AM':  5,
    'AD':  6,
    'ADM': 7,
    'AMD': 7
}

machine_code = ''

def emit(ins):
    global machine_code
    machine_code += '{:016b}'.format(ins)
    machine_code += '\n'

def isnum(str):
    try:
        int(str)
        return True
    except ValueError:
        return False

def syntax_error(num, err=''):
    print('Syntax error in line ', num)
    if len(err):
        print(err)
    exit(1)

def getaddr(sym):
    global nextAddr
    if sym in predefined:
        return predefined[sym]
    if sym in labels:
        return labels[sym]
    if sym not in variables:
        variables[sym] = nextAddr
        nextAddr += 1
    return variables[sym]

def preprocess(line):
    global nextInsAddr
    line = line.strip()
    if len(line) == 0 or line.startswith('//'):
        return
    if line[0] == '(' and line[-1] == ')' and len(line[1:-1]):
        labels[line[1:-1]] = nextInsAddr
    else:
        nextInsAddr += 1

def process(num, line):
    line = line.strip()
    if len(line) == 0 or line.startswith('//') or (line[0] == '(' and line[-1] == ')'):
        return False
    if line.startswith('@'):
        # A instruction
        addr = line[1:]
        if isnum(addr):
            emit(int(addr) & 0x7fff)
        else:
            sym_addr = getaddr(addr)
            emit(sym_addr)
    else:
        # C instruction
        # Mov command = First half till ';' or the entire line
        # Jmp command = Portion after ';'
        mov_cmd = line
        jmp_cmd = ''
        sep_pos = line.find(';')

        if (sep_pos != -1):
            mov_cmd = line[:sep_pos]
            jmp_cmd = line[sep_pos + 1 : ]

        mov_cmd = mov_cmd.strip()
        jmp_cmd = jmp_cmd.strip()

        ones  = 7
        dbits = 0
        jbits = 0
        cbits = 0
        abit  = 0

        if (mov_cmd.find('=') != -1):
            dest = mov_cmd[:mov_cmd.find('=')]
            dest = dest.strip()

            try:
                dbits = destMap[dest]
            except KeyError:
                syntax_error(num, 'Invalid destination')

        if len(jmp_cmd):
            try:
                jbits = jmpMap[jmp_cmd]
            except KeyError:
                syntax_error(num, 'Invalid jump command')

        comp_cmd = mov_cmd[mov_cmd.find('=') + 1:]
        comp_cmd = comp_cmd.replace('\t','')
        comp_cmd = comp_cmd.replace(' ','')
        try:
            cbits = compMap[comp_cmd]
            abit  = int(comp_cmd.find('M') != -1)
        except KeyError:
            syntax_error(num, 'Unexpected token encountered')


        emit(int(7<<13 | abit << 12| cbits << 6 | dbits << 3 | jbits))
        return True

if len(sys.argv) != 2:
    print('Usage incorrect');
    exit(1)

source = sys.argv[1]
if not source.endswith('.asm'):
    print('Input needs to have .asm extension')
    exit(1)

with open(source) as f:
    num = 1
    for line in f:
        preprocess(line)
    f.seek(0)
    for line in f:
        process(num, line)
        num += 1
    print(machine_code, end='')
