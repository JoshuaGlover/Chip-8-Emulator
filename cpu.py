import pygame   as pg
import bit_math as bm
import numpy    as np
from settings import *
from random   import randint
from time     import time

class Cpu():
    """
    This class emulates the execution behaviour of the Chip-8 CPU.

    Attributes:
        memory ([int]): 4KB (4096 bytes) addressable memory (0x000 to 0xFFF).

        opcode (int): Current opcode the CPU is executing

        V ([int]): 16 general purpose 8-bit registers. VF is used as a carry/no borrow flag
        I (int)  : 16-bit register used to store memory addresses.

        delay_timer (int): Description of parameter `delay_timer`.
        sound_timer (int): Description of parameter `sound_timer`.

        pc (int): Program counter. Programs start at 0x200 in memory.

        stack ([int]): Stack of 16 16-bit values, used to save pc when returning from subroutines.
        sp (int)     : Points to the topmost level of the stack

        keypad ([int]): Contains the state of keys on the keypad. A non-zero value represents a
                        pressed key.

        operation_lookup (dict): Contains functions for each opcode, indexed by the most significant
                                 bit (MSB). For operations which share their MSB, this dictionary
                                 links to additional dictionary for further decoding.
    """

    def __init__(self):
        # Memory
        self.memory = [0] * 4096

        # Current Opcode
        self.opcode = 0

        # Registers
        self.V = [0] * 16
        self.I = 0

        # Timers
        self.delay_timer = 0
        self.sound_timer = 0
        self.last_timer_decrement = time()

        # Program Counter
        self.pc = 0x200

        # Stack
        self.stack = [0] * 16
        self.sp = 0

        # Keypad
        self.keypad = [0] * 16

        # Display
        self.display = np.zeros((WIDTH, HEIGHT))

        # Draw flag
        self.draw_flag = False

        # Operation Lookup Table
        self.operation_lookup = {
            0x0: self.clear_or_return,
            0x1: self.jump_to_address,
            0x2: self.jump_to_subroutine,
            0x3: self.skip_if_reg_equal_val,
            0x4: self.skip_if_reg_not_equal_val,
            0x5: self.skip_if_reg_equal_reg,
            0x6: self.move_val_to_reg,
            0x7: self.add_val_to_reg,
            0x8: self.arithmetic_operation,
            0x9: self.skip_if_reg_not_equal_reg,
            0xA: self.load_index_reg_with_val,
            0xB: self.jump_to_address_plus_reg,
            0xC: self.generate_random_number,
            0xD: self.display_sprite,
            0xE: self.key_operation,
            0xF: self.misc_operation
        }

        # Arithmetic Operation Lookup
        self.arithmetic_operation_lookup = {
            0x0: self.move_reg_into_reg,
            0x1: self.or_reg_into_reg,
            0x2: self.and_reg_into_reg,
            0x3: self.xor_reg_into_reg,
            0x4: self.add_reg_into_reg,
            0x5: self.sub_reg_into_reg,
            0x6: self.right_shift_reg,
            0x7: self.rsub_reg_into_reg,
            0xE: self.left_shift_reg
        }

        # Miscellaneous Operation Lookup
        self.misc_operation_lookup = {
            0x07: self.move_delay_timer_into_reg ,
            0x0A: self.wait_for_keypress ,
            0x15: self.move_reg_into_delay_timer ,
            0x18: self.move_reg_into_sound_timer ,
            0x1E: self.add_reg_into_index ,
            0x29: self.load_index_with_reg_sprite ,
            0x33: self.store_bcd_into_memory ,
            0x55: self.store_regs_into_memory ,
            0x65: self.load_memory_into_regs
        }

    def execute_cycle(self):
        # Fetch opcode and increment pc
        self.opcode = (self.memory[self.pc] << 8) + self.memory[self.pc + 1]

        # Decode and execute opcode
        operation = self.opcode >> 12
        self.operation_lookup[operation]()

        # Don't increment pc if a jump occured since we want to preserve the address we jumped to
        if operation != 0x1 and operation != 0x2:
            self.pc += 2

        # Decrement timers
        self.decrement_timers()

    ####################
    # Opcode Functions #
    ####################

    def clear_or_return(self):
        """ Decodes clear and return opcodes (MSB of 0) further and calls relevant function """
        if self.opcode == 0x00E0:
            self.clear_display()
        if self.opcode == 0x00EE:
            self.return_from_subroutine()

    def clear_display(self):
        """ 00E0 - Clear display """
        self.display = np.zeros((WIDTH, HEIGHT))

    def return_from_subroutine(self):
        """ 00EE - Return from subroutine """
        self.pc = self.stack[self.sp - 1]
        self.sp -= 1

    def jump_to_address(self):
        """ 1NNN - Jumps to address NNN """
        self.pc = (self.opcode & 0x0FFF)

    def jump_to_subroutine(self):
        """ 2NNN - Calls subroutine NNN """
        self.stack[self.sp] = self.pc
        self.sp += 1
        self.pc = (self.opcode & 0x0FFF)

    def skip_if_reg_equal_val(self):
        """ 3XNN - Skips next instruction if VX == NN """
        reg = (self.opcode & 0x0F00) >> 8
        val = self.opcode & 0x00FF
        if self.V[reg] == val:
            self.pc += 2

    def skip_if_reg_not_equal_val(self):
        """ 4XNN - Skips next instruction if VX != NN """
        reg = (self.opcode & 0x0F00) >> 8
        val = self.opcode & 0x00FF
        if self.V[reg] != val:
            self.pc += 2

    def skip_if_reg_equal_reg(self):
        """ 5XY0 - Skips next instruction if VX == VY """
        reg_x = (self.opcode & 0x0F00) >> 8
        reg_y = (self.opcode & 0x00F0) >> 4
        if self.V[reg_x] == self.V[reg_y]:
            self.pc += 2

    def move_val_to_reg(self):
        """ 6XNN - Sets VX to NN """
        reg = (self.opcode & 0x0F00) >> 8
        val = self.opcode & 0x00FF
        self.V[reg] = val

    def add_val_to_reg(self):
        """ 7XNN - Adds NN to VX (VF unchanged) """
        reg = (self.opcode & 0x0F00) >> 8
        val = self.opcode & 0x00FF
        self.V[reg], _ = bm.add(8, self.V[reg], val)

    def arithmetic_operation(self):
        """ Decodes arithmetic opcodes (MSB of 8) and calls relevant function """
        operation = self.opcode & 0x000F
        x = (self.opcode & 0x0F00) >> 8
        y = (self.opcode & 0x00F0) >> 4
        self.arithmetic_operation_lookup[operation](x, y)

    def move_reg_into_reg(self, x, y):
        """ 8XY0 - Sets VX to VY """
        self.V[x] = self.V[y]

    def or_reg_into_reg(self, x, y):
        """ 8XY1 - Sets VX to VX | VY """
        self.V[x] = self.V[x] | self.V[y]

    def and_reg_into_reg(self, x, y):
        """ 8XY2 - Sets VX to VX & VY """
        self.V[x] = self.V[x] & self.V[y]

    def xor_reg_into_reg(self, x, y):
        """ 8XY3 - Sets VX to VX ^ VY """
        self.V[x] = self.V[x] ^ self.V[y]

    def add_reg_into_reg(self, x, y):
        """ 8XY4 - Sets VX to VX + VY. VF set if carry occurs """
        self.V[x], self.V[0xF] = bm.add(8, self.V[x], self.V[y])

    def sub_reg_into_reg(self, x, y):
        """ 8XY5 - Sets VX to VX - VY. VF set if no borrow occurs """
        self.V[x], self.V[0xF] = bm.sub(8, self.V[x], self.V[y])

    def right_shift_reg(self, x, y):
        """ 8XY6 - Stores LSB of VX in VF then shifts VX to the right by 1. """
        self.V[0xF] = self.V[x] & 0x01
        self.V[x] = self.V[x] >> 1

    def rsub_reg_into_reg(self, x, y):
        """ 8XY7 - Sets VX to VY - VX. VF set if no borrow occurs """
        self.V[x], self.V[0xF] = bm.sub(8, self.V[y], self.V[x])

    def left_shift_reg(self, x, y):
        """ 8XYE - Stores MSB of VX in VF then shifts VX to the left by 1. """
        self.V[0xF] = (self.V[x] & 0x80) >> 7
        self.V[x] = (self.V[x] << 1) & 0xFF

    def skip_if_reg_not_equal_reg(self):
        """ 9XY0 - Skips next instruction if VX != VY """
        reg_x = (self.opcode & 0x0F00) >> 8
        reg_y = (self.opcode & 0x00F0) >> 4
        if self.V[reg_x] != self.V[reg_y]:
            self.pc += 2

    def load_index_reg_with_val(self):
        """ ANNN - Sets I to NNN """
        self.I = self.opcode & 0x0FFF

    def jump_to_address_plus_reg(self):
        """ BNNN - Jumps to V0 + NNN """
        address = self.opcode & 0x0FFF
        self.pc, _ = bm.add(12, address, self.V[0])

    def generate_random_number(self):
        """ CXNN - Sets VX to bitwise and of NN and random number (0 to 255) """
        reg = (self.opcode & 0x0F00) >> 8
        val = self.opcode & 0x00FF
        self.V[reg] = randint(0, 255) & val

    def display_sprite(self):
        """
        DXYN - Draws a sprite at coordinate (VX, VY) of width 8 pixels and height N. Each row of
        8 pixels is read as bit-coded starting from address I. VF set if a pixel changes from 0 to 1
        """
        self.V[0xF] = 0

        col = self.V[(self.opcode & 0x0F00) >> 8]
        row = self.V[(self.opcode & 0x00F0) >> 4]
        height = self.opcode & 0x000F
        width  = 8

        for dy in range(height):
            for dx in range(width):
                x = (col + dx) % WIDTH
                y = (row + dy) % HEIGHT

                if self.display[x][y] == 1 and bm.extract_bit((width - 1) - dx, self.memory[self.I + dy]) == 1:
                    self.V[0xF] = 1

                self.display[x][y] = int(self.display[x][y]) ^ int(bm.extract_bit((width - 1) - dx, self.memory[self.I + dy]))

        self.draw_flag = True

    def key_operation(self):
        """ Decodes keypad opcodes (MSB of E) and calls relevant function """
        operation = self.opcode & 0x00FF
        reg = (self.opcode & 0x0F00) >> 8

        if operation == 0x9E:
            self.skip_if_key_pressed(self.V[reg])
        if operation == 0xA1:
            self.skip_if_key_not_pressed(self.V[reg])

    def skip_if_key_pressed(self, key):
        """ EX9E - Skips next instruction if key with value VX is pressed """
        reg = (self.opcode & 0x0F00) >> 8
        if self.keypad[key] != 0:
            self.pc += 2

    def skip_if_key_not_pressed(self, key):
        """ EXA1 - Skips next instruction if key with value VX is not pressed """
        reg = (self.opcode & 0x0F00) >> 8
        if self.keypad[key] == 0:
            self.pc += 2

    def misc_operation(self):
        """ Decodes miscellaneous opcodes (MSB of F) and calls relevant function """
        operation = self.opcode & 0x00FF
        reg = (self.opcode & 0x0F00) >> 8
        self.misc_operation_lookup[operation](reg)

    def move_delay_timer_into_reg(self, reg):
        """ FX07 - Sets VX to delay timer """
        self.V[reg] = self.delay_timer

    def wait_for_keypress(self, reg):
        """ FX0A - Waits for keypress and stores it in register VX """
        pass

    def move_reg_into_delay_timer(self, reg):
        """ FX15 - Sets delay timer to VX """
        self.delay_timer = self.V[reg]

    def move_reg_into_sound_timer(self, reg):
        """ FX18 - Sets sound timer to VX """
        self.sound_timer = self.V[reg]

    def add_reg_into_index(self, reg):
        """ FX1E - Sets I to I + VX. VF set if range overflow occurs """
        self.I, self.V[0xF] = bm.add(12, self.I, self.V[reg])

    def load_index_with_reg_sprite(self, reg):
        """ FX29 - Sets I to the location of the sprite for the character in VX """
        self.I = 0x050 + 5 * self.V[reg]

    def store_bcd_into_memory(self, reg):
        """ FX33 - Sets I to the binary-coded decimal of VX """
        digits = [int(d) for d in str(self.V[reg]).zfill(3)]
        self.memory[self.I : self.I + 3] = digits

    def store_regs_into_memory(self, reg):
        """ FX55 - Stores V0 to VX (including VX) in memory starting at address I """
        for i in range(reg + 1):
            self.memory[self.I + i] = self.V[i]

    def load_memory_into_regs(self, reg):
        """ FX65 - Fills V0 to VX (including VX) with values from memory starting at address I """
        for i in range(reg + 1):
            self.V[i] = self.memory[self.I + i]

    ##################
    # Misc Functions #
    ##################

    def decrement_timers(self):
        now = time()
        if now - self.last_timer_decrement >= 1.0/60:
            if self.delay_timer > 0:
                self.delay_timer -= 1

            if self.sound_timer > 0:
                self.sound_timer -= 1

            self.last_timer_decrement = now

    def load_file_to_memory(self, rom, start_address):
        with open(rom, "rb") as game:
            data = game.read()
            for i in range(len(data)):
                self.memory[start_address + i] = data[i]

    ####################
    # Debug Functions #
    ####################

    def insert_to_memory(self, value, address):
        print("Inserting " + hex(value).upper() + " at memory[" + hex(address).upper() + "]")
        self.memory[address] = value

    def print_program_memory(self, length):
        print([hex(x).upper() for x in self.memory[0x200:0x200 + length]])

    def print_registers(self):
        for (i, value) in enumerate(self.V):
            print("V" + hex(i).upper()[2] + ": " + hex(value).upper())
        print("I : " + hex(self.I).upper())

    def print_display(self):
        for row in range(HEIGHT):
            for col in range(WIDTH):
                if self.display[col][row] == 0:
                    print("_", end = "")
                else:
                    print("#", end = "")
            print("")
