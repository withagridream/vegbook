"""往復一致の検査（標準ライブラリのみ）。

使い方:
    python3 verify_roundtrip.py [--original 元のDB]

検査:
  1. 元のDB（--original。段階1までの vegbook.db）と、data/*.csv から作ったDBで、
     従来の13テーブルが全行・全列・型まで一致する
  2. 作ったDB → CSV に書き出し直したものが、data/*.csv とバイト単位で一致する（DB→CSV→DB の往復）
  3. 作ったDB を2回作って chunks が同じになる（生成が決まった順序で行われる）
どれかが食い違うと終了コード1で終わる。
"""
import argparse
import sqlite3
import sys
import tempfile
from pathlib import Path

from build_db import build
from export_csv import export, TABLES

HERE = Path(__file__).parent
LEGACY = ['regions', 'crop_categories', 'grow_environments', 'fertilizers', 'pests', 'pest_controls',
          'crops', 'crop_fertilizers', 'companion_plants', 'crop_pests', 'glossary',
          'climate_monthly', 'harvest_stats']


def dump(conn: sqlite3.Connection, table: str) -> tuple[list[str], list[tuple]]:
    cols = [r[1] for r in conn.execute(f'PRAGMA table_info({table})')]
    order = 'id'
    rows = conn.execute(f'SELECT {",".join(cols)}, {",".join("typeof(" + c + ")" for c in cols)} '  # noqa: S608
                        f'FROM {table} ORDER BY {order}').fetchall()
    return cols, [tuple(r) for r in rows]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--original', type=Path, default=None,
                    help='段階1までの vegbook.db（省略すると 1. の比較を飛ばす。段階2a以降は応急処置・仮の行の整理で元と違うため）')
    a = ap.parse_args()
    fail = 0
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        built = td / 'built.db'
        build(built)
        # 1. 元のDBとの一致
        b = sqlite3.connect(f'{built.resolve().as_uri()}?mode=ro', uri=True)
        o = sqlite3.connect(f'{a.original.resolve().as_uri()}?mode=ro', uri=True) if a.original else None
        for t in (LEGACY if o else []):
            oc, orows = dump(o, t)
            bc, brows = dump(b, t)
            if oc != bc:
                print(f'[NG] {t}: 列が違う {oc} / {bc}'); fail += 1; continue
            if orows != brows:
                diff = [i for i, (x, y) in enumerate(zip(orows, brows)) if x != y]
                print(f'[NG] {t}: 行数 {len(orows)}/{len(brows)}、不一致 {len(diff)} 行'); fail += 1
            else:
                print(f'[OK] 元のDBと一致: {t}（{len(orows)}行・列{len(oc)}・型まで）')
        # 2. DB→CSV がデータのCSVとバイト一致
        export(built, td / 'csv')
        for t in TABLES:
            x = (HERE / 'data' / f'{t}.csv').read_bytes()
            y = (td / 'csv' / f'{t}.csv').read_bytes()
            if x != y:
                print(f'[NG] CSV往復: {t}'); fail += 1
        print(f'[{"OK" if not fail else "NG"}] DB→CSV→DB: {len(TABLES)}テーブルのCSVが一致')
        # 3. 2回ビルドして chunks が同じ
        built2 = td / 'built2.db'
        build(built2)
        c2 = sqlite3.connect(f'{built2.resolve().as_uri()}?mode=ro', uri=True)
        q = 'SELECT id,source_id,crop_id,lang,section,text,is_translation,ref_table,ref_id FROM chunks ORDER BY id'
        same = b.execute(q).fetchall() == c2.execute(q).fetchall()
        print(f'[{"OK" if same else "NG"}] chunks の再現性（2回のビルドで同一）: {b.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]}件')
        fail += 0 if same else 1
    print('結果:', '全て一致' if not fail else f'{fail}件の不一致')
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main())
