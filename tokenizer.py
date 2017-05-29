#!/usr/bin/env python3
from enum import Enum

#token types:
class TokenType(Enum):
	name = 1
	operator = 2
	value = 3
	statement = 4
	parameter = 5#means either a name or value. only used in comparisions

#accepted values:
OPERATORS = frozenset((
	"=",
	"+",
	"-",
	"*",
	"//",
	"->",
	"(",
	")",
	"==",
	">=",
	"<=",
	">",
	"<",
	"!=",
))
STATEMENTS = frozenset((
	"func",
	"do",
	"endfunc",
	"if",
	"then",
	"else",
	"endif",
	"while",
	"endwhile",
	"var",
	"call",
	"write",
	"read",
	"increment",
	"decrement",
	"array",
	"fetch",
	"store",
))
VALUE_wildchar = None
class Character(int):#helps with debugging
	def __new__(cls, char, *args, **kwargs):
		self = int.__new__(cls, ord(char), *args, **kwargs)
		self._char = char
		return self
	def __repr__(self):
		return repr(self._char)
	__str__ = __repr__

#predefined tokens
class Token:
	def __init__(self):
		for i in STATEMENTS:
			if i not in ("else", "while", "if"):
				setattr(self, i, (TokenType.statement, i))
		self.if_    = (TokenType.statement, "if")
		self.else_  = (TokenType.statement, "else")
		self.while_ = (TokenType.statement, "while")
		
		self.any_name      = (TokenType.name    , VALUE_wildchar)
		self.any_oper      = (TokenType.operator, VALUE_wildchar)
		self.any_value     = (TokenType.value   , VALUE_wildchar)
		self.any_parameter = (TokenType.parameter, VALUE_wildchar)#name and value
		
		self.oper_assign   = (TokenType.operator, "=")
		self.oper_add      = (TokenType.operator, "+")
		self.oper_sub      = (TokenType.operator, "-")
		self.oper_mul      = (TokenType.operator, "*")
		self.oper_fdiv     = (TokenType.operator, "//")
		self.oper_write_to = (TokenType.operator, "->")
		self.oper_sbracket = (TokenType.operator, "(")
		self.oper_ebracket = (TokenType.operator, ")")
		self.oper_eq       = (TokenType.operator, "==")
		self.oper_ge       = (TokenType.operator, ">=")
		self.oper_gt       = (TokenType.operator, ">")
		self.oper_le       = (TokenType.operator, "<=")
		self.oper_lt       = (TokenType.operator, "<")
		self.oper_ne       = (TokenType.operator, "!=")
Token = Token()

#expression (for a single line)
class Expression(tuple):#makes comparisions easy
	def __new__(cls, *args, **kwargs):
		for token, value in args:
			assert type(token) is TokenType
		
		linenum = None
		if "linenum" in kwargs:
			linenum = kwargs["linenum"]
			del kwargs["linenum"]
		
		line = ""
		if "line" in kwargs:
			line = kwargs["line"]
			del kwargs["line"]
		
		self = tuple.__new__(cls, args, **kwargs)
		self.has_wildchar = sum(1 for token, value in args if value != VALUE_wildchar) > 0
		self.line = line
		self.linenum = linenum
		return self
	def __str__(self):
		return "Expressions(" + ", ".join(f"({token.name}, {value!r})" for token, value in self) + ")"
		return 
	__repr__ = __str__
	def __eq__(self, other):
		assert type(other) is Expression
		
		if len(other) != len(self):
			return False
		
		for (t1, v1), (t2, v2) in zip(self, other):
			if TokenType.parameter in (t1, t2):
				if t1 not in (TokenType.name, TokenType.value, TokenType.parameter):
					return False
				if t2 not in (TokenType.name, TokenType.value, TokenType.parameter):
					return False
			elif t1 != t2:
				return False
			if VALUE_wildchar not in (v1, v2) and v1 != v2:
				return False
		return True

#the actual tokenizer
class TokenError(Exception): pass

def tokenize_text(text):
	for i in ("(", ")", "+", "*", "//"):
		text = text.replace(i, " %s " % i)
	text = text.replace("' '", str(ord(" ")))
	
	out = []
	for linenum, line in enumerate(text.split("\n"), 1):
		tokens = []
		if not line.split("#", 1)[0].strip():
			continue
		for item in line.split("#", 1)[0].strip().split():
			if item.replace("_", "").isalpha():
				if item.lower() in STATEMENTS:
					tokens.append((TokenType.statement, item.lower()))
				else:
					tokens.append((TokenType.name, item))
			elif item.isnumeric():
				tokens.append((TokenType.value, int(item)))
			elif len(item) == 3 and item[0] == item[2] == "'":
				tokens.append((TokenType.value, Character(item[1])))
			elif item in OPERATORS:
				tokens.append((TokenType.operator, item))
			else:
				raise TokenError(f"Unrecognized item {item!r} i, line {linenum}")
		for i in tokens:
			if i[1] == None:
				raise TokenError(f"Unknown error, None as value: {tokens}")
		out.append(Expression(*tokens, line=line, linenum=linenum))
		
	return tuple(out)
