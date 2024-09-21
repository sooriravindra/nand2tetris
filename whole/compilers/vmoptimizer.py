#! /usr/bin/env python3
import sys
import os

def dfs(graph, source, visited):
    if source in visited:
        return
    visited.append(source)
    for neighbor in graph[source]:
        dfs(graph, neighbor, visited)

if len(sys.argv) != 2:
    print('Takes one argument');
    exit(1)

source_dir = sys.argv[1]
if os.path.isdir(source_dir):
    sources = [ os.path.join(source_dir,f) for f in os.listdir(source_dir) if f.endswith('.vm')]
else:
    print('Needs directory as an argument')
    exit(1)

callgraph = {}
allfunctions = []
lines = {}
for source in sources:
    with open(source) as f:
        lines[source] = []
        for line in f:
            line = line.strip()
            lines[source].append(line)
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

for source in sources:
    with open(source, 'w') as f:
        prefix = ''
        for line in lines[source]:
            if line.startswith('function '):
                name = line.split()[1]
                if name not in called:
                    prefix = '// optimized out --> | '
                else:
                    prefix = ''
            f.write(prefix + line + '\n')
