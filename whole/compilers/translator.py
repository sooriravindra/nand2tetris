#! /usr/bin/env python3
import sys
import os
import argparse
from enum import Enum

optimized = []

def dfs(graph, source, visited):
    if source in visited:
        return
    visited.append(source)
    for neighbor in graph[source]:
        dfs(graph, neighbor, visited)

def removeDeadCode(sources):
    callgraph = {}
    allfunctions = []
    # lines = {}
    for source in sources:
        with open(source) as f:
            # lines[source] = []
            print('optimizing ' + source)
            for line in f:
                line = line.strip()
                # lines[source].append(line)
                if line.startswith('call '):
                    caller = allfunctions[-1]
                    callee = line.split()[1]
                    callgraph[caller].append(callee)
                elif line.startswith('function '):
                    name = line.split()[1]
                    allfunctions.append(name)
                    callgraph[name] = []

    called = []
    dfs(callgraph, 'Sys.init', called)

    unused_functions = []
    for function in allfunctions:
        if not function in called:
            unused_functions.append(function)

    print("Unused functions list:")
    for function in unused_functions:
        print(function)

    return unused_functions

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
        self.f = open(dest, 'w')
        self.labelnum = -1
        self.currfile = '__Jack__'
        self.currfunction = '__Jill__'
        self.returnlabels = {}
        self.writeToDest = True

        # bootstrap code here
        # NOTE: Comment it out for SimpleFunction, BasicLoop and FibonacciSeries tests
        # SP <- 256
        # call Sys.init
        # NOTE: Using a goto instead of call works, but fails testcases since resulting stack is not identical
        self.emit('@256')
        self.emit('D=A')
        self.emit('@SP')
        self.emit('M=D')
        self.emit('@Sys.init')
        self.emit('0;JMP')

        if 'return' in optimized:
            self.writeOptimizedReturn()

        if 'cond' in optimized:
            self.writeOptimizedComp()

        if 'call' in optimized:
            self.writeOptimizedCall()

    def setFileName(self, fname):
        self.currfile = os.path.basename(fname)[:-3]

    def close(self):
        self.f.close()

    def emit(self, line):
        if (self.writeToDest):
            self.f.write(line + '\n')

    def writeComment(self,comment):
        self.emit('//' + comment)

    def shouldWriteToDest(self, write):
        self.writeToDest = write

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
            var = self.currfile + '.' + offset
            asm += '@' + var + '\n'
            asm += 'D=M\n'
        elif segment == 'constant':
            asm += '@' + offset + '\n'
            asm += 'D=A\n'
        elif segment == 'pointer':
            asm += '@' + ('THIS' if int(offset) == 0 else 'THAT') + '\n'
            asm += 'D=M\n'
        elif segment == 'internal':
            asm += '@' + offset + '\n'
            asm += 'D=M\n'
        else:
            raise NotImplementedError(segment)

        return asm


    def writeOptimizedComp(self):
        for ins in ['eq', 'gt', 'lt']:
            self.writeLabel('optimized.' + ins)
            asm  = '@R13\n'
            asm += 'M=D\n'
            asm += '@SP\n'
            asm += 'A=M-1\n'
            asm += 'D=M\n'
            asm += 'A=A-1\n'
            asm += 'D=M-D\n'
            asm += '@' + self.getLabel('cond.' + ins + '.true') + '\n'
            if ins == 'eq':
                asm += 'D;JEQ\n'
            elif ins == 'lt':
                asm += 'D;JLT\n'
            elif ins == 'gt':
                asm += 'D;JGT\n'
            asm += 'D=0\n'
            asm += '@' + self.getLabel('cond.' + ins + '.end') + '\n'
            asm += '0;JMP\n'
            asm += '(' + self.getLabel('cond.' + ins + '.true') + ')\n'
            asm += 'D=-1\n'
            asm += '(' + self.getLabel('cond.' + ins + '.end') + ')\n'
            asm += '@SP\n'
            asm += 'M=M-1\n'
            asm += 'A=M-1\n'
            asm += 'M=D\n'
            asm += '@R13\n'
            asm += 'A=M\n'
            asm += '0;JMP\n'
            self.emit(asm)

    def writeArithmetic(self, ins):
        conds = ['eq', 'lt' , 'gt']
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
        elif ins in conds:
            self.labelnum += 1
            if 'cond' in optimized:
                retlabel = self.getLabel(ins + '.call.' + str(self.labelnum))
                asm += '@' + retlabel + '\n'
                asm += 'D=A\n'
                asm += '@__Jill__$optimized.' + ins + '\n'
                asm += '0;JMP\n'
                asm += '(' + retlabel + ')\n'
            else:
                asm += '@SP\n'
                asm += 'A=M-1\n'
                asm += 'D=M\n'
                asm += 'A=A-1\n'
                asm += 'D=M-D\n'
                asm += '@' + self.getLabel('cond' + str(self.labelnum)+ '.true') + '\n'
                if ins == 'eq':
                    asm += 'D;JEQ\n'
                elif ins == 'lt':
                    asm += 'D;JLT\n'
                elif ins == 'gt':
                    asm += 'D;JGT\n'
                asm += 'D=0\n'
                asm += '@' + self.getLabel('cond' + str(self.labelnum)+ '.end') + '\n'
                asm += '0;JMP\n'
                asm += '(' + self.getLabel('cond' + str(self.labelnum) + '.true') + ')\n'
                asm += 'D=-1\n'
                asm += '(' + self.getLabel('cond' + str(self.labelnum) + '.end') + ')\n'
                asm += '@SP\n'
                asm += 'M=M-1\n'
                asm += 'A=M-1\n'
                asm += 'M=D'
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

    def getLabel(self, label):
        return self.currfunction + '$' + label

    def writeLabel(self,label):
        asm = '(' + self.getLabel(label) + ')'
        self.emit(asm)

    def writeGoto(self,label):
        asm = '@'+ self.getLabel(label) + '\n'
        asm += '0;JMP'
        self.emit(asm)

    def writeIf(self,label):
        asm = '@SP\n'
        asm += 'M=M-1\n'
        asm += 'A=M\n'
        asm += 'D=M\n'
        asm += '@'+ self.getLabel(label) + '\n'
        asm += 'D;JNE'
        self.emit(asm)

    def getFunctionEntry(self, fname):
        # if fname == 'Sys.init':
        #     return fname
        # return self.currfile + '.' + fname
        return fname

    def writeFunction(self,fname, nvars):
        self.currfunction = fname
        self.emit('(' + self.getFunctionEntry(fname) + ')')
        for i in range(int(nvars)):
            self.writePushPop(CommandType.C_PUSH, 'constant', '0')


    def getReturnLabel(self):
        fname = self.currfunction
        if fname in self.returnlabels:
            self.returnlabels[fname] += 1
        else:
            self.returnlabels[fname] = 0
        return fname + '$ret.'+ str(self.returnlabels[fname])

    def writeOptimizedCall(self):
        self.writeLabel('optimized.call')
        # push return-label (D)
        asm  = '@SP\n'
        asm += 'A=M\n'
        asm += 'M=D\n'
        asm += '@SP\n'
        asm += 'M=M+1'
        self.emit(asm)

        # push LCL
        self.writePushPop(CommandType.C_PUSH, 'internal', '1')

        # push ARG
        self.writePushPop(CommandType.C_PUSH, 'internal', '2')

        # push THIS
        self.writePushPop(CommandType.C_PUSH, 'internal', '3')

        # push THAT
        self.writePushPop(CommandType.C_PUSH, 'internal', '4')

        # ARG = SP - 5 - nargs
        self.writePushPop(CommandType.C_PUSH, 'internal', '0')
        self.writePushPop(CommandType.C_PUSH, 'constant', '5')
        self.writePushPop(CommandType.C_PUSH, 'internal', '14') # push nargs (R14)
        self.writeArithmetic('add')
        self.writeArithmetic('sub')
        self.writePushPop(CommandType.C_POP, 'internal', '2')

        # LCL = SP
        asm  = '@SP\n'
        asm += 'D=M\n'
        asm += '@LCL\n'
        asm += 'M=D\n'

        # go to function (R13)
        asm += '@R13\n'
        asm += 'A=M\n'
        asm += '0;JMP\n'

        self.emit(asm)

    def writeCall(self,fname, nargs):
        retlabel = self.getReturnLabel()

        if 'call' in optimized:
            # R13 <- Function
            # R14 <- Nargs
            # D   <- return label
            asm = ''
            asm += '@'+ self.getFunctionEntry(fname) + '\n'
            asm += 'D=A\n'
            asm += '@R13\n'
            asm += 'M=D\n'
            asm += '@'+ str(nargs) +'\n'
            asm += 'D=A\n'
            asm += '@R14\n'
            asm += 'M=D\n'
            asm += '@'+ str(retlabel) +'\n'
            asm += 'D=A\n'
            asm += '@__Jill__$optimized.call\n'
            asm += '0;JMP\n'
            asm += '(' + retlabel + ')'
            self.emit(asm)
            return
        # push return-label
        self.writePushPop(CommandType.C_PUSH, 'constant', retlabel)

        # push LCL
        self.writePushPop(CommandType.C_PUSH, 'internal', '1')

        # push ARG
        self.writePushPop(CommandType.C_PUSH, 'internal', '2')

        # push THIS
        self.writePushPop(CommandType.C_PUSH, 'internal', '3')

        # push THAT
        self.writePushPop(CommandType.C_PUSH, 'internal', '4')

        # ARG = SP - 5 - nargs
        self.writePushPop(CommandType.C_PUSH, 'internal', '0')
        self.writePushPop(CommandType.C_PUSH, 'constant', '5')
        self.writePushPop(CommandType.C_PUSH, 'constant', nargs)
        self.writeArithmetic('add')
        self.writeArithmetic('sub')
        self.writePushPop(CommandType.C_POP, 'internal', '2')

        # LCL = SP
        asm  = '@SP\n'
        asm += 'D=M\n'
        asm += '@LCL\n'
        asm += 'M=D\n'

        # goto function
        asm += '@'+ self.getFunctionEntry(fname) + '\n'
        asm += '0;JMP\n'

        # (return label)
        asm += '(' + retlabel + ')'
        self.emit(asm)

    def writeOptimizedReturn(self):
        self.writeLabel('optimized.return')
        self.writeFullReturn()

    def writeReturn(self):
        if 'return' in optimized:
            self.emit('@__Jill__$optimized.return')
            self.emit('0;JMP')
        else:
            self.writeFullReturn()

    def writeFullReturn(self):
        asm = ''

        # return address = *(LCL-5) 
        asm += '@LCL\n'
        asm += 'A=M-1\n'
        asm += 'A=A-1\n'
        asm += 'A=A-1\n'
        asm += 'A=A-1\n'
        asm += 'A=A-1\n'
        asm += 'D=M\n'
        asm += '@R13\n' # Temp register
        asm += 'M=D\n'
        self.emit(asm)

        # *ARG = pop()
        self.writePushPop(CommandType.C_POP, 'argument', '0')

        # SP = ARG + 1
        asm = ''
        asm += '@ARG\n'
        asm += 'D=M+1\n'
        asm += '@SP\n'
        asm += 'M=D\n'

        # end = LCL
        # THAT = *(end - 1)
        asm += '@LCL\n'
        asm += 'A=M-1\n'
        asm += 'D=M\n'
        asm += '@THAT\n'
        asm += 'M=D\n'

        # THIS = *(end - 2)
        asm += '@LCL\n'
        asm += 'A=M-1\n'
        asm += 'A=A-1\n'
        asm += 'D=M\n'
        asm += '@THIS\n'
        asm += 'M=D\n'

        # ARG = *(end - 3)
        asm += '@LCL\n'
        asm += 'A=M-1\n'
        asm += 'A=A-1\n'
        asm += 'A=A-1\n'
        asm += 'D=M\n'
        asm += '@ARG\n'
        asm += 'M=D\n'

        # LCL = *(end - 4)
        asm += '@LCL\n'
        asm += 'A=M-1\n'
        asm += 'A=A-1\n'
        asm += 'A=A-1\n'
        asm += 'A=A-1\n'
        asm += 'D=M\n'
        asm += '@LCL\n'
        asm += 'M=D\n'

        # goto return address
        asm += '@R13\n'
        asm += 'A=M\n'
        asm += '0;JMP'
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
        elif self.words[0] == 'call':
            return CommandType.C_CALL
        elif self.words[0] == 'return':
            return CommandType.C_RETURN
        elif self.words[0] == 'function':
            return CommandType.C_FUNCTION
        elif self.words[0] == 'if-goto':
            return CommandType.C_IF
        elif self.words[0] == 'label':
            return CommandType.C_LABEL
        elif self.words[0] == 'goto':
            return CommandType.C_GOTO

        raise NotImplementedError(self.words[0])


    def arg1(self):
        if self.commandType() == CommandType.C_ARITHMETIC:
            return self.words[0]
        return self.words[1]

    def arg2(self):
        return self.words[2]

