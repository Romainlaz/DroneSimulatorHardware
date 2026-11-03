#!/usr/bin/env python3
"""Test résistance : poutre console maillée par Gmsh, résolue par CalculiX.

Compare flèche et contrainte à Euler-Bernoulli, sans aucune interface.
Lancement : drone-cae-python tests/test_poutre_calculix.py [dossier_sortie]
Unités : mm, N, MPa. Encastrement en x=0, effort tranchant -z réparti sur la face x=L.

La contrainte « brute » au droit de l'encastrement contient une singularité
(blocage de l'effet Poisson) : elle ne converge pas et doit être lue comme telle.
La contrainte « extrapolée » vient d'un ajustement linéaire de SXX en fibre
supérieure, entre 25 % et 75 % de la longueur, prolongé jusqu'à x=0.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import gmsh
import numpy as np

L, B, H = 200.0, 20.0, 10.0  # longueur x, largeur y, hauteur z (mm)
E, NU = 70000.0, 0.33        # aluminium (MPa, -)
F = 50.0                     # effort total vers -z (N)

# Réussite : flèche à 2 %, contrainte extrapolée à 2 % (maillages quadratiques les plus fins).
SEUIL_FLECHE_PCT = 2.0
SEUIL_CONTRAINTE_PCT = 2.0

CAS = [  # nom, ordre des éléments, taille de maille (mm)
    ("C3D4_h5", 1, 5.0),
    ("C3D10_h10", 2, 10.0),
    ("C3D10_h5", 2, 5.0),
    ("C3D10_h2.5", 2, 2.5),
]


def theorie():
    i = B * H**3 / 12.0
    g = E / (2 * (1 + NU))
    fleche_eb = F * L**3 / (3 * E * i)
    fleche_cisaillement = F * L / ((5.0 / 6.0) * g * B * H)
    return {
        "I_mm4": i,
        "fleche_EB_mm": fleche_eb,
        "fleche_Timoshenko_mm": fleche_eb + fleche_cisaillement,
        "sigma_encastrement_MPa": F * L * (H / 2) / i,
        "sigma_mi_longueur_MPa": F * (L / 2) * (H / 2) / i,
    }


def mailler(ordre, taille):
    """Maille la poutre ; renvoie {id: xyz}, connectivité (ordre Gmsh), type d'élément."""
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setNumber("General.NumThreads", 4)
        gmsh.model.add("poutre")
        gmsh.model.occ.addBox(0, 0, 0, L, B, H)
        gmsh.model.occ.synchronize()
        gmsh.option.setNumber("Mesh.MeshSizeMax", taille)
        gmsh.option.setNumber("Mesh.MeshSizeMin", taille / 2)
        gmsh.option.setNumber("Mesh.ElementOrder", ordre)
        gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)
        gmsh.model.mesh.generate(3)
        tags, coords, _ = gmsh.model.mesh.getNodes()
        noeuds = {int(t): coords[3 * i: 3 * i + 3].copy() for i, t in enumerate(tags)}
        type_tet = 4 if ordre == 1 else 11
        _, conn = gmsh.model.mesh.getElementsByType(type_tet)
        n = 4 if ordre == 1 else 10
        return noeuds, conn.astype(int).reshape(-1, n), gmsh.__version__ if hasattr(gmsh, "__version__") else gmsh.GMSH_API_VERSION
    finally:
        gmsh.finalize()


def vers_ccx(conn):
    """Ordre Gmsh -> ordre CalculiX pour C3D10 : les nœuds 9 et 10 sont permutés."""
    if conn.shape[1] == 4:
        return conn
    return conn[:, [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]]


def verifier_ordre(noeuds, conn_ccx):
    """Vérifie sur la géométrie que chaque nœud milieu est bien au milieu de son arête ccx."""
    if conn_ccx.shape[1] == 4:
        return
    aretes = {4: (0, 1), 5: (1, 2), 6: (2, 0), 7: (0, 3), 8: (1, 3), 9: (2, 3)}
    for e in conn_ccx[:: max(1, len(conn_ccx) // 200)]:
        for m, (a, b) in aretes.items():
            ecart = np.linalg.norm(noeuds[e[m]] - 0.5 * (noeuds[e[a]] + noeuds[e[b]]))
            if ecart > 1e-6:
                raise RuntimeError(f"Ordre des nœuds C3D10 incorrect (écart {ecart})")


def efforts_nodaux(noeuds, conn):
    """Forces équivalentes à une traction uniforme sur la face x=L.

    Sur une face triangulaire : T6 -> sommets 0, milieux A/3 ; T3 -> sommets A/3.
    La somme vaut exactement F, ce qui est contrôlé plus bas.
    """
    if conn.shape[1] == 4:
        faces = [([0, 1, 2], []), ([0, 1, 3], []), ([0, 2, 3], []), ([1, 2, 3], [])]
    else:
        faces = [([0, 1, 2], [4, 5, 6]), ([0, 1, 3], [4, 7, 8]),
                 ([0, 2, 3], [6, 7, 9]), ([1, 2, 3], [5, 8, 9])]
    forces = {}
    aire_totale = 0.0
    for e in conn:  # conn en ordre CalculiX
        for sommets, milieux in faces:
            ids = [e[s] for s in sommets]
            if all(abs(noeuds[i][0] - L) < 1e-7 for i in ids):
                p = [noeuds[i] for i in ids]
                aire = 0.5 * np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0]))
                aire_totale += aire
                cibles = [e[m] for m in milieux] if milieux else ids
                for c in cibles:
                    forces[c] = forces.get(c, 0.0) + aire / 3.0
    return {k: -F * v / aire_totale for k, v in forces.items()}, aire_totale


