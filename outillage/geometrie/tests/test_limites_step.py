#!/usr/bin/env python3
"""Mesure les limites des STEP multi-pièces : instances, noms, unités, surfaces, chevauchements.

Chaque point imprime ce qui a été constaté. Les constats ci-dessous sont vérifiés par
assertion : si une version future change le comportement, le test échoue et NOTES.md est à revoir.
Lancement : drone-freecad-python tests/test_limites_step.py [dossier_sortie]
"""
import math
import os
import re
import sys
from pathlib import Path

import FreeCAD as App
import Import
import Part

ok = True


def constat(condition, texte):
    global ok
    print(("  OK    " if condition else "  ÉCART ") + texte)
    ok = ok and condition


def lire(chemin, nom_doc):
    doc = App.newDocument(nom_doc)
    Import.insert(str(chemin), doc.Name)
    doc.recompute()
    return doc


def solides_du_document(doc):
    """Solides en coordonnées globales, en parcourant pièces et liens."""
    liste = []
    for o in doc.Objects:
        if o.isDerivedFrom("Part::Feature") and o.Shape.Solids:
            liste.append((o.Label, o.TypeId, o.Shape.copy(), o.getGlobalPlacement()))
    return liste


def main():
    dossier = Path(sys.argv[1] if len(sys.argv) > 1 else
                   os.path.expanduser("~/drone-tools/resultats/limites_step"))
    dossier.mkdir(parents=True, exist_ok=True)
    positions = [(100, 100, 0), (-100, 100, 0), (-100, -100, 0), (100, -100, 0)]

    print("1. Même pièce instanciée quatre fois (App::Link), comme quatre moteurs identiques")
    doc = App.newDocument("instances")
    racine = doc.addObject("App::Part", "drone")
    modele = doc.addObject("Part::Feature", "moteur")
    modele.Shape = Part.makeCylinder(14, 15)
    modele.Visibility = False
    for k, p in enumerate(positions):
        lien = doc.addObject("App::Link", f"moteur_{k}")
        lien.LinkedObject = modele
        lien.Placement = App.Placement(App.Vector(*p), App.Rotation())
        racine.addObject(lien)
    doc.recompute()
    chemin = dossier / "instances.step"
    Import.export([racine], str(chemin))
    App.closeDocument(doc.Name)
    texte = chemin.read_text(errors="replace")
    produits = re.findall(r"PRODUCT\('([^']*)'", texte)
    print(f"  PRODUCT dans le fichier : {produits}")
    brut = Part.read(str(chemin))
    print(f"  Part.read : {len(brut.Solids)} solides, volume total {brut.Volume:.2f} mm3 "
          f"(attendu {4 * math.pi * 14**2 * 15:.2f})")
    centres = sorted((round(s.CenterOfMass.x, 6), round(s.CenterOfMass.y, 6)) for s in brut.Solids)
    print(f"  Part.read, centres (x, y) : {centres}")
    constat(len(brut.Solids) == 4 and centres == sorted((float(x), float(y)) for x, y, _ in positions),
            "Part.read restitue les 4 instances à leur position")
    doc = lire(chemin, "lecture_instances")
    trouves = solides_du_document(doc)
    print("  Import.insert, objets à solide :")
    for label, type_id, forme, place in trouves:
        print(f"    {label} ({type_id}) base globale {tuple(round(v, 6) for v in place.Base)}, "
              f"Shape.CenterOfMass {tuple(round(v, 6) for v in forme.CenterOfMass)}")
    liens = [o for o in doc.Objects if o.isDerivedFrom("App::Link")]
    print(f"  Import.insert : {len(trouves)} Part::Feature à solide, {len(liens)} App::Link")
    App.closeDocument(doc.Name)

    print("\n2. Unités : un STEP déclare son unité, et la lecture convertit")
    chemin_mm = dossier / "cube_mm.step"
    Part.makeBox(10, 10, 10).exportStep(str(chemin_mm))
    texte = chemin_mm.read_text(errors="replace")
    motif = r"SI_UNIT\(\.MILLI\.,\.METRE\.\)"
    constat(re.search(motif, texte) is not None, "unité déclarée en mm dans le fichier généré")
    chemin_m = dossier / "cube_m.step"
    chemin_m.write_text(re.sub(motif, "SI_UNIT($,.METRE.)", texte))
    v_mm, v_m = Part.read(str(chemin_mm)).Volume, Part.read(str(chemin_m)).Volume
    print(f"  mêmes nombres, unité mm : {v_mm:.6g} mm3 ; unité m : {v_m:.6g} mm3")
    constat(abs(v_m / v_mm - 1e9) < 1, "l'unité du fichier est prise en compte (rapport 1e9)")

    print("\n3. Corps surfacique : une pièce sans volume disparaît du bilan de masse")
    chemin_s = dossier / "surface.step"
    Part.Compound([Part.makeBox(10, 10, 10, App.Vector(50, 0, 0)),
                   Part.makeBox(10, 10, 10).Shells[0]]).exportStep(str(chemin_s))
    relu = Part.read(str(chemin_s))
    print(f"  relu : {len(relu.Solids)} solide(s), {len(relu.Shells)} coque(s), Volume={relu.Volume:.3f}")
    constat(len(relu.Solids) == 1, "la coque n'est pas comptée comme solide : à signaler, pas à ignorer")

    print("\n4. Chevauchement : la masse le compte deux fois si on ne vérifie pas")
    a = Part.makeBox(10, 10, 10)
    b = Part.makeBox(10, 10, 10, App.Vector(5, 0, 0))
    print(f"  somme des volumes {a.Volume + b.Volume:.1f} mm3 ; volume réel {a.fuse(b).Volume:.1f} mm3 ; "
          f"common {a.common(b).Volume:.1f} mm3")
    constat(abs(a.common(b).Volume - 500) < 1e-6, "le volume commun détecte le chevauchement")

    print("\n5. Densité : le fichier généré n'en contient aucune")
    constat(not re.search(r"DENSITY|MATERIAL_DESIGNATION", chemin_mm.read_text(errors="replace")),
            "aucun matériau exporté : la densité doit venir d'une table externe")

    print("\nRésultat :", "RÉUSSI (constats conformes)" if ok else "ÉCARTS à analyser")
    return 0 if ok else 1


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    os._exit(code)
