for directory in $(ls -d */); do
  echo "######################"
  echo "     ${directory}"
  echo "######################"
  ./compiler.py $directory 2>&1 && echo "Compilation success!"
  echo
done
