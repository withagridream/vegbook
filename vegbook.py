#!/usr/bin/env python3
"""
vegbook — Vegetable Growing Database CLI
Standard library only: sqlite3, argparse, textwrap

Usage:
  python vegbook.py search [--month M] [--category C] [--lang en]
  python vegbook.py detail <name> [--lang en]
  python vegbook.py recommend [--month M] [--lang en]
  python vegbook.py companion <name> [--lang en]
  python vegbook.py glossary [--term T] [--lang en]
"""

import argparse
import sqlite3
import textwrap
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "vegbook.db"

LABELS = {
    "ja": {
        "category":       "カテゴリ",
        "environment":    "栽培環境",
        "difficulty":     "難易度",
        "sow":            "種まき",
        "harvest":        "収穫",
        "days":           "収穫まで",
        "temp":           "適正気温",
        "sunlight":       "日照",
        "watering":       "水やり",
        "planter":        "プランター",
        "rotation":       "連作障害",
        "rotation_none":  "なし",
        "rotation_years": "年空ける",
        "failure":        "失敗しやすい点",
        "harvest_sign":   "収穫のサイン",
        "storage":        "保存方法",
        "fertilizers":    "肥料",
        "pests":          "害虫・対策",
        "companions":     "コンパニオンプランツ",
        "good":           "相性○",
        "bad":            "相性×",
        "no_companion":   "データなし",
        "month_sow":      "月 植えられる野菜",
        "month_harvest":  "月 収穫できる野菜",
        "no_result":      "該当なし",
        "days_unit":      "日",
        "month_unit":     "月",
        "reading":        "読み",
        "term":           "用語",
        "explanation":    "解説",
    },
    "en": {
        "category":       "Category",
        "environment":    "Environment",
        "difficulty":     "Difficulty",
        "sow":            "Sow",
        "harvest":        "Harvest",
        "days":           "Days to harvest",
        "temp":           "Temperature",
        "sunlight":       "Sunlight",
        "watering":       "Watering",
        "planter":        "Planter size",
        "rotation":       "Crop rotation",
        "rotation_none":  "No restriction",
        "rotation_years": "yr gap needed",
        "failure":        "Common failures",
        "harvest_sign":   "Harvest sign",
        "storage":        "Storage",
        "fertilizers":    "Fertilizers",
        "pests":          "Pests & controls",
        "companions":     "Companion plants",
        "good":           "Good",
        "bad":            "Avoid",
        "no_companion":   "No data",
        "month_sow":      "— Vegetables to sow in month",
        "month_harvest":  "— Vegetables to harvest in month",
        "no_result":      "No results found",
        "days_unit":      " days",
        "month_unit":     "",
        "reading":        "Reading",
        "term":           "Term",
        "explanation":    "Explanation",
    },
}


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def stars(n):
    n = n or 1
    return "★" * n + "☆" * (5 - n)


def wrap(text, width=72, indent="  "):
    if not text:
        return ""
    return textwrap.fill(str(text), width=width, initial_indent=indent, subsequent_indent=indent)


def name_col(lang):
    return "name_en" if lang == "en" else "name"


def print_crop_row(row, lang):
    L = LABELS[lang]
    n = row[name_col(lang)] or row["name"]
    cat = row["category_en"] if lang == "en" else row["category"]
    print(f"  {n:<22} {stars(row['difficulty'])}  "
          f"{L['sow']}: {row['sow_start']}–{row['sow_end']}{L['month_unit']}  "
          f"{L['harvest']}: {row['harvest_start']}–{row['harvest_end']}{L['month_unit']}  "
          f"[{cat or '—'}]")


