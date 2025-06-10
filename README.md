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

### String / char*

### Structs
- Ce qui fonctionne : il est possible de définir une struct, de créer une instance de struct en donnant des valeurs aux champs, d'y accéder et de les modifier
- Ce qui ne fonctionne pas : l'allocation dynamique avec new. 

### Double

Pour tester les doubles, il faut se rendre sur la branch `double`

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





