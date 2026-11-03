#!/usr/bin/env python3
"""Test géométrie : assemblage STEP multi-pièces, masse, centre de gravité, inertie.

Génère un assemblage hiérarchique de type drone, l'exporte en STEP, le RELIT dans un
document vierge, compose masse et inertie par Huygens, et compare au calcul analytique.
Le calcul analytique n'utilise aucune fonction de FreeCAD.

Lancement : drone-freecad-python tests/test_assemblage_step.py [dossier_sortie]
Unités : mm, kg. Inertie en kg.mm2, au centre de gravité global, axes globaux.
"""
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

import FreeCAD as App
import Import
import Part

SEUIL_REL = 1e-6  # écart relatif maximal accepté sur chaque grandeur


# --- Description de l'assemblage -------------------------------------------------
# Densités en kg/mm3. "parent" : translation du sous-assemblage "moteurs".
SOUS_ASSEMBLAGE = np.array([10.0, 0.0, 0.0])

PIECES = [
    dict(nom="platine_carbone", forme="boite", dim=(120.0, 60.0, 4.0), densite=1600e-9,
         centre=(0.0, 0.0, 2.0), rot=[]),
    dict(nom="batterie_lipo", forme="boite", dim=(70.0, 35.0, 25.0), densite=1900e-9,
         centre=(-25.0, 0.0, 16.5), rot=[("z", 30.0)]),
    dict(nom="bras_tube_carbone", forme="tube", dim=(8.0, 6.0, 150.0), densite=1500e-9,
         centre=(25.0 + 75.0 * math.cos(math.pi / 4), 5.0 + 75.0 * math.sin(math.pi / 4), 12.0),
         rot=[("z", 45.0), ("y", 90.0)]),
    # Les deux moteurs sont placés dans le repère du sous-assemblage.
    dict(nom="moteur_avant", forme="cylindre", dim=(14.0, 15.0), densite=5500e-9,
         centre=(121.0, 111.0, 28.0), rot=[], sous_assemblage=True),
    dict(nom="moteur_arriere_incline", forme="cylindre", dim=(14.0, 15.0), densite=5500e-9,
         centre=(-110.0, -80.0, 30.0), rot=[("x", 10.0)], sous_assemblage=True),
]


# --- Analytique, indépendant de FreeCAD -------------------------------------------
def rotation(axe, degres):
    a = math.radians(degres)
    c, s = math.cos(a), math.sin(a)
    return {
        "x": np.array([[1, 0, 0], [0, c, -s], [0, s, c]]),
        "y": np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]]),
        "z": np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]]),
    }[axe]


def matrice_rotation(rots):
    r = np.eye(3)
    for axe, degres in rots:
        r = r @ rotation(axe, degres)
    return r


def volume_et_inertie_locale(p):
    """Volume (mm3) et inertie par unité de densité au centre, axes propres (mm5)."""
    d = p["dim"]
    if p["forme"] == "boite":
        lx, ly, lz = d
        v = lx * ly * lz
        return v, v / 12 * np.diag([ly**2 + lz**2, lx**2 + lz**2, lx**2 + ly**2])
    if p["forme"] == "cylindre":
        r, h = d
        v = math.pi * r**2 * h
        return v, v * np.diag([(3 * r**2 + h**2) / 12, (3 * r**2 + h**2) / 12, r**2 / 2])
    re, ri, h = d
    v = math.pi * (re**2 - ri**2) * h
    return v, v * np.diag([(3 * (re**2 + ri**2) + h**2) / 12,
                           (3 * (re**2 + ri**2) + h**2) / 12,
                           (re**2 + ri**2) / 2])


def huygens(inertie, masse, d):
    d = np.asarray(d, dtype=float)
    return inertie + masse * (np.dot(d, d) * np.eye(3) - np.outer(d, d))


def composer(pieces):
    """pieces : liste de (masse, centre, inertie au centre, axes globaux)."""
    m = sum(x[0] for x in pieces)
    g = sum(x[0] * np.asarray(x[1]) for x in pieces) / m
    i = sum(huygens(x[2], x[0], np.asarray(x[1]) - g) for x in pieces)
    return m, g, i