# ------------------------------------------------------------------ search
def cmd_search(args):
    L = LABELS[args.lang]
    conn = get_db()

    query = """
        SELECT cr.*, cc.name AS category, cc.name_en AS category_en,
               ge.name AS environment, ge.name_en AS environment_en
        FROM crops cr
        LEFT JOIN crop_categories  cc ON cr.category_id  = cc.id
        LEFT JOIN grow_environments ge ON cr.environment_id = ge.id
        WHERE 1=1
    """
    params = []

    if args.month:
        query += " AND cr.sow_start <= ? AND cr.sow_end >= ?"
        params += [args.month, args.month]
    if args.category:
        col = "cc.name_en" if args.lang == "en" else "cc.name"
        query += f" AND {col} = ?"
        params.append(args.category)
    if args.environment:
        col = "ge.name_en" if args.lang == "en" else "ge.name"
        query += f" AND {col} = ?"
        params.append(args.environment)
    if args.difficulty:
        query += " AND cr.difficulty = ?"
        params.append(args.difficulty)

    query += " ORDER BY cr.difficulty, cr.name"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        print(L["no_result"])
        return

    header = "Search results" if args.lang == "en" else "検索結果"
    print(f"\n{'—'*60}")
    print(f" {header} ({len(rows)})")
    print(f"{'—'*60}")
    for r in rows:
        print_crop_row(r, args.lang)
    print()


# ------------------------------------------------------------------ detail
def cmd_detail(args):
    L = LABELS[args.lang]
    conn = get_db()

    col = "cr.name_en" if args.lang == "en" else "cr.name"
    row = conn.execute(f"""
        SELECT cr.*, cc.name AS category, cc.name_en AS category_en,
               ge.name AS environment, ge.name_en AS environment_en
        FROM crops cr
        LEFT JOIN crop_categories  cc ON cr.category_id  = cc.id
        LEFT JOIN grow_environments ge ON cr.environment_id = ge.id
        WHERE {col} = ? COLLATE NOCASE OR cr.name = ? COLLATE NOCASE
    """, [args.name, args.name]).fetchone()

    if not row:
        print(f"Not found: {args.name}")
        conn.close()
        return

    crop_id = row["id"]

    fertilizers = conn.execute("""
        SELECT f.name, f.name_en, f.availability, cf.ratio
        FROM crop_fertilizers cf JOIN fertilizers f ON cf.fertilizer_id = f.id
        WHERE cf.crop_id = ?
    """, [crop_id]).fetchall()

    pests = conn.execute("""
        SELECT p.name, p.name_en, pc.name AS control, pc.name_en AS control_en
        FROM crop_pests cp
        JOIN pests p       ON cp.pest_id    = p.id
        JOIN pest_controls pc ON cp.control_id = pc.id
        WHERE cp.crop_id = ?
    """, [crop_id]).fetchall()

    companions = conn.execute("""
        SELECT cr2.name, cr2.name_en, cp.effect, cp.is_positive
        FROM companion_plants cp JOIN crops cr2 ON cp.companion_id = cr2.id
        WHERE cp.crop_id = ?
    """, [crop_id]).fetchall()

    conn.close()

    n = row[name_col(args.lang)] or row["name"]
    cat = row["category_en"] if args.lang == "en" else row["category"]
    env = row["environment_en"] if args.lang == "en" else row["environment"]

    print(f"\n{'='*60}")
    print(f"  {n}")
    print(f"{'='*60}")
    print(f"  {L['category']:<16}: {cat or '—'}")
    print(f"  {L['environment']:<16}: {env or '—'}")
    print(f"  {L['difficulty']:<16}: {stars(row['difficulty'])}")
    if row["sow_start"]:
        print(f"  {L['sow']:<16}: {row['sow_start']}–{row['sow_end']}{L['month_unit']}")
    if row["harvest_start"]:
        print(f"  {L['harvest']:<16}: {row['harvest_start']}–{row['harvest_end']}{L['month_unit']}")
    if row["days_to_harvest"]:
        print(f"  {L['days']:<16}: {row['days_to_harvest']}{L['days_unit']}")
    if row["temp_min"]:
        unit = "°C"
        print(f"  {L['temp']:<16}: {row['temp_min']}–{row['temp_max']} {unit}")

    sun = row["sunlight_en"] if args.lang == "en" else row["sunlight"]
    wat = row["watering_en"] if args.lang == "en" else row["watering"]
    fai = row["failure_points_en"] if args.lang == "en" else row["failure_points"]
    sig = row["harvest_sign_en"] if args.lang == "en" else row["harvest_sign"]
    sto = row["storage_en"] if args.lang == "en" else row["storage"]

    if sun:
        print(f"\n  {L['sunlight']}:")
        print(wrap(sun))
    if wat:
        print(f"\n  {L['watering']}:")
        print(wrap(wat))
    if row["planter_size"]:
        print(f"\n  {L['planter']}: {row['planter_size']}")
    if row["rotation_years"] is not None:
        rot = L["rotation_none"] if row["rotation_years"] == 0 \
              else f"{row['rotation_years']} {L['rotation_years']}"
        print(f"  {L['rotation']}: {rot}")
    if fai:
        print(f"\n  {L['failure']}:")
        print(wrap(fai))
    if sig:
        print(f"\n  {L['harvest_sign']}:")
        print(wrap(sig))
    if sto:
        print(f"\n  {L['storage']}:")
        print(wrap(sto))

    if fertilizers:
        print(f"\n  {L['fertilizers']}:")
        for f in fertilizers:
            fn = f["name_en"] if args.lang == "en" else f["name"]
            print(f"    • {fn}")

    if pests:
        print(f"\n  {L['pests']}:")
        for p in pests:
            pn = p["name_en"] if args.lang == "en" else p["name"]
            cn = p["control_en"] if args.lang == "en" else p["control"]
            print(f"    • {pn} → {cn}")

    if companions:
        print(f"\n  {L['companions']}:")
        for c in companions:
            cn = c["name_en"] if args.lang == "en" else c["name"]
            label = L["good"] if c["is_positive"] else L["bad"]
            print(f"    [{label}] {cn}")
    print()


