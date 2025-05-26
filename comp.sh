#!/bin/bash

#execute le python nanoc.py, compile le fichier passé en argument (simple.asm ou sample.asm) et en sort l'exécutable a.out
#dcp il faut passer en argument le nom du fichier dans lequel le python écrit

if [ -z "$1" ]; then
  echo "Veuillez fournir un fichier ASM en argument."
  exit 1
fi

filename="$1"

cd ~/work/Compilation

echo "executing python"
python3 nanoc.py
echo "nasm on $1"
nasm -f elf64 "$1"
echo "compilation on ${filename%.*}.o"
gcc -no-pie "${filename%.*}.o"
rm {filename%.*}.o