def theorie():
    donnees = {}
    for p in PIECES:
        v, i_local = volume_et_inertie_locale(p)
        r = matrice_rotation(p["rot"])
        centre = np.array(p["centre"])
        if p.get("sous_assemblage"):
            centre = centre + SOUS_ASSEMBLAGE
        m = v * p["densite"]
        donnees[p["nom"]] = (m, centre, p["densite"] * r @ i_local @ r.T, r)
    return donnees


# --- Construction et export FreeCAD -----------------------------------------------
def forme_centree(p):
    d = p["dim"]
    if p["forme"] == "boite":
        return Part.makeBox(d[0], d[1], d[2], App.Vector(-d[0] / 2, -d[1] / 2, -d[2] / 2))
    if p["forme"] == "cylindre":
        return Part.makeCylinder(d[0], d[1], App.Vector(0, 0, -d[1] / 2))
    ext = Part.makeCylinder(d[0], d[2], App.Vector(0, 0, -d[2] / 2))
    return ext.cut(Part.makeCylinder(d[1], d[2], App.Vector(0, 0, -d[2] / 2)))


def rotation_freecad(rots):
    r = App.Rotation()
    for axe, degres in rots:
        vecteur = {"x": App.Vector(1, 0, 0), "y": App.Vector(0, 1, 0), "z": App.Vector(0, 0, 1)}[axe]
        r = r.multiply(App.Rotation(vecteur, degres))
    return r


def exporter(chemin):
    doc = App.newDocument("source")
    racine = doc.addObject("App::Part", "assemblage_drone")
    moteurs = doc.addObject("App::Part", "moteurs")
    moteurs.Placement = App.Placement(App.Vector(*SOUS_ASSEMBLAGE), App.Rotation())
    racine.addObject(moteurs)
    for p in PIECES:
        o = doc.addObject("Part::Feature", p["nom"])
        o.Label = p["nom"]
        o.Shape = forme_centree(p)
        o.Placement = App.Placement(App.Vector(*p["centre"]), rotation_freecad(p["rot"]))
        (moteurs if p.get("sous_assemblage") else racine).addObject(o)
    doc.recompute()
    Import.export([racine], str(chemin))
    App.closeDocument(doc.Name)


# --- Relecture ---------------------------------------------------------------------
def relire_avec_noms(chemin):
    """Relit le STEP et renvoie {nom: solide en coordonnées globales}."""
    doc = App.newDocument("lecture")
    Import.insert(str(chemin), doc.Name)
    doc.recompute()
    solides = {}
    autres = []
    for o in doc.Objects:
        if o.isDerivedFrom("Part::Feature") and o.Shape.Solids:
            forme = o.Shape.copy()
            forme.Placement = o.getGlobalPlacement()
            if len(forme.Solids) != 1:
                raise RuntimeError(f"{o.Label} contient {len(forme.Solids)} solides")
            if o.Label in solides:
                raise RuntimeError(f"Nom en double : {o.Label}")
            solides[o.Label] = forme.Solids[0]
        else:
            autres.append(f"{o.TypeId}:{o.Label}")
    print("Objets lus sans solide :", autres)
    return doc, solides


def mesure(solide, densite):
    m_fc = solide.MatrixOfInertia
    i = np.array([[m_fc.A11, m_fc.A12, m_fc.A13],
                  [m_fc.A21, m_fc.A22, m_fc.A23],
                  [m_fc.A31, m_fc.A32, m_fc.A33]])
    c = solide.CenterOfMass
    return solide.Volume * densite, np.array([c.x, c.y, c.z]), densite * i


def interferences(solides):
    """Volumes communs : un assemblage qui se chevauche compterait deux fois la matière."""
    noms = list(solides)
    total = 0.0
    for a in range(len(noms)):
        for b in range(a + 1, len(noms)):
            if solides[noms[a]].BoundBox.intersect(solides[noms[b]].BoundBox):
                total += solides[noms[a]].common(solides[noms[b]]).Volume
    return total


def axe_propre_moteur(inertie):
    """Pour un cylindre aplati, l'axe de révolution porte la plus grande inertie propre."""
    valeurs, vecteurs = np.linalg.eigh(inertie)
    v = vecteurs[:, int(np.argmax(valeurs))]
    return v if v[2] >= 0 else -v


def ecart_rel(mesure_val, reference, echelle=None):
    e = np.max(np.abs(np.asarray(mesure_val) - np.asarray(reference)))
    return float(e / (echelle if echelle else np.max(np.abs(reference))))


