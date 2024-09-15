#! /usr/bin/env python3
import os
import sys
from compilation_engine import CompilationEngine

def usage():
    print(sys.argv[0] + ' filename.jack')
    exit(1)

if len(sys.argv) != 2:
    usage()

source = sys.argv[1]

if source[-5:] != '.jack' or not os.path.isfile(source):
    usage()

ce = CompilationEngine(source)

with open(os.path.basename(source[:-5]) + '.prs', 'w') as dest:
    dest.write(ce.compile())
