#!/usr/bin/env python3
from tokenizer import Character
from compiler import Brainfuck as BF
from random import shuffle
import itertools

MAX_INT = 0xFF#remove this? Only used when precalculating values...
REG_helper = "\0HELP"#variable names assigned to temporary helper variables
REG_calc = "\0CALC"

class ProgrammingError(Exception):
	pass

class CompilingError(Exception):
	pass

def is_actual_value(i):
	return type(i) in (int, Character)

class Program:
	def __init__(self, function_parameter=None):
		self.names = set(("\0A", "\0B", "\0C", "\0D", REG_calc))
		if function_parameter:
			self.names.add(function_parameter)
		self.function_parameter = function_parameter#the name. will always have position 0
		#names is a set of the declared variable names, and will be mapped to locations in memory on compile
		#hidden values are also assigned names that will not fit within "".isalpha() which is enforced in the tokenizer
		#	names starting with "\0" are helper registers. "\0HELP" is special as it will be converted to the closes available
		#	names starting with "\1" are the names of stored constants. "\142" stores the value 42
		#	names starting with "\2" are reserved for if statements
		#	names starting with "\3" are reserved for array contents
		#	the name "\xfftail_of_stack" points to the position behind the last value on the stack. This is the position where a new stack wil be built
		self.actions = []#[i] = (Brainfuck.function, args) where args is a tuple of either values or names(str) which gets converted to pos
		
		self.if_blocks = []#[i] = bool(whether ELSE has been used or not yet)
		self.while_blocks = []#value (expression)
		self.arrays = {}#"name" : size
		
		self.functions = {}#"name" : Program()
	def compile(self, do_clean_stack=False, include_debug=False):
		if self.if_blocks:
			raise CompilingError(f"There are {len(self.if_blocks)} unterminated IF blocks in program")
		
		if hasattr(self, "_ret"):
			return self._ret
		
		ret = None
		attempts_left = 51
		while attempts_left:
			attempts_left -= 1
			out = BF()
			
			#choose random variable positions:
			var_position = {}
			left = list(range(len(self.names)))
			if self.function_parameter:
				var_position[self.function_parameter] = left.pop(0)
			shuffle(left)
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
				
				helper_registers = ("\0A", "\0B", "\0C", "\0D")
				bestlen = None
				bestargs = None
				for helpers in itertools.permutations(helper_registers, args.count(REG_helper)):
					hpos = 0
					real_args = []
					for i in args:
						if i == REG_helper:
							real_args.append(var_position[helpers[hpos]])
							hpos += 1
						elif type(i) is not str:
							real_args.append(i)
						else:
							real_args.append(var_position[i])
					
					out.set_waypoint()
					try:
						func(out, *real_args)
					except Exception as e:
						e.args = (f"{e.args[0]}\n\nIn Program.compile: func = {func.__name__}, real_args = {real_args}",)
						raise e
					
					if bestlen is None:
						bestlen = out.waypoint_diff()
						bestargs = real_args
					elif out.waypoint_diff() < bestlen:
						bestargs = real_args
					out.restore_waypoint()
				
				func(out, *bestargs)
			
			#compile stack cleansment:
			if do_clean_stack:
				to_clean = list(range(len(self.names)))
				if self.function_parameter:
					to_clean.pop(0)
				for i in to_clean[::-1]:
					out.clear(i)
			
			out.goto(0)
			
			out = out.pack()
			
			if not ret:
				ret = out
			elif len(out) < len(ret):
				attempts_left = 50
				ret = out
		
		self._ret = ret
		return ret
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
			raise ProgrammingError(f"Illegal operator {oper!r} encountered during precalc of calculation of known values")
		
		#at least one variable parameter:
		if is_actual_value(par1):
			par1 = self.store_value(par1)
		if is_actual_value(par2):
			par2 = self.store_value(par2)
		
		if oper == "+" : return (BF.add,                      (par1, par2, REG_calc, REG_helper)),                                     REG_calc
		if oper == "-" : return (BF.subtract,                 (par1, par2, REG_calc, REG_helper)),                                     REG_calc
		if oper == "*" : return (BF.multiply,                 (par1, par2, REG_calc, REG_helper, REG_helper, REG_helper)),             REG_calc
		if oper == "//": return (BF.floor_divide,             (par1, par2, REG_calc, REG_helper, REG_helper, REG_helper, REG_helper)), REG_calc
		if oper == "==": return (BF.is_equal,                 (par1, par2, REG_calc, REG_helper, REG_helper)),                         REG_calc
		if oper == "<=": return (BF.is_greater_than_or_equal, (par2, par1, REG_calc, REG_helper, REG_helper, REG_helper, REG_helper)), REG_calc
		if oper == ">=": return (BF.is_greater_than_or_equal, (par1, par2, REG_calc, REG_helper, REG_helper, REG_helper, REG_helper)), REG_calc
		if oper == "<" : return (BF.is_greater_than,          (par2, par1, REG_calc, REG_helper, REG_helper, REG_helper, REG_helper)), REG_calc
		if oper == ">" : return (BF.is_greater_than,          (par1, par2, REG_calc, REG_helper, REG_helper, REG_helper, REG_helper)), REG_calc
		if oper == "!=": return (BF.is_not_equal,             (par1, par2, REG_calc, REG_helper, REG_helper)),                         REG_calc
		raise ProgrammingError(f"Illegal operator {oper!r} encountered in calculation")
	def store_value(self, value):#declare value, returns a name
		assert is_actual_value(value)
		
		name = "\1%i" % int(value)
		if name not in self.names:
			self.names.add(name)
			self.actions.insert(0, (BF.increment, (name, value, REG_helper)))
		
		return name
	def add_var(self, name):#declare a variable
		if name not in self.names:
			self.names.add(name)
		else:
			raise ProgrammingError(f"The var {name!r} was declared twice!")
	def add_array(self, name, size):#declare a array
		if name in self.arrays:
			raise ProgrammingError(f"The array {name!r} was declared twice!")
		if size <= 0:
			raise ProgrammingError(f"The array {name!r} was declared with the illegal size {size}")
		
		self.arrays[name] = size
		for i in range(size):
			self.names.add(f"\3{name}-{i}")
	#append an action:
	def add_assign(self, name, value):
		assert name in self.names, (name, self.names)
		self.actions.append((BF.write_raw_debug, "\n\nadd_assign:\n"))
		
		if is_actual_value(value):
			self.actions.append((BF.set_to, (name, value, REG_helper)))
		elif type(value) is str:
			self.actions.append((BF.copy_to, (value, name, REG_helper)))
		else:
			value_action, value_dest = value
			self.actions.append(value_action)
			self.actions.append((BF.copy_to, (value_dest, name, REG_helper)))
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
	def add_endwhile(self):
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
			self.actions.append((BF.copy_to, (value, offset, REG_helper)))
		self.actions.append((BF.goto, (offset,)))
		
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
	def add_increment(self, name, amount = 1):
		assert name in self.names, (name, self.names)
		self.actions.append((BF.write_raw_debug, "\n\nadd_increment:\n"))
		
		self.actions.append((BF.increment, (name, amount, REG_helper)))
	def add_decrement(self, name, amount = 1):
		assert name in self.names, (name, self.names)
		self.actions.append((BF.write_raw_debug, "\n\aadd_decrement:\n"))
		
		self.actions.append((BF.decrement, (name, amount, REG_helper)))
	def add_fetch(self, arrayname, indexvalue, destname):#assumes a wrapping brainfuck implementation
		self.actions.append((BF.write_raw_debug, "\n\aadd_fetch:\n"))
		
		if arrayname not in self.arrays:
			raise ProgrammingError(f"Tried fetching from undeclared array {arrayname!r}")
		if destname not in self.names:
			raise ProgrammingError(f"Tried storing fetch result into undeclared variable {destname!r}")
		
		if is_actual_value(indexvalue):#if index is known:
			if indexvalue < 0 or indexvalue >= self.arrays[arrayname]:
				raise ProgrammingError(f"Tried accessing array {arrayname!r} with invalid index {indexvalue!r}")
			
			self.actions.append((BF.copy_to, (f"\3{arrayname}-{int(indexvalue)}", destname, REG_helper)))
		else:
			arraysize = self.arrays[arrayname]
			for i in range(arraysize):
				self.add_if(indexvalue)
				self.add_else()#if indexvalue - i == 0
				
				#copy this array position
				self.actions.append((BF.copy_to, (f"\3{arrayname}-{i}", destname, REG_helper)))
				
				self.add_endif()
				
				self.add_decrement(indexvalue)#i++
			
			#cleanup
			self.add_increment(indexvalue, arraysize)
		
		self.actions.append((BF.write_raw_debug, "\n\aadd_fetch end\n"))
	def add_store(self, value, arrayname, indexvalue):
		self.actions.append((BF.write_raw_debug, "\n\aadd_store:\n"))
		
		if arrayname not in self.arrays:
			raise ProgrammingError(f"Tried storing to undeclared array {arrayname!r}")
		
		if is_actual_value(indexvalue):#if index is known:
			if indexvalue < 0 or indexvalue >= self.arrays[arrayname]:
				raise ProgrammingError(f"Tried accessing array {arrayname!r} with invalid index {indexvalue!r}")
			
			if is_actual_value(value):
				self.actions.append((BF.set_to, (f"\3{arrayname}-{int(indexvalue)}", value, REG_helper)))
			else:
				assert type(value) is str
				if value not in self.names:
					raise ProgrammingError(f"Undeclared variable {value!r}")
				
				self.actions.append((BF.copy_to, (value, f"\3{arrayname}-{int(indexvalue)}", REG_helper)))
		else:#index unknown
			assert type(indexvalue) is str
			if indexvalue not in self.names:
				raise ProgrammingError(f"Undeclared variable {indexvalue!r}")
			
			self.actions.append((BF.copy_to, (indexvalue, REG_calc, REG_helper)))
			
			arraysize = self.arrays[arrayname]
			for i in range(arraysize):
				self.add_if(REG_calc)
				self.add_else()#if indexvalue - i == 0
				
				#store to array position
				if is_actual_value(value):
					self.actions.append((BF.set_to, (f"\3{arrayname}-{i}", value, REG_helper)))
				else:
					self.actions.append((BF.copy_to, (value, f"\3{arrayname}-{i}", REG_helper)))
				
				self.add_endif()
				
				self.add_decrement(REG_calc)#i++
			
			#cleanup
			self.add_increment(REG_calc, arraysize)
		self.actions.append((BF.write_raw_debug, "\n\aadd_store end\n"))
		