def ecrire_inp(chemin, noeuds, conn, forces):
    type_el = "C3D4" if conn.shape[1] == 4 else "C3D10"
    encastres = [i for i, p in noeuds.items() if abs(p[0]) < 1e-7]
    with open(chemin, "w") as f:
        f.write("*NODE, NSET=NALL\n")
        for i, p in noeuds.items():
            f.write(f"{i}, {p[0]:.12g}, {p[1]:.12g}, {p[2]:.12g}\n")
        f.write(f"*ELEMENT, TYPE={type_el}, ELSET=EALL\n")
        for k, e in enumerate(conn, 1):
            # CalculiX limite les lignes : une ligne de suite pour C3D10.
            valeurs = [str(k)] + [str(int(x)) for x in e]
            if len(valeurs) > 8:
                f.write(", ".join(valeurs[:8]) + ",\n" + ", ".join(valeurs[8:]) + "\n")
            else:
                f.write(", ".join(valeurs) + "\n")
        f.write("*NSET, NSET=ENCASTRE\n")
        for k in range(0, len(encastres), 10):
            f.write(", ".join(map(str, encastres[k:k + 10])) + ",\n")
        f.write(f"*MATERIAL, NAME=ALU\n*ELASTIC\n{E}, {NU}\n")
        f.write("*SOLID SECTION, ELSET=EALL, MATERIAL=ALU\n")
        f.write("*BOUNDARY\nENCASTRE, 1, 3, 0.\n")
        f.write("*STEP\n*STATIC\n*CLOAD\n")
        for i, v in forces.items():
            f.write(f"{i}, 3, {v:.12g}\n")
        f.write("*NODE FILE\nU\n*EL FILE\nS\n*END STEP\n")


def lire_frd(chemin):
    """Lit les blocs DISP et STRESS du .frd (ASCII, colonnes fixes)."""
    resultats = {}
    bloc = None
    for ligne in open(chemin):
        if ligne.startswith(" -4"):
            nom = ligne.split()[1]
            bloc = nom if nom in ("DISP", "STRESS") else None
            if bloc:
                resultats[bloc] = {}
        elif ligne.startswith(" -3"):
            bloc = None
        elif bloc and ligne.startswith(" -1"):
            nid = int(ligne[3:13])
            n = (len(ligne.rstrip("\n")) - 13) // 12
            resultats[bloc][nid] = [float(ligne[13 + 12 * k: 25 + 12 * k]) for k in range(n)]
    return resultats


def von_mises(s):
    sxx, syy, szz, sxy, syz, szx = s
    return np.sqrt(0.5 * ((sxx - syy)**2 + (syy - szz)**2 + (szz - sxx)**2)
                   + 3 * (sxy**2 + syz**2 + szx**2))