# ------------------------------------------------------------------ recommend
def cmd_recommend(args):
    L = LABELS[args.lang]
    conn = get_db()
    month = args.month or datetime.now().month

    sowable = conn.execute("""
        SELECT cr.*, cc.name AS category, cc.name_en AS category_en
        FROM crops cr LEFT JOIN crop_categories cc ON cr.category_id = cc.id
        WHERE cr.sow_start <= ? AND cr.sow_end >= ?
        ORDER BY cr.difficulty, cr.name LIMIT 8
    """, [month, month]).fetchall()

    harvestable = conn.execute("""
        SELECT cr.*, cc.name AS category, cc.name_en AS category_en
        FROM crops cr LEFT JOIN crop_categories cc ON cr.category_id = cc.id
        WHERE cr.harvest_start <= ? AND cr.harvest_end >= ?
        ORDER BY cr.name LIMIT 8
    """, [month, month]).fetchall()

    conn.close()

    sow_label = f"{month}{L['month_unit']} {L['month_sow']}" if args.lang == "ja" \
                else f"Month {month} {L['month_sow']}"
    har_label = f"{month}{L['month_unit']} {L['month_harvest']}" if args.lang == "ja" \
                else f"Month {month} {L['month_harvest']}"

    print(f"\n{'—'*60}")
    print(f" {sow_label}")
    print(f"{'—'*60}")
    if sowable:
        for r in sowable:
            print_crop_row(r, args.lang)
    else:
        print(f"  {L['no_result']}")

    print(f"\n{'—'*60}")
    print(f" {har_label}")
    print(f"{'—'*60}")
    if harvestable:
        for r in harvestable:
            print_crop_row(r, args.lang)
    else:
        print(f"  {L['no_result']}")
    print()


