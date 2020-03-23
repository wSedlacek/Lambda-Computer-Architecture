"""CPU functionality."""

import sys
import re


class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = {}
        self.reg = {}
        self.pc = 0

    def load(self, file: str):
        """Load a program into memory."""

        if not file.endswith(".ls8"):
            raise ValueError("File must end with .ls8")

        program = []
        with open(file, 'r') as file:
            lines = file.readlines()

            for line in lines:
                # Remove Comments
                match = re.match(r'^([^#]*)#(.*)$', line)
                if match:
                    line = match.group(1)

                # Remove Whitespaces
                line = line.strip()

                if line:
                    binary = int(line, 2)
                    program.append(binary)

        address = 0
        for instruction in program:
            self.ram_write(address, instruction)
            address += 1

    def ram_read(self, address: int):
        return self.ram[address]

    def ram_write(self, address: int, value: int):
        self.ram[address] = value

    def reg_read(self, register: int):
        return self.reg[register]

    def reg_write(self, register: int, value: int):
        self.reg[register] = value

    def alu(self, op: str, reg_a: int, reg_b: int):
        """ALU operations."""

        if op == "ADD":
            self.reg_write(reg_a, self.reg[reg_a] + self.reg[reg_b])
        # elif op == "SUB": etc
        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.pc,
            self.ram_read(self.pc),
            self.ram_read(self.pc + 1),
            self.ram_read(self.pc + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""

        while True:
            instruction = self.ram_read(self.pc)

            if instruction == 0b10000010:  # LDI
                reg = self.ram_read(self.pc + 1)
                value = self.ram_read(self.pc + 2)
                self.reg_write(reg, value)
                self.pc += 2

            if instruction == 0b01000111:  # PRN
                reg = self.ram_read(self.pc + 1)
                value = self.reg_read(reg)
                print(value)
                self.pc += 1

            if instruction == 0b00000001:  # HLT
                break

            self.pc += 1
