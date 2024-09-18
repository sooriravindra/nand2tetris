// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Fill.asm

// Runs an infinite loop that listens to the keyboard input. 
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, 
// the screen should be cleared.

(MAINLOOP)
@KBD
D=M
@CLEAR
// If D which is the value read from keyboard is 0, jump to CLEAR
D;JEQ
// We want to set @color to 0xffff. Constants such as 65535, -1 didn't work.
// So we will use 0 and invert the bits.
@0
D=!A 
@color
M=D
@PAINT
0;JMP
(CLEAR)
@color
M=0
// PAINT is the part where we update the screen
(PAINT)
@SCREEN
D=A
// @point is a memory location which holds the value
// corresponding to the part of screen we are updating
@point
M=D
// LOOP is the part where we update all the pixels with value in @color
(LOOP)
@color
D=M
// We need to do the following: RAM[RAM[@point]] = @color
@point
A=M
M=D
// We will increment the RAM[@point] for the next iteration
@point
D=M+1
M=D
// Screen is 256x512 pixels, word size is 16 bit. 256*512/16=8192.
// This is the number of times we need to loop
@8192
D=D-A
@SCREEN
D=D-A
// Loop as long as (point - 8192 - SCREEN) < 0
@LOOP
D;JLT
// Loop till infinity and beyond
@MAINLOOP
0;JMP