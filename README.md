# Cours de Compilation

#### Raphael Franco, Mathieu Jeannot, Aloïs Lemaux, Basile Marie

## Guide d'utilisation du projet

Le compilateur que nous avons élaboré pour ce cours est constitué par les fichiers 
>nanoc.py

>moule.asm

>comp.sh

L'utilisation du compilateur est rendue plus simple par les exécutable `comp.sh`, qui prennent en argument un fichier `*.c` pour le compiler. Un exécutable nommé `a.out` et un fichier assembleur x86 `sample.asm` seront créés.

_Exemple d'utilisation :_ 
> \> ./comp_[branche].sh ./sample.c

___

## Fonctionnalités des compilateurs

Les fonctionnalités que nous devions implémenter sont : le typage, les nombres flottants, les strings/char* et les structs.

### Typage
Nous avons décidé, dans ce projet, de faire un typage statique. Pour ce fait, nous utiliseons un dictionnaire python qui stocke les variables ainsi que leurs types à la compilation. Ceci permet de vérifier les types lors des affectations, et empêche les doubles déclarations. <br>
Les types que nous avons implémentés sont les `int`, les `short`, les `char` et les `long`, dont les tailles en mémoire correspondent à celles du langage c.
Notre implémentation permet aussi de donner un type de retour à la fonction main, et de vérifier si le type fourni dans la clause `return` y correspond. <br>
Un exemple de code implémentant les fonctionnalités de typage est fourni. Compilez le fichier `sample_typage.c` pour obtenir un exécutable. Ce dernier prend en argument deux entiers et renvoie la somme des deux, à laquelle il ajoute 10. Cet exemple illustre également la déclaration de variables : dans la section `.data` du fichier assembleur, on trouve une déclaration pour la variable A, et une pour la variable B.<br>
Le typage est marche avec toutes les branches. Nous proposons d'utiliser :
> \>./comp_double.sh sample_typage.c

### String / char*

### Structs

Pour utiliser le compilateur de la branche _struct__, nous proposons l'exécutable `comp_struct.sh`, ainsi que le code d'exemple `sample_struct.c`. <br>
Exemple d'utilisation : 
> \> ./comp_struct.sh sample_struct.c

- Ce qui fonctionne : il est possible de définir une struct, de créer une instance de struct en donnant des valeurs aux champs, d'y accéder et de les modifier
- Ce qui ne fonctionne pas : l'allocation dynamique avec new et l'appel à printf. 

### Double

Pour utiliser le compilateur de la branche _double_, nous proposons l'exécutable `comp_double.sh`. <br>
Exemple d'utilisation : 
> \> ./comp_double.sh [fichier utlisant des doubles].c

Lors de l'implémentation des doubles, nous avions plusieurs objectifs :
> Manipuler les registres des doubles

> Faire une somme de double

> Manipuler les casts forcés mais aussi les casts automatique lors de l'addition d'un int et d'un double

Une grande partie de ces objectifs ont été réalisé avec succès. Avec le code en C présent sur la branche, il est possible de faire la somme de double. De plus, il est possible de sommer un double et un int même si l'on parle de variables ou non. Voilà des exemples qui marchent ci dessous

> X = 2.1 + 3
>
> X = 4 + 5 

ou encore en ayant `int Z = 3 et double X = 2.6` il est possible de faire en castant temporairement la valeur de Z

> X = X + Z

Il faut cependant noter que l'écrire sous la forme ci dessous ne marchera pas (mais on aime le code bien écris)

> X = Z + X

Il y a cependant certaines fonctionnalités qui ne fonctionnent pas encore. On compte là dedans la cast automatique. Celui ci n'est pas si difficile à implémenter mais nous avons décidé de nous concentrer sur les autres fonctionnalités que l'on trouvait plus intéréssantes.

Il est aussi impossible (mais cela reste du bon sens) lors de la déclaration d'un double de réaliser :

> double X = 3

 Cela retournera que les deux types ne sont pas les mêmes pour la déclaration





