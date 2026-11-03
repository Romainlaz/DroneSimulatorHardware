#!/usr/bin/env python3
"""Vol court piloté avec l'API MAVSDK, seconde voie à côté de pymavlink (test_minimal.py).

Depuis un shell où env.sh est chargé :
    python3 outillage/simulation/exemple_mavsdk.py
Code de sortie 0 si le vol s'est déroulé. Pas de vérification du journal ici : voir test_minimal.py.
"""
import argparse
import asyncio
import sys
import tempfile
from pathlib import Path

from mavsdk import System

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_minimal import Simulation, journal  # noqa: E402


async def premier(generateur, condition=lambda _: True):
    async for valeur in generateur:
        if condition(valeur):
            return valeur
    raise RuntimeError("flux de télémétrie terminé")


async def voler(altitude):
    drone = System()
    await drone.connect(system_address="udpin://0.0.0.0:14540")
    await premier(drone.core.connection_state(), lambda e: e.is_connected)
    journal("MAVSDK connecté")
    await premier(drone.telemetry.health(), lambda h: h.is_global_position_ok and h.is_home_position_ok)
    version = await drone.info.get_version()
    journal(f"PX4 {version.flight_sw_major}.{version.flight_sw_minor}.{version.flight_sw_patch}")
    await drone.action.set_takeoff_altitude(altitude)
    for _ in range(30):
        try:
            await drone.action.arm()
            break
        except Exception as e:  # EKF pas encore prêt
            journal(f"armement refusé : {e}")
            await asyncio.sleep(2)
    await drone.action.takeoff()
    await premier(drone.telemetry.position(), lambda p: p.relative_altitude_m > altitude - 0.3)
    p = await premier(drone.telemetry.position())
    journal(f"altitude relative : {p.relative_altitude_m:.2f} m")
    await asyncio.sleep(5)
    await drone.action.land()
    await premier(drone.telemetry.armed(), lambda a: not a)
    journal("posé et désarmé")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--altitude", type=float, default=2.5)
    ap.add_argument("--delai", type=float, default=150.0)
    args = ap.parse_args()
    # Options attendues par Simulation.
    args.vitesse, args.monde = 1.0, "default"
    with tempfile.TemporaryDirectory() as dossier:
        sim = Simulation(args, Path(dossier))
        sim.demarrer()
        try:
            asyncio.run(asyncio.wait_for(voler(args.altitude), args.delai))
            journal("REUSSITE MAVSDK")
            return 0
        except (asyncio.TimeoutError, RuntimeError) as e:
            journal(f"ECHEC MAVSDK : {e!r}")
            return 1
        finally:
            sim.arreter()


if __name__ == "__main__":
    sys.exit(main())
