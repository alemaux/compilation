import sys
from lark import Lark, Tree

g = Lark("""
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
OPBIN: /[+\\-*\\/>]/
NUMBER: /[1-9][0-9]*/ |"0"
STRING: /"[^"]*"/
TYPE: "long" | "int" | "char" | "void" | "short" | "string" | "double"
declaration: (TYPE | struct_type) IDENTIFIER 
DOUBLE : /[0-9]+\\.[0-9]*([eE][+-]?[0-9]+)?/ | /[0-9]+[eE][+-]?[0-9]+/
CAST : "double" | "int"
struct_type: IDENTIFIER
field_access: IDENTIFIER "." IDENTIFIER ("." IDENTIFIER)*
liste_var: ->vide
         |declaration ("," declaration)* ->vars
expression: IDENTIFIER ->var
         | expression OPBIN expression -> opbin
         | DOUBLE -> double
         | NUMBER ->number
         | STRING ->string
         | "len(" expression ")" -> len
         | expression "[" expression "]" -> index
         | field_access ->field_access
command: (command ";")+ ->sequence
         |"while" "(" expression ")" "{" command "}" -> while
         |declaration ("=" expression)? -> declaration
         |IDENTIFIER "=" expression -> affectation
         |declaration "=" "new" struct_type "("expression ("," expression)* ")" -> malloc
         |IDENTIFIER "=""("CAST")" expression -> casting
         |field_access "=" expression -> set_value
         |"if" "(" expression ")" "{" command "}" ("else" "{" command "}")? -> ite
         |"printf" "(" expression ")" -> print
         |"skip" ->skip
struct_field : (TYPE IDENTIFIER ";") -> base_type
         |IDENTIFIER IDENTIFIER ";" -> struct_type
struct:"typedef struct" "{" struct_field+ "}" IDENTIFIER ";"-> struct
main: TYPE "main" "(" liste_var ")" "{" command "return" "(" expression")" "}" -> main
program: (struct)* main -> programme
%import  common.WS
%ignore WS
""", start='program')

cpt = iter(range(1000000))

types = ["long", "int", "char", "void", "short"]

variables = {}
struct = {} #structures qui sont déclarées (pas possible d'instancier un point pax exemple si la structure n'a pas été définie)
#contient les structures sous la forme struct[nom] = [(type1, champ1), ...]
#pour les variables qui sont déclarées mais non initialisées (ex : Point P;)
struct_bss = {}
allocated_vars = {}#pour les var avec malloc

op2asm = {'+' : "add rax, rbx", '-' : "sub rax, rbx"}

size_map = {
    'char': 1,
    'int': 8,  
    'long': 8,
    'void': 0,
    'float': 8 ,
    'double': 8   
}

types_len = {
        "char" : "db",
        "short" : "dw",
        "int" : "dd",
        "long" : "dq"
    }

asm_decl_struct = ""

def parse_struct_def(tree):
    struct_name = tree.children[-1].value
    fields = []
    size = 0
    for i in range(len(tree.children) - 1):#on exclut le nom de la struct
        fields.append((tree.children[i].children[0].value, tree.children[i].children[1].value))
        size += size_map[tree.children[i].children[0].value]
    struct[struct_name] = fields
    size_map[struct_name] = size


def get_type_expression(e):
    if e.data == "number":
        return "int" #Entier par défaut : int
    if e.data == "double":
        return "double" #Float par défaut : double
    if e.data == "var":
        var_name = e.children[0].value
        if var_name in variables:
            return variables[var_name] #Si la variable est déclarée
        else:
            raise ValueError(f"Variable {var_name} utilisée mais pas initialisée")
    if e.data == "opbin":
        type1 = get_type_expression(e.children[0])
        type2 = get_type_expression(e.children[2])
        if(type1==type2):
            return type1
    if e.data == "field_access":
        objet = e.children[0].children[0].value
        type_objet = struct_bss[objet]
        champ = e.children[0].children[1].value
        for elem in struct[type_objet]:
            if elem[1] == champ:
                return elem[0] 
        raise ValueError(f"Expression inattendue pour type : {e}")
    else:
        raise ValueError(f"Expression inattendue pour type : {e}")


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
    if e.data == "field_access":
        objet = e.children[0].children[0].value
        field = e.children[0].children[1].value
        return f"{objet}.{field}"
    if e.data == 'opbin' :
        e_left = e.children[0]
        e_op = e.children[1]
        e_right = e.children[2]
        if e_left.data in ['var','number','double', 'string', 'opbin', 'len', 'index', "field_access"] :
            return f"{pp_expression(e_left)} {e_op.value} {pp_expression(e_right)}"
        else :
            raise Exception("pas le bon type")
    if e.data == "parentheses": return f"({pp_expression(e.children[0])}) {e.children[1].value} {pp_expression(e.children[2])}"        
    

