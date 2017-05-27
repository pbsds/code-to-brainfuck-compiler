#!/usr/bin/env python3
from tokenizer import Character
from compiler import Brainfuck as BF

MAX_INT = 0xFF
REG_A = "\0A"#variable names assigned to temporary helper variables
REG_B = "\0B"
REG_C = "\0C"
REG_D = "\0D"
REG_calc = "\0CALC"

class ProgrammingError(Exception):
	pass

class CompilingError(Exception):
	pass

def is_actual_value(i):
	return type(i) in (int, Character)

class Program:
	def __init__(self, function_parameter=None):
		self.names = set((REG_A, REG_B, REG_C, REG_D, REG_calc))
		if function_parameter:
			self.names.add(function_parameter)
		self.function_parameter = function_parameter#the name. will always have position 0
		
		self.actions = []#[i] = (Brainfuck.function, args) where args is a tuple of either values or names(str) which gets converted to pos
		
		self.if_blocks = []#[i] = bool(whether ELSE has been used or not yet)
		self.while_blocks = []#value (expression)
		
		self.functions = {}
	def compile(self, do_clean_stack=False, include_debug=False):
		if self.if_blocks:
			raise CompilingError(f"There are {len(self.if_blocks)} unterminated IF blocks in program")
		
		out = BF()
		
		#choose variable positions:
		var_position = {}
		left = list(range(len(self.names)))
		if self.function_parameter:
			var_position[self.function_parameter] = left.pop(0)
		for i in self.names:
			if i != self.function_parameter:
				var_position[i] = left.pop(0)
		var_position["\xfftail_of_stack"] = len(self.names)
		
		#compile actions:
		for i, (func, args) in enumerate(self.actions):
			if func in (BF.write_raw, BF.write_raw_debug):
				if func is BF.write_raw_debug and not include_debug: continue
				func(out, args)
				continue
			
			assert type(args) is tuple, (func, args)
			assert hasattr(func, "__call__"), (func, args)
			
			real_args = [i if type(i) is not str else var_position[i] for i in args]
			try:
				func(out, *real_args)
			except Exception as e:
				e.args = (f"{e.args[0]}\n\nIn Program.compile: func = {func.__name__}, real_args = {real_args}",)
				raise e
				
		#compile stack cleansment:
		if do_clean_stack:
			to_clean = list(range(len(self.names)))
			if self.function_parameter:
				to_clean.pop(0)
			for i in to_clean[::-1]:
				out.clear(i)
		
		out.goto(0)
		
		if include_debug:
			return out.pack()
		else:
			return out.remove_redundancies(out.pack())
	#used to convert a simple calculation to a action+value:
	def calculation_to_value(self, par1, oper, par2):#returns either an int or (action, outputpos)
		if oper in ("=", "->", "(", ")"):
			raise ProgrammingError(f"The operator {oper!r} was used in a calculation")
		if is_actual_value(par1) and is_actual_value(par2):#precalculate
			#print("precalculate", par1, oper, par2)
			if oper == "+" : return min(par1 +  par2, MAX_INT)
			if oper == "-" : return max(par1 -  par2, 0)
			if oper == "*" : return min(par1 *  par2, MAX_INT)
			if oper == "//": return     par1 // par2
			if oper == "==": return int(par1 == par2)
			if oper == ">=": return int(par1 >= par2)
			if oper == "<=": return int(par1 <= par2)
			if oper == ">" : return int(par1 >  par2)
			if oper == "<" : return int(par1 <  par2)
			if oper == "!=": return int(par1 != par2)
			raise ProgrammingError(f"Unknown operator {oper!r} encountered during precalc of calculation of known values")
		
		#at least one variable parameter:
		if is_actual_value(par1):
			par1 = self.store_value(par1)
		if is_actual_value(par2):
			par2 = self.store_value(par2)
		
		if oper == "+" : return (BF.add,                      (par1, par2, REG_calc, REG_A)),                      REG_calc
		if oper == "-" : return (BF.subtract,                 (par1, par2, REG_calc, REG_A)),                      REG_calc
		if oper == "*" : return (BF.multiply,                 (par1, par2, REG_calc, REG_A, REG_B, REG_C)),        REG_calc
		if oper == "//": return (BF.floor_divide,             (par1, par2, REG_calc, REG_A, REG_B, REG_C, REG_D)), REG_calc
		if oper == "==": return (BF.is_equal,                 (par1, par2, REG_calc, REG_A, REG_B)),               REG_calc
		if oper == "<=": return (BF.is_greater_than_or_equal, (par2, par1, REG_calc, REG_A, REG_B, REG_C, REG_D)), REG_calc
		if oper == ">=": return (BF.is_greater_than_or_equal, (par1, par2, REG_calc, REG_A, REG_B, REG_C, REG_D)), REG_calc
		if oper == "<" : return (BF.is_greater_than,          (par2, par1, REG_calc, REG_A, REG_B, REG_C, REG_D)), REG_calc
		if oper == ">" : return (BF.is_greater_than,          (par1, par2, REG_calc, REG_A, REG_B, REG_C, REG_D)), REG_calc
		if oper == "!=": return (BF.is_not_equal,             (par1, par2, REG_calc, REG_A, REG_B)),               REG_calc
	def store_value(self, value):#declare value, returns a name
		assert is_actual_value(value)
		
		name = "\1%i" % int(value)
		if name not in self.names:
			self.names.add(name)
			self.actions.insert(0, (BF.set_to, (name, value, REG_A)))
		
		return name
	def add_var(self, name):#declare a variable
		if name not in self.names:
			self.names.add(name)
		else:
			raise ProgrammingError(f"The var {name!r} was declared twice!")
	#append a action:
	def add_assign(self, name, value):
		assert name in self.names, (name, self.names)
		self.actions.append((BF.write_raw_debug, "\n\nadd_assign:\n"))
		
		if is_actual_value(value):
			self.actions.append((BF.set_to, (name, value, REG_A)))
		elif type(value) is str:
			self.actions.append((BF.copy_to, (value, name, REG_A)))
		else:
			value_action, value_dest = value
			self.actions.append(value_action)
			self.actions.append((BF.copy_to, (value_dest, name, REG_A)))
	def add_function(self, name, program):
		if name in self.functions:
			raise ProgrammingError(f"The function name {name!r} has been used!")
		self.functions[name] = program
	def add_if(self, value):
		self.actions.append((BF.write_raw_debug, "\n\nadd_if:\n"))
		self.if_blocks.append(False)
		
		i = len(self.if_blocks)
		helperpos1 = "\2%ia" % i
		helperpos2 = "\2%ib" % i
		if helperpos1 not in self.names: self.names.add(helperpos1)
		if helperpos2 not in self.names: self.names.add(helperpos2)
		
		if is_actual_value(value):
			value = self.store_value(value)
		if type(value) is not str:
			action, outputpos = value
			self.actions.append(action)
			value = outputpos
		elif value not in self.names:
			raise ProgrammingError(f"{value!r} used before declaration")
		self.actions.append((BF.if_then, (value, helperpos1, helperpos2)))
	def add_else(self):
		self.actions.append((BF.write_raw_debug, "\n\nadd_else:\n"))
		i = len(self.if_blocks)
		if i == 0:
			raise ProgrammingError("ENDIF with no corresponding IF-THEN")
		helperpos1 = "\2%ia" % i
		helperpos2 = "\2%ib" % i
		assert helperpos1 in self.names
		assert helperpos2 in self.names
		
		if self.if_blocks[-1]:
			raise ProgrammingError("IF block with more than one ELSE")
		self.if_blocks[-1] = True
		
		self.actions.append((BF.else_, (helperpos1, helperpos2)))
	def add_endif(self):
		self.actions.append((BF.write_raw_debug, "\n\nadd_endif:\n"))
		i = len(self.if_blocks)
		if i == 0:
			raise ProgrammingError("ENDIF with no corresponding IF-THEN")
		helperpos1 = "\2%ia" % i
		helperpos2 = "\2%ib" % i
		assert helperpos1 in self.names
		assert helperpos2 in self.names
		
		if self.if_blocks.pop(-1):
			self.actions.append((BF.endelse, (helperpos1,)))
		else:
			self.actions.append((BF.endif, (helperpos1, helperpos2)))
	def add_while(self, value):
		self.actions.append((BF.write_raw_debug, "\n\nadd_while:\n"))
		
		self.while_blocks.append(value)
		
		if is_actual_value(value):
			value = self.store_value(value)
		if type(value) is not str:
			action, outputpos = value
			self.actions.append(action)
			value = outputpos
		elif value not in self.names:
			raise ProgrammingError(f"{value!r} used before declaration")
		
		
		
		self.actions.append((BF.while_do, (value,)))
	def add_endwhile(self):#todo
		self.actions.append((BF.write_raw_debug, "\n\nadd_endwhile:\n"))
		
		value = self.while_blocks.pop(-1)
		
		if is_actual_value(value):
			value = self.store_value(value)
		if type(value) is not str:
			action, outputpos = value
			self.actions.append(action)
			value = outputpos
		elif value not in self.names:
			raise ProgrammingError(f"{value!r} used before declaration")
		
		self.actions.append((BF.endwhile, (value,)))
	def add_functioncall(self, functionname, value=None, returninto=None):
		self.actions.append((BF.write_raw_debug, "\n\nadd_functioncall:\n"))
		if functionname not in self.functions:
			raise ProgrammingError(f"{functionname!r} called before declaration")
		
		if value != None:
			if is_actual_value(value):
				value = self.store_value(value)
			if type(value) is not str:
				action, outputpos = value
				self.actions.append(action)
				value = outputpos
			elif value not in self.names:
				raise ProgrammingError(f"{value!r} used before declaration")
		
		program = self.functions[functionname]
		offset = "\xfftail_of_stack"
		
		if value != None:
			self.actions.append((BF.copy_to, (value, offset, REG_A)))
		self.actions.append((BF.goto, (offset,)))
		
		#self.actions.append((program.compile, ()))
		self.actions.append((BF.write_func_output, (program.compile, (True,))))
				
		if returninto:
			self.actions.append((BF.move_to, (offset, returninto)))
	def add_read(self, name):
		self.actions.append((BF.write_raw_debug, "\n\nadd_read:\n"))
		if name not in self.names:
			raiseProgrammingError(f"{name!r} used before declaration")
		self.actions.append((BF.read, (name,)))
	def add_write(self, value):
		self.actions.append((BF.write_raw_debug, "\n\nadd_write:\n"))
		if is_actual_value(value):
			value = self.store_value(value)
		if type(value) is str:
			self.actions.append((BF.write, (value,)))
		else:
			action, outputpos = value
			self.actions.append(action)
			self.actions.append((BF.write, (outputpos,)))
