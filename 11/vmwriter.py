from enum import Enum
class Segment(Enum):
    CONSTANT = 'constant'
    ARGUMENT = 'argument'
    LOCAL    = 'local'
    STATIC   = 'static'
    THIS     = 'this'
    THAT     = 'that'
    POINTER  = 'pointer'
    TEMP     = 'temp'

class ArithmeticCmd(Enum):
    ADD = 'add'
    SUB = 'sub'
    NEG = 'neg'
    EQ  = 'eq'
    GT  = 'gt'
    LT  = 'lt'
    AND = 'and'
    OR  = 'or'
    NOT = 'not'

class VMWriter(object):
    def __init__(self, outputfile):
        self.f = open(outputfile, 'w')

    def emit(self, line):
        self.f.write(line + '\n')

    def writePush(self, seg, index):
        segment = None
        if type(seg) == Segment:
            segment = seg.value
        else:
            assert (seg in Segment), seg
            segment = seg
        self.emit('push ' + segment + ' ' + str(int(index)))


    def writePop(self, seg, index):
        segment = None
        if type(seg) == Segment:
            segment = seg.value
        else:
            assert (seg in Segment), seg
            segment = seg
        self.emit('pop ' + segment + ' ' + str(int(index)))

    def writeArithmetic(self, command):
        assert(type(command) == ArithmeticCmd)
        self.emit(command.value)

    def writeLabel(self, label):
        self.emit('label ' + label)

    def writeGoto(self, label):
        self.emit('goto ' + label)

    def writeIf(self, label):
        self.emit('if-goto ' + label)

    def writeCall(self, fname, nargs):
        self.emit('call ' + fname + ' ' + str(nargs))

    def writeFunction(self, fname, nvars):
        self.emit('function ' + fname + ' ' + str(nvars))

    def writeReturn(self):
        self.emit('return')

    def close():
        self.f.close()

