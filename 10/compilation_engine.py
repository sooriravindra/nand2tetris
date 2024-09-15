from tokenizer_core import JackTokenizer
from html import escape

class CompilationEngine:
    def __init__(self, source):
        self.tokenizer = JackTokenizer(source)
        self.output = ''
        self.indentLevel = 0
        self.tokenizer.advance()

    def emit(self, line):
        self.output += '  ' * self.indentLevel + line + '\n'

    def __process(self, expected_type, expected_repr):
        if not self.tokenizer.hasMoreTokens():
            raise SyntaxError('Ran out of tokens')

        tokenT = self.tokenizer.tokenType()
        tokenR = self.tokenizer.tokenRepr()

        if  expected_type and expected_type != tokenT:
            raise SyntaxError('Expected ' + expected_type + ', but got ' + tokenT + '. ' + tokenR)

        if  expected_repr and expected_repr != tokenR:
            raise SyntaxError('Expected ' + expected_repr + ', but got ' + tokenR)

    def process(self, expected_type = None, expected_repr = None):
        tokenT = self.tokenizer.tokenType()
        tokenR = self.tokenizer.tokenRepr()
        self.__process(expected_type, expected_repr)
        self.emit('<' + tokenT + '> ' + escape(tokenR) + ' </' + tokenT + '>')
        self.tokenizer.advance()

    def peek(self, expected_type, expected_repr = None):
        try:
            self.__process(expected_type, expected_repr)
        except SyntaxError:
            return False
        return True

    def processType(self):
        if self.peek('keyword', 'int') or self.peek('keyword', 'char') or self.peek('keyword', 'boolean'):
            self.process()
            return
        self.process('identifier')

    def peekOp(self):
        ops = ['+', '-', '*', '/', '&', '|', '<', '=', '>']

        if not self.hasMoreTokens():
            raise SyntaxError('Ran out of tokens!')

        if self.tokenizer.tokenType() != 'symbol' and self.tokenizer.tokenRepr() in ops:
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
        self.process('symbol', '{')

        while self.peek('keyword', 'static') or self.peek('keyword', 'field'):
            self.compileClassVarDec()

        while self.peek('keyword', 'constructor') or self.peek('keyword', 'function') or self.peek('keyword', 'method'):
            self.compileSubroutine()

        self.process('symbol', '}')
        self.end('class')

    def compileClassVarDec(self):
        self.begin('classVarDec')
        self.process('keyword') # Should be static or field. Presumably caller verifies!
        self.processType()
        self.process('identifier')
        while self.peek('symbol', ','):
            self.process()
            self.process('identifier')
        self.process('symbol', ';')
        self.end('classVarDec')

    def compileSubroutine(self):
        self.begin('subroutineDec')
        self.process('keyword') # Pray caller verifies: constructor, function, method
        if self.peek('keyword', 'void'):
            self.process()
        else:
            self.processType()
        self.process('identifier')
        self.process('symbol', '(')
        self.compileParameterList()
        self.process('symbol', ')')
        self.compileSubroutineBody()
        self.end('subroutineDec')

    def compileParameterList(self):
        self.begin('parameterList')

        if self.peek('keyword', 'int') or self.peek('keyword', 'char') or self.peek('keyword', 'boolean'):
            self.process()
            self.process('identifier')

            while(self.peek('symbol', ',')):
                self.process()
                self.processType()
                self.process('identifier')

        self.end('parameterList')

    def compileSubroutineBody(self):
        self.begin('subroutineBody')
        self.process('symbol', '{')
        while self.peek('keyword', 'var'):
            self.compileVarDec()
        self.compileStatements()
        self.process('symbol', '}')
        self.end('subroutineBody')

    def compileVarDec(self):
        self.begin('varDec')
        self.process('keyword','var')
        self.processType()
        self.process('identifier')
        while self.peek('symbol', ','):
            self.process()
            self.process('identifier')
        self.process('symbol', ';')
        self.end('varDec')

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
        if self.peek('symbol', '['):
            self.process()
            self.compileExpression()
            self.process('symbol',']')
        self.process('symbol', '=')
        self.compileExpression()
        self.process('symbol', ';')
        self.end('letStatement')

    def compileIf(self):
        self.begin('ifStatement')
        self.process('keyword', 'if')
        self.process('symbol', '(')
        self.compileExpression()
        self.process('symbol', ')')
        self.process('symbol', '{')
        self.compileStatements()
        self.process('symbol', '}')
        if self.peek('keyword', 'else'):
            self.process()
            self.process('symbol', '{')
            self.compileStatements()
            self.process('symbol', '}')
        self.end('ifStatement')

    def compileWhile(self):
        self.begin('whileStatement')
        self.process('keyword','while')
        self.process('symbol','(')
        self.compileExpression()
        self.process('symbol',')')
        self.process('symbol', '{')
        self.compileStatements()
        self.process('symbol', '}')
        self.end('whileStatement')

    def compileDo(self):
        self.begin('doStatement')
        self.process('keyword','do')
        # Subroutine call
        self.process('identifier')
        if self.peek('symbol', '.'):
            # some.func()
            self.process()
            self.process('identifier')
        self.process('symbol', '(')
        self.compileExpressionList()
        self.process('symbol', ')')
        self.process('symbol', ';')
        self.end('doStatement')

    def compileReturn(self):
        self.begin('returnStatement')
        self.process('keyword', 'return')
        if not self.peek('symbol', ';'):
            self.compileExpression()
        self.process('symbol', ';')
        self.end('returnStatement')

    def compileExpression(self):
        # TODO implement expression
        self.begin('expression')
        self.compileTerm()
        self.end('expression')

    def compileTerm(self):
        # TODO implement term
        self.begin('term')
        self.process()
        self.end('term')

    def compileExpressionList(self):
        self.begin('expressionList')
        # TODO revisit below condition
        if not self.peek('symbol'):
            self.compileExpression()
            while self.peek('symbol', ','):
                self.process()
                self.compileExpression()
        self.end('expressionList')

    def compile(self):
        self.compileClass()
        if self.tokenizer.hasMoreTokens():
            raise SyntaxError('Trailing tokens found')
        return self.output
