from lark import Lark

#probleme avec le void devant le main
g = Lark("""
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
OPBIN: /[+\\-*\\/>]/
NUMBER: /[1-9][0-9]*/ |"0"
STRING: /"[^"]*"/
TYPE: "long" | "int" | "char" | "void" | "short" | "string" | "double"
DOUBLE : /[0-9]+\.[0-9]*([eE][+-]?[0-9]+)?/ | /[0-9]+[eE][+-]?[0-9]+/
CAST : "double" | "int"
liste_var: ->vide
         |declaration ("," declaration)* ->vars
declaration: TYPE IDENTIFIER ("=" expression)? ->declaration
expression: IDENTIFIER ->var
         | expression OPBIN expression ->opbin
         | DOUBLE -> double
         | NUMBER ->number
         | STRING ->string
         | "len(" expression ")" -> len
         | expression "[" expression "]" -> index
command: command ";" (command)* ->sequence
         |"while" "(" expression ")" "{" command "}" ->while
         |IDENTIFIER "=" expression ->affectation
         |declaration    -> declar
         |IDENTIFIER "=" "("CAST")" expression -> casting
         |"if" "(" expression ")" "{" command "}" ("else" "{" command "}")? ->ite
         |"printf" "(" expression ")" ->print
         |"skip" ->skip
program: TYPE "main" "(" liste_var ")" "{" command* "return" "(" expression");" "}" ->main
%import  common.WS
%ignore WS
""", start='program')

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
    elif c.data == "decl":
        type = c.children[0].children[0]
        var = c.children[0].children[1]
        if len(c.children) >1:
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
types_len = {
        "char" : "db",
        "short" : "dw",
        "int" : "dd",
        "long" : "dq",
        "double" : "dq"
    }

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
            raise ValueError(f"Variable {var_name} utilisée mais pas initialisée")
    if e.data == "opbin":
        type1 = get_type_expression(e.children[0])
        type2 = get_type_expression(e.children[2])

        if type1 == type2:
            return type1

        # Si le cast int → double est possible (même si c'est une constante ou une var)
        if type1 == "double" and type2 == "int":
            return "cast"

        raise ValueError(f"Types incompatibles pour opération binaire : {type1} et {type2}")

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

        type_exp = get_type_expression(e)

        if(type_exp == "cast"):
            if(e_left.data == "var"):
                if e_right.data == "var":
                    return f"""{asm_left}
sub rsp, 8
movsd [rsp], xmm0
mov eax, [{e_right.children[0].value}]
cvtsi2sd xmm0, eax
movsd xmm1, xmm0
movsd xmm0, [rsp]
add rsp, 8
{op2asm_double[e_op.value]}
"""
                else:
                    int_val = e_right.children[0].value
                    return f"""{asm_left}
sub rsp, 8
movsd [rsp], xmm0
mov eax, {int_val}
cvtsi2sd xmm0, eax
movsd xmm1, xmm0
movsd xmm0, [rsp]
add rsp, 8
{op2asm_double[e_op.value]}
"""
            else:
            # Sinon cas plus compliqué : c'est une expression, on fait un asm spécifique
            # Par exemple on génère asm_right en rax, puis conversion

                asm_right_int = asm_expression(e_right)  # une fonction spécifique à faire
                return f"""{asm_left}
sub rsp, 8
movsd [rsp], xmm0
{asm_right_int}
cvtsi2sd xmm0, rax
movsd xmm1, xmm0
movsd xmm0, [rsp]
add rsp, 8
{op2asm_double[e_op.value]}
"""

            

        if(type_exp == "double"):
                        return f"""{asm_left}
sub rsp, 8
movsd [rsp], xmm0\n
{asm_right}
movsd xmm1, xmm0
movsd xmm0, [rsp]
add rsp, 8
{op2asm_double[e_op.value]}"""

        elif(type_exp == "int"):
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
        if type.value == "void":
            raise Exception("c'est pas un vrai type void")

        code = ""
        if len(decla.children) >2:
            exp = decla.children[2]
            if(get_type_expression(exp)!=type):
                raise ValueError("Les deux éléments ne sont pas du même type")
            code_init = asm_expression(exp)
            if type.value == "double":
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
        if (type_var != type_exp and type_exp!='cast'):
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
        
        code_exp = asm_expression(exp)
        code_body = asm_commande(body)

        # On teste le type de retour de l'expression
        if get_type_expression(exp) == "double":
            return f"""loop{idx}:
{code_exp}
xorpd xmm1, xmm1
ucomisd xmm0, xmm1
jbe end{idx}
{code_body}
jmp loop{idx}
end{idx}: nop"""
        else:  # int (par défaut)
            return f"""loop{idx}:
{code_exp}
cmp rax, 0
jz end{idx}
{code_body}
jmp loop{idx}
end{idx}: nop"""
    
    elif c.data == "sequence":
        head = c.children[0]
        if len(c.children)>1:
            tail = c.children[1]
            return f"{asm_commande(head)}\n{asm_commande(tail)}"
        return f"{asm_commande(head)}\n"
    return ""

def asm_decl_var():
    decl_var = ""
    for var,type in variables.items():
        decl_var += f"{var} : {types_len[type]} 0\n"
    return decl_var

def asm_programme(p):
    with open("moule.asm") as f:
        prog_asm = f.read()
    
    init_vars = ""
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

    prog_asm = prog_asm.replace("COMMANDE", asm_commande(p.children[2])) 

    prog_asm = prog_asm.replace("INIT_VARS", init_vars)

    decl_vars = asm_decl_var()
    prog_asm = prog_asm.replace("DECL_VARS", decl_vars)
    

    for val, label in float_literals.items():
        float_data += f"{label}: dq {val}\n"
    prog_asm = prog_asm.replace("FLOAT_CONSTS", float_data)

    ret = asm_expression(p.children[3])
    prog_asm = prog_asm.replace("RETOUR", ret)
        
    return prog_asm

if __name__ == "__main__":
    with open("sample.c") as f:
        src = f.read()
        ast = g.parse(src)
        res = asm_programme(ast)
    with open("sample.asm", "w") as result:
        result.write(res)