def main():
    dossier = Path(sys.argv[1] if len(sys.argv) > 1 else
                   os.path.expanduser("~/drone-tools/resultats/assemblage"))
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / "assemblage_drone.step"
    exporter(chemin)
    print(f"STEP généré : {chemin} ({chemin.stat().st_size} octets)")

    th = theorie()
    doc, solides = relire_avec_noms(chemin)
    print("Solides relus par nom :", sorted(solides))
    manquants = set(th) - set(solides)
    if manquants:
        print("ÉCHEC : noms perdus à la relecture :", manquants)
        return 1

    compound = Part.read(str(chemin))
    print(f"Part.read : {len(compound.Solids)} solides (noms indisponibles par cette voie)")

    densites = {p["nom"]: p["densite"] for p in PIECES}
    mesures = {n: mesure(solides[n], densites[n]) for n in th}
    print(f"Volume commun entre pièces : {interferences(solides):.6g} mm3\n")

    print(f"{'pièce':<25}{'masse g mesurée':>17}{'théorie':>13}{'écart %':>12}{'centre mesuré mm':>32}{'écart max mm':>14}")
    for n in th:
        m, c, _ = mesures[n]
        print(f"{n:<25}{m * 1e3:>17.6f}{th[n][0] * 1e3:>13.6f}{100 * (m - th[n][0]) / th[n][0]:>12.2e}"
              f"{str(np.round(c, 4)):>32}{np.max(np.abs(c - th[n][1])):>14.2e}")

    m_th, g_th, i_th = composer([th[n][:3] for n in th])
    m_me, g_me, i_me = composer([mesures[n] for n in th])

    np.set_printoptions(precision=5, suppress=True, linewidth=120)
    print(f"\nMasse totale : mesurée {m_me * 1e3:.7f} g ; théorie {m_th * 1e3:.7f} g ; "
          f"écart {100 * (m_me - m_th) / m_th:.3e} %")
    print(f"CG mesuré  (mm) : {g_me}\nCG théorie (mm) : {g_th}\n"
          f"Écart CG max : {np.max(np.abs(g_me - g_th)):.3e} mm")
    print(f"\nInertie mesurée au CG (kg.mm2) :\n{i_me}\nInertie théorique au CG (kg.mm2) :\n{i_th}")
    print(f"Écart absolu max : {np.max(np.abs(i_me - i_th)):.3e} kg.mm2")

    print("\nÉcart relatif terme à terme sur l'inertie (%) :")
    with np.errstate(divide="ignore", invalid="ignore"):
        print(100 * (i_me - i_th) / i_th)

    # Axe et position des moteurs, deux informations à extraire pour le simulateur.
    print("\nMoteurs :")
    e_axe_max = 0.0
    for p in PIECES:
        if p["forme"] != "cylindre":
            continue
        n = p["nom"]
        axe_th = th[n][3] @ np.array([0.0, 0.0, 1.0])
        axe_me = axe_propre_moteur(mesures[n][2])
        angle = math.degrees(math.acos(min(1.0, abs(float(axe_th @ axe_me)))))
        e_axe_max = max(e_axe_max, angle)
        print(f"  {n}: position {np.round(mesures[n][1], 6)} (théorie {th[n][1]}), "
              f"axe {np.round(axe_me, 6)}, écart angulaire {angle:.2e} deg")

    e_m = abs(m_me - m_th) / m_th
    e_g = float(np.max(np.abs(g_me - g_th)) / np.max(np.abs(g_th)))
    e_i = ecart_rel(i_me, i_th)
    ok = max(e_m, e_g, e_i) <= SEUIL_REL and len(compound.Solids) == len(th)
    (dossier / "resultats.json").write_text(json.dumps({
        "masse_kg": {"mesure": m_me, "theorie": m_th},
        "cg_mm": {"mesure": g_me.tolist(), "theorie": g_th.tolist()},
        "inertie_kg_mm2": {"mesure": i_me.tolist(), "theorie": i_th.tolist()},
        "densites_kg_mm3": densites,
    }, indent=2))
    print(f"\nÉcarts relatifs : masse {e_m:.2e}, CG {e_g:.2e}, inertie {e_i:.2e} (seuil {SEUIL_REL:.0e})")
    print("Résultat :", "RÉUSSI" if ok else "ÉCHEC")
    App.closeDocument(doc.Name)
    return 0 if ok else 1


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    os._exit(code)
