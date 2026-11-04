#!/usr/bin/env python3
"""Vol de contrôle sans affichage : PX4 SITL + Gazebo, piloté en MAVLink (pymavlink).

Séquence : démarrage -> armement -> décollage -> stationnaire -> atterrissage -> désarmement,
puis vérification du journal .ulg et mesure de la fréquence et du facteur temps réel.

Lancer via test_minimal.sh, qui charge l'environnement. Code de sortie : 0 si tous les critères
passent, 1 sinon. Résultat détaillé : <dossier du run>/resultat.json

Isolation : GZ_PARTITION propre à chaque lancement, pour ne pas s'attacher au Gazebo d'un autre
processus (px4-rc.gzsim réutilise tout monde qu'il trouve sur le réseau gz-transport).
"""
import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

import numpy as np
import psutil
from pymavlink import mavutil
from pyulog import ULog

ON_GROUND, IN_AIR, TAKEOFF, LANDING = 1, 2, 3, 4
AUTOSTART_X500 = "4001"
TOPICS_REQUIS = [
    "vehicle_local_position", "vehicle_status", "vehicle_land_detected",
    "sensor_combined", "actuator_outputs", "vehicle_attitude",
]


def journal(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


class EchecVol(RuntimeError):
    pass


class StatsGazebo(threading.Thread):
    """Lit /world/<monde>/stats : temps simulé, temps réel et nombre d'itérations de physique."""
    MOTIF = re.compile(
        r"sim_time\s*\{(?P<sim>[^}]*)\}.*?real_time\s*\{(?P<reel>[^}]*)\}.*?iterations:\s*(?P<it>\d+)",
        re.S)

    def __init__(self, env, monde):
        super().__init__(daemon=True)
        self.echantillons = []  # (horloge murale, temps simulé, temps réel gz, itérations)
        self.proc = subprocess.Popen(
            ["stdbuf", "-oL", "gz", "topic", "-e", "-t", f"/world/{monde}/stats"],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
            start_new_session=True)

    @staticmethod
    def _duree(bloc):
        s = re.search(r"sec:\s*(\d+)", bloc.replace("nsec", "nnn"))
        n = re.search(r"nsec:\s*(\d+)", bloc)
        return (int(s.group(1)) if s else 0) + (int(n.group(1)) * 1e-9 if n else 0.0)

    def run(self):
        tampon = ""
        for ligne in self.proc.stdout:
            tampon += ligne
            m = self.MOTIF.search(tampon)
            if m:
                self.echantillons.append((time.monotonic(), self._duree(m.group("sim")),
                                          self._duree(m.group("reel")), int(m.group("it"))))
                tampon = tampon[m.end():]

    def arreter(self):
        try:
            os.killpg(self.proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass

    def bilan(self, debut, fin):
        """Facteur temps réel et fréquence de physique entre deux instants muraux."""
        e = [x for x in self.echantillons if debut <= x[0] <= fin]
        if len(e) < 2:
            return None
        duree_murale = e[-1][0] - e[0][0]
        duree_sim = e[-1][1] - e[0][1]
        pas = e[-1][3] - e[0][3]
        if duree_murale <= 0 or pas <= 0:
            return None
        return {
            "echantillons": len(e),
            "duree_murale_s": round(duree_murale, 2),
            "duree_simulee_s": round(duree_sim, 2),
            "iterations_physique": pas,
            "pas_simule_ms": round(1000 * duree_sim / pas, 3),
            "facteur_temps_reel": round(duree_sim / duree_murale, 3),
            "frequence_physique_reelle_hz": round(pas / duree_murale, 1),
        }


class Simulation:
    """Lance et arrête proprement PX4 et le gz-server qu'il démarre."""

    def __init__(self, args, dossier):
        self.args = args
        self.dossier = dossier
        px4_dir = Path(os.environ["PX4_DIR"])
        self.build = px4_dir / "build" / "px4_sitl_default"
        self.rootfs = self.build / "rootfs"
        self.env = dict(os.environ)
        for var in ("DISPLAY", "WAYLAND_DISPLAY", "XAUTHORITY"):  # preuve du « sans affichage »
            self.env.pop(var, None)
        self.env.update({
            "HEADLESS": "1",
            "PX4_SYS_AUTOSTART": AUTOSTART_X500,
            "PX4_SIM_MODEL": "gz_x500",
            "PX4_GZ_WORLD": args.monde,
            "GZ_IP": "127.0.0.1",
            "GZ_PARTITION": f"testmin_{os.getpid()}",
        })
        if args.vitesse != 1:
            self.env["PX4_SIM_SPEED_FACTOR"] = str(args.vitesse)
        self.proc = None
        self.fichier_log = None

    def demarrer(self):
        # Paramètres remis à zéro : un run ne dépend pas du précédent.
        for f in self.rootfs.glob("parameters*.bson"):
            f.unlink()
        self.fichier_log = open(self.dossier / "px4.log", "w")
        self.proc = subprocess.Popen(
            [str(self.build / "bin" / "px4"), "-d"],
            cwd=self.rootfs, env=self.env, stdin=subprocess.DEVNULL,
            stdout=self.fichier_log, stderr=subprocess.STDOUT, start_new_session=True)

    def processus(self):
        """Tous les processus du groupe (px4, gz-server et enfants)."""
        groupe = []
        for p in psutil.process_iter(["pid"]):
            try:
                if os.getpgid(p.pid) == self.proc.pid:
                    groupe.append(p)
            except (ProcessLookupError, psutil.Error):
                pass
        return groupe

    def temps_cpu(self):
        total = 0.0
        for p in self.processus():
            try:
                t = p.cpu_times()
                total += t.user + t.system
            except psutil.Error:
                pass
        return total

    def arreter(self):
        if self.proc is None:
            return
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(self.proc.pid, sig)
            except ProcessLookupError:
                break
            time.sleep(3)
        self.proc.wait(timeout=10)
        if self.fichier_log:
            self.fichier_log.close()

    def altitude_gazebo(self):
        """Vérité terrain : position du modèle lue directement dans Gazebo, sans passer par PX4."""
        r = subprocess.run(["gz", "model", "-m", "x500_0", "-p"], env=self.env,
                           capture_output=True, text=True, timeout=20)
        m = re.search(r"Pose \[ XYZ \(m\) \] \[ RPY \(rad\) \]:\s*\[([^\]]+)\]", r.stdout)
        if not m:
            raise EchecVol(f"pose Gazebo illisible : {r.stdout!r} {r.stderr!r}")
        return [float(v) for v in m.group(1).split()]


class Vol:
    """Pilotage MAVLink. Les durées de vol sont en temps simulé (time_boot_ms de PX4)."""

    def __init__(self, port, timeout_mur):
        self.m = mavutil.mavlink_connection(f"udpin:127.0.0.1:{port}", source_system=245)
        self.timeout = timeout_mur
        self.t_ms = 0
        self.alt_rel = None
        self.etat_sol = None
        self.arme = False
        self.textes = []
        self.t_hb = 0.0

    def battement(self):
        """Heartbeat station sol à 1 Hz : sans lui, PX4 refuse d'armer (« No connection to the GCS »)."""
        if time.monotonic() - self.t_hb >= 1.0:
            self.m.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_GCS,
                                      mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0)
            self.t_hb = time.monotonic()

    def pomper(self, duree=0.05):
        fin = time.monotonic() + duree
        while True:
            self.battement()
            restant = fin - time.monotonic()
            msg = self.m.recv_match(blocking=restant > 0, timeout=max(restant, 0.001))
            if msg is None:
                if restant <= 0:
                    return
                continue
            t = msg.get_type()
            if t == "GLOBAL_POSITION_INT":
                self.t_ms, self.alt_rel = msg.time_boot_ms, msg.relative_alt / 1000.0
            elif t == "EXTENDED_SYS_STATE":
                self.etat_sol = msg.landed_state
            elif t == "HEARTBEAT" and msg.get_srcSystem() == self.m.target_system:
                self.arme = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
            elif t == "STATUSTEXT":
                self.textes.append(msg.text)
                journal(f"  PX4 : {msg.text}")

    def attendre(self, condition, quoi):
        limite = time.monotonic() + self.timeout
        while time.monotonic() < limite:
            self.pomper()
            if condition():
                return
        raise EchecVol(f"délai dépassé : {quoi}")

    def commande(self, cmd, *p, essais=5):
        p = list(p) + [0.0] * (7 - len(p))
        for _ in range(essais):
            self.battement()
            self.m.mav.command_long_send(self.m.target_system, self.m.target_component, cmd, 0, *p)
            ack = self.m.recv_match(type="COMMAND_ACK", blocking=True, timeout=2)
            if ack and ack.command == cmd:
                return ack.result
        return None

    def connecter(self):
        hb = self.m.wait_heartbeat(timeout=self.timeout)
        if hb is None:
            raise EchecVol("aucun heartbeat MAVLink")
        intervalles = {
            mavutil.mavlink.MAVLINK_MSG_ID_EXTENDED_SYS_STATE: 200_000,
            mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT: 100_000,
        }
        for msg_id, us in intervalles.items():
            self.commande(mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL, msg_id, us)
        self.attendre(lambda: self.alt_rel is not None and self.etat_sol is not None,
                      "position et état au sol")

    def regler_altitude_decollage(self, alt):
        for _ in range(10):
            self.m.mav.param_set_send(self.m.target_system, self.m.target_component,
                                      b"MIS_TAKEOFF_ALT", float(alt),
                                      mavutil.mavlink.MAV_PARAM_TYPE_REAL32)
            r = self.m.recv_match(type="PARAM_VALUE", blocking=True, timeout=2)
            if r and r.param_id == "MIS_TAKEOFF_ALT" and abs(r.param_value - alt) < 0.01:
                return
        raise EchecVol("MIS_TAKEOFF_ALT non réglé")

    def armer_et_decoller(self):
        limite = time.monotonic() + self.timeout
        while time.monotonic() < limite:
            r = self.commande(mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 1.0)
            self.pomper(1.0)
            if r == mavutil.mavlink.MAV_RESULT_ACCEPTED and self.arme:
                break
            time.sleep(1)  # EKF pas encore prêt : on réessaie
        else:
            raise EchecVol("armement refusé jusqu'au délai")
        nan = float("nan")
        r = self.commande(mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, -1.0, 0, 0, nan, nan, nan, nan)
        if r != mavutil.mavlink.MAV_RESULT_ACCEPTED:
            raise EchecVol(f"décollage refusé : {r}")

    def stationnaire(self, duree_sim):
        t0 = self.t_ms
        limite = time.monotonic() + self.timeout
        while self.t_ms - t0 < duree_sim * 1000:
            self.pomper()
            if time.monotonic() > limite:
                raise EchecVol("stationnaire : temps simulé bloqué")

    def atterrir(self):
        r = self.commande(mavutil.mavlink.MAV_CMD_NAV_LAND)
        if r != mavutil.mavlink.MAV_RESULT_ACCEPTED:
            raise EchecVol(f"atterrissage refusé : {r}")
        self.attendre(lambda: self.etat_sol == ON_GROUND and not self.arme,
                      "au sol et désarmé")


def version_px4(code):
    """ver_sw_release = 0xMMmmppTT ; TT = 0xFF pour une version finale."""
    if code is None:
        return None
    return f"{code >> 24 & 0xFF}.{code >> 16 & 0xFF}.{code >> 8 & 0xFF} (type {code & 0xFF:#x})"


def verite_journal(u, t, z, t0, t1):
    """Palier comparé à vehicle_local_position_groundtruth, publié par gz_bridge et journalisé par PX4.

    Bien plus dense que « gz model » (un point par seconde au mieux) : c'est la mesure à regarder pour
    juger le vol. Purement informatif : n'entre dans aucun critère de réussite.
    """
    try:
        g = u.get_dataset("vehicle_local_position_groundtruth").data
    except (IndexError, KeyError, ValueError):
        return None
    zg = np.interp(t, g["timestamp"] / 1e6, -g["z"]) - float(-g["z"][0])
    pal = (t >= t0) & (t <= t1)
    err = z[pal] - float(z[0]) - zg[pal]
    return {
        "hauteur_moy_m": round(float(zg[pal].mean()), 3),
        "hauteur_ecart_type_m": round(float(zg[pal].std()), 4),
        "hauteur_min_m": round(float(zg[pal].min()), 3),
        "hauteur_max_m": round(float(zg[pal].max()), 3),
        "erreur_estimation_moy_m": round(float(err.mean()), 3),
        "erreur_estimation_max_abs_m": round(float(np.abs(err).max()), 3),
    }


def analyser_ulog(chemin, alt_cible, t_stat_debut_s=None):
    """Lit le .ulg, indépendamment de la télémétrie, et renvoie mesures et critères."""
    u = ULog(str(chemin))
    noms = {d.name for d in u.data_list}
    res = {"fichier": str(chemin), "taille_octets": chemin.stat().st_size,
           "duree_journal_s": round((u.last_timestamp - u.start_timestamp) / 1e6, 2),
           "corrompu": bool(u.file_corruption),
           "pertes_ms": sum(d.duration for d in u.dropouts),
           "nb_topics": len(noms),
           "topics_manquants": [t for t in TOPICS_REQUIS if t not in noms],
           "version_px4": version_px4(u.msg_info_dict.get("ver_sw_release")),
           "commit_px4": u.msg_info_dict.get("ver_sw"),
           "materiel": u.msg_info_dict.get("ver_hw"),
           "autostart": u.initial_parameters.get("SYS_AUTOSTART"),
           "avertissements": [m.message for m in u.logged_messages if m.log_level_str() in ("ERROR", "CRITICAL", "EMERGENCY", "ALERT")][:15]}
    if res["topics_manquants"]:
        return res

    def donnees(nom, i=0):
        return u.get_dataset(nom, i).data

    pos = donnees("vehicle_local_position")
    t, z = pos["timestamp"] / 1e6, -pos["z"]
    z_rel = z - np.median(z[t < t[0] + 2])
    land = donnees("vehicle_land_detected")
    t_l, posed = land["timestamp"] / 1e6, land["landed"]
    en_vol = np.where(posed == 0)[0]
    res["altitude_max_m"] = round(float(z_rel.max()), 3)
    if len(en_vol):
        t_decol, t_pose = t_l[en_vol[0]], t_l[en_vol[-1]]
        res["duree_en_vol_s"] = round(float(t_pose - t_decol), 2)
        res["pose_en_fin_de_journal"] = bool(posed[-1])
        # Stationnaire : dans le palier à ±0,5 m de la cible, hors 5 s de stabilisation
        dans = np.where((np.abs(z_rel - alt_cible) < 0.5) & (t > t_decol) & (t < t_pose))[0]
        if len(dans):
            t0, t1 = t[dans[0]] + 5.0, t[dans[-1]] - 1.0
            pal = (t >= t0) & (t <= t1)
            if pal.sum() > 10:
                x, y = pos["x"][pal], pos["y"][pal]
                res["verite_journal"] = verite_journal(u, t, z, t0, t1)
                res["stationnaire"] = {
                    "duree_s": round(float(t1 - t0), 2),
                    "altitude_moy_m": round(float(z_rel[pal].mean()), 3),
                    "altitude_ecart_type_m": round(float(z_rel[pal].std()), 4),
                    "derive_horizontale_max_m": round(float(np.hypot(x - x.mean(), y - y.mean()).max()), 4),
                }
    st = donnees("vehicle_status")
    res["arme_vu"] = bool((st["arming_state"] == 2).any())
    res["desarme_en_fin"] = bool(st["arming_state"][-1] != 2)

    def frequence(nom):
        d = donnees(nom)["timestamp"]
        return round((len(d) - 1) / ((d[-1] - d[0]) / 1e6), 1) if len(d) > 1 else None

    # Trous dans le flux IMU (en temps simulé) : indicateur de fidélité, très sensible à la charge CPU.
    dt_imu = np.diff(donnees("sensor_combined")["timestamp"]) / 1e3
    res["imu_ecarts_ms"] = {
        "attendu": 4.0, "mediane": round(float(np.median(dt_imu)), 2),
        "p99": round(float(np.percentile(dt_imu, 99)), 1), "max": round(float(dt_imu.max()), 1),
        "part_au_dela_de_6ms": round(float((dt_imu > 6).mean()), 4),
        "nb_au_dela_de_20ms": int((dt_imu > 20).sum()),
    }
    # Altitude estimée une fois posé : l'écart à zéro mesure la dérive de l'estimateur pendant le vol.
    res["altitude_estimee_fin_m"] = round(float(z_rel[-1]), 3)

    sor = donnees("actuator_outputs")
    actifs = sor["output[0]"] > 0
    res["frequences_journal_hz_temps_simule"] = {
        n: frequence(n) for n in ("sensor_combined", "vehicle_attitude", "vehicle_local_position", "actuator_outputs")}
    res["sortie_moteur_max"] = round(float(sor["output[0]"][actifs].max()), 1) if actifs.any() else 0.0
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--altitude", type=float, default=3.0, help="altitude de décollage (m)")
    ap.add_argument("--stationnaire", type=float, default=20.0, help="durée de stationnaire, en temps simulé (s)")
    ap.add_argument("--vitesse", type=float, default=1.0, help="PX4_SIM_SPEED_FACTOR demandé")
    ap.add_argument("--monde", default="default")
    ap.add_argument("--attente", type=float, default=0.0, help="attente au sol avant armement (s murales)")
    ap.add_argument("--nice", type=int, default=0, help="priorité de la simulation (une valeur > 0 dégrade le flux IMU sur machine chargée)")
    ap.add_argument("--points", type=int, default=5, help="lectures « gz model » pendant le stationnaire (0 : aucune, vol de diagnostic, critère Gazebo alors en échec)")
    ap.add_argument("--delai", type=float, default=180.0, help="délai mural par étape (s)")
    ap.add_argument("--sortie", default=str(Path.home() / "drone-tools/logs"))
    args = ap.parse_args()

    if "PX4_DIR" not in os.environ:
        sys.exit("Environnement absent : lancer via test_minimal.sh")
    os.nice(args.nice)
    dossier = Path(args.sortie) / time.strftime("test_%Y%m%d_%H%M%S")
    dossier.mkdir(parents=True)
    resultat = {"args": vars(args), "charge_machine_debut": os.getloadavg()[0],
                "uptime_avant": os.getloadavg(),
                "criteres": {}, "gazebo_verite": {}}
    sim = Simulation(args, dossier)
    stats = None
    journal(f"Run dans {dossier} (partition {sim.env['GZ_PARTITION']}, DISPLAY absent)")
    log_avant = set(sim.rootfs.glob("log/*/*.ulg"))
    t_lancement = time.monotonic()
    try:
        sim.demarrer()
        vol = Vol(14540, args.delai)
        vol.connecter()
        # Après la connexion : lancé avant que le monde existe, « gz topic -e » s'arrête aussitôt.
        stats = StatsGazebo(sim.env, args.monde)
        stats.start()
        resultat["demarrage_jusqu_a_mavlink_s"] = round(time.monotonic() - t_lancement, 1)
        journal(f"MAVLink prêt en {resultat['demarrage_jusqu_a_mavlink_s']} s")
        vol.regler_altitude_decollage(args.altitude)

        z_sol = sim.altitude_gazebo()
        resultat["gazebo_verite"]["avant_decollage_xyz"] = z_sol[:3]
        if args.attente > 0:
            journal(f"Attente de {args.attente} s avant armement")
            limite = time.monotonic() + args.attente
            while time.monotonic() < limite:
                vol.pomper(0.5)
        cpu0, t0 = sim.temps_cpu(), time.monotonic()
        psutil.cpu_percent()  # démarre la mesure de la charge machine

        journal("Armement et décollage")
        vol.armer_et_decoller()
        vol.attendre(lambda: vol.alt_rel is not None and vol.alt_rel > args.altitude - 0.3,
                     "altitude de décollage")
        journal(f"Altitude atteinte : {vol.alt_rel:.2f} m (télémétrie)")

        vol.pomper(2.0)
        journal(f"Stationnaire {args.stationnaire} s simulées")
        t_h0 = time.monotonic()
        # Vérité terrain Gazebo comparée à l'altitude estimée par PX4, à plusieurs instants.
        paires = []
        if args.points <= 0:
            vol.stationnaire(args.stationnaire)
        for _ in range(max(args.points, 0)):
            vol.stationnaire(args.stationnaire / args.points)
            vol.pomper(0.2)
            paires.append((round(sim.altitude_gazebo()[2] - z_sol[2], 3), round(vol.alt_rel, 3)))
        t_h1 = time.monotonic()
        verite = [p[0] for p in paires] or [float("nan")]
        resultat["gazebo_verite"]["stationnaire_hauteur_verite_estimee_m"] = paires
        resultat["gazebo_verite"]["stationnaire_hauteur_moyenne_m"] = round(float(np.mean(verite)), 3)
        resultat["gazebo_verite"]["ecart_estimation_moins_verite_m"] = round(float(np.mean([p[1] - p[0] for p in paires] or [float("nan")])), 3)
        journal(f"Hauteur Gazebo en stationnaire (moyenne de {len(paires)}) : {np.mean(verite):.2f} m")

        journal("Atterrissage")
        vol.atterrir()
        t1, cpu1 = time.monotonic(), sim.temps_cpu()
        time.sleep(3)  # fermeture du journal après désarmement
        apres = sim.altitude_gazebo()
        resultat["gazebo_verite"]["apres_atterrissage_xyz"] = apres[:3]
        journal(f"Posé et désarmé. Altitude Gazebo : {apres[2]:.2f} m")

        resultat["temps_reel_vol_complet"] = stats.bilan(t0, t1)
        resultat["temps_reel_stationnaire"] = stats.bilan(t_h0, t_h1)
        resultat["charge_machine_fin"] = os.getloadavg()[0]
        resultat["cpu_machine_pourcent_pendant_vol"] = psutil.cpu_percent()
        resultat["cpu"] = {"coeurs_utilises_px4_gz": round((cpu1 - cpu0) / (t1 - t0), 2),
                           "duree_murale_vol_s": round(t1 - t0, 1)}

        nouveaux = sorted(set(sim.rootfs.glob("log/*/*.ulg")) - log_avant, key=lambda p: p.stat().st_mtime)
        if not nouveaux:
            raise EchecVol("aucun nouveau fichier .ulg")
        ulg = dossier / nouveaux[-1].name
        shutil.copy2(nouveaux[-1], ulg)
        resultat["ulog"] = analyser_ulog(ulg, args.altitude)

        u, c, g = resultat["ulog"], resultat["criteres"], resultat["gazebo_verite"]
        s = u.get("stationnaire", {})
        duree_palier_mini = max(args.stationnaire - 6.0, 0)
        c["journal_lisible_sans_corruption"] = not u["corrompu"] and not u["topics_manquants"]
        c["arme_puis_desarme_journal"] = bool(u.get("arme_vu") and u.get("desarme_en_fin"))
        c["pose_en_fin_de_journal"] = bool(u.get("pose_en_fin_de_journal"))
        c["altitude_journal_proche_cible"] = abs(s.get("altitude_moy_m", 1e9) - args.altitude) < 0.3
        c["stationnaire_stable_0_15m"] = s.get("altitude_ecart_type_m", 1e9) < 0.15
        c["stationnaire_derive_moins_1m"] = s.get("derive_horizontale_max_m", 1e9) < 1.0
        c["stationnaire_duree_suffisante"] = s.get("duree_s", 0) >= duree_palier_mini
        c["gazebo_confirme_altitude"] = abs(g["stationnaire_hauteur_moyenne_m"] - args.altitude) < 0.5
        c["gazebo_confirme_retour_au_sol"] = abs(g["apres_atterrissage_xyz"][2] - g["avant_decollage_xyz"][2]) < 0.2
        c["processus_sans_display"] = "DISPLAY" not in sim.env
    except EchecVol as e:
        resultat["erreur"] = str(e)
        journal(f"ECHEC : {e}")
    finally:
        if stats:
            stats.arreter()
        sim.arreter()

    resultat["uptime_apres"] = os.getloadavg()
    ok = "erreur" not in resultat and resultat["criteres"] and all(resultat["criteres"].values())
    resultat["reussite"] = bool(ok)
    (dossier / "resultat.json").write_text(json.dumps(resultat, indent=2, ensure_ascii=False, default=str))
    print(json.dumps(resultat, indent=2, ensure_ascii=False, default=str))
    journal(("REUSSITE" if ok else "ECHEC") + f" : {dossier / 'resultat.json'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
