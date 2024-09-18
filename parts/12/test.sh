#! /bin/bash

echo " > Begin Screen test <"
cp Screen.jack ScreenTest
../../tools/JackCompiler.sh ScreenTest && echo "Load the ScreenTest directory in VMEmulator"
rm ScreenTest/Screen.jack
echo

echo " > Begin Memory test <"
cp Memory.jack MemoryTest
../../tools/JackCompiler.sh MemoryTest && echo "Load the MemoryTest directory in VMEmulator"
cp ../../tools/OS/*vm MemoryTest/MemoryDiag/
cp MemoryTest/Memory.vm MemoryTest/MemoryDiag/
../../tools/JackCompiler.sh MemoryTest/MemoryDiag
echo "Running memory diagnostics.."
../../tools/VMEmulator.sh MemoryTest/MemoryDiag/MemoryDiag.tst
rm MemoryTest/Memory.jack MemoryTest/*vm
rm MemoryTest/MemoryDiag/*vm MemoryTest/MemoryDiag/MemoryDiag.out
echo

echo " > Begin Math test <"
cp ../../tools/OS/*vm MathTest/
cp Math.jack MathTest
../../tools/JackCompiler.sh MathTest && echo "Running Math Tests.." &&  ../../tools/VMEmulator.sh MathTest/MathTest.tst
rm MathTest/Math.jack
rm MathTest/MathTest.out
rm MathTest/*vm
echo

echo " > Begin Array test <"
cp ../../tools/OS/*vm ArrayTest/
cp Array.jack ArrayTest
../../tools/JackCompiler.sh ArrayTest && echo "Running Array Tests.." && ../../tools/VMEmulator.sh ArrayTest/ArrayTest.tst
rm ArrayTest/Array.jack
rm ArrayTest/*vm
rm ArrayTest/ArrayTest.out
echo

echo " > Begin Sys test <"
cp ../../tools/OS/*vm SysTest/
cp Sys.jack SysTest
../../tools/JackCompiler.sh SysTest && echo "Load the SysTest directory in VMEmulator"
rm SysTest/Sys.jack
echo

echo " > Begin String test <"
cp ../../tools/OS/*vm StringTest/
cp String.jack StringTest
../../tools/JackCompiler.sh StringTest && echo "Load the StringTest directory in VMEmulator"
rm StringTest/String.jack
echo

echo " > Begin Keyboard test <"
cp ../../tools/OS/*vm KeyboardTest/
cp Keyboard.jack KeyboardTest
../../tools/JackCompiler.sh KeyboardTest && echo "Load the KeyboardTest directory in VMEmulator"
rm KeyboardTest/Keyboard.jack
echo

echo " > Begin Output test <"
cp ../../tools/OS/*vm OutputTest/
cp Output.jack OutputTest
../../tools/JackCompiler.sh OutputTest && echo "Load the OutputTest directory in VMEmulator"
rm OutputTest/Output.jack
echo
