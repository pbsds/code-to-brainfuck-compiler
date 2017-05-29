# code to brainfuck compiler

I had a dank idea for how to make a brainfuck compiler and now i regret it because my head hurts.
This compiler translates my made-up language into more or less functional brainfuck code.
In the folder **examples** you can see how the language should like. This is written in
python 3.6 and uses the module plac when standalone.
`pip3 install plac`

### Quick run-through of the language:
* you can only store single integers
* one line per statement
* calculations can be done one operand at a time(1 + 2 is ok, 2*2 - 3 is not)
* `var foo` : declares a variable called foo
* `array foo 5` : declares a array called foo of size 5
* `increment variable [amount=1]` : increments a variable by amount
* `decrement variable [amount=1]` : decrements a variable by amount
* `fetch foo i -> bar` : Fetches value at position i from array foo and stores it in the variable bar
* `store bar -> foo i` : Stores the variable bar in position i in the array called foo
* `if ... then` : start of a if block
* A value written like `'A'`, including the quotation marks will be converted to integers
* `func function_name(parameter) do` : begins a function declaration
* `call function_name(parameter) -> outvalue` : calls function_name and writes the final value to returnvalue
* `while ... do` : while statement
* You can't break from a while or return from a function. You must let them finish
* `write ...` : writes the value to stdout
* `read variable` : fetches a byte from stdin and stores it in variable

### Operators:
* `= ` : assign
* `+ ` : add
* `- ` : subtract
* `* ` : multiply
* `//` : floor division
* `->` : store to
* `==` : equal to
* `!=` : not equal to
* `>=` : greater than or equal to
* `> ` : greater than
* `<=` : lower  than or equal
* `< ` : lower than

### Made by
Peder Bergebakken Sundt - pbsds
under MIT License 2017