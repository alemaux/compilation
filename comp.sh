#!/bin/bash

#compile le fichier .c passé en argument
#Pour utliser, juste besoin de faire "./comp.sh ./sample.c" par exemple
if [ -z "$1" ]; then
  echo "Veuillez fournir un fichier ASM en argument."
  exit 1
fi

filename="$1"

cd ~/Bureau/dep_info/S8/compilation_bonfante/compilation

echo "executing python on $1"
python3 nanoc.py $1
echo "nasm on sample.asm"
nasm -f elf64 sample.asm
echo "compilation on sample.o"
gcc -no-pie "sample.o"
rm sample.o
