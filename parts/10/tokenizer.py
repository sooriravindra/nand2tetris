#! /usr/bin/env python3

import sys
import os
from html import escape
from tokenizer_core import JackTokenizer

def usage():
    print(sys.argv[0] + ' filename.jack')
    exit(1)

if len(sys.argv) != 2:
    usage()

source = sys.argv[1]

if source[-5:] != '.jack' or not os.path.isfile(source):
    usage()

tokenizer = JackTokenizer(source)
tokenizer.advance()
output = '<tokens>\n'
while tokenizer.hasMoreTokens():
    curr_token = tokenizer.tokenType()
    output += '<' + curr_token + '> ' + escape(tokenizer.tokenRepr()) + ' </' + curr_token + '>\n'
    tokenizer.advance()
output += '</tokens>\n'

with open(os.path.basename(source[:-5]) + '.tkn', 'w') as dest:
    dest.write(output)
