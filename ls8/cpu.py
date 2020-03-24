"""CPU functionality."""

import sys


class CPU:
    """LS-8 compliant CPU"""

    def __init__(self):
        """Construct a new CPU"""
        self.ram = {}
        self.reg = [-1] * 8
        self.pc = -1

        self.operations = {}
        self.operations[0b10000010] = self.ldi
        self.operations[0b01000111] = self.prn
        self.operations[0b10100000] = self.alu('ADD')
        self.operations[0b10100001] = self.alu('SUB')
        self.operations[0b10100010] = self.alu('MUL')
        self.operations[0b10100011] = self.alu('DIV')

    @property
    def next_byte(self):
        """Get the next byte tracked by the pc"""
        self.pc += 1
        return self.ram[self.pc]

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

    def ram_load(self, value: int):
        """Load a value into the next memory address"""
        address = len(self.ram.values())
        self.ram[address] = value

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
