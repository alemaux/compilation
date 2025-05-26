from lark import Lark

#probleme avec le void devant le main
g = Lark("""
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
OPBIN: /[+\\-*\\/>]/
NUMBER: /[1-9][0-9]*/ |"0"
TYPE: "long" | "int" | "char" | "void" | "short" | "double"
DOUBLE : /[0-9]+\.[0-9]*([eE][+-]?[0-9]+)?/ | /[0-9]+[eE][+-]?[0-9]+/
CAST : "double" | "int"
liste_var: ->vide
         |declaration ("," declaration)* ->vars
declaration: TYPE IDENTIFIER ("=" expression)? ->declaration
expression: IDENTIFIER ->var
         | expression OPBIN expression ->opbin
         | DOUBLE -> double
         | NUMBER ->number
command: command ";" (command)* ->sequence
         |"while" "(" expression ")" "{" command "}" ->while
         |IDENTIFIER "=" expression ->affectation
         |declaration    -> declar
         |IDENTIFIER "=" "("CAST")" expression -> casting
         |"if" "(" expression ")" "{" command "}" ("else" "{" command "}")? ->ite
         |"printf" "(" expression ")" ->print
         |"skip" ->skip
program: TYPE "main" "(" liste_var ")" "{" command "return" "(" expression");" "}" ->main
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
        if len(c.children)>1:
            tail = c.children[1]
            return f"{pp_commande(head)} ; {pp_commande(tail)}"
        return f"{pp_commande(head)}"

def get_vars_expression(e):
    pass

def get_vars_commande(c):
    pass

op2asm_int = {'+': "add rax, rbx", "-": "sub rax, rbx"}
op2asm_double = {'+' : "addsd xmm0, xmm1", "-": "subsd xmm0, xmm1"} #pour le moment juste les sommes et soustraction mais faire le reste
cpt = iter(range(1000000))
variables = {}
float_literals = {}

def get_type_expression(e):
    if e.data == "number":
        return "int"
    if e.data == "double":
        return "double"
    if e.data == "var":
        var_name = e.children[0].value
        if var_name in variables:
            return variables[var_name]
        else:
            raise ValueError("Variable {var_name} utilisée mais pas initialisée")
    if e.data == "opbin":
        type1 = get_type_expression(e.children[0])
        type2 = get_type_expression(e.children[2])
        if(type1==type2):
            if type1 == "double":
                return "double"
            else:
                return "int" 
    else:
        raise ValueError(f"Expression inattendue pour type : {e}")

def get_label(val):
    if val not in float_literals:
        label = f"float_{str(val).replace('.', '_').replace('-', 'm')}"
        float_literals[val] = label
    return float_literals[val]

def asm_expression(e):
    if e.data == 'var' : 
        if variables[e.children[0].value] == "double":
            return f"movsd xmm0, [{e.children[0].value}]"
        else :
            return f"mov rax, [{e.children[0].value}]"
            
    if e.data == 'number' : return f"mov rax, {e.children[0].value}"
    if e.data == 'double' :
        val = e.children[0].value
        label = get_label(val)
        return f"movsd xmm0, [{label}]"

    if e.data == "opbin":
        e_left = e.children[0]
        e_op = e.children[1]
        e_right = e.children[2]
        asm_left = asm_expression(e_left)
        asm_right = asm_expression(e_right)

        type_left = get_type_expression(e_left)
        type_right = get_type_expression(e_right)
        
        if(type_left != type_right):
            raise ValueError("Les deux éléments ne sont pas du même type")
        elif(type_left == "double"):
                        return f"""{asm_left}
sub rsp, 8
movsd [rsp], xmm0
{asm_right}
movsd xmm1, xmm0
movsd xmm0, [rsp]
add rsp, 8
{op2asm_double[e_op.value]}"""

        elif(type_left == "int"):
                        return f"""{asm_left}
push rax
{asm_right}
mov rbx, rax
pop rax
{op2asm_int[e_op.value]}"""

        
def asm_commande(c):
    if c.data == "declar":
        decla = c.children[0]
        type = decla.children[0]
        var = decla.children[1]
        variables[var.value] = f"{type.value}"
        print(variables)

        code = ""
        if len(decla.children) >2:
            exp = decla.children[2]
            code_init = asm_expression(exp)
            if var == "double":
                code += f"{code_init}\nmovsd [{var}], xmm0\n"
            else:
                code += f"{code_init}\nmov [{var}], rax\n"
        return code or "nop"
        
    if c.data == "affectation":
        var = c.children[0]
        exp = c.children[1]
        asm_exp = asm_expression(exp)
        type_var = variables[var.value]
        type_exp = get_type_expression(exp)
        if type_var != type_exp:
            raise ValueError("Affectation avec deux types différents")
        elif type_var == "double":
            return f"""{asm_exp}
movsd [{var.value}], xmm0 \n"""
        
        elif type_var == "int":
            return f"""{asm_exp}
mov [{var.value}], rax\n"""
        
    elif c.data == "skip": return "nop\n"

    elif c.data == "print":  
        asm_exp = asm_expression(c.children[0])
        typ = get_type_expression(c.children[0])
        if typ == "double":
            fmt = "fmt_double"
            rax_init = "mov rax, 1"
        else:
            fmt = "fmt_int"
            rax_init = "xor rax, rax"
        return f"""{asm_exp}
mov rdi, {fmt}
{rax_init}
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
        if len(c.children)>1:
            tail = c.children[1]
            return f"{asm_commande(head)}\n{asm_commande(tail)}"
        return f"{asm_commande(head)}\n"
    return ""

def asm_programme(p):
    with open("moule.asm") as f:
        prog_asm = f.read()
    
    init_vars = ""
    decl_vars = ""
    float_data = ""
    for i, c in enumerate(p.children[1].children):
        if c.data == "declaration":
            type = c.children[0].value
            name = c.children[1].value
            variables[name] = f"{type}"
            index = list(p.children[1].children).index(c)

            if type == "double":
                init_vars += f"""mov rbx, [argv]
mov rdi, [rbx + {(i+1)*8}]
call atof
movsd [{name}], xmm0\n"""
                
            else:
                init_vars += f"""mov rbx, [argv] 
mov rdi, [rbx + {(i+1)*8}]
call atoi
mov [{name}], rax\n"""
                
        decl_vars += f"{c.children[1].value}: dq 0 \n"
    prog_asm = prog_asm.replace("INIT_VARS", init_vars)
    prog_asm = prog_asm.replace("DECL_VARS", decl_vars)
    prog_asm = prog_asm.replace("COMMANDE", asm_commande(p.children[2]))
    ret = asm_expression(p.children[3])

    for val, label in float_literals.items():
        float_data += f"{label}: dq {val}\n"
    prog_asm = prog_asm.replace("FLOAT_CONSTS", float_data)

    prog_asm = prog_asm.replace("RETOUR", ret)
        
    return prog_asm

if __name__ == "__main__":
    with open("sample.c") as f:
        src = f.read()
        ast = g.parse(src)
        res = asm_programme(ast)
        print(res)
    with open("sample.asm", "w") as result:
        result.write(res)