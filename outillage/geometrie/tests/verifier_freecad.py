#!/usr/bin/env python3
"""Critère de choix de la source FreeCAD : module Python, Part, Mesh et FEM sans interface.

S'exécute avec freecadcmd ou avec le Python de la distribution FreeCAD. Ne quitte
jamais silencieusement : chaque vérification imprime OK ou ECHEC.
"""
import shutil
import sys
import traceback

resultats = []


def verifie(nom, fonction):
    try:
        info = fonction()
        print(f"OK     {nom} : {info}")
        resultats.append(True)
    except Exception as exc:  # le critère est justement de tout essayer
        print(f"ECHEC  {nom} : {exc!r}")
        traceback.print_exc()
        resultats.append(False)


import FreeCAD  # noqa: E402

print("Python", sys.version.split()[0], sys.executable)
print("FreeCAD", ".".join(FreeCAD.Version()[:3]), FreeCAD.Version()[3][:40])
print("GuiUp :", FreeCAD.GuiUp)


def part():
    import Part
    b = Part.makeBox(1, 2, 3)
    return f"volume boîte = {b.Volume}"


def mesh():
    import Mesh
    return f"module {Mesh.__name__}"


def fem():
    import Fem
    import ObjectsFem
    import femtools.ccxtools  # noqa: F401
    doc = FreeCAD.newDocument("critere")
    a = ObjectsFem.makeAnalysis(doc, "Analyse")
    s = ObjectsFem.makeSolverCalculiX(doc, "Solveur") if hasattr(ObjectsFem, "makeSolverCalculiX") \
        else ObjectsFem.makeSolverCalculixCcxTools(doc, "Solveur")
    a.addObject(s)
    FreeCAD.closeDocument(doc.Name)
    return "Fem, ObjectsFem, ccxtools ; analyse et solveur créés"


def fem_maillage():
    import Fem  # noqa: F401
    doc = FreeCAD.newDocument("critere2")
    import Part
    import ObjectsFem
    from femmesh.gmshtools import GmshTools
    boite = doc.addObject("Part::Feature", "Boite")
    boite.Shape = Part.makeBox(10, 10, 10)
    doc.recompute()
    m = ObjectsFem.makeMeshGmsh(doc, "Maillage")
    m.Shape = boite
    m.CharacteristicLengthMax = 5.0
    doc.recompute()
    outil = GmshTools(m)
    erreur = outil.create_mesh()
    if erreur:
        raise RuntimeError(erreur)
    n = m.FemMesh.NodeCount
    FreeCAD.closeDocument(doc.Name)
    if n == 0:
        raise RuntimeError("maillage vide")
    return f"{n} nœuds via Gmsh"


verifie("Part", part)
verifie("Mesh", mesh)
verifie("FEM (analyse + solveur)", fem)
verifie("FEM + Gmsh (création de maillage)", fem_maillage)
print("gmsh trouvé :", shutil.which("gmsh"))
print("ccx trouvé  :", shutil.which("ccx"))
print("BILAN", "OK" if all(resultats) else "ECHEC")
sys.stdout.flush()
# freecadcmd lancé avec un script reste sinon en console interactive.
import os  # noqa: E402
os._exit(0 if all(resultats) else 1)
