# Pilotage manuel au centre et tests généraux

Date : 2026-11-04
Statut : validé par l'utilisateur.

## Contexte

Le cahier des charges demandait un drone à regarder et à piloter, ainsi qu'une fiche de performances. La
question de l'usage visé (course, freestyle, longue portée, charge utile) restait ouverte.

## Décision 1 : centre de l'expérience

- Options : fiche de performances d'abord ; pilotage manuel d'abord.
- Choix : **le centre de l'expérience est de piloter son drone à la main, pour en juger le ressenti.** La
  fiche de performances reste produite, en complément.
- Raison : choix de l'utilisateur.
- Conséquences à instruire : temps réel tenu sur ce PC, latence de la commande à l'image, pilotage à la
  manette ou à la radio, et poids de ces critères dans le choix du firmware.

- Moyens de pilotage (options : radio FPV, manette, clavier) : **manette et clavier**. Pas de radio ni de
  lunettes pour l'instant. Le clavier sert de dépannage : ses commandes tout-ou-rien ne donnent pas un
  ressenti valable.
- Précision de l'utilisateur : pas de manette pour l'instant, **les premiers tests se font au clavier**. La
  couche d'entrée utilise le clavier par défaut et bascule automatiquement sur une manette dès qu'elle est
  branchée.
- Vues (options : FPV seule, FPV et extérieure) : **FPV et vue extérieure**, FPV par défaut.

## Décision 3 : priorités de l'outillage

- Fiche [2] (CFD) : reportée après la chaîne minimale, car le ressenti en vol passe d'abord. Options
  envisagées : la reprendre maintenant ; la reporter.
- Essai de charge provoquée sur PX4 : non retenu pour l'instant. La consigne pratique suffit : garder le PC
  libre pendant le vol. Options envisagées : prouver la cause ; s'en tenir à la consigne.

## Décision 2 : tests standardisés

- Options : tests adaptés à un usage précis ; tests généraux.
- Choix : **tests généraux**, qui donnent des données intéressantes pour tout drone.
- Commande brusque : échelon de vitesse de roulis, de tangage puis de lacet, à 50 % de la vitesse max, en
  partant du stationnaire.
- Temps de réponse : temps pour atteindre 90 % de la consigne. Dépassement : pic au-dessus de la consigne.
- Croisière : vol en palier à la vitesse qui maximise la distance par charge de batterie, avec l'autonomie
  à une ou deux vitesses fixes en complément.
- Raison : même calcul pour tous les drones, donc comparable. Ces valeurs sont des choix du projet, et non
  celles d'une norme.
