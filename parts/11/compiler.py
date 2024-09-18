#! /usr/bin/env python3
import os
import sys
from compilation_engine import CompilationEngine

def usage():
    print(sys.argv[0] + '[filename.jack | directory]')
    exit(1)

if len(sys.argv) != 2:
    usage()

source = sys.argv[1]

sources = []

if source.endswith('.jack') and os.path.isfile(source):
    sources = [source]
elif os.path.isdir(source):
    sources = [ os.path.join(source,f) for f in os.listdir(source) if f.endswith('.jack')]

if len(sources) == 0:
    print('Expected a directory with some .jack files or a .jack file')
    usage()

for source_file in sources:
    dest_file = source_file[:-5] + '.vm'
    ce = CompilationEngine(source_file , dest_file)
    ce.compile()
