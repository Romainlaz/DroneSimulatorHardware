#!/usr/bin/env python3
"""Lit l'historique de Cd d'un cas et le compare à la référence. Écrit resultat.json.

Usage : analyser.py <dossier_du_cas>
Référence à Re = 100 : voir NOTES.md.
"""
import json
import math
import pathlib
import re
import sys

CD_REF = 1.09          # Mittal 1999, arrondi ; Schiller-Naumann donne 1.0918 ; voir NOTES.md
CD_SN = 24 / 100 * (1 + 0.15 * 100 ** 0.687)


def lire_cd(cas):
    fichiers = sorted(cas.glob("postProcessing/forceCoeffs/*/coefficient*.dat"))
    if not fichiers:
        sys.exit(f"Pas de coefficient*.dat dans {cas}/postProcessing/forceCoeffs")
    colonnes, serie = None, []
    for ligne in fichiers[-1].read_text().splitlines():
        if ligne.startswith("#"):
            mots = ligne[1:].split()
            if "Cd" in mots:
                colonnes = mots
            continue
        if ligne.strip():
            v = ligne.split()
            serie.append((float(v[colonnes.index("Time")]), float(v[colonnes.index("Cd")])))
    return serie


def main():
    cas = pathlib.Path(sys.argv[1])
    serie = lire_cd(cas)
    cd = [c for _, c in serie]
    n = min(100, len(cd))
    moyenne = sum(cd[-n:]) / n
    amplitude = max(cd[-n:]) - min(cd[-n:])
    resultat = {
        "cas": cas.name,
        "iterations": int(serie[-1][0]),
        "Cd_final": round(cd[-1], 5),
        "Cd_moyen_100_dernieres": round(moyenne, 5),
        "amplitude_100_dernieres": float(f"{amplitude:.2e}"),
        "Cd_reference": CD_REF,
        "ecart_pct": round(100 * (cd[-1] - CD_REF) / CD_REF, 2),
        "Cd_schiller_naumann": round(CD_SN, 4),
        "ecart_schiller_naumann_pct": round(100 * (cd[-1] - CD_SN) / CD_SN, 2),
    }
    if not math.isfinite(cd[-1]):
        sys.exit("Cd non fini : calcul divergé")
    (cas / "resultat.json").write_text(json.dumps(resultat, indent=2) + "\n")
    print(json.dumps(resultat, indent=2))


if __name__ == "__main__":
    main()
