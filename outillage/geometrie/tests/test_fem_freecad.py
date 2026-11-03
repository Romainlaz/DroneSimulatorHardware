#!/usr/bin/env python3
"""Test du module FEM de FreeCAD sans interface : même poutre, chaîne FreeCAD + Gmsh + CalculiX.

Complète test_poutre_calculix.py, qui pilote Gmsh et CalculiX directement. Ici, tout passe
par les objets FEM de FreeCAD, comme le ferait un utilisateur de l'atelier FEM.
Lancement : drone-freecad-python tests/test_fem_freecad.py [dossier_sortie]
"""
import os
import sys
from pathlib import Path

import FreeCAD as App
import ObjectsFem
import Part
from femmesh.gmshtools import GmshTools
from femtools import ccxtools

L, B, H = 200.0, 20.0, 10.0
E, NU, F = 70000.0, 0.33, 50.0
SEUIL_PCT = 2.0


def face_en_x(forme, x):
    for i, face in enumerate(forme.Faces, 1):
        if abs(face.BoundBox.XMin - x) < 1e-7 and abs(face.BoundBox.XMax - x) < 1e-7:
            return f"Face{i}"
    raise RuntimeError(f"Pas de face en x={x}")


def arete_selon_z(forme):
    for i, arete in enumerate(forme.Edges, 1):
        if abs(arete.BoundBox.ZLength - H) < 1e-7 and arete.BoundBox.XLength < 1e-7:
            return f"Edge{i}"
    raise RuntimeError("Pas d'arête selon z")


def main():
    dossier = Path(sys.argv[1] if len(sys.argv) > 1 else
                   os.path.expanduser("~/drone-tools/resultats/fem_freecad"))
    dossier.mkdir(parents=True, exist_ok=True)
    doc = App.newDocument("poutre")
    poutre = doc.addObject("Part::Feature", "Poutre")
    poutre.Shape = Part.makeBox(L, B, H)
    doc.recompute()

    analyse = ObjectsFem.makeAnalysis(doc, "Analyse")
    solveur = ObjectsFem.makeSolverCalculiXCcxTools(doc, "Solveur")
    solveur.WorkingDir = str(dossier)
    analyse.addObject(solveur)

    materiau = ObjectsFem.makeMaterialSolid(doc, "Alu")
    materiau.Material = {"Name": "Alu", "YoungsModulus": f"{E} MPa",
                         "PoissonRatio": str(NU), "Density": "2700 kg/m^3"}
    analyse.addObject(materiau)

    encastre = ObjectsFem.makeConstraintFixed(doc, "Encastrement")
    encastre.References = [(poutre, face_en_x(poutre.Shape, 0.0))]
    analyse.addObject(encastre)

    effort = ObjectsFem.makeConstraintForce(doc, "Effort")
    effort.References = [(poutre, face_en_x(poutre.Shape, L))]
    effort.Force = f"{F} N"
    effort.Direction = (poutre, [arete_selon_z(poutre.Shape)])
    effort.Reversed = True
    analyse.addObject(effort)

    maillage = ObjectsFem.makeMeshGmsh(doc, "Maillage")
    maillage.Shape = poutre
    maillage.ElementOrder = "2nd"
    maillage.CharacteristicLengthMax = "5 mm"
    doc.recompute()
    erreur = GmshTools(maillage).create_mesh()
    if erreur:
        print("Erreur de maillage :", erreur)
    analyse.addObject(maillage)
    doc.recompute()
    print(f"Maillage : {maillage.FemMesh.NodeCount} nœuds, {maillage.FemMesh.VolumeCount} volumes")

    fea = ccxtools.FemToolsCcx(analyse, solveur)
    fea.update_objects()
    fea.setup_working_dir(str(dossier))
    fea.setup_ccx()
    probleme = fea.check_prerequisites()
    if probleme:
        print("Prérequis FEM non remplis :", probleme)
        return 1
    fea.purge_results()
    fea.write_inp_file()
    fea.ccx_run()
    fea.load_results()
    trouves = [o for o in analyse.Group if o.isDerivedFrom("Fem::FemResultObject")]
    if not trouves:
        print("Résultat : ÉCHEC (aucun résultat chargé)")
        return 1
    resultat = trouves[0]

    i = B * H**3 / 12
    fleche_th = F * L**3 / (3 * E * i)
    sigma_th = F * L * (H / 2) / i
    noeuds = resultat.Mesh.FemMesh.Nodes
    dz = dict(zip(resultat.NodeNumbers, [v.z for v in resultat.DisplacementVectors]))
    sxx = dict(zip(resultat.NodeNumbers, resultat.NodeStressXX))
    bout = [abs(dz[n]) for n, p in noeuds.items() if abs(p.x - L) < 1e-7]
    fleche = sum(bout) / len(bout)
    # SXX en fibre supérieure à mi-longueur, zone libre de singularité.
    mi = [sxx[n] for n, p in noeuds.items() if abs(p.z - H) < 1e-7 and 0.45 * L < p.x < 0.55 * L]
    sigma_mi = sum(mi) / len(mi)
    sigma_max = max(sxx.values())
    e_f = 100 * (fleche - fleche_th) / fleche_th
    e_m = 100 * (sigma_mi - sigma_th / 2) / (sigma_th / 2)
    e_b = 100 * (sigma_max - sigma_th) / sigma_th
    print(f"Flèche : {fleche:.5f} mm ; théorie {fleche_th:.5f} mm ; écart {e_f:.2f} %")
    print(f"SXX à mi-longueur : {sigma_mi:.3f} MPa ; théorie {sigma_th / 2:.3f} MPa ; écart {e_m:.2f} %")
    print(f"SXX max brut (singularité d'encastrement) : {sigma_max:.3f} MPa ; théorie {sigma_th:.3f} MPa ; écart {e_b:.2f} %")
    ok = abs(e_f) <= SEUIL_PCT and abs(e_m) <= SEUIL_PCT
    print("Résultat :", "RÉUSSI" if ok else "ÉCHEC")
    return 0 if ok else 1


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    os._exit(code)