def pp_commande(c):
    if c.data == "decl":
        type = c.children[0].children[0]
        var = c.children[0].children[1]
        if len(c.children) > 1:
            exp = c.children[1]
            return f"{type.value} {var.value} = {pp_expression(exp)};"
        return f"{type.value} {var.value};"
    elif c.data == "declaration":
        if isinstance(c.children[0].children[0], Tree) :
            type = c.children[0].children[0].children[0]
            var = c.children[0].children[1]
            if len(c.children) >1:
                exp = c.children[1]
                return f"{type.value} {var.value} = {pp_expression(exp)};"
            return f"{type.value} {var.value};"
        else :
            type = c.children[0].children[0]
            var = c.children[0].children[1]
            if len(c.children) >1:
                exp = c.children[1]
                return f"{type.value} {var.value} = {pp_expression(exp)};"
            return f"{type.value} {var.value};"

    elif c.data == "affectation":
        var = c.children[0]
        exp = c.children[1]
        return f"{var.value} = {pp_expression(exp)};"
    elif c.data == "casting" :
        var = c.children[0]
        cast = c.children[1]
        exp = c.children[2]
        return f"{var.value} = ({cast.value}) {pp_expression(exp)};"
    elif c.data == "skip": return "skip"
    elif c.data == "print": return f"print({pp_expression(c.children[0])});"
    elif c.data == "while":
        exp = c.children[0]
        body = c.children[1]
        return f"while ({pp_expression(exp)})\n  {{{pp_commande(body)}}};"
    elif c.data == "sequence":
        result = ""
        for command in c.children:
            result += f"    {pp_commande(command)}\n"
        return result
    elif c.data == "set_value":
        left = c.children[0]
        objet = left.children[0]
        champ = left.children[1]
        value = c.children[1]
        return f"{objet.value}.{champ.value} = {pp_expression(value)};"


    return ""

def pp_list_var(lv):
    list_var = ""
    for v in lv:
        list_var += pp_declaration(v)
        list_var += ", "
    return list_var[:-2]


def get_vars_expression(e):
    pass 



def pp_declaration(d):
    type = d.children[0]
    var = d.children[1]
    return f"{type.value} {var.value}"

def pp_main(p):
    type = p.children[0].value
    list_var = pp_list_var(p.children[1].children)
    commands = pp_commande(p.children[2])
    retour = pp_expression(p.children[3])
    corps = f"""{commands}    return({retour})
    """
    return f"""{type} main({list_var}) {{
{corps}}} """

def pp_struct(p):
    result = ""
    for i in range(len(p.children)-1):
        result += f"{pp_declaration(p.children[i])};\n"
    return f"typedef struct {{{result}}}{p.children[-1]};\n\n"

def pp_programme(p):
    result = ""
    if len(p.children) >= 2:
        for i in range(len(p.children) - 1):
            result += pp_struct(p.children[i])
    result += pp_main(p.children[-1])
    return result
    

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
    if e.data == "field_access":
        #le type est celui du champ de la struct
        objet = e.children[0].children[0].value
        field = e.children[0].children[1].value
        struct_name = struct_bss[objet]
        for values in struct[struct_name]:
            if values[1] == field:
                return values[0]


    raise ValueError(f"Expression inattendue pour type : {e}")

def get_label(val):
    if val not in float_literals:
        label = f"float_{str(val).replace('.', '_').replace('-', 'm')}"
        float_literals[val] = label
    return float_literals[val]

def asm_expression(e):
    if e.data == 'var': 
        if e.children[0].value in variables and variables[e.children[0].value] == "double":
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
        elif(e_left.data == 'double' or e_right.data == 'double'):
            return f"""{asm_left}
sub rsp, 8
movsd [rsp], xmm0
{asm_right}
movsd xmm1, xmm0
movsd xmm0, [rsp]
add rdp, 8
{op2asm_double[e_op.value]}"""
        elif e_left.data == "field_access" or e_right.data == "field_access":
            code_left = asm_expression(e_left)
            code_right = asm_expression(e_right)
            return f"""{code_left}
push rax
{code_right}
mov rbx, rax
pop rax
{op2asm_int[e_op.value]}"""
    elif e.data == "field_access":
        var = e.children[0].children[0].value  # exemple : p
        field = e.children[0].children[1].value  # exemple : A
        struct_type = struct_bss[var]  # exemple : "Point"
        offset = get_struct_offset(struct_type, field)
        return f"mov rax, [{var} + {offset}]"


