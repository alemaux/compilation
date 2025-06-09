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

### Nombres flottants

### String / char*

### Structs
- Ce qui fonctionne : il est possible de définir une struct, de créer une instance de struct en donnant des valeurs aux champs, d'y accéder et de les modifier
- Ce qui ne fonctionne pas : l'allocation dynamique avec new. 

