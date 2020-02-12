import chip8
import sys
import argparse

# Process command line arguments
# -r argument specifies game file
# -f argument enables fullscreen
parser = argparse.ArgumentParser(description="Chip-8 Emulator")
parser.add_argument("-r", "--rom", type=str, metavar=" ", required=True, help="Name of Chip-8 Rom File")
parser.add_argument("-f", "--fullscreen", action='store_true', help="Enables Fullscreen")
args = parser.parse_args()

# Run the emulator
chip8 = chip8.Chip8(args.rom, args.fullscreen)
while True:
    chip8.run()
