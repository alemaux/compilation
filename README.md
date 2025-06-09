# Cours de Compilation

#### Raphael Franco, Mathieu Jeannot, Aloïs Lemaux, Basile Marie

## Guide d'utilisation du projet

Le compilateur que nous avons élaboré pour ce cours est constitué par les fichiers 
>nanoc.py

>moule.asm

>comp.sh

L'utilisation du compilateur est rendue plus simple par l'exécutable `comp.sh`, qui prend en argument un fichier `*.c` et le compile. Un exécutable nommé `a.out` et un fichier assembleur x86 `sample.asm` seront créés.

_Exemple d'utilisation :_ 
> \> ./comp.sh ./sample.c

___

## Fonctionnalités du compilateur

Les fonctionnalités que nous devions implémenter sont : le typage, les nombres flottants, les strings/char* et les structs.

### Typage
Nous avons décidé, dans ce projet, de faire un typage statique. Pour ce fait, nous utiliseons un dictionnaire python qui stocke les variables ainsi que leurs types à la compilation. Ceci permet de vérifier les types lors des affectations, et empêche les doubles déclarations. <br>
Les types que nous avons implémentés sont les `int`, les `short`, les `char` et les `long`, dont les tailles en mémoire correspondent à celles du langage c.
Notre implémentation permet aussi de donner un type de retour à la fonction main, et de vérifier si le type fourni dans la clause `return` y correspond. 
### Nombres flottants

### String / char*

### Structs
- Ce qui fonctionne : il est possible de définir une struct, de créer une instance de struct en donnant des valeurs aux champs, d'y accéder et de les modifier
- Ce qui ne fonctionne pas : l'allocation dynamique avec new. 

