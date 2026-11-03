#!/usr/bin/env python3
"""Contre-vérification : relit le STEP de test_assemblage_step.py avec Gmsh.

Deuxième lecteur du même fichier. Compare masse, CG et inertie à la théorie déjà
calculée par le test FreeCAD (resultats.json), et montre si les noms de pièces survivent.
Lancement : drone-cae-python tests/test_assemblage_gmsh.py [dossier_resultats]
"""
import json
import os
import sys
from pathlib import Path

import gmsh
import numpy as np

SEUIL_REL = 1e-6


def main():
    dossier = Path(sys.argv[1] if len(sys.argv) > 1 else
                   os.path.expanduser("~/drone-tools/resultats/assemblage"))
    ref = json.loads((dossier / "resultats.json").read_text())
    densites = ref["densites_kg_mm3"]
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("assemblage")
    gmsh.model.occ.importShapes(str(dossier / "assemblage_drone.step"))
    gmsh.model.occ.synchronize()
    pieces = []
    ok = True
    for _, tag in gmsh.model.getEntities(3):
        nom_complet = gmsh.model.getEntityName(3, tag)
        nom = nom_complet.split("/")[-1]
        print(f"Volume {tag} : nom Gmsh '{nom_complet}'")
        if nom not in densites:
            print(f"  nom inconnu, densité impossible à attribuer : {nom!r}")
            ok = False
            continue
        v = gmsh.model.occ.getMass(3, tag)
        c = np.array(gmsh.model.occ.getCenterOfMass(3, tag))
        i = np.array(gmsh.model.occ.getMatrixOfInertia(3, tag)).reshape(3, 3)
        pieces.append((v * densites[nom], c, i * densites[nom]))
    gmsh.finalize()
    if not ok or len(pieces) != len(densites):
        print(f"Résultat : ÉCHEC ({len(pieces)} pièces identifiées sur {len(densites)})")
        return 1
    m = sum(p[0] for p in pieces)
    g = sum(p[0] * p[1] for p in pieces) / m
    inertie = np.zeros((3, 3))
    for mi, ci, ii in pieces:
        d = ci - g
        inertie += ii + mi * (d @ d * np.eye(3) - np.outer(d, d))
    m_t = ref["masse_kg"]["theorie"]
    g_t = np.array(ref["cg_mm"]["theorie"])
    i_t = np.array(ref["inertie_kg_mm2"]["theorie"])
    e_m = abs(m - m_t) / m_t
    e_g = float(np.max(np.abs(g - g_t)) / np.max(np.abs(g_t)))
    e_i = float(np.max(np.abs(inertie - i_t)) / np.max(np.abs(i_t)))
    print(f"Gmsh : masse {m * 1e3:.7f} g, CG {g}")
    print(f"Écarts relatifs à la théorie : masse {e_m:.2e}, CG {e_g:.2e}, inertie {e_i:.2e}")
    reussi = max(e_m, e_g, e_i) <= SEUIL_REL
    print("Résultat :", "RÉUSSI" if reussi else "ÉCHEC")
    return 0 if reussi else 1


if __name__ == "__main__":
    sys.exit(main())
