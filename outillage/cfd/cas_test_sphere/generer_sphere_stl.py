#!/usr/bin/env python3
"""Écrit une sphère facettée en STL binaire, par subdivision d'un icosaèdre (bibliothèque standard).

Usage : generer_sphere_stl.py <sortie.stl> [diamètre=1] [subdivisions=6]
"""
import math
import struct
import sys


def icosphere(subdivisions):
    p = (1 + 5 ** 0.5) / 2
    points = [(-1, p, 0), (1, p, 0), (-1, -p, 0), (1, -p, 0), (0, -1, p), (0, 1, p),
              (0, -1, -p), (0, 1, -p), (p, 0, -1), (p, 0, 1), (-p, 0, -1), (-p, 0, 1)]
    points = [unitaire(v) for v in points]
    faces = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4),
             (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8),
             (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    for _ in range(subdivisions):
        milieux, suivantes = {}, []

        def milieu(a, b):
            cle = (min(a, b), max(a, b))
            if cle not in milieux:
                points.append(unitaire(tuple((u + v) / 2 for u, v in zip(points[a], points[b]))))
                milieux[cle] = len(points) - 1
            return milieux[cle]

        for a, b, c in faces:
            ab, bc, ca = milieu(a, b), milieu(b, c), milieu(c, a)
            suivantes += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        faces = suivantes
    return points, faces


def unitaire(v):
    n = math.sqrt(sum(x * x for x in v))
    return tuple(x / n for x in v)


def main():
    sortie = sys.argv[1]
    diametre = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    subdivisions = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    points, faces = icosphere(subdivisions)
    r = diametre / 2
    with open(sortie, "wb") as f:
        f.write(b"sphere icosaedre subdivise".ljust(80, b" "))
        f.write(struct.pack("<I", len(faces)))
        for a, b, c in faces:
            normale = unitaire(tuple(x + y + z for x, y, z in zip(points[a], points[b], points[c])))
            f.write(struct.pack("<3f", *normale))
            for i in (a, b, c):
                f.write(struct.pack("<3f", *(r * x for x in points[i])))
            f.write(b"\0\0")
    print(f"{sortie} : {len(faces)} facettes, diamètre {diametre}")


if __name__ == "__main__":
    main()
