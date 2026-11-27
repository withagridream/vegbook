"""vegbook.db の各テーブルを data/<テーブル名>.csv に書き出す（標準ライブラリのみ）。

使い方:
    python3 export_csv.py [DBのパス] [出力先ディレクトリ] [--force]

- 出力先が data/（正本）のときは --force がないと止まる。

- 行は主キー順。UTF-8・改行は LF。
- NULL は \\N、空文字列は空欄で書く（区別して往復一致させるため）。
- chunks / chunks_fts は build_db.py が生成するので書き出さない。
"""
import csv
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).parent

# CSV で管理するテーブルと並び順（外部キーの依存順）
TABLES: list[str] = [
    'regions', 'crop_categories', 'grow_environments', 'fertilizers', 'pests',
    'pest_controls', 'crops', 'crop_fertilizers', 'companion_plants', 'crop_pests',
    'glossary', 'climate_monthly', 'harvest_stats',
    'sources', 'crop_field_sources', 'dataset_sources', 'crop_aliases',
    'crop_soil', 'crop_storage', 'troubles', 'causes', 'trouble_causes',
    'cause_conditions', 'remedies', 'questions', 'data_issues', 'trouble_aliases',
]

# 並び順（主キー）。複合主キーのテーブルだけ指定する
ORDER: dict[str, str] = {
    'crop_field_sources': 'crop_id, field, source_id',
    'dataset_sources': 'table_name, source_id',
    'crop_soil': 'crop_id',
}

NULL = '\\N'


def encode(v: object) -> str:
    if v is None:
        return NULL
    return str(v)


def export(db: Path, out: Path) -> dict[str, int]:
    out.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(f'{db.resolve().as_uri()}?mode=ro', uri=True)
    counts: dict[str, int] = {}
    for t in TABLES:
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)
        ).fetchone()
        if not exists:
            continue
        cols = [r[1] for r in conn.execute(f'PRAGMA table_info({t})')]
        order = ORDER.get(t, 'id')
        rows = conn.execute(f'SELECT {", ".join(cols)} FROM {t} ORDER BY {order}').fetchall()  # noqa: S608
        with open(out / f'{t}.csv', 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f, lineterminator='\n')
            w.writerow(cols)
            for r in rows:
                w.writerow([encode(v) for v in r])
        counts[t] = len(rows)
    conn.close()
    return counts


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--force']
    force = '--force' in sys.argv[1:]
    db = Path(args[0]) if len(args) > 0 else HERE / 'vegbook.db'
    out = Path(args[1]) if len(args) > 1 else HERE / 'data'
    # data/ は正本。確認なしに上書きしない（上書きするなら --force）
    if out.resolve() == (HERE / 'data').resolve() and not force:
        sys.exit('data/（正本のCSV）への書き出しは上書きになるため止めました。出力先を別のフォルダにするか、'
                 '本当に上書きするなら --force を付けてください。\n'
                 '例: python3 export_csv.py vegbook.db /tmp/csv_out   /   python3 export_csv.py vegbook.db data --force')
    for name, n in export(db, out).items():
        print(f'{name}: {n}行')