def generateCode(sources, dest, unused_functions):
    cw = CodeWriter(dest)

    for s in sources:
        p = Parser(s)
        cw.setFileName(s)

        while p.hasMoreLines():
            p.advance()
            cw.writeComment(p.currentCmd())
            cmd = p.commandType()
            if cmd == CommandType.C_ARITHMETIC:
                cw.writeArithmetic(p.arg1())
            elif cmd == CommandType.C_PUSH or cmd == CommandType.C_POP:
                cw.writePushPop(cmd, p.arg1(), p.arg2())
            elif cmd == CommandType.C_LABEL:
                cw.writeLabel(p.arg1())
            elif cmd == CommandType.C_IF:
                cw.writeIf(p.arg1())
            elif cmd == CommandType.C_GOTO:
                cw.writeGoto(p.arg1())
            elif cmd == CommandType.C_FUNCTION:
                if (p.arg1() in unused_functions):
                    cw.shouldWriteToDest(False)
                else:
                    cw.shouldWriteToDest(True)
                cw.writeFunction(p.arg1(), p.arg2())
            elif cmd == CommandType.C_RETURN:
                cw.writeReturn()
            elif cmd == CommandType.C_CALL:
                cw.writeCall(p.arg1(),p.arg2())
            else:
                raise NotImplementedError(cmd)
    cw.close()

def main():
    global optimized
    unused_functions = []
    dest = None

    ap = argparse.ArgumentParser()
    ap.add_argument('--optimize', help='A comma seperated list of optimizations to apply such as "deadcode,cond"')
    ap.add_argument('source', help='A .vm file or a directory containing one more .vm files')
    args = ap.parse_args()

    if args.optimize:
        optimized = args.optimize.split(',')
        for each in optimized:
            print('optimizing ' + each)

    if args.source.endswith('.vm') and os.path.isfile(args.source):
        sources = [args.source]
        dest   = args.source[:-3] + '.asm'
    elif os.path.isdir(args.source):
        sources = [ os.path.join(args.source,f) for f in os.listdir(args.source) if f.endswith('.vm')]
        dest = args.source + '.asm'

    if len(sources) == 0:
        print('Expected a directory with some .vm files or a .vm file')
        exit(1)

    if 'deadcode' in optimized:
        unused_functions = removeDeadCode(sources)

    generateCode(sources, dest, unused_functions)

# Now we begin
if __name__ == '__main__':
    main()
