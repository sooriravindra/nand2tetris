#! /bin/bash
cp Screen.jack ScreenTest
../tools/JackCompiler.sh ScreenTest
rm ScreenTest/Screen.jack
