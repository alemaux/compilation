from lark import Lark
g = Lark("""
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
OPBIN: /[+\\-*\\/>]/
NUMBER: /[1-9][0-9]*/ |"0"
DOUBLE : /[0-9]+\.[0-9]*([eE][+-]?[0-9]+)?/ | /[0-9]+[eE][+-]?[0-9]+/
CAST : "double" | "int"
liste_var: ->vide
         |IDENTIFIER ("," IDENTIFIER)* ->vars
expression: IDENTIFIER ->var
         | expression OPBIN expression ->opbin
         | DOUBLE -> double
         | NUMBER ->number
command: command ";" (command)* ->sequence
         |"while" "(" expression ")" "{" command "}" ->while
         |IDENTIFIER "=" expression ->affectation
         |IDENTIFIER "=""("CAST")" expression -> casting
         |"if" "(" expression ")" "{" command "}" ("else" "{" command "}")? ->ite
         |"printf" "(" expression ")" ->print
         |"skip" ->skip
program: "main" "(" liste_var ")" "{" command "return" "(" expression")" "}" ->main
%import  common.WS
%ignore WS
""", start='program')

def pp_expression(e):
    if e.data in ['var','number','double'] : return f"{e.children[0].value}"
    if e.data == "parentheses": return f"({pp_expression(e.children[0])}) {e.children[1].value} {pp_expression(e.children[2])}"
    if e.data != "parentheses":
        e_left = e.children[0]
        e_op = e.children[1]
        e_right = e.children[2]
        return f"{pp_expression(e_left)} {e_op.value} {pp_expression(e_right)}"

def pp_commande(c):
    if c.data == "affectation":
        var = c.children[0]
        exp = c.children[1]
        return f"{var.value} = {pp_expression(exp)};"
    if c.data == "casting" :
        var = c.children[0]
        cast = c.children[1]
        exp = c.children[2]
        return f"{var.value} = ({cast.value}) {pp_expression(exp)}"
    elif c.data == "skip": return "skip"
    elif c.data == "print": return f"print({pp_expression(c.children[0])})"
    elif c.data == "while":
        exp = c.children[0]
        body = c.children[1]
        return f"while {pp_expression(exp)}\n  {{{pp_commande(body)}}}"
    elif c.data == "sequence":
        head = c.children[0]
        tail = c.children[1]
        return f"{pp_commande(head)} ; {pp_commande(tail)}"

def get_vars_expression(e):
    pass

def get_vars_commande(c):
    pass

op2asm_int = {'+': "add rax, rbx", "-": "sub rax, rbx"}
op2asm_double = {'+' : "addsd xmm0, xmm1", "-": "subsd xmm0, xmm1"} #pour le moment juste les sommes et soustraction mais faire le reste
cpt = iter(range(1000000))


def asm_expression(e):
    if e.data == 'var' : return f"mov rax, [{e.children[0].value}]"
    if e.data == 'number' : return f"mov rax, {e.children[0].value}"
    if e.data == 'double' : return f"movsd xmm0, {e.children[0].value}"
    if e.data == "opbin":
        e_left = e.children[0]
        e_op = e.children[1]
        e_right = e.children[2]
        asm_left = asm_expression(e_left)
        asm_right = asm_expression(e_right)

        if(e_left.data in  ['number', 'var'] and e_right.data in ['number', 'var']):
            return f"""{asm_left}
push rax
{asm_right}
mov rbx, rax
pop rax
{op2asm_int[e_op.value]}"""
        elif(e_left.data == 'double' or e_right.data == 'double'):
            return f"""{asm_left}
sub rsp, 8
movsd [rsp], xmm0
{asm_right}
movsd xmm1, xmm0
movsd xmm0, [rsp]
add rdp, 8
{op2asm_double[e_op.value]}"""


def asm_commande(c):
    if c.data == "affectation":
        var = c.children[0]
        exp = c.children[1]
        asm_exp = asm_expression(exp)
        return f"""{asm_exp}
mov [{var.value}], rax\n"""
    elif c.data == "skip": return "nop\n"
    elif c.data == "print": 
        asm_exp = asm_expression(c.children[0])
        return f"""{asm_exp}
mov rdi, rax
mov rsi, fmt
xor rax, rax
call printf
"""
    elif c.data == "while":
        exp = c.children[0]
        body = c.children[1]
        idx = next(cpt)
        return f"""loop{idx}: {asm_expression(exp)}
cmp rax, 0
jz end{idx}
{asm_commande(body)}
jmp loop{idx}
end{idx}: nop"""
    elif c.data == "sequence":
        head = c.children[0]
        tail = c.children[1]
        return f"{asm_commande(head)}\n{asm_commande(tail)}"
    return ""

def asm_programme(p):
    with open("moule.asm") as f:
        prog_asm = f.read()
    ret = asm_expression(p.children[2])
    prog_asm = prog_asm.replace("RETOUR", ret)
    init_vars = ""
    decl_vars = ""
    for i, c in enumerate(p.children[0].children):
        init_vars += f"""mov rbx, [argv]
mov rdi, [rbx + {(i+1)*8}]
call atoi
mov [{c.value}], rax\n"""
        decl_vars += f"{c.value}: dq 0 \n"
    prog_asm = prog_asm.replace("INIT_VARS", init_vars)
    prog_asm = prog_asm.replace("DECL_VARS", decl_vars)
    prog_asm = prog_asm.replace("COMMANDE", asm_commande(p.children[1]))    
    return prog_asm



if __name__ == "__main__":
    with open("sample.c") as f:
        src = f.read()
        ast = g.parse(src)
        res = asm_programme(ast)
        print(res)
    with open("sample.asm", "w") as result:
        result.write(res)