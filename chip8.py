import argparse
import random
import pygame
import sys


class Chip8:
    def __init__(self):
        self.mem = [0] * 4096
        
        self.V = [0] * 16
        self.I = 0
        self.pc = 0x200

        self.gfx = [0] * (64 * 32)

        self.delay_timer = 0
        self.sound_timer = 0
        self.delay_frame = 0

        self.keys = [0] * 16

        self.stack = []

        fontset = [ 0xF0, 0x90, 0x90, 0x90, 0xF0, #0
                    0x20, 0x60, 0x20, 0x20, 0x70, #1
                    0xF0, 0x10, 0xF0, 0x80, 0xF0, #2
                    0xF0, 0x10, 0xF0, 0x10, 0xF0, #3
                    0x90, 0x90, 0xF0, 0x10, 0x10, #4
                    0xF0, 0x80, 0xF0, 0x10, 0xF0, #5
                    0xF0, 0x80, 0xF0, 0x90, 0xF0, #6
                    0xF0, 0x10, 0x20, 0x40, 0x40, #7
                    0xF0, 0x90, 0xF0, 0x90, 0xF0, #8
                    0xF0, 0x90, 0xF0, 0x10, 0xF0, #9
                    0xF0, 0x90, 0xF0, 0x90, 0x90, #A
                    0xE0, 0x90, 0xE0, 0x90, 0xE0, #B
                    0xF0, 0x80, 0x80, 0x80, 0xF0, #C
                    0xE0, 0x90, 0x90, 0x90, 0xE0, #D
                    0xF0, 0x80, 0xF0, 0x80, 0xF0, #E
                    0xF0, 0x80, 0xF0, 0x80, 0x80] #F
        
        for i, byte in enumerate(fontset):
            self.mem[i] = byte

    def load_rom(self, file):
        with open(file, "rb") as f:
            rom = f.read()
        for i, byte in enumerate(rom):
            self.mem[0x200 + i] = byte
    
    def emulate_cycle(self):
        opcode = (self.mem[self.pc] << 8) | self.mem[self.pc + 1]

        self.execute_command(opcode)

        if pygame.time.get_ticks() > self.delay_frame + (1000 / 60):
            self.update_timers()
            self.delay_frame += 1000 / 60

    def update_timers(self):
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1
    
    def execute_command(self, opcode):
        self.pc += 2
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        n = opcode & 0x000F
        nn = opcode & 0x00FF
        nnn = opcode & 0x0FFF

        if opcode == 0x00E0: #00E0 - cls
            self.gfx = [0] * (64 * 32)
        elif opcode == 0x00EE: #00EE - pc = stack
            self.pc = self.stack.pop()
        elif opcode & 0xF000 == 0x1000: #1NNN - goto NNN
            self.pc = nnn
        elif opcode & 0xF000 == 0x2000: #2NNN - goto subroutine NNN
            self.stack.append(self.pc)
            self.pc = nnn
        elif opcode & 0xF000 == 0xB000: #BNNN - goto v0 + NNN
            self.pc = self.V[0] + nnn
        elif opcode & 0xF000 == 0x3000: #3XNN - skip next if VX == NN
            if self.V[x] == nn:
                self.pc += 2
        elif opcode & 0xF000 == 0x4000: #4XNN - skip next if VX != NN
            if self.V[x] != nn:
                self.pc += 2
        elif opcode & 0xF000 == 0x5000: #5XY0 - skip next if VX == VY
            if self.V[x] == self.V[y]:
                self.pc += 2
        elif opcode & 0xF000 == 0x9000: #9XY0 - skip next if VX != VY
            if self.V[x] != self.V[y]:
                self.pc += 2
        elif opcode & 0xF000 == 0x6000: #6XNN - VX = NN
            self.V[x] = nn
        elif opcode & 0xF000 == 0x8000: #8XY0 - VX = VY
            self.V[x] = self.V[y]
        elif opcode & 0xF000 == 0xA000: #ANNN - I = NNN
            self.I = nnn
        elif opcode & 0xF000 == 0x7000: #7XNN - VX += NN
            self.V[x] = (self.V[x] + nn) & 0xFF
        elif opcode & 0xF000 == 0x8000:
            if n == 0x1:
                self.V[x] |= self.V[y]  #8XY1 - VX |= VY
            elif n == 0x2:
                self.V[x] &= self.V[y] #8XY2 - VX &= VY
            elif n == 0x3:
                self.V[x] ^= self.V[y] #8XY3 - VX ^= VY
            elif n == 0x4:
                sum = self.V[x] + self.V[y]  #8XY4 - VX += VY with carry
                self.V[x] = sum & 0xFF
                self.V[15] = 1 if sum > 0xFF else 0
            elif n == 0x5: 
                self.V[x] = (self.V[x] - self.V[y]) & 0xFF #8XY5 - VX -= VY with carry
                self.V[15] = 1 if self.V[x] >= self.V[y] else 0
            elif n == 0x6:
                self.V[15] = self.V[x] & 0x01
                self.V[x] >>= 1 #8XY6 - VX >>= 1
            elif n == 0x7: 
                self.V[15] = 1 if self.V[x] <= self.V[y] else 0
                self.V[x] = (self.V[y] - self.V[x]) & 0xFF #8XY7 - VX = VY - VX with carry
            elif n == 0xE:
                self.V[15] = self.V[x] >> 7
                self.V[x] <<= 1 #8XY6 - VX <<= 1
        elif opcode & 0xF000 == 0xC000: #CXNN - VX = rand(0, 255) & NN
            self.V[x] = random.randint(0, 0xFF) & nn
        elif opcode & 0xF000 == 0xD000: #DXYN - draw a n-byte sprite at VX,VY
            self.V[15] = 0
            for row in range(n):
                pixel = self.mem[self.I + row]
                for col in range(8):
                    if pixel & (0x80 >> col):
                        px = (self.V[x] + col) % 64
                        py = (self.V[y] + row) % 32
                        idx = px + (py * 64)
                        if self.gfx[idx] == 1:
                            self.V[15] = 1
                        self.gfx[idx] ^= 1
        elif opcode & 0xF0FF == 0xE09E: #FX9E - skip next if vx pressed
            if self.keys[self.V[x] & 0x7] == 1:
                self.pc += 2
        elif opcode & 0xF0FF == 0xE0A1: #FXA1 - skip next if vx not pressed
            if self.keys[self.V[x] & 0x7] == 0:
                self.pc += 2
        elif opcode & 0xF0FF == 0xF00A: #FX0A - wait for key
            key_pressed = False
            for i in range(16):
                if self.keys[i]:
                    self.V[x] = i
                    key_pressed = True
                    break
            if not key_pressed:
                self.pc -= 2
        elif opcode & 0xF0FF == 0xF007: #FX07 - VX = delay_timer
            self.V[x] = self.delay_timer
        elif opcode & 0xF0FF == 0xF015: #FX15 - delay_timer = VX
            self.delay_timer = self.V[x]
        elif opcode & 0xF0FF == 0xF018: #FX18 - sound_timer = VX
            self.sound_timer = self.V[x]
        elif opcode & 0xF0FF == 0xF01E: #FX1E - I += VX
            self.I = (self.I + self.V[x]) & 0xFFF
        elif opcode & 0xF0FF == 0xF029: #FX29 - I = X sprite address
            self.I = self.V[x] * 5
        elif opcode & 0xF0FF == 0xF033: #FX33 - BCD of VX in I, I+1, I+2
            self.mem[self.I] = self.V[x] // 100
            self.mem[self.I + 1] = self.V[x] % 100 // 10
            self.mem[self.I + 2] = self.V[x] % 10
        elif opcode & 0xF0FF == 0xF055: #FX55 - dump V0..Vx to memory starting from I
            for offset in range(x+1):
                self.mem[self.I + offset] = self.V[offset]
        elif opcode & 0xF0FF == 0xF065: #FX65 - load V0..Vx from memory starting from I
            for offset in range(x+1):
                 self.V[offset] = self.mem[self.I + offset]
        else:
            print(f"unknown instruction {hex(opcode)}")

    def draw_screen(self, surface):
        surface.fill((0, 0, 0))
        for y in range(32):
            for x in range(64):
                if self.gfx[x + y * 64]:
                    pygame.draw.rect(surface, (255, 255, 255), (x*args.scale, y*args.scale, args.scale, args.scale))
        pygame.display.flip()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CHIP-8 Emulator")
    parser.add_argument("rom", help="Path to ROM (e.g.: pong.ch8)")
    parser.add_argument("-c", "--clock_speed", type=int, default=1000, help="Clock speed of the emulator")
    parser.add_argument("-s", "--scale", type=int, default=10, help="Window size scale")
    args = parser.parse_args()

    pygame.init()
    win_width = 64 * args.scale
    win_height = 32 * args.scale
    screen = pygame.display.set_mode((win_width, win_height))
    pygame.display.set_caption("CHIP-8 Emulator")
    clock = pygame.time.Clock()

    chip8 = Chip8()
    chip8.load_rom(args.rom)

    keymap = {
        pygame.K_1: 0x1, pygame.K_2: 0x2, pygame.K_3: 0x3, pygame.K_4: 0xC,
        pygame.K_q: 0x4, pygame.K_w: 0x5, pygame.K_e: 0x6, pygame.K_r: 0xD,
        pygame.K_a: 0x7, pygame.K_s: 0x8, pygame.K_d: 0x9, pygame.K_f: 0xE,
        pygame.K_z: 0xA, pygame.K_x: 0x0, pygame.K_c: 0xB, pygame.K_v: 0xF
    }

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in keymap:
                    chip8.keys[keymap[event.key]] = 1
                if event.key == pygame.K_BACKSPACE:
                    chip8 = Chip8()
                    chip8.load_rom(args.rom)
                    chip8.delay_frame = pygame.time.get_ticks()
            elif event.type == pygame.KEYUP:
                if event.key in keymap:
                    chip8.keys[keymap[event.key]] = 0

        chip8.emulate_cycle()
        chip8.draw_screen(screen)
        clock.tick(args.clock_speed)
