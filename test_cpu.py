import unittest
import cpu
import numpy as np
from settings import *

class Test_Cpu(unittest.TestCase):
    """ Test file containing unit tests for cpu.py. Tests all opcodes """

    def setUp(self):
        """ Setup performed before each test """
        self.cpu = cpu.Cpu()

    def test_clear_display(self):
        for i in range(WIDTH):
            for j in range(HEIGHT):
                if i == j:
                    self.cpu.display[i][j] = 1
        self.cpu.clear_display()
        self.assertTrue(np.array_equal(self.cpu.display, np.zeros((WIDTH, HEIGHT))))

    def test_return_from_subroutine(self):
        for address in range(0x200, 0xFFF, 0x10):
            self.cpu.opcode = concat_hex([0x0, 0x0, 0xEE])
            self.cpu.pc = address
            self.cpu.sp = 0
            self.cpu.jump_to_subroutine()
            self.cpu.return_from_subroutine()
            self.assertEqual(self.cpu.pc, address)
            self.assertEqual(self.cpu.sp, 0)

    def test_jump_to_address(self):
        for address in range(0x200, 0xFFF, 0x10):
            self.cpu.opcode = concat_hex([0x1, address])
            self.cpu.jump_to_address()
            self.assertEqual(self.cpu.pc, address)

    def test_jump_to_subroutine(self):
        for address in range(0x200, 0xFFF, 0x10):
            self.cpu.opcode = concat_hex([0x2, address])
            self.cpu.pc = 0x333
            self.cpu.sp = 0
            self.cpu.jump_to_subroutine()
            self.assertEqual(self.cpu.pc, address)
            self.assertEqual(self.cpu.sp, 1)
            self.assertEqual(self.cpu.stack[0], 0x333)

    def test_skip_if_reg_equal_val(self):
        for reg in range(15):
            self.cpu.opcode = concat_hex([0x3, reg, 0xAB])
            self.cpu.V[reg] = 0xAB
            self.cpu.pc = 0
            self.cpu.skip_if_reg_equal_val()
            self.assertEqual(self.cpu.pc, 0x2)
            self.cpu.V[reg] = 0xCD
            self.cpu.pc = 0
            self.cpu.skip_if_reg_equal_val()
            self.assertEqual(self.cpu.pc, 0x0)

    def test_skip_if_reg_not_equal_val(self):
        for reg in range(15):
            self.cpu.opcode = concat_hex([0x4, reg, 0xAB])
            self.cpu.V[reg] = 0xAB
            self.cpu.pc = 0
            self.cpu.skip_if_reg_not_equal_val()
            self.assertEqual(self.cpu.pc, 0x0)
            self.cpu.V[reg] = 0xCD
            self.cpu.pc = 0
            self.cpu.skip_if_reg_not_equal_val()
            self.assertEqual(self.cpu.pc, 0x2)

    def test_skip_if_reg_equal_reg(self):
        for reg in range(1, 15):
            self.cpu.opcode = concat_hex([0x5, 0x0, reg, 0x0])
            self.cpu.V[0x0] = 0xAB
            self.cpu.V[reg] = 0xAB
            self.cpu.pc = 0
            self.cpu.skip_if_reg_equal_reg()
            self.assertEqual(self.cpu.pc, 0x2)
            self.cpu.V[reg] = 0xCD
            self.cpu.pc = 0
            self.cpu.skip_if_reg_equal_reg()
            self.assertEqual(self.cpu.pc, 0x0)

    def test_move_val_to_reg(self):
        for reg in range(15):
            self.cpu.opcode = concat_hex([0x6, reg, 0xCC])
            self.cpu.move_val_to_reg()
            self.assertEqual(self.cpu.V[reg], 0xCC)

    def test_add_val_to_reg(self):
        for reg in range(15):
            self.cpu.opcode = concat_hex([0x6, reg, 0x2A])
            self.cpu.V[reg] = 0x08
            self.cpu.add_val_to_reg()
            self.assertEqual(self.cpu.V[reg], 0x32)
            self.cpu.opcode = concat_hex([0x6, reg, 0xEE])
            self.cpu.add_val_to_reg()
            self.assertEqual(self.cpu.V[reg], 0x20)
            self.assertEqual(self.cpu.V[0xF], 0)

    def test_move_reg_into_reg(self):
        for reg in range(1, 15):
            self.cpu.opcode = concat_hex([0x8, reg, 0x0, 0x0])
            self.cpu.V[0x0] = 0xCC
            self.cpu.arithmetic_operation()
            self.assertEqual(self.cpu.V[reg], self.cpu.V[0x0])
            self.assertEqual(self.cpu.V[reg], 0xCC)

    def test_or_reg_into_reg(self):
        for reg in range(1, 15):
            self.cpu.opcode = concat_hex([0x8, reg, 0x0, 0x1])
            self.cpu.V[0x0] = 0x99
            self.cpu.V[reg] = 0x54
            self.cpu.arithmetic_operation()
            self.assertEqual(self.cpu.V[reg], 0x99 | 0x54)

    def test_and_reg_into_reg(self):
        for reg in range(1, 15):
            self.cpu.opcode = concat_hex([0x8, reg, 0x0, 0x2])
            self.cpu.V[0x0] = 0x99
            self.cpu.V[reg] = 0x54
            self.cpu.arithmetic_operation()
            self.assertEqual(self.cpu.V[reg], 0x99 & 0x54)

    def test_xor_reg_into_reg(self):
        for reg in range(1, 15):
            self.cpu.opcode = concat_hex([0x8, reg, 0x0, 0x3])
            self.cpu.V[0x0] = 0x99
            self.cpu.V[reg] = 0x54
            self.cpu.arithmetic_operation()
            self.assertEqual(self.cpu.V[reg], 0x99 ^ 0x54)

    def test_add_reg_into_reg_no_carry(self):
        for reg in range(1, 15):
            self.cpu.opcode = concat_hex([0x8, reg, 0x0, 0x4])
            self.cpu.V[0x0] = 0x12
            self.cpu.V[reg] = 0x34
            self.cpu.arithmetic_operation()
            self.assertEqual(self.cpu.V[reg], 0x12 + 0x34)
            self.assertEqual(self.cpu.V[0xF], 0x0)

    def test_add_reg_into_reg_carry(self):
        for reg in range(1, 15):
            self.cpu.opcode = concat_hex([0x8, reg, 0x0, 0x4])
            self.cpu.V[0x0] = 0xAB
            self.cpu.V[reg] = 0xCD
            self.cpu.arithmetic_operation()
            self.assertEqual(self.cpu.V[reg], (0xAB + 0xCD) & 0xFF)
            self.assertEqual(self.cpu.V[0xF], 0x1)

    def test_sub_reg_into_reg_no_borrow(self):
        for reg in range(1, 15):
            self.cpu.opcode = concat_hex([0x8, reg, 0x0, 0x5])
            self.cpu.V[0x0] = 0xAB
            self.cpu.V[reg] = 0xCD
            self.cpu.arithmetic_operation()
            self.assertEqual(self.cpu.V[reg], 0xCD - 0xAB)
            self.assertEqual(self.cpu.V[0xF], 0x1)

    def test_sub_reg_into_reg_borrow(self):
        for reg in range(1, 15):
            self.cpu.opcode = concat_hex([0x8, reg, 0x0, 0x5])
            self.cpu.V[0x0] = 0xCD
            self.cpu.V[reg] = 0xAB
            self.cpu.arithmetic_operation()
            self.assertEqual(self.cpu.V[reg], (0xAB - 0xCD) & 0xFF)
            self.assertEqual(self.cpu.V[0xF], 0x0)

    def test_right_shift_reg(self):
        for reg in range(15):
            self.cpu.opcode = concat_hex([0x8, reg, 0x0, 0x6])
            self.cpu.V[reg] = 0b10101101
            self.cpu.arithmetic_operation()
            self.assertEqual(self.cpu.V[reg], 0b01010110)
            self.assertEqual(self.cpu.V[0xF], 0b1)

    def test_rsub_reg_into_reg_no_borrow(self):
        for reg in range(1, 15):
            self.cpu.opcode = concat_hex([0x8, reg, 0x0, 0x7])
            self.cpu.V[0x0] = 0xCD
            self.cpu.V[reg] = 0xAB
            self.cpu.arithmetic_operation()
            self.assertEqual(self.cpu.V[reg], 0xCD - 0xAB)
            self.assertEqual(self.cpu.V[0xF], 0x1)

    def test_rsub_reg_into_reg_borrow(self):
        for reg in range(1, 15):
            self.cpu.opcode = concat_hex([0x8, reg, 0x0, 0x7])
            self.cpu.V[0x0] = 0xAB
            self.cpu.V[reg] = 0xCD
            self.cpu.arithmetic_operation()
            self.assertEqual(self.cpu.V[reg], (0xAB - 0xCD) & 0xFF)
            self.assertEqual(self.cpu.V[0xF], 0x0)

    def left_shift_reg(self):
        for reg in range(15):
            self.cpu.V[reg] = 0b10101101
            self.cpu.opcode = concat_hex([0x8, reg, 0x0, 0xE])
            self.cpu.arithmetic_operation()
            self.assertEqual(self.cpu.V[reg], 0b010111010)
            self.assertEqual(self.cpu.V[0xF], 0b1)

    def test_skip_if_reg_not_equal_reg(self):
        for reg in range(1, 15):
            self.cpu.opcode = concat_hex([0x9, 0x0, reg, 0x0])
            self.cpu.V[0x0] = 0xAB
            self.cpu.V[reg] = 0xAB
            self.cpu.pc = 0
            self.cpu.skip_if_reg_not_equal_reg()
            self.assertEqual(self.cpu.pc, 0x0)
            self.cpu.V[reg] = 0xCD
            self.cpu.pc = 0
            self.cpu.skip_if_reg_not_equal_reg()
            self.assertEqual(self.cpu.pc, 0x2)

    def test_load_index_reg_with_val(self):
        self.cpu.opcode = concat_hex([0xA, 0xABC])
        self.cpu.load_index_reg_with_val()
        self.assertEqual(self.cpu.I, 0xABC)

    def test_jump_to_address_plus_reg_no_overflow(self):
        self.cpu.opcode = concat_hex([0xB, 0x123])
        self.cpu.V[0x0] = 0xFF
        self.cpu.jump_to_address_plus_reg()
        self.assertEqual(self.cpu.pc, 0x123 + 0xFF)

    def test_jump_to_address_plus_reg_overflow(self):
        self.cpu.opcode = concat_hex([0xB, 0xFFE])
        self.cpu.V[0x0] = 0xFF
        self.cpu.jump_to_address_plus_reg()
        self.assertEqual(self.cpu.pc, (0xFFE + 0xFF) & 0xFFF)

    def test_generate_random_number(self):
        self.cpu.opcode = concat_hex([0xC, 0x0, 0x00])
        self.cpu.generate_random_number()
        self.assertEqual(self.cpu.V[0x0], 0x00)
        self.cpu.opcode = concat_hex([0xC, 0x0, 0xFF])
        self.cpu.generate_random_number()
        self.assertTrue(self.cpu.V[0x0] >= 0 and self.cpu.V[0x0] <= 255)

    @unittest.SkipTest
    def test_display_sprite(self):
        pass

    def test_skip_if_key_pressed(self):
        for key in range(16):
            self.cpu.opcode = concat_hex([0xE, 0x0, 0x9E])
            self.cpu.pc = 0x0
            self.cpu.V[0x0] = key
            self.cpu.key_operation()
            self.assertEqual(self.cpu.pc, 0x0)
            self.cpu.keypad[key] = 1
            self.cpu.key_operation()
            self.assertEqual(self.cpu.pc, 0x2)

    def test_skip_if_key_not_pressed(self):
        for key in range(16):
            self.cpu.opcode = concat_hex([0xE, 0x0, 0xA1])
            self.cpu.pc = 0x0
            self.cpu.V[0x0] = key
            self.cpu.keypad[key] = 1
            self.cpu.key_operation()
            self.assertEqual(self.cpu.pc, 0x0)
            self.cpu.keypad[key] = 0
            self.cpu.key_operation()
            self.assertEqual(self.cpu.pc, 0x2)

    def test_move_delay_timer_into_reg(self):
        for reg in range(15):
            self.cpu.opcode = concat_hex([0xF, reg, 0x0, 0x7])
            self.cpu.delay_timer = 0xAB
            self.cpu.misc_operation()
            self.assertEqual(self.cpu.V[reg], 0xAB)

    @unittest.SkipTest
    def test_wait_for_keypress(self):
        pass

    def test_move_reg_into_delay_timer(self):
        for reg in range(15):
            self.cpu.opcode = concat_hex([0xF, reg, 0x15])
            self.cpu.V[reg] = 0xAB + reg
            self.cpu.misc_operation()
            self.assertEqual(self.cpu.delay_timer, 0xAB + reg)

    def test_move_reg_into_sound_timer(self):
        for reg in range(15):
            self.cpu.opcode = concat_hex([0xF, reg, 0x18])
            self.cpu.V[reg] = 0xAB + reg
            self.cpu.misc_operation()
            self.assertEqual(self.cpu.sound_timer, 0xAB + reg)

    def test_add_reg_into_index_no_overflow(self):
        for reg in range(15):
            self.cpu.opcode = concat_hex([0xF, reg, 0x1E])
            self.cpu.I = 0x123
            self.cpu.V[reg] = 0xFF
            self.cpu.misc_operation()
            self.assertEqual(self.cpu.I, 0x123 + 0xFF)
            self.assertEqual(self.cpu.V[0xF], 0x0)

    def test_add_reg_into_index_overflow(self):
        for reg in range(15):
            self.cpu.opcode = concat_hex([0xF, reg, 0x1E])
            self.cpu.I = 0xFF0
            self.cpu.V[reg] = 0xFF
            self.cpu.misc_operation()
            self.assertEqual(self.cpu.I, (0xFF0 + 0xFF) & 0xFFF)
            self.assertEqual(self.cpu.V[0xF], 0x1)

    def test_load_index_with_reg_sprite(self):
        for sprite in range(16):
            self.cpu.opcode = concat_hex([0xF, 0x0, 0x29])
            self.cpu.V[0x0] = sprite
            self.cpu.misc_operation()
            self.assertEqual(self.cpu.I, 0x050 + 5 * self.cpu.V[0x0])

    def test_store_bcd_into_memory(self):
        for reg in range(15):
            self.cpu.opcode = concat_hex([0xF, reg, 0x33])
            self.cpu.I = 0x300
            self.cpu.V[reg] = 123
            self.cpu.misc_operation()
            self.assertEqual(self.cpu.memory[0x300], 1)
            self.assertEqual(self.cpu.memory[0x301], 2)
            self.assertEqual(self.cpu.memory[0x302], 3)

    def test_store_regs_into_memory(self):
        self.cpu.I = 0x333
        self.cpu.V = list(range(15))
        for reg in range(15):
            self.cpu.opcode = concat_hex([0xF, reg, 0x55])
            self.cpu.misc_operation()
            for i in range(reg + 1):
                self.assertEqual(self.cpu.memory[0x333 + i], self.cpu.V[i])

    def test_load_memory_into_regs(self):
        self.cpu.I = 0x333
        for reg in range(15):
            self.cpu.memory[0x333 + reg] = reg
        for reg in range(15):
            self.cpu.opcode = concat_hex([0xF, reg, 0x65])
            self.cpu.V = [0] * 16
            self.cpu.misc_operation()
            for i in range(reg + 1):
                self.assertEqual(self.cpu.V[i], i)

####################
# Helper Functions #
####################

def concat_hex(digits):
    """
    Converts the ints in the list to hex strings and joins them.
    [0xF, 0x33, 0x4] -> 0xF334

    Args:
        digits ([ints]): List of ints representing hex digits

    Returns:
        int: int after concatenation

    """
    joined = "".join([hex(digit)[2:] for digit in digits])
    return int(joined, 16)

if __name__ == "__main__":
    unittest.main()
