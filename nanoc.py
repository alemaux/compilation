from lark import Lark

g = Lark("""
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
OPBIN: /[+\\-*\\/>]/
NUMBER: /[1-9][0-9]*/ |"0"
TYPE: "long"| "int"| "char"| "void"
liste_var: ->vide
         |declaration ("," declaration)* ->vars
declaration: TYPE IDENTIFIER ->decl
expression: IDENTIFIER ->var
         | expression OPBIN expression ->opbin  
         | NUMBER ->number
command: command ";" (command)* ->sequence
         |"while" "(" expression ")" "{" command "}" ->while
         |declaration "=" expression ->declaration
         |IDENTIFIER "=" expression ->affectation
         |"if" "(" expression ")" "{" command "}" ("else" "{" command "}")? ->ite
         |"printf" "(" expression ")" ->print
         |"skip" ->skip
struct:"typedef struct" "{" (declaration ";")* "}" IDENTIFIER -> struct
main: TYPE "main" "(" liste_var ")" "{" command "return" "(" expression")" "}" ->main
program: (struct)* main -> programme
%import  common.WS
%ignore WS
""", start='program')

def pp_expression(e):
    if e.data in ['var','number'] : return f"{e.children[0].value}"
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
        return f"{var.value} = {pp_expression(exp)}"
    elif c.data == "skip": return "skip"
    elif c.data == "print": return f"print({pp_expression(c.children[0])})"
    elif c.data == "while":
        exp = c.children[0]
        body = c.children[1]
        return f"while ({pp_expression(exp)}) {{{pp_commande(body)}}}"
    elif c.data == "sequence":
        head = c.children[0]
        tail = c.children[1]
        return f"{pp_commande(head)};\n{pp_commande(tail)}"

    return ""

def pp_list_var(lv):
    list_var = ""
    for v in lv:
        list_var += pp_declaration(v)
        list_var += ", "

    return list_var[: -2]

def pp_declaration(d):
    type = d.children[0]
    var = d.children[1]
    return f"{type.value} {var.value}"

def pp_main(p):
    type = p.children[0].value
    list_var = pp_list_var(p.children[1].children)
    commands = pp_commande(p.children[2])
    retour = pp_expression(p.children[3])
    corps = f"""{commands}
    return({retour})
    """
    return f"""{type} main({list_var}) {{
    {corps}}} """

def pp_struct(p):
    result = ""
    for i in range(len(p.children)-1):
        result += f"{pp_declaration(p.children[i])};\n"
    return f"typedef struct {{{result}}}{p.children[-1]}\n"

def pp_programme(p):
    result = ""
    if len(p.children) >= 2:
        for i in range(len(p.children) - 1):
            result += pp_struct(p.children[i])
    result += pp_main(p.children[-1])
    return result

op2asm = {'+': "add rax, rbx", "-": " sub rax, rbx"}
cpt = iter(range(1000000))


def asm_expression(e):
    if e.data == 'var' : return f"mov rax, [{e.children[0].value}]\n"
    if e.data == 'number' : return f"mov rax, {e.children[0].value}\n"
    if e.data != "parentheses":
        e_left = e.children[0]
        e_op = e.children[1]
        e_right = e.children[2]
        asm_left = asm_expression(e_left)
        asm_right = asm_expression(e_right)
        return f"""{asm_left}
push rax
{asm_right}
mov rbx, rax
pop rax
{op2asm[e_op.value]}\n"""

    
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

def asm_struct(p):
    struct_name = p.children[-1].value 
    size_map = {
        'char': 1,
        'int': 8,   # pour l'alignement mémoire
        'long': 8,
        'void': 0   # void n'a pas de taille ici
    }
    
    total_size_bytes = 0
    for field in p.children[:-1]:
        typename = field.children[0].value
        total_size_bytes += size_map[typename]

    size_qword = (total_size_bytes + 7) // 8
    return f"{struct_name}: resq {size_qword} ; taille {total_size_bytes} pour {struct_name}\n"


def asm_main(p):
    with open("moule.asm") as f:
        prog_asm = f.read()
    ret = asm_expression(p.children[3])
    prog_asm = prog_asm.replace("RETOUR", ret)
    init_vars = ""
    decl_vars = ""
    for i, c in enumerate(p.children[1].children):
        init_vars += f"""mov rbx, [argv]
        mov rdi, [rbx + {(i+1)*8}]
        call atoi
        mov [{c.children[1].value}], rax\n"""
        decl_vars += f"{c.children[1].value}: dq 0 \n"
    prog_asm = prog_asm.replace("INIT_VARS", init_vars)
    prog_asm = prog_asm.replace("DECL_VARS", decl_vars)
    prog_asm = prog_asm.replace("COMMANDE", asm_commande(p.children[2]))    
    return prog_asm

def asm_programme(p):
    struct_def = ""
    if len(p.children) >= 2:
        for i in range(len(p.children) - 1):
            struct_def += asm_struct(p.children[i])
    res = asm_main(p.children[-1])
    return res.replace("DECL_STRUCT", struct_def)
    



if __name__ == "__main__":
    with open("/home/mathus/compilation/compilo/compilation/sample.c") as f:
        src = f.read()
    ast = g.parse(src)
    print(ast)
    print(pp_programme(ast))
    print(asm_programme(ast))
    res = asm_programme(ast)
    with open("simple.asm", "w") as result:
        result.write(res)

    
    """res = asm_programme(ast)
    print(pp_programme(ast))
    with open("simple.asm", "w") as result:
        result.write(res)"""

    #print(ast.pretty('  '))
#print(ast.data)
#print(ast.children)
#print(ast.children[0])
#print(ast.children[0].type)
#print(ast.children[0].value)
