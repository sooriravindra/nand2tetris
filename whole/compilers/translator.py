#! /usr/bin/env python3
import sys
from enum import Enum

class CommandType(Enum):
    C_ARITHMETIC = 0
    C_PUSH       = 1
    C_POP        = 2
    C_LABEL      = 3
    C_GOTO       = 4
    C_IF         = 5
    C_FUNCTION   = 6
    C_RETURN     = 7
    C_CALL       = 8

class CodeWriter(object):
    def __init__(self, dest):
        self.f = open(dest, 'x')
        self.labelnum = -1
        # self.f.write('@256\n')
        # self.f.write('D=A\n')
        # self.f.write('@SP\n')
        # self.f.write('M=D\n')

    def close(self):
        self.f.close()

    def emit(self, line):
        self.f.write(line + '\n')

    def writeComment(self,comment):
        self.emit('//' + comment)

    def segmentSpecificCode(self, segment, offset):
        asm = ''
        segment_map = {
                       'local'    : 'LCL',
                       'argument' : 'ARG',
                       'this'     : 'THIS',
                       'that'     : 'THAT'
                      }
        if segment in segment_map:
            asm += '@' + segment_map[segment] + '\n'
            asm += 'D=M\n'
            asm += '@' + str(int(offset)) + '\n'
            asm += 'A=D+A\n'
            asm += 'D=M\n'
        elif segment == 'temp':
            asm += '@' + str(5 + int(offset)) + '\n'
            asm += 'D=M\n'
        elif segment == 'static':
            var = 'TODO.' + offset
            asm += '@' + var + '\n'
            asm += 'D=M\n'
        elif segment == 'constant':
            asm += '@' + str(int(offset)) + '\n'
            asm += 'D=A\n'
        elif segment == 'pointer':
            asm += '@' + ('THIS' if not int(offset) else 'THAT') + '\n'
            asm += 'D=M\n'
        else:
            raise NotImplementedError(segment)

        return asm



    def writeArithmetic(self, ins):
        asm = ''
        if ins == 'add' or ins == 'sub' or ins == 'and' or ins == 'or':
            asm += '@SP\n'
            asm += 'A=M\n'
            asm += 'A=A-1\n'
            asm += 'D=M\n'
            asm += 'A=A-1\n'
            if ins == 'add':
                asm += 'M=D+M\n'
            elif ins == 'sub':
                asm += 'M=M-D\n'
            elif ins == 'and':
                asm += 'M=D&M\n'
            elif ins == 'or':
                asm += 'M=D|M\n'
            asm += 'D=A+1\n'
            asm += '@SP\n'
            asm += 'M=D\n'
        elif ins == 'neg' or ins == 'not':
            asm += '@SP\n'
            asm += 'A=M\n'
            asm += 'A=A-1\n'
            if ins == 'neg':
                asm += 'M=-M\n'
            elif ins == 'not':
                asm += 'M=!M\n'
        elif ins =='eq' or ins == 'lt' or ins == 'gt':
            self.labelnum += 1
            asm += '@SP\n'
            asm += 'A=M-1\n'
            asm += 'D=M\n'
            asm += 'A=A-1\n'
            asm += 'D=M-D\n'
            asm += '@__internal__.' + str(self.labelnum) + '.true\n'
            if ins == 'eq':
                asm += 'D;JEQ\n'
            elif ins == 'lt':
                asm += 'D;JLT\n'
            elif ins == 'gt':
                asm += 'D;JGT\n'
            asm += 'D=0\n'
            asm += '@__internal__.' + str(self.labelnum) + '.end\n'
            asm += '0;JMP\n'
            asm += '(__internal__.' + str(self.labelnum) + '.true)\n'
            asm += 'D=-1\n'
            asm += '(__internal__.' + str(self.labelnum) + '.end)\n'
            asm += '@SP\n'
            asm += 'M=M-1\n'
            asm += 'A=M-1\n'
            asm += 'M=D\n'
        else:
            raise NotImplementedError(ins)
        self.emit(asm)

    def writePushPop(self, cmd, arg1, arg2):
        asm = self.segmentSpecificCode(arg1, arg2)
        if cmd == CommandType.C_PUSH:
            asm += '@SP\n'
            asm += 'A=M\n'
            asm += 'M=D\n'
            asm += '@SP\n'
            asm += 'M=M+1'
        elif cmd == CommandType.C_POP:
            asm += 'D=A\n'
            asm += '@SP\n'
            asm += 'M=M-1\n'
            asm += 'A=M\n'
            asm += 'A=M\n'
            asm += 'A=D+A\n'
            asm += 'D=A-D\n'
            asm += 'A=A-D\n'
            asm += 'M=D'
        self.emit(asm)


class Parser(object):
    def __init__(self, source):
        self.curr_line_num = -1
        self.lines = []
        if not source.endswith('.vm'):
            print('Input needs to have .vm extension')
            exit(1)

        with open(source, 'r') as f:
            for line in f:
                line = line.strip()
                if not (len(line) == 0 or line.startswith('//')):
                    self.lines.append(line)

    def hasMoreLines(self):
        return (self.curr_line_num + 1) < len(self.lines)

    def advance(self):
        self.curr_line_num+=1
        line = self.lines[self.curr_line_num]
        self.words = line.split()

    def currentCmd(self):
        return self.lines[self.curr_line_num]

    def commandType(self):
        arithmetic = [ 'add', 'sub', 'neg',
                      'eq', 'gt', 'lt', 'and', 'or', 'not' ]

        if self.words[0] == 'push':
            return CommandType.C_PUSH
        elif self.words[0] == 'pop':
            return CommandType.C_POP
        elif self.words[0] in arithmetic:
            return CommandType.C_ARITHMETIC

        raise NotImplementedError(self.words[0])


    def arg1(self):
        if self.commandType() == CommandType.C_ARITHMETIC:
            return self.words[0]
        return self.words[1]

    def arg2(self):
        return self.words[2]

if len(sys.argv) != 2:
    print('Usage incorrect')
    exit(1)

source = sys.argv[1]
dest   = source[:-3] + '.asm'
p      = Parser(source)
cw     = CodeWriter(dest)

while p.hasMoreLines():
    p.advance()
    cw.writeComment(p.currentCmd())
    cmd = p.commandType()
    if cmd == CommandType.C_ARITHMETIC:
        cw.writeArithmetic(p.arg1())
    else:
        cw.writePushPop(cmd, p.arg1(), p.arg2())
cw.close()
