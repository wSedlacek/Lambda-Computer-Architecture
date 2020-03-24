"""CPU functionality."""

import sys


class CPU:
    """Main CPU class."""

    def __init__(self):
        """Construct a new CPU."""
        self.ram = {}
        self.reg = [-1] * 8
        self.pc = -1

    @property
    def counter(self):
        self.pc += 1
        return self.pc

    def load(self, file: str):
        """Load a program into memory."""

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
        address = len(self.ram.values())
        self.ram[address] = value

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

        elif op == "SUB":
            self.reg_write(reg_a, self.reg[reg_a] - self.reg[reg_b])

        elif op == "MUL":
            self.reg_write(reg_a, self.reg[reg_a] * self.reg[reg_b])

        elif op == "DIV":
            self.reg_write(reg_a, self.reg[reg_a] / self.reg[reg_b])

        else:
            raise Exception("Unsupported ALU operation")

    def trace(self):
        """
        Handy function to print out the CPU state. You might want to call this
        from run() if you need help debugging.
        """

        print(f"TRACE: %02X | %02X %02X %02X |" % (
            self.counter,
            self.ram_read(self.counter),
            self.ram_read(self.counter + 1),
            self.ram_read(self.counter + 2)
        ), end='')

        for i in range(8):
            print(" %02X" % self.reg[i], end='')

        print()

    def run(self):
        """Run the CPU."""

        while True:
            instruction = self.ram_read(self.counter)

            if instruction == 0b10000010:  # LDI
                reg_a = self.ram_read(self.counter)
                value = self.ram_read(self.counter)
                self.reg_write(reg_a, value)

            elif instruction == 0b01000111:  # PRN
                reg_a = self.ram_read(self.counter)
                value = self.reg_read(reg_a)
                print(value)

            elif instruction == 0b10100000:  # ADD
                reg_a = self.ram_read(self.counter)
                reg_b = self.ram_read(self.counter)
                self.alu("ADD", reg_a, reg_b)

            elif instruction == 0b10100001:  # SUB
                reg_a = self.ram_read(self.counter)
                reg_b = self.ram_read(self.counter)
                self.alu("SUB", reg_a, reg_b)

            elif instruction == 0b10100010:  # MUL
                reg_a = self.ram_read(self.counter)
                reg_b = self.ram_read(self.counter)
                self.alu("MUL", reg_a, reg_b)

            elif instruction == 0b10100011:  # DIV
                reg_a = self.ram_read(self.counter)
                reg_b = self.ram_read(self.counter)
                self.alu("DIV", reg_a, reg_b)

            elif instruction == 0b00000001:  # HLT
                break

            else:
                raise Exception("Unsupported instruction")
