from lark import Lark
g = Lark("""
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
OPBIN: /[+\\-*\\/>]/
NUMBER: /[1-9][0-9]*/ |"0"
STRING: /"[^"]*"/
TYPE: "long" | "int" | "char" | "void" | "short" | "string"
declaration: TYPE IDENTIFIER 
DOUBLE : /[0-9]+\\.[0-9]*([eE][+-]?[0-9]+)?/ | /[0-9]+[eE][+-]?[0-9]+/
CAST : "double" | "int"
liste_var: ->vide
         |declaration ("," declaration)* ->vars
expression: IDENTIFIER ->var
         | expression OPBIN expression ->opbin
         | DOUBLE -> double
         | NUMBER ->number
         | STRING ->string
         | "len(" expression ")" -> len
         | expression "[" expression "]" -> index
command: command ";" (command)* ->sequence
         |"while" "(" expression ")" "{" command "}" ->while
         |declaration ("=" expression)? ->decl
         |IDENTIFIER "=" expression ->affectation
         |IDENTIFIER "=""("CAST")" expression -> casting
         |"if" "(" expression ")" "{" command "}" ("else" "{" command "}")? ->ite
         |"printf" "(" expression ")" ->print
         |"skip" ->skip
program: TYPE "main" "(" liste_var ")" "{" command "return" "(" expression")" "}" ->main
%import  common.WS
%ignore WS
""", start='program')

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
    return f""";operation
{asm_left}
push rax
{asm_right}
mov rbx, rax
pop rax
{op2asm[e_op.value]}"""

cpt = iter(range(1000000))

variables = {}
op2asm = {'+' : "add rax, rbx", '-' : "sub rax, rbx"}

types_len = {
        "char" : "db",
        "short" : "dw",
        "int" : "dd",
        "long" : "dq"
    }

def pp_expression(e):
    if e.data in ['var','number','double', 'string'] : return f"{e.children[0].value}"
    if e.data == 'len' :
        child = e.children[0]
        if child.data in ['string', 'var']: #gérer les var qui ne sont pas des string pour ne pas les accepter
            return f"len ({pp_expression(child)})"
        else :
            raise Exception("pas le bon type")
    if e.data == 'index' : #Aloïs gérera que l'index soit attribué qu'à des int
        e_left = e.children[0]
        e_right = e.children[1]
        if e_left.data in ['string', 'var'] and e_right.data in ['number', 'var'] :
            return f"{pp_expression(e_left)}[{pp_expression(e_right)}]"
        else :
            raise Exception("pas le bon type")
    if e.data == 'opbin' :
        e_left = e.children[0]
        e_op = e.children[1]
        e_right = e.children[2]
        if e_left.data in ['var','number','double', 'string', 'opbin', 'len', 'index'] :
            return f"{pp_expression(e_left)} {e_op.value} {pp_expression(e_right)}"
        else :
            raise Exception("pas le bon type")
    if e.data == "parentheses": return f"({pp_expression(e.children[0])}) {e.children[1].value} {pp_expression(e.children[2])}"        
    

def pp_commande(c):
    if c.data == "decl" :
        type = c.children[0].children[0]
        var = c.children[0].children[1]
        if len(c.children) > 1:
            exp = c.children[1]
            return f"{type.value} {var.value} = {pp_expression(exp)}"
        return f"{type.value} {var.value}"
    elif c.data == "affectation":
        var = c.children[0]
        exp = c.children[1]
        return f"{var.value} = {pp_expression(exp)};"
    elif c.data == "casting" :
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

        return f"{pp_commande(head)};\n{pp_commande(tail)}"

    return ""

def pp_list_var(lv):
    list_var = ""
    for v in lv:
        list_var += v.children[0].value + " " + v.children[1].value
        list_var += ", "
    return list_var[:-2]


def get_vars_expression(e):
    pass


def pp_programme(p):
    list_var = pp_list_var(p.children[1].children)
    commands = pp_commande(p.children[2])
    retour = pp_expression(p.children[3])
    corps = f"""{commands}
    return({retour})"""
    return f"""{p.children[0].value} main({list_var}) {{
    {corps}
}} """

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
    if c.data == "declaration":
        type = c.children[0].children[0]
        var = c.children[0].children[1]
        variables[var.value] = type.value
        if len(c.children) >=2:
            exp = c.children[1]
            return f"{asm_expression(exp)}\nmov [{var.value}], rax"
    
    elif c.data == "affectation":
        var = c.children[0]
        exp = c.children[1]
        if var in variables.keys():
            return f"{asm_expression(exp)}\nmov [{var.value}], rax"
        else :
            raise Exception("Variable non déclarée")
        
    elif c.data =="skip": return "nop\n"

    elif c.data == "print": 
        return f"""[{asm_expression(c.children[0])}]
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

def asm_decl_var(lst):
    
    decl_var = ""
    for var,type in variables.items():
        decl_var += f"{var} : {types_len[type]} 0\n"
    return decl_var


def asm_programme(p):
    with open("moule.asm") as f:
        prog_asm = f.read()
    ret = asm_expression(p.children[3])
    prog_asm = prog_asm.replace("RETOUR", ret)
    init_vars = ""
    for i, c in enumerate(p.children[1].children):
        variables[c.children[1].value] = c.children[0].value
        init_vars += f"""mov rbx, [argv]

mov rdi, [rbx + {8 * (i+1)}]
call atoi
mov [{c.children[1].value}], rax
"""
    decl_var = asm_decl_var(p.children[1].children)
    prog_asm = prog_asm.replace("DECL_VARS", decl_var)

    prog_asm = prog_asm.replace("INIT_VARS", init_vars)
    prog_asm = prog_asm.replace("COMMANDE", asm_commande(p.children[2]))
    return prog_asm



if __name__ == "__main__":
    with open("sample.c") as f:
        src = f.read()
        ast = g.parse(src)
        res = asm_programme(ast)
        #print(res)
        print(pp_programme(ast))
    with open("sample.asm", "w") as result:
        result.write(res)
