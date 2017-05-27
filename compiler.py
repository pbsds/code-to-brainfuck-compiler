#!/usr/bin/env python3
from math import sqrt

class Brainfuck:#creates brainfuck code when commands are done on it
	def __init__(self):
		self.bytecode = []
		self.pos = 0
	def remove_redundancies(self, bytecode):
		#count = 0
		out = list(bytecode)
		i = 0
		while i < len(out)-1:
			if out[i]+out[i+1] in ("+-", "-+", "<>", "><"):
				out.pop(i)
				out.pop(i)
				#count += 1
				if i: i -= 1
			else:
				i += 1
		return "".join(out)
	def pack(self):
		return "".join(self.bytecode)
	#commands:
	def write_raw(self, data):#you must leave the cursor at the same position at the end
		self.bytecode.append(data)
	def write_raw_debug(self, data):#you must leave the cursor at the same position at the end
		self.bytecode.append(data)
	def write_func_output(self, func, args):#you must leave the cursor at the same position at the end
		self.bytecode.append(func(*args))
	#cursorsafe:
	def goto(self, pos):
		if pos == None or pos == self.pos:
			return
		if pos > self.pos:
			self.bytecode.extend([">"]*(pos-self.pos))
		else:
			self.bytecode.extend(["<"]*(self.pos-pos))
		self.pos = pos
	def clear(self, pos=None):#set to 0
		self.goto(pos)
		self.bytecode.append("[-]")
	def increment(self, pos, amount=1, helperpos=None):
		assert pos != helperpos, (pos, helperpos)
		
		
		if helperpos == None or amount <= 15:
			self.goto(pos)
			self.bytecode.extend(["+"]*(amount))
		else:
			inc = int(sqrt(amount))
			
			self.set_to(helperpos, inc)
			self.bytecode.append("[")
			self.increment(pos, inc)
			self.decrement(helperpos)
			self.bytecode.append("]")
			
			self.increment(pos, amount - inc**2)
	def decrement(self, pos, amount=1, helperpos=None):
		assert pos != helperpos
		
		if helperpos == None or amount <= 15:
			self.goto(pos)
			self.bytecode.extend(["-"]*(amount))
		else:
			dec = int(sqrt(amount))
			
			self.set_to(helperpos, dec)
			self.bytecode.append("[")
			self.decrement(pos, dec)
			self.decrement(helperpos)
			self.bytecode.append("]")
	def add(self, posa, posb, outputpos, helperpos):
		assert posa != posb
		
		if outputpos in (posa, posb):
			x = outputpos
			y = posa if posa != outputpos else posb
			
			self.clear(helperpos)
			
			self.goto(y)
			self.bytecode.append("[")
			self.increment(helperpos)
			self.increment(x)
			self.decrement(y)
			self.bytecode.append("]")
			
			self.move_to(helperpos, y, True)
		else:
			self.copy_to(posa, outputpos, helperpos)
			self.add(outputpos, posb, outputpos, helperpos)
	def subtract(self, posa, posb, outputpos, helperpos):
		assert posa != posb
		
		if outputpos == posa:
			x = outputpos
			y = posb
			
			self.clear(helperpos)
			
			self.goto(y)
			self.bytecode.append("[")
			self.decrement(x)
			self.increment(helperpos)
			self.decrement(y)
			self.bytecode.append("]")
			
			self.move_to(helperpos, y, True)
		else:
			self.copy_to(posa, outputpos, helperpos)
			self.subtract(outputpos, posb, outputpos, helperpos)
	def multiply(self, posa, posb, outputpos, helperpos1, helperpos2, helperpos3):
		if posa != posb:
			if outputpos in (posa, posb):
				x = outputpos
				y = posa if posa != outputpos else posb
				
				self.clear(helperpos1)
				self.move_to(x, helperpos2)
				
				self.goto(helperpos2)
				self.bytecode.append("[")
				
				self.goto(y)
				self.bytecode.append("[")
				self.increment(x)
				self.increment(helperpos1)
				self.decrement(y)
				self.bytecode.append("]")
				self.goto(helperpos1)
				self.bytecode.append("[")
				self.increment(y)
				self.decrement(helperpos1)
				self.bytecode.append("]")
				
				self.decrement(helperpos2)
				self.bytecode.append("]")
			else:
				self.copy_to(posa, outputpos, helperpos1)
				self.multiply(outputpos, posb, outputpos, helperpos1, helperpos2, helperpos3)
		else:
			self.square(posa, outputpos, helperpos1, helperpos2, helperpos3)
	def square(self, pos, outputpos, helperpos1, helperpos2, helperpos3):
		self.copy_to(pos, helperpos1, helperpos2)
		self.multiply(pos, helperpos1, outputpos, helperpos2, helperpos3, None)
	def floor_divide(self, posa, posb, outputpos, helperpos1, helperpos2, helperpos3, helperpos4):
		assert posa != posb
		if outputpos in (posa, posb):
			x = outputpos
			y = posb
			
			#helperpos1[-]
			self.clear(helperpos1)			
			
			#helperpos2[-]
			self.clear(helperpos2)
			
			#helperpos3[-]
			self.clear(helperpos3)
			
			#helperpos4[-]
			self.clear(helperpos4)

			#x[helperpos1+x-]
			self.goto(x)
			self.bytecode.append("[")
			self.increment(helperpos1)
			self.decrement(x)
			self.bytecode.append("]")
			
			#helperpos1[
			self.goto(helperpos1)
			self.bytecode.append("[")
			
			# y[helperpos2+helperpos3+y-]
			self.goto(y)
			self.bytecode.append("[")
			self.increment(helperpos2)
			self.increment(helperpos3)
			self.decrement(y)
			self.bytecode.append("]")
			
			# helperpos3[y+helperpos3-]
			self.goto(helperpos3)
			self.bytecode.append("[")
			self.increment(y)
			self.decrement(helperpos3)
			self.bytecode.append("]")
			
			# helperpos2[
			self.goto(helperpos2)
			self.bytecode.append("[")
			
			#  helperpos3+
			self.increment(helperpos3)
			
			#  helperpos1-[helperpos3[-]helperpos4+helperpos1-]
			self.decrement(helperpos1)
			self.bytecode.append("[")
			self.clear(helperpos3)
			self.increment(helperpos4)
			self.decrement(helperpos1)
			self.bytecode.append("]")
			
			#  helperpos4[helperpos1+helperpos4-]
			self.goto(helperpos4)
			self.bytecode.append("[")
			self.increment(helperpos1)
			self.decrement(helperpos4)
			self.bytecode.append("]")
			
			#  helperpos3[
			self.goto(helperpos3)
			self.bytecode.append("[")
			
			#   helperpos2-
			self.decrement(helperpos2)
			
			#   [x-helperpos2[-]]+
			self.bytecode.append("[")
			self.decrement(x)
			self.clear(helperpos2)
			self.bytecode.append("]")
			self.increment(helperpos2)
			
			#  helperpos3-]
			self.decrement(helperpos3)
			self.bytecode.append("]")
			
			# helperpos2-]
			self.decrement(helperpos2)
			self.bytecode.append("]")
			
			# x+
			self.increment(x)
			
			#helperpos1]
			self.goto(helperpos1)
			self.bytecode.append("]")
		else:
			self.copy_to(posa, outputpos, helperpos1)
			self.floor_divide(outputpos, posb, outputpos, helperpos1, helperpos2, helperpos3, helperpos4)
	def is_equal(self, posa, posb, outputpos, helperpos1, helperpos2):
		assert posa != posb
		if outputpos in (posa, posb):
			x = outputpos
			y = posa if posa != outputpos else posb
			
			#helperpos1[-]
			self.clear(helperpos1)
			
			#helperpos2[-]
			self.clear(helperpos2)
			
			#x[helperpos2+x-]+
			self.goto(x)
			self.bytecode.append("[")
			self.increment(helperpos2)
			self.decrement(x)
			self.bytecode.append("]")
			self.increment(x)
			
			#y[helperpos2-helperpos1+y-]
			self.goto(y)
			self.bytecode.append("[")
			self.decrement(helperpos2)
			self.increment(helperpos1)
			self.decrement(y)
			self.bytecode.append("]")
			
			#helperpos1[y+helperpos1-]
			self.goto(helperpos1)
			self.bytecode.append("[")
			self.increment(y)
			self.decrement(helperpos1)
			self.bytecode.append("]")
			
			#helperpos2[x-helperpos2[-]]
			self.goto(helperpos2)
			self.bytecode.append("[")
			self.decrement(x)
			self.clear(helperpos2)
			self.bytecode.append("]")
		else:
			self.copy_to(posa, outputpos, helperpos1)
			self.is_equal(outputpos, posb, outputpos, helperpos1, helperpos2)
	def is_greater_than(self, posa, posb, outputpos, helperpos1, helperpos2, helperpos3, helperpos4):#assumes unsigned bytes
		assert posa != posb
		#outputpos = x > y
		#The temporaries and x are left at 0; y is set to y-x.
		x = helperpos3
		y = helperpos4
		self.copy_to(posa, x, helperpos1)
		self.copy_to(posb, y, helperpos1)
		
		#helperpos1[-]helperpos2[-]outputpos[-]
		self.clear(helperpos1)
		self.clear(helperpos2)
		self.clear(outputpos)
		
		#x[ helperpos1+
		self.goto(x)
		self.bytecode.append("[")
		self.increment(helperpos1)
		
		#       y[- helperpos1[-] helperpos2+ y]
		self.goto(y)
		self.bytecode.append("[")
		self.decrement(y)
		self.clear(helperpos1)
		self.increment(helperpos2)
		self.goto(y)
		self.bytecode.append("]")
		
		#   helperpos1[- outputpos+ helperpos1]
		self.goto(helperpos1)
		self.bytecode.append("[")
		self.increment(outputpos)
		self.decrement(helperpos1)
		self.bytecode.append("]")
		
		#   helperpos2[- y+ helperpos2]
		self.goto(helperpos2)
		self.bytecode.append("[")
		self.increment(y)
		self.decrement(helperpos2)
		self.bytecode.append("]")
		
		#   y- x- ]
		self.decrement(y)
		self.decrement(x)
		self.bytecode.append("]")
	def is_greater_than_or_equal(self, posa, posb, outputpos, helperpos1, helperpos2, helperpos3, helperpos4):#assumes unsigned bytes
		#posa >= posb    ==    not (posb > posa)
		self.is_greater_than(posb, posa, outputpos, helperpos1, helperpos2, helperpos3, helperpos4)
		self.logical_not(outputpos, outputpos, helperpos1)
	def is_not_equal(self, posa, posb, outputpos, helperpos1, helperpos2):
		self.is_equal(posa, posb, outputpos, helperpos1, helperpos2)
		self.logical_not(outputpos, outputpos, helperpos1)
	def logical_not(self, pos, outputpos, helperpos):
		if pos != outputpos:
			self.copy_to(pos, outputpos, helperpos)
		
		self.clear(helperpos)
		
		self.goto(outputpos)
		self.bytecode.append("[")
		self.increment(helperpos)
		self.clear(outputpos)
		self.bytecode.append("]")
		self.increment(outputpos)
		
		self.goto(helperpos)
		self.bytecode.append("[")
		self.decrement(outputpos)
		self.decrement(helperpos)
		self.bytecode.append("]")
	def set_to(self, pos, value, helperpos=None):
		self.clear(pos)
		self.increment(pos, value, helperpos)
	def move_to(self, sourcepos, destpos, dest_is_clear=False):
		assert sourcepos != destpos
		
		if not dest_is_clear:
			self.clear(destpos)
		
		self.goto(sourcepos)
		self.bytecode.append("[")
		self.increment(destpos)
		self.decrement(sourcepos)
		self.bytecode.append("]")
	def copy_to(self, sourcepos, destpos, helperpos):
		assert sourcepos != destpos
		
		self.clear(helperpos)
		self.clear(destpos)
		
		self.goto(sourcepos)
		self.bytecode.append("[")
		self.increment(destpos)
		self.increment(helperpos)
		self.decrement(sourcepos)
		self.bytecode.append("]")
		
		self.move_to(helperpos, sourcepos, True)
	def swap(self, posa, posb, helperpos):
		raise NotImplementedError()
	def read(self, outputpos):
		self.goto(outputpos)
		self.bytecode.append(",")
	def write(self, pos):
		self.goto(pos)
		self.bytecode.append(".")
	#These require the same helpers unmodified throughout the if block:
	def if_then(self, checkpos, helperpos1, helperpos2):
		#helperpos1[-]
		#helperpos2[-]
		self.clear(helperpos1)
		self.clear(helperpos2)
		
		#x[helperpos1+helperpos2+x-]helperpos1[x+helperpos1-]+
		self.goto(checkpos)
		self.bytecode.append("[")
		self.increment(helperpos1)
		self.increment(helperpos2)
		self.decrement(checkpos)
		self.bytecode.append("]")
		
		self.goto(helperpos1)
		self.bytecode.append("[")
		self.increment(checkpos)
		self.decrement(helperpos1)
		self.bytecode.append("]")
		self.increment(helperpos1)
		
		#helperpos2[
		self.goto(helperpos2)
		self.bytecode.append("[")
		
		
		
		# code1
	def else_(self, helperpos1, helperpos2):#must come after a corresponding if_then
		# helperpos1-
		self.decrement(helperpos1)
		
		#helperpos2[-]]
		self.clear(helperpos2)
		self.bytecode.append("]")
		
		#helperpos1[
		self.goto(helperpos1)
		self.bytecode.append("[")
		
		# code2
	def endelse(self, helperpos1):#must come after a corresponding else_
		#helperpos1-]
		self.decrement(helperpos1)
		self.bytecode.append("]")
	def endif(self, helperpos1, helperpos2):#must come after a corresponding if_then
		# helperpos1-
		self.decrement(helperpos1)
		
		#helperpos2[-]]
		self.clear(helperpos2)
		self.bytecode.append("]")
	#these require you to evaluate your condition before both the while and endwhile and supply its position
	#They must use the same positions
	def while_do(self, pos):
		self.goto(pos)
		self.bytecode.append("[")
	def endwhile(self, pos):
		self.goto(pos)
		self.bytecode.append("]")
		