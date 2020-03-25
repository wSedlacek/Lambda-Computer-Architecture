from alu import ALU
from datetime import datetime, timedelta

interrupt_mask = 5
interrupt_status = 6
stack_pointer = 7
stack_start = -13

interupts = list(range(-8, 0))


class CPU:
    """CPU - Central Processing Unit"""

    def __init__(self):
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

        alu = ALU(self)

        self.operations = {}
        self.operations[0b00010001] = self.RET
        self.operations[0b00010011] = self.IRET
        self.operations[0b01000101] = self.PUSH
        self.operations[0b01000110] = self.POP
        self.operations[0b01000111] = self.PRN
        self.operations[0b01001000] = self.PRA
        self.operations[0b01010000] = self.CALL
        self.operations[0b01010010] = self.INT
        self.operations[0b01010100] = self.JMP
        self.operations[0b01010101] = self.JEQ
        self.operations[0b01010110] = self.JNE
        self.operations[0b01010111] = self.JGT
        self.operations[0b01011000] = self.JLT
        self.operations[0b01011001] = self.JLE
        self.operations[0b01011010] = self.JGE
        self.operations[0b10000010] = self.LDI
        self.operations[0b10000011] = self.LD
        self.operations[0b10000100] = self.ST
        self.operations[0b10100000] = alu.ADD
        self.operations[0b10100001] = alu.SUB
        self.operations[0b10100010] = alu.MUL
        self.operations[0b10100011] = alu.DIV
        self.operations[0b10100100] = alu.MOD
        self.operations[0b10100101] = alu.INC
        self.operations[0b10100110] = alu.DEC
        self.operations[0b10100111] = alu.CMP
        self.operations[0b10101000] = alu.AND
        self.operations[0b10101001] = alu.NOT
        self.operations[0b10101010] = alu.OR
        self.operations[0b10101011] = alu.XOR
        self.operations[0b10101100] = alu.SHL
        self.operations[0b10101101] = alu.SHR

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

        running = 1
        while running:
            self.process_interupt()
            running = self.execute()
            self.interupt_timer()

    def process_interupt(self):
        """Process any interupts if they exist"""

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

                    self.program_counter = self.ram[interupts[i]] - 1
                    break

    def execute(self):
        """Execute the next operation"""

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
        """Trigger a timer interupt if 1 second has passed between the last timer interupt"""

        current_time = datetime.now()
        if current_time - self.last_timer > timedelta(seconds=1) and self.ram[interupts[0]]:
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
    def RET(self):
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

        self.program_counter = self.stack_pop()

    def IRET(self):
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

    def PUSH(self):
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

    def POP(self):
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

    def PRN(self):
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

    def PRA(self):
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

    def CALL(self):
        """
        `CALL register`

        Calls a subroutine (function) at the address stored in the register.

        1. The address of the **_instruction_** _directly after_ `CALL` is
        pushed onto the stack. This allows us to return to where we left off
        when the subroutine finishes executing.
        2. The PC is set to the address stored in the given register. We jump
        to that location in RAM and execute the first instruction in the
        subroutine. The PC can move forward or backwards from its current
        location.

        Machine code:
        ```byte
        01010000 00000rrr
        50 0r
        ```
        """

        reg_a = self.next_byte
        to = self.registers[reg_a]

        self.stack_push(self.program_counter)
        self.program_counter = to - 1

    def INT(self):
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

    def JMP(self):
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

    def JEQ(self):
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
            self.JMP()
        else:
            self.next_byte

    def JNE(self):
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
            self.JMP()
        else:
            self.next_byte

    def JGT(self):
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
            self.JMP()
        else:
            self.next_byte

    def JLT(self):
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
            self.JMP()
        else:
            self.next_byte

    def JLE(self):
        """
        `JLE register`

        If `less-than` flag or `equal` flag is set (true), jump to the address stored
        in the given register.

        Machine code:
        ```byte
        01011001 00000rrr
        59 0r
        ```
        """

        if self.flags['E'] or self.flags['L']:
            self.JMP()
        else:
            self.next_byte

    def JGE(self):
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
            self.JMP()
        else:
            self.next_byte

    def LDI(self):
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

    def LD(self):
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

    def ST(self):
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
