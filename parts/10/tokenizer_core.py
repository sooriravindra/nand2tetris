class JackTokenizer(object):
    def __init__(self, filename):
        self.filename = filename
        self.f = open(filename, 'r')
        self.readbuffer = ''
        self.currType = None
        self.currRepr = ''
        self.over = False
        self.lastReadChar = None
        self.whitespace = ' \t\n\r'
        self.symbols = ['{','}','(',')','[',']','.',',',';','+','-','*','/','&','|','<','>','=','~']
        self.keywords = ['class', 'constructor', 'function', 'method', 'field',
                    'static', 'var', 'int', 'char', 'boolean', 'void' , 'true' ,'false',
                    'null' ,'this', 'let', 'do', 'if', 'else', 'while' ,'return']


    def __readchar(self):
        c = self.f.read(1)
        self.readbuffer += c
        return c

    def getErrorLine(self):
        i = self.readbuffer.rfind('\n')
        if i == -1:
            return self.readbuffer
        return self.readbuffer[i:]

    def eat(self):
        if not self.lastReadChar:
            return
        while self.lastReadChar in self.whitespace:
            self.lastReadChar = self.__readchar()
            if not self.lastReadChar:
                return

    def flushTill(self, end):
        self.currRepr = ''
        self.lastReadChar = None
        # Hacky
        queue = 'A'*len(end)
        c = True
        while c and queue != end:
            c = self.__readchar()
            queue += c
            queue = queue[1:]

    def advance(self):

        self.currType = None
        self.currRepr = ''

        while True:

            processing_string = len(self.currRepr) and self.currRepr[0] == '"'

            if processing_string:

                if self.lastReadChar == '\n':
                    raise ValueError('String cannot contain newline: ' + self.currRepr)
                # String constant
                if self.lastReadChar == '"':
                    self.lastReadChar = None
                    self.currRepr = self.currRepr[1:]
                    self.currType = 'stringConstant';
                    break

            elif len(self.currRepr):
                # Symbol
                if self.currRepr in self.symbols:
                    if self.currRepr == '/' and self.lastReadChar == '/':
                        self.flushTill('\n')
                        continue
                    if self.currRepr == '/' and self.lastReadChar == '*':
                        self.flushTill('*/')
                        continue
                    self.currType = 'symbol'
                    break
                if (self.lastReadChar in self.symbols or self.lastReadChar in self.whitespace):

                    # Keywords
                    if self.currRepr in self.keywords:
                        self.currType = 'keyword'
                        break

                    # Integer constant
                    try:
                        num = int(self.currRepr)
                        if num >= 0 and num < 32768:
                            self.currType = 'integerConstant'
                            break
                        else:
                            # TODO choose apt error
                            raise RuntimeError(self.currRepr + ' needs be in 0..32767')
                    except ValueError:
                        # We don't fail
                        pass

                    # Identifier
                    for char in self.currRepr:
                        if not char.isalpha() and not char.isdigit() and char != '_':
                            raise ValueError('Plausible use of illegal character in an identifier: ' + char + ' : >' + self.currRepr + '<')

                    if self.currRepr[0].isdigit():
                        raise ValueError('Encountered a possible identifier starting with a digit')

                    self.currType = 'identifier'
                    break

            # Apppend only when there is a valid non-whitespace character for first char 
            if self.lastReadChar and (self.currRepr != '' or self.lastReadChar not in self.whitespace):
                self.currRepr += self.lastReadChar

            self.lastReadChar = self.__readchar()
            if not self.lastReadChar:
                self.over = True
                return

        self.eat()


    def hasMoreTokens(self):
        return not self.over

    def tokenType(self):
        return self.currType

    def tokenRepr(self):
        return self.currRepr
