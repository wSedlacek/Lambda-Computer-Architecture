"""CPU functionality."""

import sys


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
        self.operations[0b01010000] = self.call
        self.operations[0b01010100] = self.jmp
        self.operations[0b10000010] = self.ldi
        self.operations[0b10100000] = self.alu('ADD')
        self.operations[0b10100001] = self.alu('SUB')
        self.operations[0b10100010] = self.alu('MUL')
        self.operations[0b10100011] = self.alu('DIV')

    @property
    def next_byte(self):
        """Get the next byte tracked by the pc"""
        self.pc += 1
        return self.ram[self.pc]

    @property
    def stack(self):
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
        if self.used_ram < self.ram_size:
            self.ram[self.used_ram] = value
            self.used_ram += 1
        else:
            raise Exception("RAM is FULL")

    def alu(self, operation: str):
        """ALU operations"""
        alu_operations = {}

        alu_operations["ADD"] = lambda a, b: a + b
        alu_operations["SUB"] = lambda a, b: a - b
        alu_operations["MUL"] = lambda a, b: a * b
        alu_operations["DIV"] = lambda a, b: a / b

        if operation not in alu_operations:
            raise Exception("Unsupported ALU operation")

        def alu_operation():
            reg_a = self.next_byte
            reg_b = self.next_byte

            a = self.reg[reg_a]
            b = self.reg[reg_b]

            self.reg[reg_a] = alu_operations[operation](a, b)

        return alu_operation

    def ldi(self):
        reg_a = self.next_byte
        value = self.next_byte
        self.reg[reg_a] = value

    def prn(self):
        reg_a = self.next_byte
        value = self.reg[reg_a]
        print(value)

    def push(self):
        reg_a = self.next_byte
        value = self.reg[reg_a]
        self.ram[self.stack_end] = value
        self.stack_end -= 1

    def pop(self):
        self.stack_end += 1
        value = self.ram[self.stack_end]
        reg_a = self.next_byte
        self.reg[reg_a] = value

    def jmp(self):
        reg_a = self.next_byte
        to = self.reg[reg_a]
        self.pc = to - 1

    def call(self):
        reg_a = self.next_byte
        to = self.reg[reg_a]

        self.ram[self.stack_end] = self.pc
        self.stack_end -= 1

        self.pc = to - 1

    def ret(self):
        self.stack_end += 1
        self.pc = self.ram[self.stack_end]

    def run(self):
        """Run the program currently loaded into RAM"""

        while True:
            operation = self.next_byte

            if operation in self.operations:
                self.operations[operation]()

            elif operation == 0b00000001:  # HLT
                break

            else:
                raise Exception("Unsupported instruction")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            self.next_byte,
            self.next_byte,
            self.next_byte
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()
