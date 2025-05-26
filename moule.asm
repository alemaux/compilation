extern printf, atoi, atof

section .data
DECL_VARS
FLOAT_CONSTS
argv : dq 0
fmt_int: db "%d", 10, 0
fmt_double: db "%lf", 10, 0

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