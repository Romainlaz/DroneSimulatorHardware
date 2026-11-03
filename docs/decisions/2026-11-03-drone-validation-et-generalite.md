# Drone de validation et généralité de la chaîne

Date : 2026-11-03
Statut : validé par l'utilisateur.

## Contexte

La chaîne doit être validée sur un drone réel à mesures publiées avant tout usage sur les designs de
l'utilisateur. La fiche [7] a retenu TII Racing pour les performances de vol. Sa CAO est très incomplète et
son inertie n'est pas publiée. Agilicious et NeuroBEM n'ont pas de CAO exploitable trouvée.

## Décision 1 : drone de validation

- Options : TII Racing ; Agilicious ; NeuroBEM.
- Choix : **TII Racing**, avec une CAO simplifiée à notre charge, signalée comme estimée.
- Raison : seul candidat à références complètes, sous Betaflight et avec des données sous licence libre.

## Décision 2 : la chaîne ne doit pas marcher que pour ce drone

Exigence de l'utilisateur : TII Racing sert à contrôler la chaîne, pas à la façonner.

Traduction proposée dans les contrats (à valider avec eux) :

- rien de propre à TII dans le code : le drone n'entre que par sa fiche hardware, comme tout autre ;
- les vols de calage et les vols de validation sont strictement séparés ;
- tout paramètre recalé sur des vols est tracé comme tel dans la fiche de performances, et n'est jamais
  réutilisé pour un autre drone sans être signalé ;
- la chaîne est aussi lancée sur d'autres configurations, de 3 à 7 pouces, pour contrôler qu'elle
  fonctionne et que ses tendances sont physiquement cohérentes. Ce contrôle n'est pas une validation ;
- NeuroBEM, qui publie masse, inertie et vitesses moteur, peut servir de second contrôle indépendant sur
  le modèle de vol et la dynamique moteur, sans la partie CAO. À étudier.

## Décision 3 : domaine de validité

- Options : étiquette « domaine validé / hors domaine » ; annoncer une chaîne valable de 3 à 7 pouces.
- Choix : **l'étiquette**. Proche de 5 pouces : domaine validé. Autres tailles : hors domaine validé.
- Raison : les mesures ne portent que sur un drone. L'étiquette informe et ne limite pas l'usage.
- Précision de l'utilisateur : le but est de tester du nouveau hardware et de découvrir de nouvelles
  mesures, donc on sera souvent hors du domaine validé. Ce cas est le cas normal d'usage, et non une
  exception.

## Décision 4 : prédire du nouveau hardware

- Options : étiquette seule ; conception centrée sur la prédiction hors domaine.
- Choix : **conception centrée sur la prédiction**, base des contrats :
  1. incertitude résultat par résultat : origine du chiffre et distance au drone validé ;
  2. comparaison entre drones ; l'idée que les écarts sont plus fiables que les valeurs absolues reste une
     hypothèse à tester, marquée comme non démontrée ;
  3. pour chaque composant, dans l'ordre : mesures de l'utilisateur, tableau d'essais publié, composant
     voisin ou calcul à partir de la géométrie, signalé comme estimation et validé par question groupée ;
  4. une mesure obtenue plus tard resserre l'incertitude de tous les drones qui utilisent ce composant.
- Raison : le but de l'outil est de tester du nouveau hardware, sans vol ni tableau d'essais disponibles.
- Révisé par la décision 5 : le point 3 est remplacé, et le point 1 est rouvert.

## Décision 5 : estimer d'abord à partir du modèle 3D

- Options : tableaux d'essais d'abord, le 3D en dernier recours ; 3D d'abord, valeurs en option.
- Choix : **3D d'abord**. Par défaut, le système estime les valeurs à partir du modèle 3D, sans utiliser de
  valeurs externes même si elles existent. Des valeurs plus précises peuvent être ajoutées en option.
- Raison : choix de l'utilisateur ; un hardware créé de toutes pièces n'a aucune valeur externe.
- Précision de l'utilisateur, qui prime sur le choix ci-dessus : **la source dépend du composant**. Pour le
  châssis et les pièces conçues, le 3D et le matériau comptent. Pour le moteur et la batterie, c'est le
  modèle commercial, et le système va chercher ses données : on n'invente pas un moteur.
- Conséquences : la recherche de données reste une étape de la chaîne pour ces composants, et la chaîne
  minimale peut repartir d'un tableau d'essais.
- Hélice : par référence si elle est commerciale, par le 3D si elle est conçue par l'utilisateur. ESC et
  contrôleur de vol : par référence. L'estimation de la propulsion à partir du 3D (fiche [9]) est reportée
  après la chaîne minimale.
- Marges d'incertitude (remplace le point 1 de la décision 4 et l'exigence initiale du cahier des charges) :
  options envisagées : marges « ± » par résultat ; origine de chaque valeur et écart du test à l'aveugle.
  Choix : **pas de marges « ± »** : chaque valeur indique son origine, et la fiche donne l'écart constaté
  sur le drone de validation, sans le présenter comme une garantie. Raison : un hardware nouveau n'a rien à
  quoi se comparer, une marge serait surtout une extrapolation. La comparaison entre drones est confirmée.

## Décision 6 : test à l'aveugle et vols

- Choix : le test principal est une prédiction à l'aveugle de TII Racing, et les vols servent au diagnostic.
  Ellipses et lemniscates pour le diagnostic, les six `trackRATM` autonomes réservés à la comparaison. Les
  règles de la décision 2 sont gardées.
- Raison : c'est la seule mesure de la capacité à prédire du nouveau hardware.
