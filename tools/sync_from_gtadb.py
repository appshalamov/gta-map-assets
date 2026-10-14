#!/usr/bin/env python3
"""Обновить зеркало gtadb: плитки GTA 5 (satellite) и кадры игры ,ig.jpg.

Берёт файлы из sparse-клона rolux/gtadb.org (git, как просит автор gtadb),
а список нужных кадров — из данных приложения Secret Base (data/map):
  gta5.json / gta6.json             — ссылки .../map/photos/{5|6}/{Lid},ig.jpg (любой хост)
  gtadb_gta5.json / gtadb_gta6.json — points: [0] = Lid, [7] = 1 — кадр игры есть

Не переносит: фото из жизни ,rl.jpg (Street View) и плитки GTA 6 (утечки).
Файлы только добавляет и обновляет; удалённое из приложения не стирает —
старые версии приложения в кэше могут на него ссылаться.
Из gtadb скачивает только то, чего здесь нет или что изменилось
(сравнение по git-хэшу блоба), поэтому повторный запуск почти ничего не тянет.

Запуск (без venv — только стандартная библиотека):
  python3 -I tools/sync_from_gtadb.py \
      --gtadb ~/Developer/gtadb.org \
      --app-data "/Volumes/Work SSD/Система/Cloude/GTA 5:6 /cheats-pwa/data/map"
Клон gtadb, если его нет, создаётся сам (blobless + sparse, depth 1).
С --strict код выхода 1, если нужных кадров нет в gtadb (список — в выводе).
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GTADB_URL = "https://github.com/rolux/gtadb.org.git"
TILES = "maps/tiles/5/satellite"
PHOTO_RE = re.compile(r"map/photos/([56])/(L\d+),ig\.jpg")
LICENSES = {"LICENSE": "gtadb-LICENSE", "LICENSE-DATA": "gtadb-LICENSE-DATA"}


def git(gtadb, *args, **kw):
    return subprocess.run(["git", "-C", gtadb, *args], check=True, **kw)


def needed_lids(app_data):
    need = {"5": set(), "6": set()}
    for name in ("gta5.json", "gta6.json"):
        with open(os.path.join(app_data, name), encoding="utf-8") as f:
            for ver, lid in PHOTO_RE.findall(f.read()):
                need[ver].add(lid)
    for name, ver in (("gtadb_gta5.json", "5"), ("gtadb_gta6.json", "6")):
        with open(os.path.join(app_data, name), encoding="utf-8") as f:
            for p in json.load(f)["points"]:
                if len(p) > 7 and p[7] == 1:
                    need[ver].add(p[0])
    return need


def blob_sha(path):
    """git hash-object без запуска git."""
    if not os.path.isfile(path):
        return None
    with open(path, "rb") as f:
        data = f.read()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def remote_tree(gtadb):
    # без -l: размер блоба заставил бы git докачивать каждый блоб по одному
    out = git(gtadb, "ls-tree", "-r", "HEAD", "--", TILES, "map/photos/5", "map/photos/6",
              *LICENSES, capture_output=True, text=True).stdout
    tree = {}
    for line in out.splitlines():
        meta, path = line.split("\t", 1)
        _, kind, sha = meta.split()
        if kind == "blob":
            tree[path] = sha
    return tree


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gtadb", default=os.path.expanduser("~/Developer/gtadb.org"))
    ap.add_argument("--app-data", required=True)
    ap.add_argument("--no-fetch", action="store_true", help="не обновлять клон gtadb")
    ap.add_argument("--strict", action="store_true", help="код 1, если нужных кадров нет в gtadb")
    a = ap.parse_args()

    if not os.path.isdir(os.path.join(a.gtadb, ".git")):
        subprocess.run(["git", "clone", "--filter=blob:none", "--no-checkout", "--depth=1",
                        "--sparse", GTADB_URL, a.gtadb], check=True)
    elif not a.no_fetch:
        git(a.gtadb, "fetch", "--depth=1", "origin", "main")
        git(a.gtadb, "update-ref", "HEAD", "FETCH_HEAD")
    commit = git(a.gtadb, "rev-parse", "HEAD", capture_output=True, text=True).stdout.strip()
    tree = remote_tree(a.gtadb)  # только деревья — блобы не качаются

    need = needed_lids(a.app_data)
    wanted = {p: p for p in tree if p.startswith(TILES + "/") and p.endswith(".jpg")}
    missing = []
    for ver in "56":
        for lid in sorted(need[ver]):
            p = f"map/photos/{ver}/{lid},ig.jpg"
            if p in tree:
                wanted[p] = p
            else:
                missing.append(p)
    wanted.update({src: dst for src, dst in LICENSES.items() if src in tree})

    todo = {src: dst for src, dst in wanted.items()
            if blob_sha(os.path.join(REPO, dst)) != tree[src]}
    if todo:
        # sparse-checkout ровно этих файлов: git докачает их блобы одной пачкой
        git(a.gtadb, "sparse-checkout", "set", "--no-cone", "--stdin",
            input="".join("/" + p + "\n" for p in todo), text=True)
        git(a.gtadb, "reset", "--hard", "-q", "HEAD")
        for src, dst in todo.items():
            out = os.path.join(REPO, dst)
            os.makedirs(os.path.dirname(out) or REPO, exist_ok=True)
            shutil.copyfile(os.path.join(a.gtadb, src), out)  # без xattr

    zooms, photos = {}, {}
    for p in (p for p in wanted if p.startswith(TILES + "/")):
        z = p.split("/")[4]
        zooms.setdefault(z, {"files": 0, "bytes": 0})
        zooms[z]["files"] += 1
        zooms[z]["bytes"] += os.path.getsize(os.path.join(REPO, p))
    for ver in "56":
        d = os.path.join(REPO, "map/photos", ver)
        names = [n for n in os.listdir(d) if n.endswith(",ig.jpg") and not n.startswith("._")] \
            if os.path.isdir(d) else []
        photos[ver] = {"files": len(names),
                       "bytes": sum(os.path.getsize(os.path.join(d, n)) for n in names)}

    manifest = {
        "source": "https://github.com/rolux/gtadb.org",
        "source_commit": commit,
        "tiles_gta5_satellite": {
            "template": TILES + "/{z}/{z},{y},{x}.jpg",
            "zooms": dict(sorted(zooms.items(), key=lambda kv: int(kv[0]))),
        },
        "photos_ig": {"template": "map/photos/{5|6}/{Lid},ig.jpg", **photos},
        "missing_in_gtadb": missing,
    }
    old = None
    mpath = os.path.join(REPO, "manifest.json")
    if os.path.exists(mpath):
        with open(mpath, encoding="utf-8") as f:
            old = json.load(f)
    if todo or old is None or {**old, "source_commit": commit} != manifest:
        with open(mpath, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=1)
            f.write("\n")

    print(json.dumps({"downloaded": len(todo), "already_here": len(wanted) - len(todo),
                      "missing_in_gtadb": missing, "photos_ig": photos,
                      "tiles": {z: v["files"] for z, v in manifest["tiles_gta5_satellite"]["zooms"].items()}},
                     ensure_ascii=False))
    return 1 if missing and a.strict else 0


if __name__ == "__main__":
    sys.exit(main())
