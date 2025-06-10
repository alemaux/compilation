#!/bin/bash

#compile le fichier .c passé en argument
#Pour utliser, juste besoin de faire "./comp_string.sh ./sample_string.c" par exemple


echo "COMPILATION - VERSION STRING"


echo "executing python on $1"
python3 nanoc_string.py $1
echo "nasm on sample.asm"
nasm -f elf64 sample.asm
echo "compilation on sample.o"
gcc -no-pie "sample.o"
rm sample.o

echo "DONE !"
