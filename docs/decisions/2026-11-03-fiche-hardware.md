# Fiche hardware et données manquantes

Date : 2026-11-03
Statut : validé par l'utilisateur. Ces choix alimenteront le contrat d'interface, qui reste à rédiger.

## Contexte

La fiche hardware est la seule entrée du système. Elle doit rester simple à remplir pour un humain,
et le système ne doit jamais inventer une donnée manquante.

## Décision 1 : association des matériaux

- Options : par nom de pièce ; un fichier par pièce ; masses mesurées d'abord.
- Choix : **par nom de pièce**. Les pièces sont nommées dans le STEP, et la fiche associe chaque nom
  à un matériau. Une pièce sans matériau déclenche une question.
- Raison : choix de l'utilisateur ; une seule saisie, sans export multiple.
- Fichiers acceptés (décidé ensuite) : le STEP reste le format préféré ; le STL est accepté avec **un
  fichier par pièce**, le nom du fichier servant de nom de pièce. Options envisagées : un STL par pièce ;
  STEP seul. Raison : respecte le cahier des charges et permet d'utiliser des pièces téléchargées.
- Conséquences pour le contrat : unités à déclarer, volumes fermés, même repère pour tous les fichiers ;
  un STL fusionné est refusé avec un message clair.

## Décision 2 : composants hors CAO

- Options : masse et position dans la fiche ; CAO complète obligatoire ; masse seule.
- Choix : **CAO complète obligatoire**. Batterie, électronique et charge utile figurent dans l'assemblage.
- Raison : choix de l'utilisateur ; centre de gravité et inertie plus fiables, au prix de plus de
  modélisation. Cela sert la priorité donnée au comportement en vol.
- Conséquence : les drones de validation publiés devront peut-être voir leur CAO complétée.

## Décision 3 : format

- Options : YAML commenté ; tableur ; formulaire guidé.
- Choix : **YAML commenté**, à partir d'un modèle rempli d'exemples.
- Raison : facile à contrôler automatiquement, à versionner et à comparer entre drones.

## Décision 4 : données manquantes

- Options : question groupée ; estimer et signaler ; arrêt systématique.
- Choix : **question groupée**. Avant les calculs longs, le système liste tous les manques d'un coup.
  Pour chacun, l'utilisateur fournit la donnée ou accepte une estimation signalée, avec son incertitude.
- Raison : applique la règle « ne jamais inventer » sans interruptions répétées.
