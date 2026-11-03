#!/usr/bin/env python3
"""Mesure les limites des STL : facettage, volume ouvert, unités absentes, pièces fusionnées.

Ce test réussit si les défauts attendus sont bien détectés ou chiffrés : un STL ouvert doit
être repéré, et l'absence d'unité doit être démontrée. Lancement :
drone-freecad-python tests/test_limites_stl.py [dossier_sortie]
"""
import math
import os
import sys
from pathlib import Path

import numpy as np

import FreeCAD as App
import Mesh
import MeshPart
import Part

R, H_CYL = 14.0, 15.0  # cylindre type moteur (mm)
RHO = 5500e-9          # kg/mm3


def proprietes_triangles(triangles):
    """Volume, centre et inertie (densité 1) par tétraèdres signés depuis l'origine.

    Le résultat n'a de sens que si la surface est fermée et bien orientée.
    """
    v = 0.0
    premier = np.zeros(3)
    second = np.zeros((3, 3))
    for a, b, c in triangles:
        det = float(np.dot(a, np.cross(b, c)))
        v += det / 6
        s = a + b + c
        premier += det / 24 * s
        second += det / 120 * (np.outer(a, a) + np.outer(b, b) + np.outer(c, c) + np.outer(s, s))
    centre = premier / v
    inertie_o = np.trace(second) * np.eye(3) - second
    d = centre
    return v, centre, inertie_o - v * (d @ d * np.eye(3) - np.outer(d, d))


def triangles_de(maillage):
    return [np.array([list(p) for p in f.Points]) for f in maillage.Facets]


def main():
    dossier = Path(sys.argv[1] if len(sys.argv) > 1 else
                   os.path.expanduser("~/drone-tools/resultats/stl"))
    dossier.mkdir(parents=True, exist_ok=True)
    ok = True
    v_th = math.pi * R**2 * H_CYL
    izz_th = v_th * R**2 / 2
    ixx_th = v_th * (3 * R**2 + H_CYL**2) / 12
    cylindre = Part.makeCylinder(R, H_CYL)

    print("1. Facettage du cylindre R14 H15, volume et inertie par rapport à la théorie")
    print(f"{'flèche corde mm':>16}{'facettes':>10}{'V mesuré mm3':>14}{'V %':>9}{'Ixx %':>9}{'Izz %':>9}{'zG mm':>9}")
    for corde in (1.0, 0.1, 0.01, 0.001):
        m = Mesh.Mesh(MeshPart.meshFromShape(Shape=cylindre, LinearDeflection=corde,
                                             AngularDeflection=0.5, Relative=False))
        chemin = dossier / f"cylindre_{corde}.stl"
        m.write(str(chemin))
        relu = Mesh.Mesh(str(chemin))
        v, c, i = proprietes_triangles(triangles_de(relu))
        print(f"{corde:>16}{relu.CountFacets:>10}{v:>14.3f}{100 * (v - v_th) / v_th:>9.3f}"
              f"{100 * (i[0, 0] - ixx_th) / ixx_th:>9.3f}{100 * (i[2, 2] - izz_th) / izz_th:>9.3f}{c[2]:>9.4f}")

    print("\n2. STL ouvert : une facette retirée sur un cube de 10 mm (théorie 1000 mm3)")
    cube = Mesh.createBox(10, 10, 10)
    print(f"  fermé  : isSolid={cube.isSolid()}, Volume={cube.Volume:.3f}")
    ouvert = cube.copy()
    ouvert.removeFacets([0])
    v_ouvert_mesh = ouvert.Volume
    # Translation sur les trois axes : la facette retirée a une normale quelconque parmi eux.
    t_ouvert = [t + np.array([100.0, 100.0, 100.0]) for t in triangles_de(ouvert)]
    v_loin, _, _ = proprietes_triangles(t_ouvert)
    v_o, _, _ = proprietes_triangles(triangles_de(ouvert))
    print(f"  ouvert : isSolid={ouvert.isSolid()}, hasNonManifolds={ouvert.hasNonManifolds()}, "
          f"Mesh.Volume={v_ouvert_mesh}")
    print(f"  intégrale non protégée : {v_o:.3f} mm3 avant translation, {v_loin:.3f} mm3 après "
          "translation de (100, 100, 100) mm")
    if ouvert.isSolid() or abs(v_o - v_loin) < 1:
        print("  ÉCHEC : le défaut n'est pas détecté comme attendu")
        ok = False

    print("\n3. Unités absentes : le même cube lu en mm ou en m")
    chemin = dossier / "cube_ascii.ast"
    cube.write(str(chemin), "AST")
    entete = chemin.read_text().splitlines()[0]
    print(f"  première ligne du fichier : {entete!r}")
    v_mm3 = cube.Volume
    print(f"  coordonnées lues en mm : {v_mm3 * RHO * 1e3:.4f} g ; "
          f"lues en m : {v_mm3 * 1e9 * RHO * 1e3:.4g} g, à la même densité (rapport 1e9) ; "
          f"lues en pouces : {v_mm3 * 25.4**3 * RHO * 1e3:.4f} g")
    print("  rien dans le fichier ne permet de trancher : l'unité doit être fournie ou confirmée")

    print("\n4. Assemblage fusionné : deux pièces dans un même STL")
    a = Mesh.createBox(10, 10, 10)
    b = Mesh.createBox(10, 10, 10)
    b.translate(30, 0, 0)
    a.addMesh(b)
    chemin = dossier / "fusion.stl"
    a.write(str(chemin))
    fusion = Mesh.Mesh(str(chemin))
    composantes = fusion.getSeparateComponents()
    print(f"  composantes séparées retrouvées : {len(composantes)} ; noms et densités : aucun dans le fichier")
    if len(composantes) != 2:
        print("  ÉCHEC : composantes non retrouvées")
        ok = False
    c1 = Mesh.createBox(10, 10, 10)
    c2 = Mesh.createBox(10, 10, 10)
    c2.translate(5, 0, 0)
    c1.addMesh(c2)
    print(f"  deux cubes qui se chevauchent à moitié : Volume mesuré {c1.Volume:.1f} mm3, "
          f"volume réel 1500 mm3, composantes {len(c1.getSeparateComponents())}, isSolid={c1.isSolid()}")

    print("\nRésultat :", "RÉUSSI (défauts détectés et chiffrés)" if ok else "ÉCHEC")
    return 0 if ok else 1


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    os._exit(code)
