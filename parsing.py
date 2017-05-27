#!/usr/bin/env python3
from tokenizer import Token as T, Expression, VALUE_wildchar
from program import Program, ProgrammingError

#T expression patterns:
EX_func1    = Expression(T.func, T.any_name, T.oper_sbracket, T.oper_ebracket, T.do)
EX_func2    = Expression(T.func, T.any_name, T.oper_sbracket, T.any_name, T.oper_ebracket, T.do)
EX_endfunc  = Expression(T.endfunc)
EX_if1      = Expression(T.if_, T.any_parameter, T.any_oper, T.any_parameter, T.then)
EX_if2      = Expression(T.if_, T.any_name, T.then)
EX_else     = Expression(T.else_)
EX_endif    = Expression(T.endif)
EX_while1   = Expression(T.while_, T.any_parameter, T.any_oper, T.any_parameter, T.do)
EX_while2   = Expression(T.while_, T.any_name, T.do)
EX_endwhile = Expression(T.endwhile)
EX_var1     = Expression(T.var, T.any_name)
EX_var2     = Expression(T.var, T.any_name, T.oper_assign, T.any_parameter)
EX_var3     = Expression(T.var, T.any_name, T.oper_assign, T.any_parameter, T.any_oper, T.any_parameter)
EX_assign1  = Expression(T.any_name, T.oper_assign, T.any_parameter)
EX_assign2  = Expression(T.any_name, T.oper_assign, T.any_parameter, T.any_oper, T.any_parameter)
EX_call1    = Expression(T.call, T.any_name, T.oper_sbracket, T.oper_ebracket)
EX_call2    = Expression(T.call, T.any_name, T.oper_sbracket, T.any_parameter, T.oper_ebracket)
EX_call3    = Expression(T.call, T.any_name, T.oper_sbracket, T.oper_ebracket, T.oper_write_to, T.any_name)
EX_call4    = Expression(T.call, T.any_name, T.oper_sbracket, T.any_parameter, T.oper_ebracket, T.oper_write_to, T.any_name)
EX_read     = Expression(T.read, T.any_name)
EX_write1   = Expression(T.write, T.any_parameter)
EX_write2   = Expression(T.write, T.any_parameter, T.any_oper, T.any_parameter)


class ParseError(Exception):
	def __init__(self, ex, description):
		description = f"Line {ex.linenum}: {ex.line}\n{description}"
		Exception.__init__(self, description)

def parse_expressions(expressions, top_level=True, parameter=None):
	if parameter:
		out = Program(function_parameter=parameter)
	else:
		out = Program()
	
	#handle blocks:
	function_inside = False
	function_parameter = None
	function_name = None
	function_expressions = []
	#loop through
	for ex in expressions:
		#if not function_inside: print("parse_expressions:",ex[0][1], len(expressions))
		#if not function_inside: print(ex)
		
		try:
			if function_inside:#while inside function declaration
				if ex == EX_endfunc:
					function = parse_expressions(
						function_expressions,
						top_level = False,
						parameter = function_parameter,
					)
					out.add_function(function_name, function)
					function_inside = False
				else:
					function_expressions.append(ex)
			elif ex in (EX_func1, EX_func2):#start of function declaration
				function_inside = True
				if not top_level:
					raise ParseError(ex, "Function declaration not at top level.")
				if ex == EX_func2:
					function_parameter = ex[3][1]
				else:
					function_parameter = None
				function_expressions = []
				function_name = ex[1][1]
			elif ex == EX_if1:
				par1, oper, par2 = ex[1:4]
				out.add_if(out.calculation_to_value(par1[1], oper[1], par2[1]))
			elif ex == EX_if2:				
				out.add_if(ex[1][1])
			elif ex == EX_else:
				out.add_else()
			elif ex == EX_endif:
				out.add_endif()
			elif ex == EX_while1:
				par1, oper, par2 = ex[1:4]
				out.add_while(out.calculation_to_value(par1[1], oper[1], par2[1]))
			elif ex == EX_while2:
				out.add_while(ex[1][1])
			elif ex == EX_endwhile:
				out.add_endwhile()
			elif ex == EX_var1:
				out.add_var(ex[1][1])
			elif ex == EX_var2:
				out.add_var(ex[1][1])
				out.add_assign(ex[1][1], ex[3][1])
			elif ex == EX_var3:
				out.add_var(ex[1][1])
				par1, oper, par2 = ex[3:6]
				out.add_assign(ex[1][1], out.calculation_to_value(par1[1], oper[1], par2[1]))
			elif ex == EX_assign1:
				out.add_assign(ex[0][1], ex[2][1])
			elif ex == EX_assign2:
				par1, oper, par2 = ex[2:5]
				out.add_assign(ex[0][1], out.calculation_to_value(par1[1], oper[1], par2[1]))
			elif ex == EX_call1:
				out.add_functioncall(ex[1][1])
			elif ex == EX_call2:
				out.add_functioncall(ex[1][1], ex[3][1])
			elif ex == EX_call3:
				out.add_functioncall(ex[1][1], returnname = ex[6][1])
			elif ex == EX_call4:
				out.add_functioncall(ex[1][1], ex[3][1], ex[6][1])
			elif ex == EX_read:
				out.add_read(ex[1][1])
			elif ex == EX_write1:
				out.add_write(ex[1][1])
			elif ex == EX_write2:
				par1, oper, par2 = ex[1:4]
				out.add_write(out.calculation_to_value(par1[1], oper[1], par2[1]))
			else:
				raise ParseError(ex, "Syntax unrecognized")
		except ProgrammingError as e:
			e.args = (f"Line {ex.linenum}: {ex.line}\n{e.args[0]}", )
			raise e
	return out
		
	