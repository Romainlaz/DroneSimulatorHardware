#!/usr/bin/env python3
"""Vol court piloté avec l'API MAVSDK, seconde voie à côté de pymavlink (test_minimal.py).

Écrit pour la liaison native de mavsdk >= 4 (Mavsdk -> first_autopilot -> plugins, appels bloquants),
incompatible avec l'ancienne API gRPC de mavsdk < 4.

Depuis un shell où env.sh est chargé :
    python3 outillage/simulation/exemple_mavsdk.py
Code de sortie 0 si le vol s'est déroulé. Pas de vérification du journal ici : voir test_minimal.py.
Sortie : ~/drone-tools/logs/mavsdk_<date>/px4.log
"""
import argparse
import os
import sys
import threading
import time
from pathlib import Path

from mavsdk import ComponentType, Configuration, Mavsdk
from mavsdk.plugins.action import Action
from mavsdk.plugins.info import Info
from mavsdk.plugins.telemetry import Telemetry

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_minimal import Simulation, journal  # noqa: E402


def attendre(condition, quoi, delai=90.0):
    """Interroge la télémétrie jusqu'à ce que la condition soit vraie. Les erreurs transitoires sont retentées."""
    limite = time.monotonic() + delai
    derniere = None
    while time.monotonic() < limite:
        try:
            if condition():
                return
        except Exception as e:  # télémétrie pas encore reçue
            derniere = e
        time.sleep(0.2)
    raise RuntimeError(f"délai dépassé : {quoi} (dernière erreur : {derniere!r})")


def voler(altitude):
    mavsdk = Mavsdk(Configuration.create_with_component_type(ComponentType.GROUND_STATION))
    resultat = mavsdk.add_any_connection("udpin://0.0.0.0:14540")
    journal(f"connexion : {resultat!r}")
    systeme = mavsdk.first_autopilot(120.0)
    if systeme is None:
        raise RuntimeError("aucun autopilote détecté")
    journal("MAVSDK connecté")
    action, telemetrie, info = Action(systeme), Telemetry(systeme), Info(systeme)

    attendre(lambda: telemetrie.health().is_global_position_ok and telemetrie.health().is_home_position_ok,
             "position globale et position d'origine")
    v = info.get_version()
    journal(f"PX4 {v.flight_sw_major}.{v.flight_sw_minor}.{v.flight_sw_patch}")
    action.set_takeoff_altitude(altitude)

    for _ in range(30):
        try:
            action.arm()
            break
        except Exception as e:  # EKF pas encore prêt
            journal(f"armement refusé : {e!r}")
            time.sleep(2)
    else:
        raise RuntimeError("armement refusé jusqu'au délai")
    journal("armé")
    action.takeoff()
    attendre(lambda: telemetrie.position().relative_altitude_m > altitude - 0.3, "altitude de décollage")
    journal(f"altitude relative : {telemetrie.position().relative_altitude_m:.2f} m")
    time.sleep(5)
    journal(f"altitude relative après 5 s : {telemetrie.position().relative_altitude_m:.2f} m")
    action.land()
    attendre(lambda: not telemetrie.armed(), "désarmement")
    journal("posé et désarmé")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--altitude", type=float, default=2.5)
    ap.add_argument("--delai", type=float, default=150.0)
    args = ap.parse_args()
    # Options attendues par Simulation.
    args.vitesse, args.monde = 1.0, "default"
    dossier = Path.home() / "drone-tools/logs" / time.strftime("mavsdk_%Y%m%d_%H%M%S")
    dossier.mkdir(parents=True)
    sim = Simulation(args, dossier)
    sim.demarrer()

    # Les appels MAVSDK bloquent dans la bibliothèque C : le délai global se tient depuis un autre fil.
    issue = {}

    def vol():
        try:
            voler(args.altitude)
            issue["ok"] = True
        except Exception as e:
            issue["erreur"] = repr(e)

    fil = threading.Thread(target=vol, daemon=True)
    fil.start()
    fil.join(args.delai)
    sim.arreter()
    if issue.get("ok"):
        journal(f"REUSSITE MAVSDK : {dossier}")
        code = 0
    else:
        journal(f"ECHEC MAVSDK : {issue.get('erreur', 'délai global dépassé')} ({dossier})")
        code = 1
    sys.stdout.flush()
    os._exit(code)  # un appel MAVSDK peut rester bloqué dans le fil de vol


if __name__ == "__main__":
    main()
