from enum import Enum
class SymbolKind(Enum):
    STATIC = 'static'
    FIELD  = 'this'
    ARG    = 'argument'
    VAR    = 'local'

class SymbolTable(object):
    def __init__(self):
        self.table = []

    def reset(self):
        self.table = []

    def define(self, name, symtype, kind):
        assert(type(kind) == SymbolKind)
        try:
            self.__getEntryForName(name, 1)
            raise SyntaxError('Duplicate symbol defined: ' + name)
        except KeyError:
            pass
        count = self.varCount(kind)
        self.table.append([name, symtype, kind, count])

    def varCount(self, kind):
        return len(list(filter(lambda x: x[2] == kind, self.table)))

    def __getEntryForName(self, name, index):
        for x in self.table:
            if x[0] == name:
                return x[index]
        raise KeyError(name)

    def typeOf(self, name):
        return self.__getEntryForName(name, 1)

    def kindOf(self, name):
        return self.__getEntryForName(name, 2)

    def indexOf(self, name):
        return self.__getEntryForName(name, 3)
