import cpu
import sys
import pygame as pg
import numpy  as np
from settings import *

class Chip8():

    def __init__(self, rom, fullscreen):
        """ Initialise the emulator """
        # General PyGame setup
        pg.init()
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()

        if fullscreen:
            self.screen = pg.display.set_mode((WIDTH * PIXEL_DIM, HEIGHT * PIXEL_DIM), pg.FULLSCREEN)
        else:
            self.screen = pg.display.set_mode((WIDTH * PIXEL_DIM, HEIGHT * PIXEL_DIM))

        # 2D numpy array containing (R, G, B) values for each pixel
        self.pixels = np.zeros((WIDTH, HEIGHT, 3))

        # Create the CPU, load the fontset and game rom
        self.cpu = cpu.Cpu()
        self.cpu.load_file_to_memory("fontset.bin", 0x050)
        self.cpu.load_file_to_memory("roms/" + rom, 0x200)

        # Keypad index translates PyGame key values to Chip-8 key values
        # Keys shown below as they appear on a standard keyboard
        self.keypad_index = {
            pg.K_1 : 1,  pg.K_2 : 2,  pg.K_3 : 3,  pg.K_4 : 12,
            pg.K_q : 4,  pg.K_w : 5,  pg.K_e : 6,  pg.K_r : 13,
            pg.K_a : 7,  pg.K_s : 8,  pg.K_d : 9,  pg.K_f : 14,
            pg.K_z : 10, pg.K_x : 0,  pg.K_c : 11, pg.K_v : 15
        }

    def run(self):
        """ Run the game. Begins the game loop """
        self.playing = True
        while self.playing:
            self.clock.tick(FPS)

            # Run the specified number of cycles within the current frame
            cycles_left = CYCLES_PER_FRAME
            while cycles_left > 0:
                self.events()
                self.cpu.execute_cycle()
                cycles_left -= 1

            # Only draw if the CPU sets the draw flag
            if self.cpu.draw_flag:
                self.cpu.draw_flag = False
                self.draw()

    def events(self):
        """ Listens for events bound to terminating the game or keypad inputs """
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.quit()
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self.quit()
            if event.type == pg.KEYDOWN and event.key in self.keypad_index:
                self.cpu.keypad[self.keypad_index[event.key]] = 1
            if event.type == pg.KEYUP and event.key in self.keypad_index:
                self.cpu.keypad[self.keypad_index[event.key]] = 0

    def draw(self):
        """ Draws the updated sprites to the screen """
        # Converts display (binary) to pixel values (R, G, B)
        for i in range(WIDTH):
            for j in range(HEIGHT):
                if self.cpu.display[i][j] == 1:
                    self.pixels[i][j] = WHITE
                else:
                    self.pixels[i][j] = BG_COLOUR

        # Clear the screen
        self.screen.fill(BG_COLOUR)

        # Draw the pixels to the screen
        next_frame = pg.Surface((WIDTH, HEIGHT))
        pg.surfarray.blit_array(next_frame, self.pixels)
        next_frame = pg.transform.scale(next_frame, (WIDTH * PIXEL_DIM, HEIGHT * PIXEL_DIM))
        self.screen.blit(next_frame, (0, 0))

        # Draws the image in the double buffer to the screen
        pg.display.flip()

    def quit(self):
        """ Terminates the program """
        pg.quit()
        sys.exit()
