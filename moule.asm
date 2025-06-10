extern printf, atoi, atof
extern malloc
extern free

section .data
DECL_VARS
FLOAT_CONSTS
argv : dq 0
fmt_int: db "%d", 10, 0
fmt_double: db "%lf", 10, 0

section .bss
DECL_STRUCT

global main
section .text

main:
push rbp
mov [argv], rsi

INIT_VARS
COMMANDE
RETOUR

pop rbp
ret