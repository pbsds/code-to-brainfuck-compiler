#!/usr/bin/env python3
#https://esolangs.org/wiki/Brainfuck_algorithms
import sys
from parsing import parse_expressions
from tokenizer import tokenize_text


def main(input, output=None, code_width=70, debug=False):
	if input == "-":
		text = sys.stdin.read()
	else:
		with open(input, "r") as f:
			text = f.read()
	
	if output != "-": print("Tokenizing...")
	tokens = tokenize_text(text)
	
	if output != "-": print("Parsing and building program...")
	program = parse_expressions(tokens)
	
	if output != "-": print("Compiling program...")
	if debug and debug[0] not in "0Ff":
		bf = program.compile(include_debug=True)
	else:
		code_width = int(code_width)
		bf = program.compile()
		bf = "\n".join(bf[i*code_width:i*code_width+code_width] for i in range(int((len(bf)/code_width)+0.5)+1))
	
	if not output or output=="None":
		output = input+".bf"
	if output == "-":
		sys.stdout.write(bf)
	else:
		with open(output, "w") as f:
			f.write(bf)

if __name__ == '__main__':
	import plac; plac.call(main)