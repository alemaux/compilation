extern printf, atoi
extern malloc
extern free

section .data
DECL_VARS
argv : dq 0
fmt_int: db "%d", 10, 0
fmt_string: db "%s", 10, 0

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
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf

pop rbp
ret