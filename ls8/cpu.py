"""CPU functionality."""

import sys
from typing import Callable


class CPU:
    """LS-8 compliant CPU"""

    def __init__(self):
        """Construct a new CPU"""
        self.used_ram = 0
        self.ram_size = 2048
        self.ram = [0] * self.ram_size
        self.reg = [-1] * 8
        self.pc = -1

        self.stack_start = -13
        self.stack_end = -13

        self.operations = {}
        self.operations[0b00010001] = self.ret
        self.operations[0b01000101] = self.push
        self.operations[0b01000110] = self.pop
        self.operations[0b01000111] = self.prn
        self.operations[0b01001000] = self.pra
        self.operations[0b01010000] = self.call
        self.operations[0b01010100] = self.jmp
        self.operations[0b10000010] = self.ldi
        self.operations[0b10000011] = self.ld
        self.operations[0b10000100] = self.st
        self.operations[0b10100000] = self.alu('ADD')
        self.operations[0b10100001] = self.alu('SUB')
        self.operations[0b10100010] = self.alu('MUL')
        self.operations[0b10100011] = self.alu('DIV')
        self.operations[0b10100100] = self.alu('MOD')
        self.operations[0b01100101] = self.alu('INC')
        self.operations[0b01100110] = self.alu('DEC')

    @property
    def next_byte(self):
        """Get the next byte tracked by the pc"""
        self.pc += 1
        return self.ram[self.pc]

    @property
    def stack(self):
        """Return an array of the current stack"""
        return self.ram[self.stack_start:self.stack_end:-1]

    def load(self, file: str):
        """Load a program into RAM"""

        if not file.endswith(".ls8"):
            raise ValueError("File must end with .ls8")

        with open(file, 'r') as file:
            for line in file:
                line = line.split("#")[0]
                line = line.strip()

                if line:
                    binary = int(line, 2)
                    self.ram_load(binary)

        self.ram_load(0b00000001)  # HTL (End of Program)

    def ram_load(self, value: int):
        """Load a value into the next memory address"""
        if self.used_ram < self.ram_size + self.stack_end:
            self.ram[self.used_ram] = value
            self.used_ram += 1
        else:
            raise Exception("RAM is FULL")

    def run(self):
        """Run the program currently loaded into RAM"""

        while True:
            operation = self.next_byte

            if operation in self.operations:
                self.operations[operation]()

            elif operation == 0b00000000:  # NOP
                pass

            elif operation == 0b00000001:  # HLT
                break

            else:
                raise Exception("Unsupported instruction")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            self.next_byte,
            self.next_byte,
            self.next_byte
        ), end='')

        for reg in self.reg:
            print(" %02X" % reg, end='')

        print()

    ##### OPERATIONS ####
    def ret(self):
        """
        `RET`

        Return from subroutine.

        Pop the value from the top of the stack and store it in the `PC`.

        Machine Code:
        ```byte
        00010001
        11
        ```
        """
        self.stack_end += 1
        self.pc = self.ram[self.stack_end]

    def push(self):
        """
        `PUSH register`

        Push the value in the given register on the stack.

        1. Decrement the `SP`.
        2. Copy the value in the given register to the address pointed to by
        `SP`.

        Machine code:
        ```byte
        01000101 00000rrr
        45 0r
        ```
        """
        reg_a = self.next_byte
        value = self.reg[reg_a]
        self.ram[self.stack_end] = value
        self.stack_end -= 1

    def pop(self):
        """
        `POP register`

        Pop the value at the top of the stack into the given register.

        1. Copy the value from the address pointed to by `SP` to the given register.
        2. Increment `SP`.

        Machine code:
        ```byte
        01000110 00000rrr
        46 0r
        ```
        """
        self.stack_end += 1
        value = self.ram[self.stack_end]
        reg_a = self.next_byte
        self.reg[reg_a] = value

    def prn(self):
        """
        `PRN register` pseudo-instruction

        Print numeric value stored in the given register.

        Print to the console the decimal integer value that is stored in the given
        register.

        Machine code:
        ```byte
        01000111 00000rrr
        47 0r
        ```
        """
        reg_a = self.next_byte
        value = self.reg[reg_a]
        print(value)

    def pra(self):
        """
        `PRA register` pseudo-instruction

        Print alpha character value stored in the given register.

        Print to the console the ASCII character corresponding to the value in the
        register.

        Machine code:
        ```byte
        01001000 00000rrr
        48 0r
        ```
        """
        reg_a = self.next_byte
        value = self.reg[reg_a]
        print(chr(value))

    def call(self):
        """
        `CALL register`

        Calls a subroutine (function) at the address stored in the register.

        1. The address of the **_instruction_** _directly after_ `CALL` is
        pushed onto the stack. This allows us to return to where we left off when the subroutine finishes executing.
        2. The PC is set to the address stored in the given register. We jump to that location in RAM and execute the first instruction in the subroutine. The PC can move forward or backwards from its current location.

        Machine code:
        ```byte
        01010000 00000rrr
        50 0r
        ```
        """
        reg_a = self.next_byte
        to = self.reg[reg_a]

        self.ram[self.stack_end] = self.pc
        self.stack_end -= 1

        self.pc = to - 1

    def jmp(self):
        """
        `JMP register`

        Jump to the address stored in the given register.

        Set the `PC` to the address stored in the given register.

        Machine code:
        ```byte
        01010100 00000rrr
        54 0r
        ```
        """
        reg_a = self.next_byte
        to = self.reg[reg_a]
        self.pc = to - 1

    def ldi(self):
        """
        `LDI register immediate`

        Set the value of a register to an integer.

        Machine code:
        ```byte
        10000010 00000rrr iiiiiiii
        82 0r ii
        ```
        """
        reg_a = self.next_byte
        value = self.next_byte
        self.reg[reg_a] = value

    def ld(self):
        """
        `LD registerA registerB`

        Loads registerA with the value at the memory address stored in registerB.

        This opcode reads from memory.

        Machine code:
        ```byte
        10000011 00000aaa 00000bbb
        83 0a 0b
        ```
        """
        reg_a = self.next_byte
        reg_b = self.next_byte
        address = self.reg[reg_b]
        value = self.ram[address]
        self.reg[reg_a] = value

    def st(self):
        """
        `ST registerA registerB`

        Store value in registerB in the address stored in registerA.

        This opcode writes to memory.

        Machine code:
        ```byte
        10000100 00000aaa 00000bbb
        84 0a 0b
        ```
        """
        reg_a = self.next_byte
        reg_b = self.next_byte
        address = self.reg[reg_a]
        value = self.reg[reg_b]

        self.ram[address] = value

    def alu(self, op_code: str):
        """
        ALU - Arithmetic Logic Unit

        Returns a function for the given ALU operation
        """
        alu_operations = {}

        def two_reg_operation(alu_operation: Callable):
            def operation():
                reg_a = self.next_byte
                reg_b = self.next_byte

                a = self.reg[reg_a]
                b = self.reg[reg_b]

                self.reg[reg_a] = alu_operation(a, b)

            return operation

        def one_reg_operation(alu_operation: Callable):
            def operation():
                reg_a = self.next_byte
                a = self.reg[reg_a]

                self.reg[reg_a] = alu_operation(a)

            return operation

        """
        `ADD registerA registerB`

        Add the value in two registers and store the result in registerA.

        Machine code:
        ```byte
        10100000 00000aaa 00000bbb
        A0 0a 0b
        ```
        """
        alu_operations["ADD"] = two_reg_operation(lambda a, b: a + b)

        """
        `SUB registerA registerB`

        Subtract the value in the second register from the first, storing the
        result in registerA.

        Machine code:
        ```byte
        10100001 00000aaa 00000bbb
        A1 0a 0b
        ```
        """
        alu_operations["SUB"] = two_reg_operation(lambda a, b: a - b)

        """
        `MUL registerA registerB`

        Multiply the values in two registers together and store the result in registerA.

        Machine code:
        ```byte
        10100010 00000aaa 00000bbb
        A2 0a 0b
        ```
        """
        alu_operations["MUL"] = two_reg_operation(lambda a, b: a * b)

        """
        `DIV registerA registerB`

        Divide the value in the first register by the value in the second,
        storing the result in registerA.

        If the value in the second register is 0, the system should print an
        error message and halt.

        Machine code:
        ```byte
        10100011 00000aaa 00000bbb
        A3 0a 0b
        ```
        """
        alu_operations["DIV"] = two_reg_operation(lambda a, b: a / b)

        """
        `MOD registerA registerB`

        Divide the value in the first register by the value in the second,
        storing the _remainder_ of the result in registerA.

        If the value in the second register is 0, the system should print an
        error message and halt.

        Machine code:
        ```byte
        10100100 00000aaa 00000bbb
        A4 0a 0b
        ```
        """
        alu_operations["MOD"] = two_reg_operation(lambda a, b: a % b)

        """
        `INC register`

        Increment (add 1 to) the value in the given register.

        Machine code:

        ```byte
        01100101 00000rrr
        65 0r
        ```
        """
        alu_operations["INC"] = one_reg_operation(lambda a: a + 1)

        """
        `DEC register`

        Decrement (subtract 1 from) the value in the given register.

        Machine code:
        ```byte
        01100110 00000rrr
        66 0r
        ```
        """
        alu_operations["DEC"] = one_reg_operation(lambda a: a - 1)

        if op_code not in alu_operations:
            raise Exception("Unsupported ALU operation")

        return alu_operations[op_code]
