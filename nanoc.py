from lark import Lark


g = Lark("""
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
OPBIN: /[+\\-*\\/>]/
NUMBER: /[1-9][0-9]*/ |"0"
TYPE: "long" | "int" | "char" | "void" | "short"
liste_var: ->vide
         |declaration ("," declaration)* ->vars
declaration: TYPE IDENTIFIER ->decl
expression: IDENTIFIER ->var
         | expression OPBIN expression ->opbin
         | NUMBER ->number
command: command ";" (command)* ->sequence
         |"while" "(" expression ")" "{" command "}" ->while
         |declaration ("=" expression)? ->declaration
         |IDENTIFIER "=" expression ->affectation
         |"if" "(" expression ")" "{" command "}" ("else" "{" command "}")? ->ite
         |"printf" "(" expression ")" ->print
         |"skip" ->skip
program: TYPE "main" "(" liste_var ")" "{" command "return" "(" expression")" "}" ->main
%import  common.WS
%ignore WS
""", start='program')

cpt = iter(range(1000000))

variables = {}


def pp_expression(e):
    if e.data in ("var", "number"):
        return f"{e.children[0].value}"
    e_left = e.children[0]
    e_op = e.children[1]
    e_right = e.children[2]
    return f"({pp_expression(e_left)} {e_op.value} {pp_expression(e_right)})"

def pp_command(c):
    if c.data == "affectation":
        var = c.children[0]
        exp = c.children[1]
        return f"{var.value} = {pp_expression(exp)}"
    elif c.data =="skip": return "skip"
    elif c.data == "print": return f"printf({pp_expression(c.children[0])})"
    elif c.data =="while":
        exp = c.children[0]
        body = c.children[1]
        return f"while({pp_expression(exp)}){{\n\t{pp_command(body)}\n}}"
    elif c.data == "ite":
            exp = c.children[0]
            i_body = c.children[1]
            if len(c.children) > 2:
                e_body = c.children[2]
                return f"if({pp_expression(exp)}){{\n{pp_command(i_body)}}} else {{{pp_command(e_body)}\n}}"
            return f"if({pp_expression(exp)}){{{pp_command(i_body)}}}"
    elif c.data == "sequence":
        if len(c.children) == 1:return f"{pp_command(c.children[0])};"
        lchild = c.children[0]
        rchild = c.children[1]
        return f"{pp_command(lchild)};{pp_command(rchild)}"

def pp_list_var(lv):
    list_var = ""
    for v in lv:
        list_var += v.children[0].value + " " + v.children[1].value
        list_var += ", "

    return list_var[: -2]

def pp_programme(p):
    list_var = pp_list_var(p.children[1].children)
    commands = pp_command(p.children[2])
    retour = pp_expression(p.children[3])
    corps = f"""{commands}
    return({retour})"""
    return f"""{p.children[0].value} main({list_var}) {{
    {corps}
}} """

def asm_expression(e):
    if e.data == "number":
        return f"mov rax, {e.children[0].value}\n"
    elif e.data == "var":
        return f"mov rax, [{e.children[0].value}]\n"
    e_left = e.children[0]
    e_op = e.children[1]
    e_right = e.children[2]
    asm_left = asm_expression(e_left)
    asm_right = asm_expression(e_right)
    op2asm = {'+' : "add rax, rbx", '-' : "sub rax, rbx"}
    return f"""{asm_right}
push rax
{asm_left}
mov rbx, rax
pop rax
{op2asm[e_op.value]}"""

def asm_command(c):
    if c.data == "declaration":
        type = c.children[0].children[0]
        var = c.children[0].children[0]
        variables[var.value] = type.value
        if len(c.children >=1):
            exp = c.children[1]
            return f"{asm_expression(exp)}\nmov [{var.value}], rax"
    elif c.data == "affectation":
        var = c.children[0]
        exp = c.children[1]
        if var in variables.keys():
            return f"{asm_expression(exp)}\nmov [{var.value}], rax"
        else :
            raise Exception("Variable non déclarée")
    elif c.data =="skip": return "nop"

    elif c.data == "print": return f"""[{asm_expression(exp)}]
mov rdi, rax
mov rsi, fmt
xor rax, rax
call printf"""
    
    elif c.data =="while":
        exp = c.children[0]
        body = c.children[1]
        idx = next(cpt)
        return f"""loop{idx}:{asm_expression(exp)}
cmp rax, 0
jz end{idx}
{asm_command(body)}
jmp loop{idx}
end{idx}: nop"""
    
    elif c.data == "ite":
        exp = c.children[0]
        i_body = c.children[1]
        idx = next(cpt)
        if len(c.children) > 2:
            e_body = c.children[2]
            return f"""{asm_expression(exp)}
cmp rax, 0
jz at{idx}
{asm_command(i_body)}
jmp end{idx}
at{idx}:{asm_command(e_body)}
end{idx}:nop"""

        return f"""{asm_expression(exp)}
cmp rax, 0
jz end{idx}
{asm_command(i_body)}
end{idx}:nop"""

    elif c.data == "sequence":
        if len(c.children) == 1:return f"{asm_command(c.children[0])};"
        lchild = c.children[0]
        rchild = c.children[1]
        return f"{asm_command(lchild)}\n{asm_command(rchild)}"

def asm_decl_var(lst):
    types_len = {
        "char" : "db",
        "short" : "dw",
        "int" : "dd",
        "long" : "dq"
    }
    decl_var = ""
    for var,type in variables.items():
        decl_var += f"{var} : {types_len[type]} 0\n"
    return decl_var


def asm_prg(p):
    with open("moule.asm") as f:
        prog_asm = f.read()
    ret = asm_expression(p.children[3])
    prog_asm = prog_asm.replace("RETOUR", ret)
    init_vars = ""
    for i, c in enumerate(p.children[1].children):
        variables[c.children[1].value] = c.children[0].value
        init_vars += f"""mov rbx, [argv]
mov rdi, [rbx + {8 * (i+1)}]
xor rax, rax
call atoi
mov [{c.children[1].value}], rax
"""
    decl_var = asm_decl_var(p.children[1].children)
    prog_asm = prog_asm.replace("DECL_VARS", decl_var)
    prog_asm = prog_asm.replace("INIT_VARS", init_vars)
    prog_asm = prog_asm.replace("COMMANDE", asm_command(p.children[2]))
    return prog_asm



if __name__ == '__main__':
    with open("sample.c", "r") as f:
        src  = f.read()
    ast = g.parse(src)
    variables = {}
    #print(pp_programme(ast))
    print(asm_prg(ast))