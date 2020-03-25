"""CPU functionality"""

from typing import Callable

from datetime import datetime, timedelta
import sys

interrupt_mask = 5
interrupt_status = 6
stack_pointer = 7
stack_start = -13

interupt = list(range(-8, 0))


class CPU:
    """LS-8 compliant CPU"""

    def __init__(self):
        """Construct a new CPU"""
        self.used_ram = 0
        self.ram_size = 256
        self.ram = [0] * self.ram_size

        self.registers = [-1] * 8
        self.registers[interrupt_mask] = 0
        self.registers[interrupt_status] = 0
        self.registers[stack_pointer] = stack_start

        self.interupting = False
        self.last_timer = datetime.now()

        self.flags = {'E': 0, 'L': 0, 'G': 0}
        self.program_counter = -1

        self.operations = {}
        self.operations[0b00010001] = self.ret
        self.operations[0b00010011] = self.iret
        self.operations[0b01000101] = self.push
        self.operations[0b01000110] = self.pop
        self.operations[0b01000111] = self.prn
        self.operations[0b01001000] = self.pra
        self.operations[0b01010000] = self.call
        self.operations[0b01010010] = self.int
        self.operations[0b01010100] = self.jmp
        self.operations[0b01010101] = self.jeq
        self.operations[0b01010110] = self.jne
        self.operations[0b01010111] = self.jgt
        self.operations[0b01011000] = self.jlt
        self.operations[0b01011001] = self.jle
        self.operations[0b01011010] = self.jge
        self.operations[0b10000010] = self.ldi
        self.operations[0b10000011] = self.ld
        self.operations[0b10000100] = self.st
        self.operations[0b10100000] = self.alu('ADD')
        self.operations[0b10100001] = self.alu('SUB')
        self.operations[0b10100010] = self.alu('MUL')
        self.operations[0b10100011] = self.alu('DIV')
        self.operations[0b10100100] = self.alu('MOD')
        self.operations[0b10100101] = self.alu('INC')
        self.operations[0b10100110] = self.alu('DEC')
        self.operations[0b10100111] = self.alu('CMP')
        self.operations[0b10101000] = self.alu('AND')
        self.operations[0b10101001] = self.alu('NOT')
        self.operations[0b10101010] = self.alu('OR')
        self.operations[0b10101011] = self.alu('XOR')
        self.operations[0b10101100] = self.alu('SHL')
        self.operations[0b10101101] = self.alu('SHR')

    @property
    def next_byte(self):
        """Get the next byte tracked by the pc"""
        self.program_counter += 1
        return self.ram[self.program_counter]

    @property
    def stack(self):
        """Return an array of the current stack"""
        return self.ram[stack_start:self.registers[stack_pointer]:-1]

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
        if self.used_ram < self.ram_size + self.registers[stack_pointer]:
            self.ram[self.used_ram] = value
            self.used_ram += 1
        else:
            raise Exception("RAM is FULL")

    def run(self):
        """Run the program currently loaded into RAM"""

        running = True
        while running:
            self.interupt()
            running = self.execute()
            self.interupt_timer()

    def interupt(self):
        if self.registers[interrupt_status] and not self.interupting:
            masked_interrupts = self.registers[interrupt_mask] & self.registers[interrupt_status]

            for i in range(8):
                interrupt_happened = ((masked_interrupts >> i) & 1) == 1
                if interrupt_happened:
                    self.interupting = True
                    self.registers[interrupt_status] ^= 1 << i

                    self.stack_push(self.program_counter)
                    self.stack_push(self.flags)

                    for reg in range(7):
                        self.stack_push(self.registers[reg])

                    self.program_counter = self.ram[interupt[i]] - 1
                    break

    def execute(self):
        operation = self.next_byte

        if operation in self.operations:
            self.operations[operation]()

        elif operation == 0b00000000:  # NOP
            return 2

        elif operation == 0b00000001:  # HLT
            return 0

        else:
            raise Exception("Unsupported instruction")

        return 1

    def interupt_timer(self):
        current_time = datetime.now()
        if current_time - self.last_timer > timedelta(seconds=1) and self.ram[interupt[0]]:
            self.last_timer = current_time
            self.registers[interrupt_status] = 1

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.program_counter,
            self.next_byte,
            self.next_byte,
            self.next_byte
        ), end='')

        for reg in self.registers:
            print(" %02X" % reg, end='')

        print()

    def stack_push(self, value):
        if (self.used_ram - self.registers[stack_pointer]) - self.ram_size < 0:
            self.ram[self.registers[stack_pointer]] = value
            self.registers[stack_pointer] -= 1
        else:
            raise Exception("Stack Overflow")

    def stack_pop(self):
        if self.registers[stack_pointer] < stack_start:
            self.registers[stack_pointer] += 1
            return self.ram[self.registers[stack_pointer]]
        else:
            raise Exception("Stack Underflow")

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
        self.registers[stack_pointer] += 1
        self.program_counter = self.ram[self.registers[stack_pointer]]

    def iret(self):
        """
        `IRET`

        Return from an interrupt handler.

        The following steps are executed:

        1. Registers R6-R0 are popped off the stack in that order.
        2. The `FL` register is popped off the stack.
        3. The return address is popped off the stack and stored in `PC`.
        4. Interrupts are re-enabled

        Machine code:
        ```byte
        00010011
        13
        ```
        """
        for i in range(6, -1, -1):
            self.registers[i] = self.stack_pop()

        self.flags = self.stack_pop()
        self.program_counter = self.stack_pop()
        self.interupting = False

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
        value = self.registers[reg_a]
        self.stack_push(value)

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
        reg_a = self.next_byte
        self.registers[reg_a] = self.stack_pop()

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
        value = self.registers[reg_a]
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
        value = self.registers[reg_a]
        print(chr(value), end='')

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
        to = self.registers[reg_a]

        self.ram[self.registers[stack_pointer]] = self.program_counter
        self.registers[stack_pointer] -= 1

        self.program_counter = to - 1

    def int(self):
        """
        `INT register`

        Issue the interrupt number stored in the given register.

        This will set the \_n_th bit in the `IS` register to the value in the given
        register.

        Machine code:
        ```byte
        01010010 00000rrr
        52 0r
        ```
        """
        reg_a = self.next_byte
        bit = self.registers[reg_a]
        self.registers[interrupt_status] |= 1 << bit

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
        to = self.registers[reg_a]
        self.program_counter = to - 1

    def jeq(self):
        """
        `JEQ register`

        If `equal` flag is set (true), jump to the address stored in the given register.

        Machine code:
        ```byte
        01010101 00000rrr
        55 0r
        ```
        """
        if self.flags['E']:
            self.jmp()
        else:
            self.next_byte

    def jne(self):
        """
        `JNE register`

        If `E` flag is clear (false, 0), jump to the address stored in the given
        register.

        Machine code:
        ```byte
        01010110 00000rrr
        56 0r
        ```
        """
        if not self.flags['E']:
            self.jmp()
        else:
            self.next_byte

    def jgt(self):
        """
        `JGT register`

        If `greater-than` flag is set (true), jump to the address stored in the given
        register.

        Machine code:

        ```byte
        01010111 00000rrr
        57 0r
        ```
        """
        if self.flags['G']:
            self.jmp()
        else:
            self.next_byte

    def jlt(self):
        """
        `JLT register`

        If `less-than` flag is set (true), jump to the address stored in the given
        register.

        Machine code:

        ```byte
        01011000 00000rrr
        58 0r
        ```
        """
        if self.flags['L']:
            self.jmp()
        else:
            self.next_byte

    def jle(self):
        """
        `JLE register`

        If `less-than` flag or `equal` flag is set (true), jump to the address stored in the given
        register.

        Machine code:
        ```byte
        01011001 00000rrr
        59 0r
        ```
        """
        if self.flags['E'] or self.flags['L']:
            self.jmp()
        else:
            self.next_byte

    def jge(self):
        """
        `JGE register`

        If `greater-than` flag or `equal` flag is set (true), jump to the address stored
        in the given register.

        Machine code:

        ```byte
        01011010 00000rrr
        5A 0r
        ```
        """
        if self.flags['E'] or self.flags['G']:
            self.jmp()
        else:
            self.next_byte

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
        self.registers[reg_a] = value

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
        address = self.registers[reg_b]
        value = self.ram[address]
        self.registers[reg_a] = value

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
        address = self.registers[reg_a]
        value = self.registers[reg_b]

        self.ram[address] = value

    def alu(self, op_code: str):
        """
        ALU - Arithmetic Logic Unit

        Returns a function for the given ALU operation
        """
        alu_operations = {}

        def one_reg_operation(alu_operation: Callable):
            def operation():
                reg_a = self.next_byte
                a = self.registers[reg_a]

                self.registers[reg_a] = alu_operation(a)

            return operation

        def two_reg_operation(alu_operation: Callable):
            def operation():
                reg_a = self.next_byte
                reg_b = self.next_byte

                a = self.registers[reg_a]
                b = self.registers[reg_b]

                self.registers[reg_a] = alu_operation(a, b)

            return operation

        def compare_operation():
            reg_a = self.next_byte
            reg_b = self.next_byte

            a = self.registers[reg_a]
            b = self.registers[reg_b]

            self.flags['E'] = int(a == b)
            self.flags['L'] = int(a < b)
            self.flags['G'] = int(a > b)

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

        """
        `CMP registerA registerB`

        Compare the values in two registers.

        - If they are equal, set the Equal `E` flag to 1, otherwise set it to 0.

        - If registerA is less than registerB, set the Less-than `L` flag to 1,
        otherwise set it to 0.

        - If registerA is greater than registerB, set the Greater-than `G` flag
        to 1, otherwise set it to 0.

        Machine code:
        ```byte
        10100111 00000aaa 00000bbb
        A7 0a 0b
        ```
        """
        alu_operations["CMP"] = compare_operation

        """
        `AND registerA registerB`

        Bitwise-AND the values in registerA and registerB, then store the result in
        registerA.

        Machine code:
        ```byte
        10101000 00000aaa 00000bbb
        A8 0a 0b
        ```
        """
        alu_operations["AND"] = two_reg_operation(lambda a, b: a & b)

        """
        `NOT register`

        Perform a bitwise-NOT on the value in a register, storing the result in the register.

        Machine code:

        ```byte
        01101001 00000rrr
        69 0r
        ```
        """
        alu_operations["NOT"] = one_reg_operation(lambda a: ~a)

        """
        `OR registerA registerB`

        Perform a bitwise-OR between the values in registerA and registerB, storing the
        result in registerA.

        Machine code:

        ```byte
        10101010 00000aaa 00000bbb
        AA 0a 0b
        ```
        """
        alu_operations["OR"] = two_reg_operation(lambda a, b: a | b)

        """
        `XOR registerA registerB`

        Perform a bitwise-XOR between the values in registerA and registerB, storing the
        result in registerA.

        Machine code:

        ```byte
        10101011 00000aaa 00000bbb
        AB 0a 0b
        ```
        """
        alu_operations["XOR"] = two_reg_operation(lambda a, b: a ^ b)

        """
        Shift the value in registerA left by the number of bits specified in registerB,
        filling the low bits with 0.

        Machine Code:
        ```byte
        10101100 00000aaa 00000bbb
        AC 0a 0b
        ```
        """
        alu_operations["SHL"] = two_reg_operation(lambda a, b: a << b)

        """
        Shift the value in registerA right by the number of bits specified in registerB,
        filling the high bits with 0.

        Machine Code:
        ```byte
        10101101 00000aaa 00000bbb
        AD 0a 0b
        ```
        """
        alu_operations["SHR"] = two_reg_operation(lambda a, b: a >> b)

        if op_code not in alu_operations:
            raise Exception("Unsupported ALU operation")

        return alu_operations[op_code]
