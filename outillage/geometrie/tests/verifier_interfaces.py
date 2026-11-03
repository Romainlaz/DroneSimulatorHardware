#!/usr/bin/env python3
"""Charge l'interface FreeCAD sans écran (Qt offscreen) et ouvre sa fenêtre principale.

Ce test prouve que les bibliothèques graphiques se chargent. Il ne prouve PAS qu'une fenêtre
s'affiche sur le bureau : seul l'utilisateur peut le confirmer.
Lancement : QT_QPA_PLATFORM=offscreen drone-freecad-python tests/verifier_interfaces.py
"""
import os
import sys

if os.environ.get("QT_QPA_PLATFORM") != "offscreen":
    print("Refus : ce test ne doit pas ouvrir de fenêtre sur le bureau de l'utilisateur.")
    sys.exit(2)

import FreeCAD  # noqa: E402
import FreeCADGui  # noqa: E402



def dire(texte):
    # showMainWindow redirige sys.stdout vers la vue rapport de FreeCAD.
    os.write(1, (texte + "\n").encode())


FreeCADGui.showMainWindow()
fenetre = FreeCADGui.getMainWindow()
dire(f"GuiUp : {FreeCAD.GuiUp}")
dire(f"Fenêtre principale : {type(fenetre).__name__} '{fenetre.windowTitle()}'")
FreeCADGui.activateWorkbench("FemWorkbench")
dire(f"Atelier actif : {FreeCADGui.activeWorkbench().name()}")
dire("Résultat : RÉUSSI (hors écran)")
os._exit(0)
