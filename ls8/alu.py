from typing import Callable, TYPE_CHECKING


if TYPE_CHECKING:
    from cpu import CPU


class ALU:
    """ALU - Arithmetic Logic Unit"""

    def __init__(self, cpu: "CPU"):
        self.cpu = cpu

    def one_reg_operation(self, alu_operation: Callable):
        """
        Build an ALU operation that takes only one register
        and sets the result to that same register
        """

        def operation():
            reg_a = self.cpu.next_byte
            a = self.cpu.registers[reg_a]

            self.cpu.registers[reg_a] = alu_operation(a)

            return 1

        return operation

    def two_reg_operation(self, alu_operation: Callable):
        """
        Build an ALU operation that uses two registers and
        sets the result to the first register
        """
        def operation():
            reg_a = self.cpu.next_byte
            reg_b = self.cpu.next_byte

            a = self.cpu.registers[reg_a]
            b = self.cpu.registers[reg_b]

            self.cpu.registers[reg_a] = alu_operation(a, b)

            return 1

        return operation

    def compare_operation(self):
        """
        Compare the two registers and set CPU flags based on
        the results
        """
        reg_a = self.cpu.next_byte
        reg_b = self.cpu.next_byte

        a = self.cpu.registers[reg_a]
        b = self.cpu.registers[reg_b]

        self.cpu.flags['E'] = int(a == b)
        self.cpu.flags['L'] = int(a < b)
        self.cpu.flags['G'] = int(a > b)

        return 1

    ##### OPERATIONS ####
    @property
    def ADD(self):
        """
        `ADD registerA registerB`

        Add the value in two registers and store the result in registerA.

        Machine code:
        ```byte
        10100000 00000aaa 00000bbb
        A0 0a 0b
        ```
        """

        return self.two_reg_operation(lambda a, b: a + b)

    @property
    def SUB(self):
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

        return self.two_reg_operation(lambda a, b: a - b)

    @property
    def MUL(self):
        """
        `MUL registerA registerB`

        Multiply the values in two registers together and store the result in registerA.

        Machine code:
        ```byte
        10100010 00000aaa 00000bbb
        A2 0a 0b
        ```
        """

        return self.two_reg_operation(lambda a, b: a * b)

    @property
    def DIV(self):
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

        return self.two_reg_operation(lambda a, b: a / b)

    @property
    def MOD(self):
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

        return self.two_reg_operation(lambda a, b: a % b)

    @property
    def INC(self):
        """
        `INC register`

        Increment (add 1 to) the value in the given register.

        Machine code:

        ```byte
        01100101 00000rrr
        65 0r
        ```
        """

        return self.one_reg_operation(lambda a: a + 1)

    @property
    def DEC(self):
        """
        `DEC register`

        Decrement (subtract 1 from) the value in the given register.

        Machine code:
        ```byte
        01100110 00000rrr
        66 0r
        ```
        """

        return self.one_reg_operation(lambda a: a - 1)

    @property
    def CMP(self):
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

        return self.compare_operation

    @property
    def AND(self):
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

        return self.two_reg_operation(lambda a, b: a & b)

    @property
    def NOT(self):
        """
        `NOT register`

        Perform a bitwise-NOT on the value in a register, storing the result in the register.

        Machine code:

        ```byte
        01101001 00000rrr
        69 0r
        ```
        """

        return self.one_reg_operation(lambda a: ~a)

    @property
    def OR(self):
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

        return self.two_reg_operation(lambda a, b: a | b)

    @property
    def XOR(self):
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

        return self.two_reg_operation(lambda a, b: a ^ b)

    @property
    def SHL(self):
        """
        Shift the value in registerA left by the number of bits specified in registerB,
        filling the low bits with 0.

        Machine Code:
        ```byte
        10101100 00000aaa 00000bbb
        AC 0a 0b
        ```
        """

        return self.two_reg_operation(lambda a, b: a << b)

    @property
    def SHR(self):
        """
        Shift the value in registerA right by the number of bits specified in registerB,
        filling the high bits with 0.

        Machine Code:
        ```byte
        10101101 00000aaa 00000bbb
        AD 0a 0b
        ```
        """

        return self.two_reg_operation(lambda a, b: a >> b)