def resoudre(nom, ordre, taille, dossier):
    noeuds, conn, _ = mailler(ordre, taille)
    conn = vers_ccx(conn)
    verifier_ordre(noeuds, conn)
    forces, aire = efforts_nodaux(noeuds, conn)
    if abs(aire - B * H) > 1e-6 or abs(sum(forces.values()) + F) > 1e-6:
        raise RuntimeError(f"Chargement incohérent : aire={aire}, somme={sum(forces.values())}")
    travail = Path(dossier) / nom
    travail.mkdir(parents=True, exist_ok=True)
    ecrire_inp(travail / "poutre.inp", noeuds, conn, forces)
    env = dict(os.environ, OMP_NUM_THREADS="4", CCX_NPROC_STIFFNESS="4",
               CCX_NPROC_EQUATION_SOLVER="4", CCX_NPROC_RESULTS="4")
    proc = subprocess.run(["ccx", "-i", "poutre"], cwd=travail, env=env,
                          capture_output=True, text=True)
    (travail / "ccx.log").write_text(proc.stdout + proc.stderr)
    if proc.returncode != 0 or "*ERROR" in proc.stdout or not (travail / "poutre.frd").exists():
        raise RuntimeError(f"CalculiX a échoué (code {proc.returncode}), voir {travail/'ccx.log'}")
    r = lire_frd(travail / "poutre.frd")
    if not r.get("DISP") or not r.get("STRESS"):
        raise RuntimeError("Blocs DISP/STRESS absents du .frd")

    ids_bout = [i for i, p in noeuds.items() if abs(p[0] - L) < 1e-7]
    uz = np.array([r["DISP"][i][2] for i in ids_bout])
    ids = list(r["STRESS"])
    x = np.array([noeuds[i][0] for i in ids])
    z = np.array([noeuds[i][2] for i in ids])
    sxx = np.array([r["STRESS"][i][0] for i in ids])
    vm = np.array([von_mises(r["STRESS"][i][:6]) for i in ids])
    haut = (np.abs(z - H) < 1e-7) & (x > 0.25 * L) & (x < 0.75 * L)
    pente, origine = np.polyfit(x[haut], sxx[haut], 1)
    return {
        "cas": nom, "noeuds": len(noeuds), "elements": len(conn),
        "fleche_moy_mm": float(-uz.mean()),
        "sigma_xx_max_brut_MPa": float(sxx.max()),
        "von_mises_max_brut_MPa": float(vm.max()),
        "sigma_extrapole_encastrement_MPa": float(origine),
        "sigma_mi_longueur_MPa": float(origine + pente * L / 2),
        "points_ajustement": int(haut.sum()),
    }


def pct(v, ref):
    return 100.0 * (v - ref) / ref


def main():
    dossier = Path(sys.argv[1] if len(sys.argv) > 1 else
                   os.path.expanduser("~/drone-tools/resultats/poutre"))
    dossier.mkdir(parents=True, exist_ok=True)
    t = theorie()
    print(f"Poutre {L}x{B}x{H} mm, E={E} MPa, nu={NU}, F={F} N")
    print(f"Théorie : flèche EB {t['fleche_EB_mm']:.5f} mm, avec cisaillement "
          f"{t['fleche_Timoshenko_mm']:.5f} mm ; sigma encastrement "
          f"{t['sigma_encastrement_MPa']:.3f} MPa ; sigma mi-longueur "
          f"{t['sigma_mi_longueur_MPa']:.3f} MPa\n")
    print(f"{'cas':<12}{'noeuds':>8}{'élém':>8}{'flèche mm':>11}{'/EB %':>8}{'/Timo %':>9}"
          f"{'SXX brut':>10}{'%':>8}{'VM brut':>9}{'SXX extr':>10}{'%':>8}{'SXX L/2':>9}{'%':>7}")
    res = []
    for nom, ordre, taille in CAS:
        r = resoudre(nom, ordre, taille, dossier)
        res.append(r)
        print(f"{nom:<12}{r['noeuds']:>8}{r['elements']:>8}{r['fleche_moy_mm']:>11.5f}"
              f"{pct(r['fleche_moy_mm'], t['fleche_EB_mm']):>8.2f}"
              f"{pct(r['fleche_moy_mm'], t['fleche_Timoshenko_mm']):>9.2f}"
              f"{r['sigma_xx_max_brut_MPa']:>10.3f}"
              f"{pct(r['sigma_xx_max_brut_MPa'], t['sigma_encastrement_MPa']):>8.2f}"
              f"{r['von_mises_max_brut_MPa']:>9.3f}"
              f"{r['sigma_extrapole_encastrement_MPa']:>10.3f}"
              f"{pct(r['sigma_extrapole_encastrement_MPa'], t['sigma_encastrement_MPa']):>8.2f}"
              f"{r['sigma_mi_longueur_MPa']:>9.3f}"
              f"{pct(r['sigma_mi_longueur_MPa'], t['sigma_mi_longueur_MPa']):>7.2f}")
    (dossier / "resultats.json").write_text(json.dumps({"theorie": t, "cas": res}, indent=2))
    fin = res[-1]
    e_f = abs(pct(fin["fleche_moy_mm"], t["fleche_EB_mm"]))
    e_s = abs(pct(fin["sigma_extrapole_encastrement_MPa"], t["sigma_encastrement_MPa"]))
    ok = e_f <= SEUIL_FLECHE_PCT and e_s <= SEUIL_CONTRAINTE_PCT
    print(f"\nMaillage le plus fin {fin['cas']} : écart flèche {e_f:.3f} % (seuil {SEUIL_FLECHE_PCT} %), "
          f"écart contrainte extrapolée {e_s:.3f} % (seuil {SEUIL_CONTRAINTE_PCT} %)")
    print("Résultat :", "RÉUSSI" if ok else "ÉCHEC")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
