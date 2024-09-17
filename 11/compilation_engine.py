from tokenizer_core import JackTokenizer
from vmwriter import ArithmeticCmd, Segment, VMWriter
from symboltable import SymbolKind, SymbolTable
from html import escape

class CompilationEngine:
    def __init__(self, source, dest):
        self.tokenizer   = JackTokenizer(source)
        self.output      = ''
        self.indentLevel = 0
        self.vm          = VMWriter(dest)
        self.symTab      = []
        self.tokenT      = None
        self.tokenR      = None
        self.currClass   = None
        self.labelnum    = 0
        self.tokenizer.advance()

    def getSymbolType(self, name):
        try:
            ty = self.symTab[-1].typeOf(name)
        except KeyError:
            ty = self.symTab[-2].typeOf(name)
        return ty

    def getSymbolSegment(self, name):
        try:
            seg = self.symTab[-1].kindOf(name)
        except KeyError:
            seg = self.symTab[-2].kindOf(name)
        return seg.value

    def getSymbolOffset(self, name):
        try:
            off = self.symTab[-1].indexOf(name)
        except KeyError:
            off = self.symTab[-2].indexOf(name)
        return off

    def getLabel(self):
        self.labelnum += 1
        return 'vm.__label__.' + str(self.labelnum)

    def emit(self, line):
        self.output += '  ' * self.indentLevel + line + '\n'

    def __process(self, expected_type, expected_repr):
        if not self.tokenizer.hasMoreTokens():
            raise SyntaxError('Ran out of tokens. ' + self.tokenizer.getErrorLine())

        tokenT = self.tokenizer.tokenType()
        tokenR = self.tokenizer.tokenRepr()

        if  expected_type and expected_type != tokenT:
            raise SyntaxError('Expected ' + expected_type + ', but got ' + tokenT + '. ' + tokenR + '\n' + self.tokenizer.getErrorLine())

        if  expected_repr and expected_repr != tokenR:
            raise SyntaxError('Expected ' + expected_repr + ', but got ' + tokenR + '. ' + tokenR + '\n' + self.tokenizer.getErrorLine())

    def process(self, expected_type = None, expected_repr = None):
        self.tokenT = self.tokenizer.tokenType()
        self.tokenR = self.tokenizer.tokenRepr()
        self.__process(expected_type, expected_repr)
        self.emit('<' + self.tokenT + '> ' + escape(self.tokenR) + ' </' + self.tokenT + '>')
        self.tokenizer.advance()

    def peek(self, expected_type, expected_repr = None):
        try:
            self.__process(expected_type, expected_repr)
        except SyntaxError:
            return False
        return True

    def peekType(self):
        isType = self.peek('keyword', 'int')
        isType = isType or self.peek('keyword', 'char')
        isType = isType or self.peek('keyword', 'boolean')
        isType = isType or self.peek('identifier')
        return isType

    def processType(self):
        if self.peekType():
            self.process()

    def peekOp(self):
        ops = ['+', '-', '*', '/', '&', '|', '<', '=', '>']

        if not self.tokenizer.hasMoreTokens():
            raise SyntaxError('Ran out of tokens!')

        if self.tokenizer.tokenType() == 'symbol' and self.tokenizer.tokenRepr() in ops:
            return True
        return False

    def begin(self, tag):
        self.emit('<' + tag + '>')
        self.indentLevel += 1

    def end(self, tag):
        self.indentLevel -= 1
        self.emit('</' + tag + '>')

    def compileClass(self):
        self.begin('class')
        self.process('keyword', 'class')
        self.process('identifier')
        self.currClass = self.tokenR
        self.process('symbol', '{')

        self.symTab.append(SymbolTable())

        while self.peek('keyword', 'static') or self.peek('keyword', 'field'):
            self.compileClassVarDec()

        while self.peek('keyword', 'constructor') or self.peek('keyword', 'function') or self.peek('keyword', 'method'):
            self.compileSubroutine()

        self.process('symbol', '}')

        self.symTab = self.symTab[:-1]

        self.end('class')

    def compileClassVarDec(self):
        self.begin('classVarDec')
        self.process('keyword') # Should be static or field. Presumably caller verifies!

        symkind = {'static' : SymbolKind.STATIC, 'field' : SymbolKind.FIELD }[self.tokenR]

        self.processType()
        symtype = self.tokenR

        self.process('identifier')
        symname = self.tokenR

        self.symTab[-1].define(symname, symtype, symkind)

        while self.peek('symbol', ','):
            self.process()
            self.process('identifier')
            symname = self.tokenR
            self.symTab[-1].define(symname, symtype, symkind)

        self.process('symbol', ';')
        self.end('classVarDec')

    def compileSubroutine(self):
        self.begin('subroutineDec')
        self.process('keyword') # Pray caller verifies: constructor, function, method
        ftype = self.tokenR
        rettype = 'void'
        if self.peek('keyword', 'void'):
            self.process()
        else:
            self.processType()
            rettype = self.tokenR

        # Subroutines have their own tables
        self.symTab.append(SymbolTable())

        self.process('identifier')
        fname = self.tokenR

        self.process('symbol', '(')
        self.compileParameterList(ftype)
        self.process('symbol', ')')
        self.compileSubroutineBody(fname, ftype)
        self.symTab = self.symTab[:-1]
        self.end('subroutineDec')

    def compileParameterList(self, ftype):
        self.begin('parameterList')
        count = 0
        if ftype == 'method':
            self.symTab[-1].define('this', self.currClass, SymbolKind.ARG)
            count += 1 # Reserved for 'this'
        if self.peekType():
            self.process()
            vartype = self.tokenR
            self.process('identifier')
            varname = self.tokenR
            self.symTab[-1].define(varname, vartype, SymbolKind.ARG)
            count += 1

            while(self.peek('symbol', ',')):
                self.process()
                self.processType()
                vartype = self.tokenR
                self.process('identifier')
                varname = self.tokenR
                self.symTab[-1].define(varname, vartype, SymbolKind.ARG)
                count += 1

        self.end('parameterList')
        return count

    def compileSubroutineBody(self, fname, ftype):
        self.begin('subroutineBody')
        self.process('symbol', '{')
        nvars = 0
        while self.peek('keyword', 'var'):
            nvars += self.compileVarDec()

        # We now write the function label
        self.vm.writeFunction(self.currClass + '.' + fname, nvars)

        if ftype == 'constructor':
            nfields = self.symTab[-2].varCount(SymbolKind.FIELD)
            if True or nfields: # TODO check this
                self.vm.writePush(Segment.CONSTANT, nfields)
                self.vm.writeCall('Memory.alloc', 1)
                self.vm.writePop(Segment.POINTER, 0)
        elif ftype == 'method':
            self.vm.writePush(Segment.ARGUMENT, 0)
            self.vm.writePop(Segment.POINTER, 0)

        self.compileStatements()
        self.process('symbol', '}')
        self.end('subroutineBody')

    def compileVarDec(self):
        count = 1
        self.begin('varDec')
        self.process('keyword','var')
        self.processType()
        symtype = self.tokenR
        self.process('identifier')
        symname = self.tokenR
        self.symTab[-1].define(symname, symtype, SymbolKind.VAR)
        while self.peek('symbol', ','):
            self.process()
            self.process('identifier')
            symname = self.tokenR
            self.symTab[-1].define(symname, symtype, SymbolKind.VAR)
            count += 1
        self.process('symbol', ';')
        self.end('varDec')
        return count

    def compileStatements(self):
        self.begin('statements')
        while True:
            if self.peek('keyword', 'let'):
                self.compileLet()

            elif self.peek('keyword', 'if'):
                self.compileIf()

            elif self.peek('keyword', 'while'):
                self.compileWhile()

            elif self.peek('keyword', 'do'):
                self.compileDo()

            elif self.peek('keyword', 'return'):
                self.compileReturn()
            else:
                break;
        self.end('statements')

    def compileLet(self):
        self.begin('letStatement')
        self.process('keyword', 'let')
        self.process('identifier')
        seg = self.getSymbolSegment(self.tokenR)
        off = self.getSymbolOffset(self.tokenR)
        assigningToArray = False
        if self.peek('symbol', '['):
            self.vm.writePush(seg, off)
            self.process()
            self.compileExpression()
            self.process('symbol',']')
            self.vm.writeArithmetic(ArithmeticCmd.ADD)
            assigningToArray = True
        self.process('symbol', '=')
        self.compileExpression()
        self.process('symbol', ';')
        if assigningToArray:
        # The code below ensures expressions such as let x[i] = y[j]; are handled right
            #self.vm.writePop(Segment.POINTER, 1)
            #self.vm.writePush(Segment.THAT, 0)
            self.vm.writePop(Segment.TEMP, 0)
            self.vm.writePop(Segment.POINTER, 1)
            self.vm.writePush(Segment.TEMP, 0)
            self.vm.writePop(Segment.THAT, 0)
        else:
            self.vm.writePop(seg, off)
        self.end('letStatement')

    def compileIf(self):
        self.begin('ifStatement')
        self.process('keyword', 'if')
        self.process('symbol', '(')
        self.compileExpression()
        self.process('symbol', ')')
        elsebody = self.getLabel()
        end = self.getLabel()
        # We add a 'NOT' because we will encounter the body
        # of the if condition next. By inverting the condition we
        # can elegantly make the if-body follow the if-goto
        self.vm.writeArithmetic(ArithmeticCmd.NOT)
        self.vm.writeIf(elsebody)
        self.process('symbol', '{')
        self.compileStatements()
        self.process('symbol', '}')
        self.vm.writeGoto(end)
        self.vm.writeLabel(elsebody)
        if self.peek('keyword', 'else'):
            self.process()
            self.process('symbol', '{')
            self.compileStatements()
            self.process('symbol', '}')
        self.vm.writeLabel(end)
        self.end('ifStatement')

    def compileWhile(self):
        self.begin('whileStatement')
        self.process('keyword','while')
        loop = self.getLabel()
        end = self.getLabel()
        self.vm.writeLabel(loop)
        self.process('symbol','(')
        self.compileExpression()
        self.process('symbol',')')
        self.vm.writeArithmetic(ArithmeticCmd.NOT)
        self.vm.writeIf(end)
        self.process('symbol', '{')
        self.compileStatements()
        self.process('symbol', '}')
        self.vm.writeGoto(loop)
        self.vm.writeLabel(end)
        self.end('whileStatement')

    def compileDo(self):
        self.begin('doStatement')
        self.process('keyword','do')
        self.compileExpression()
        self.process('symbol', ';')
        self.vm.writePop(Segment.TEMP, 0)
        self.end('doStatement')

    def compileReturn(self):
        self.begin('returnStatement')
        self.process('keyword', 'return')
        if not self.peek('symbol', ';'):
            self.compileExpression()
        else:
            self.vm.writePush(Segment.CONSTANT, 0)
        self.process('symbol', ';')
        self.vm.writeReturn()
        self.end('returnStatement')

    def compileExpression(self):
        self.begin('expression')
        self.compileTerm()
        while self.peekOp():
            self.process()
            op = self.tokenR
            self.compileTerm()
            if op == '+':
                self.vm.writeArithmetic(ArithmeticCmd.ADD)
            elif op == '-':
                self.vm.writeArithmetic(ArithmeticCmd.SUB)
            elif op == '*':
                self.vm.writeCall('Math.multiply', 2)
            elif op == '/':
                self.vm.writeCall('Math.divide', 2)
            elif op == '&':
                self.vm.writeArithmetic(ArithmeticCmd.AND)
            elif op == '|':
                self.vm.writeArithmetic(ArithmeticCmd.OR)
            elif op == '<':
                self.vm.writeArithmetic(ArithmeticCmd.LT)
            elif op == '=':
                self.vm.writeArithmetic(ArithmeticCmd.EQ)
            elif op == '>':
                self.vm.writeArithmetic(ArithmeticCmd.GT)
            else:
                raise NotImplementedError(op)
        self.end('expression')

    def compileTerm(self):
        self.begin('term')
        if self.peek('integerConstant'):
            self.process()
            self.vm.writePush(Segment.CONSTANT, self.tokenR)
        elif self.peek('stringConstant'):
            self.process()
            string = self.tokenR
            if not len(string):
                raise SyntaxError('Encountered empty string ""')
            self.vm.writePush(Segment.CONSTANT, len(string))
            self.vm.writeCall('String.new', 1)
            for char in string:
                self.vm.writePush(Segment.CONSTANT, ord(char))
                self.vm.writeCall('String.appendChar', 2)

        elif self.peek('keyword', 'null'):
            self.process()
            self.vm.writePush(Segment.CONSTANT, 0)
        elif self.peek('keyword', 'this'):
            self.process()
            self.vm.writePush(Segment.POINTER, 0)
        elif self.peek('keyword', 'true'):
            self.process()
            self.vm.writePush(Segment.CONSTANT, 0)
            self.vm.writeArithmetic(ArithmeticCmd.NOT)
        elif self.peek('keyword', 'false'):
            self.process()
            self.vm.writePush(Segment.CONSTANT, 0)
        elif self.peek('symbol', '-'):
            self.process()
            self.compileTerm()
            self.vm.writeArithmetic(ArithmeticCmd.NEG)
        elif self.peek('symbol', '~'):
            self.process()
            self.compileTerm()
            self.vm.writeArithmetic(ArithmeticCmd.NOT)
        elif self.peek('symbol', '('):
            self.process()
            self.compileExpression()
            self.process('symbol', ')')
        elif self.peek('identifier'):
            self.process()
            identifier = self.tokenR
            # TODO : Do we need more careful consideration, like so:
            # varName = self.tokenizer.tokenRepr()
            # assert(self.tokenizer.hasMoreTokens()) # Can't end in a term
            # self.advance()

            if self.peek('symbol', '['):
                # somearray[expr]
                self.process()
                self.vm.writePush(self.getSymbolSegment(identifier), self.getSymbolOffset(identifier))
                self.compileExpression()
                self.process('symbol', ']')
                self.vm.writeArithmetic(ArithmeticCmd.ADD)
                self.vm.writePop(Segment.POINTER, 1)
                self.vm.writePush(Segment.THAT, 0)
            elif self.peek('symbol', '.'):
                self.process()
                self.process('identifier')
                fname = self.tokenR
                nargs = 0
                try:
                    # obj.func(expr..)
                    className = self.getSymbolType(identifier)
                    thisSeg = self.getSymbolSegment(identifier)
                    thisOff = self.getSymbolOffset(identifier)
                    self.vm.writePush(thisSeg, thisOff)
                    nargs += 1
                except KeyError:
                    # ClassName.func(expr..)
                    className = identifier
                fname = className + '.' + fname
                self.process('symbol', '(')
                nargs += self.compileExpressionList()
                self.process('symbol', ')')
                self.vm.writeCall(fname, nargs)
            elif self.peek('symbol', '('):
                # somfunc(expr..)
                self.process()
                # TODO Should this only be done for methods?
                self.vm.writePush(Segment.POINTER, 0) # push this
                nargs = 1 + self.compileExpressionList()
                self.process('symbol', ')')
                self.vm.writeCall(self.currClass + '.' + identifier, nargs)
            else:
                # variable
                self.vm.writePush(self.getSymbolSegment(identifier), self.getSymbolOffset(identifier))
        else:
            raise SyntaxError('Invalid term: ' + self.tokenizer.tokenRepr() + '\n' + self.token.getErrorLine())

        self.end('term')

    def compileExpressionList(self):
        self.begin('expressionList')
        nargs = 0
        # We rely on the fact that expression list is empty only if
        # next token is a ')' symbol. This is because expression lists
        # are used only in case of subroutineCalls
        if not self.peek('symbol', ')'):
            self.compileExpression()
            nargs = 1
            while self.peek('symbol', ','):
                self.process()
                self.compileExpression()
                nargs += 1
        self.end('expressionList')
        return nargs

    def compile(self):
        self.compileClass()
        if self.tokenizer.hasMoreTokens():
            raise SyntaxError('Trailing tokens found' + self.tokenizer.getErrorLine())
        return self.output
