import sys
from lark import Lark, Tree

g = Lark("""
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
OPBIN: /[+\\-*\\/>]/
NUMBER: /[1-9][0-9]*/ |"0"
STRING: /"[^"]*"/
TYPE: "long" | "int" | "char" | "void" | "short" | "string"
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

boucles = []

cpt = iter(range(1000000))

types = ["long", "int", "char", "void", "short", "string"]

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
    'double': 8,
    'string':8,
    'len':8
}

types_len = {
        "char" : "db",
        "short" : "dw",
        "int" : "dd",
        "long" : "dq",
        "string" : "dq", # pointeur
        "len" : "dq"
    }

format = {
    "number" : "fmt_int",
    "int" : "fmt_int",
    "string" : "fmt_string",
    "len" : "fmt_int"
}

asm_decl_struct = ""

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
    if e.data == 'index' : #on gérera que l'index soit attribué qu'à des int
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
            return f"{type.value} {var.value} = {pp_expression(exp)}"
        return f"{type.value} {var.value}"
    elif c.data == "declaration":
        type = c.children[0].children[0]#.children[0]
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
        result = ""
        for command in c.children:
            result += f"    {pp_commande(command)};\n"
        return result
    elif c.data == "set_value":
        left = c.children[0]
        objet = left.children[0]
        champ = left.children[1]
        value = c.children[1]
        return f"{objet.value}.{champ.value} = {pp_expression(value)}"


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

def asm_expression(e):
    if e.data == 'var' : 
        return f"mov rax, [{e.children[0].value}]"  #[h] : on rprend le contenu du pointeur h 
    if e.data == 'number' : 
        return f"mov rax, {e.children[0].value}"
    if e.data == 'double' : 
        return f"movsd xmm0, {e.children[0].value}"
    if e.data == 'string' :
        # par convention malloc regarde la taille allouée dans rdi et renvoie le pointeur dans rax
        s = e.children[0].value
        l = len(s)
        #return f"mov rdi, {len(s)}\ncall malloc"
        # on garde la valeur du pointeur dans rax et on la copie dans rbx pour écrire la chaîne de caractères, tout en gardent le pointeur
        resultat = f"""mov rdi, {l+1}
call malloc
mov rbx, rax"""
        for i in range(l):
            resultat = resultat + f"\nmov byte [rbx + {i}], {ord(s[i])}" # donne le caractère ASCII correspondant au char (ex "h" --> 104)
        resultat = resultat + f"\nmov byte [rbx + {l}], 0"
        return resultat

    if e.data == 'len' :
        child = e.children[0]
        if child.data == 'var' and variables[child.children[0].value] == "string":
            pointeur = child.children[0].value
            len_boucles = len(boucles)
            id = str(len_boucles)
            boucles.append(id)
            resultat = f"""mov rdi, [{pointeur}]
xor rcx, rcx       ; compteur longueur
.len_loop{id}:
    cmp byte [rdi], 0
    je .len_done{id}
    inc rcx
    inc rdi
    jmp .len_loop{id}
.len_done{id}:
    mov rax, rcx
    dec rax
    dec rax"""
            return resultat
        #elif child.data == 'string':
        else :
            raise Exception("pas le bon type")
    
    if e.data == 'index' : #on gérera que l'index soit attribué qu'à des int
        e_left = e.children[0]
        e_right = e.children[1]
        if e_left.data == 'var' and variables[e_left.children[0].value] == "string" and e_right.data in ['number','int']: #in ['number', 'var'] :
            pointeur = e_left.children[0].value
            indice = e_right.children[0].value
            len_boucles = len(boucles)
            id = str(len_boucles)
            boucles.append(id)
            resultat = f"""mov rdi, [{pointeur}]
inc rdi   ; on saute le guillemet
xor rcx, rcx       ; compteur longueur
.index_loop{id}:
    cmp rcx, {indice}
    je .index_done{id}
    inc rcx
    inc rdi
    jmp .index_loop{id}
.index_done{id}:
    movzx rax, byte [rdi]   ; charger l'octet, et l'étendre en entier (valeur ASCII)
    ;mov rax, rdi
    """
            # convertir en int :
            # resultat = resultat + f"""\n"""
            return resultat
        else :
            raise Exception("pas le bon type")
        
    # début opbin
    if e.data == "opbin":
        e_left = e.children[0]
        e_op = e.children[1]
        e_right = e.children[2]
        asm_left = asm_expression(e_left)
        asm_right = asm_expression(e_right)

        # le premier cas de figure traitera des var pour ne plus avoir à s'embêter avec après en fonction du typage
        if(e_left.data == 'var' and e_right.data == 'var'):
            pointeur_left = e_left.children[0].value
            pointeur_right = e_right.children[0].value
            type_left = variables[pointeur_left]
            type_right = variables[pointeur_right]
            # variables_bss[var.value] = type.value
            if(type_left == 'string' and type_right == 'string' and e_op.value == '+'):
                resultat = ""
                len_boucles = len(boucles)
                id = str(len_boucles)
                boucles.append(id)
                # Calculer la longueur de chaque chaîne (s_left et s_right)
                resultat = resultat + f"""; Début concaténation
mov rdi, [{pointeur_left}] ; copie pour ne pas perdre rsi
xor rcx, rcx
.len1_loop{id}:
    cmp byte [rdi], 0
    je .len1_done{id}
    inc rcx
    inc rdi
    jmp .len1_loop{id}
.len1_done{id}:
    mov r8, rcx ; r8 = len1"""
                
                resultat = resultat + f"""\nmov rdi, [{pointeur_right}]
xor rcx, rcx
.len2_loop{id}:
    cmp byte [rdi], 0
    je .len2_done{id}
    inc rcx
    inc rdi
    jmp .len2_loop{id}
.len2_done{id}:
    mov r9, rcx ; r9 = len2"""

                # Allouer malloc(len1 + len2 + 1)
                # r8 = len1, r9 = len2
                resultat = resultat + f"""\nmov rax, r8
add rax, r9
add rax, 1 ; pour le 'backslash 0'
mov rdi, rax ; rdi = taille
call malloc ; retourne pointeur dans rax
mov rbx, rax ; rbx = pointeur du buffer alloué"""

                # Copier string_left dans le buffer
                resultat = resultat + f"""\nmov rsi, [{pointeur_left}]
mov rdi, rbx ; pointeur de destination = buffer
.copy_s1{id}:
    mov al, byte [rsi]
    cmp al, 0
    je .copy_s1_done{id}
    mov [rdi], al
    inc rsi
    inc rdi
    jmp .copy_s1{id}"""

                # Copier string_right à la suite
                resultat = resultat + f"""\n.copy_s1_done{id}:
dec rdi
mov rsi, [{pointeur_right}]
inc rsi
.copy_s2{id}:
    mov al, byte [rsi]
    cmp al, 0
    je .concat_done{id}
    mov [rdi], al
    inc rsi
    inc rdi
    jmp .copy_s2{id}
.concat_done{id}:
"""
                # Terminer par 0
                resultat = resultat + "mov byte [rdi], 0    ; assurer la terminaison"

                # Retourner le pointeur du buffer résultant : mettre le résultat dans rax à la fin (le pointeur)
                resultat = resultat + f"\nmov rax, rbx"
                return resultat              

        elif(e_left.data in  ['number', 'var'] and e_right.data in ['number', 'var']):
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
# fin opbin


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
        if var in variables.keys():
            return f"{asm_expression(exp)}\nmov [{var.value}], rax"
        else :
            raise Exception("Variable non déclarée")
        
    elif c.data =="skip": return "nop\n"

    elif c.data == "print":
        if(c.children[0].children[0].value in variables):
            fmt = format[variables[c.children[0].children[0]]]
        else :
            fmt = format[c.children[0].data]
        return f"""{asm_expression(c.children[0])}
mov rdi, {fmt}
mov rsi, rax
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
{asm_command(body)}
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

def asm_decl_var(lst):#variables en argument
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
    decl_vars = ""
    for i, c in enumerate(p.children[1].children):
        variables[c.children[1].value] = c.children[0].value
        init_vars += f"""mov rbx, [argv]
mov rdi, [rbx + {8 * (i+1)}]
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
    ret = ret + f"\nmov rdi, {format[p.children[0].value]}\n"
    prog_asm = prog_asm.replace("RETOUR\nmov rdi, fmt_int", ret) # on s'adapte au moule en supprimant le fmt_int pour pouvoir print des string notamment
    return prog_asm

def asm_programme(p):
    if len(p.children) >= 2:
        for i in range(len(p.children) - 1):
            parse_struct_def(p.children[i])
    res = asm_main(p.children[-1])
    return res

if __name__ == "__main__":
    with open(sys.argv[1]) as f: #"sample.c"
        src = f.read()
        ast = g.parse(src)
        res = asm_programme(ast)
        print(res)
        print(struct)
        print(ast)
        print(pp_programme(ast))
    with open("sample.asm", "w") as result:
        result.write(res)