# ------------------------------------------------------------------ companion
def cmd_companion(args):
    L = LABELS[args.lang]
    conn = get_db()

    col = "name_en" if args.lang == "en" else "name"
    crop = conn.execute(
        f"SELECT id, name, name_en FROM crops WHERE {col} = ? COLLATE NOCASE OR name = ? COLLATE NOCASE",
        [args.name, args.name]
    ).fetchone()

    if not crop:
        print(f"Not found: {args.name}")
        conn.close()
        return

    rows = conn.execute("""
        SELECT cr2.name, cr2.name_en, cp.effect, cp.effect_en, cp.is_positive
        FROM companion_plants cp JOIN crops cr2 ON cp.companion_id = cr2.id
        WHERE cp.crop_id = ?
        ORDER BY cp.is_positive DESC, cr2.name
    """, [crop["id"]]).fetchall()
    conn.close()

    display = crop["name_en"] if args.lang == "en" else crop["name"]
    print(f"\n{'—'*60}")
    print(f"  {L['companions']}: {display}")
    print(f"{'—'*60}")

    if not rows:
        print(f"  {L['no_companion']}")
    else:
        for r in rows:
            cn     = r["name_en"]   if args.lang == "en" else r["name"]
            effect = r["effect_en"] if args.lang == "en" else r["effect"]
            label  = L["good"] if r["is_positive"] else L["bad"]
            print(f"  [{label}] {cn}")
            print(wrap(effect, indent="        "))
    print()


# ------------------------------------------------------------------ glossary
def cmd_glossary(args):
    L = LABELS[args.lang]
    conn = get_db()

    if args.term:
        t = f"%{args.term}%"
        rows = conn.execute(
            "SELECT * FROM glossary WHERE term LIKE ? OR reading LIKE ? OR plain_en LIKE ?",
            [t, t, t]
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM glossary ORDER BY category, term"
        ).fetchall()
    conn.close()

    if not rows:
        print(L["no_result"])
        return

    cur_cat = None
    for r in rows:
        if r["category"] != cur_cat:
            cur_cat = r["category"]
            print(f"\n[{cur_cat}]")
        exp = r["plain_en"] if args.lang == "en" else r["plain_ja"]
        reading = f" ({r['reading']})" if r["reading"] and args.lang == "ja" else ""
        print(f"  {r['term']}{reading}")
        print(wrap(exp))
    print()


# ------------------------------------------------------------------ main
def main():
    parser = argparse.ArgumentParser(
        prog="vegbook",
        description="Vegetable growing database CLI / 家庭菜園データベース CLI"
    )
    parser.add_argument("--lang", choices=["ja", "en"], default="ja",
                        help="Output language (ja/en)")
    sub = parser.add_subparsers(dest="command")

    # search
    p_search = sub.add_parser("search", help="Search crops / 作物を検索")
    p_search.add_argument("--month",       type=int, help="Sowing month (1–12)")
    p_search.add_argument("--category",    help="Category name")
    p_search.add_argument("--environment", help="Growing environment")
    p_search.add_argument("--difficulty",  type=int, choices=range(1, 6),
                          help="Difficulty level 1–5")
    p_search.add_argument("--lang", choices=["ja", "en"], default="ja")

    # detail
    p_detail = sub.add_parser("detail", help="Show crop detail / 作物の詳細")
    p_detail.add_argument("name", help="Crop name (Japanese or English)")
    p_detail.add_argument("--lang", choices=["ja", "en"], default="ja")

    # recommend
    p_rec = sub.add_parser("recommend", help="This month's recommendations / 今月のおすすめ")
    p_rec.add_argument("--month", type=int, help="Month (1–12, default: current month)")
    p_rec.add_argument("--lang", choices=["ja", "en"], default="ja")

    # companion
    p_comp = sub.add_parser("companion", help="Companion plants / コンパニオンプランツ")
    p_comp.add_argument("name", help="Crop name")
    p_comp.add_argument("--lang", choices=["ja", "en"], default="ja")

    # glossary
    p_glos = sub.add_parser("glossary", help="Glossary / 用語集")
    p_glos.add_argument("--term", help="Search term")
    p_glos.add_argument("--lang", choices=["ja", "en"], default="ja")

    args = parser.parse_args()

    if args.command == "search":
        cmd_search(args)
    elif args.command == "detail":
        cmd_detail(args)
    elif args.command == "recommend":
        cmd_recommend(args)
    elif args.command == "companion":
        cmd_companion(args)
    elif args.command == "glossary":
        cmd_glossary(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