def asm_command(c, lst = None):
    if c.data == "declaration":
        type = c.children[0].children[0]
        var = c.children[0].children[1]
        if not isinstance(type, Tree):
            if type.value == "void":
                raise Exception("c'est pas un vrai type void")
            variables[var.value] = type.value
            #variables_bss[var.value] = type.value
        else :#c'est une struct
            #variables[var.value] = type.children[0].value
            struct_bss[var.value] = type.children[0].value
        if len(c.children) >=2:
            exp = c.children[1]
            return f"{asm_expression(exp)}\nmov [{var.value}], rax"
    
    elif c.data == "affectation":
        var = c.children[0]
        exp = c.children[1]
        asm_exp = asm_expression(exp)
        type_var = variables[var.value]
        type_exp = get_type_expression(exp)
        if (type_var != type_exp and type_exp!='cast'): #pour le moment juste double = int + int
            return f"""{asm_exp}
cvtsi2sd xmm0, rax
movsd [{var.value}], xmm0
"""
        
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
        code_body = asm_command(body)

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
    elif c.data == "set_value":
        var = c.children[0].children[0].value 
        field = c.children[0].children[1].value  
        exp = c.children[1]
        struct_type = struct_bss[var]
        offset = get_struct_offset(struct_type, field)
        return f"""{asm_expression(exp)}
mov [{var} + {offset}], rax"""
    elif c.data == "malloc":
        var = c.children[0].children[1].value
        var_type = c.children[0].children[0].value
        decl_type = c.children
    elif c.data == "sequence":
        result = ""
        for command in c.children:
            result += f"{asm_command(command)}\n"
        return result
    

    return ""


def asm_struct(p):
    struct_name = p.children[-1].value
    total_size_bytes = 0
    for field in p.children[:-1]:
        typename = field.children[0].value
        total_size_bytes += size_map[typename]

    size_qword = (total_size_bytes + 7) // 8
    return f"{struct_name}: resq {size_qword} ; taille {total_size_bytes} pour {struct_name}\n"

def asm_decl_var(lst=None):#variables en argument
    decl_var = ""
    for var, type in variables.items():
        if type in types_len:
            decl_var += f"{var} : {types_len[type]} 0\n"
        elif type in struct:
            size_bytes = sum(
                8 for field_type, _ in struct[type]  # on suppose alignement sur 8 octets
            )
            size_qword = (size_bytes + 7) // 8
            decl_var += f"{var} : resq {size_qword}\n"
        else:
            raise Exception(f"Type inconnu : {type}")
    return decl_var

def get_struct_offset(struct_name, field_name):
    offset = 0
    for field_type, field in struct[struct_name]:
        if field == field_name:
            return offset
        offset += 8  #on suppose 8 octets d'alignement
    raise Exception(f"Champ {field_name} non trouvé dans struct {struct_name}")


def asm_main(p):
    with open("moule.asm") as f:
        prog_asm = f.read()

    init_vars = ""
    float_data = ""
    decl_vars = ""
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
mov [{c.children[1].value}], rax
"""
    prog_asm = prog_asm.replace("COMMANDE", asm_command(p.children[2])) 
    decl_vars += asm_decl_var(p.children[1].children)
    prog_asm = prog_asm.replace("DECL_VARS", decl_vars)
    prog_asm = prog_asm.replace("INIT_VARS", init_vars)
    
    structure = ""
    for variable, type in struct_bss.items():
        total_size_bytes = 0
        for field in struct[type]:
            total_size_bytes += size_map[field[0]]
        size_qword = (total_size_bytes + 7) // 8
        structure += f"{variable}: resq {size_qword} ; taille {total_size_bytes} pour {variable}\n"
    prog_asm = prog_asm.replace("DECL_STRUCT", structure)
    #Gestion du retour, nécessite que les variables soient déclarées
    #Check de la correspondance des types 
    decl_type = p.children[0].value
    given_type = get_type_expression(p.children[3])
    if((given_type != decl_type) and (decl_type != "void")):
        raise Exception(f"Pas le bon type de retour : déclaré {p.children[0].value}, donné {get_type_expression(p.children[3])}")
    ret = asm_expression(p.children[3])
    prog_asm = prog_asm.replace("RETOUR", ret)

    decl_vars = asm_decl_var()
    prog_asm = prog_asm.replace("DECL_VARS", decl_vars)
    

    for val, label in float_literals.items():
        float_data += f"{label}: dq {val}\n"
    prog_asm = prog_asm.replace("FLOAT_CONSTS", float_data)

    ret = asm_expression(p.children[3])
    prog_asm = prog_asm.replace("RETOUR", ret)
        
    return prog_asm

def asm_programme(p):
    if len(p.children) >= 2:
        for i in range(len(p.children) - 1):
            parse_struct_def(p.children[i])
    res = asm_main(p.children[-1])
    return res

if __name__ == "__main__":
    with open("sample_struct.c") as f:
        src = f.read()
        ast = g.parse(src)
        res = asm_programme(ast)
        print(res)
        print(struct)
        print(ast)
        print(pp_programme(ast))
    with open("sample.asm", "w") as result:
        result.write(res)