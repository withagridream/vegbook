"""data/*.csv と schema.sql から vegbook.db を生成する（標準ライブラリのみ）。

使い方:
    python3 build_db.py [--out 出力先DB]   # 省略時は同じフォルダの vegbook.db

- 正本は data/*.csv と schema.sql。vegbook.db は生成物。
- 一時ファイルに作ってから置き換える（途中で失敗しても既存の vegbook.db は壊れない）。
- chunks（RAG用の文章）と全文検索索引 chunks_fts は、ここで生成する。
- 次の検査に違反があればビルドを止める：外部キー（foreign_key_check）／関門（provisional=0 の行は
  根拠に使える出典を持つ）／農薬の語には注意書き／data_issues と実データの整合。
"""
import argparse
import csv
import os
import sqlite3
import sys
from pathlib import Path

from export_csv import TABLES
from vegbook_core import (STORAGE_METHODS, STORAGE_NOTE_COLS, TROUBLE_NOTE_COLS, crop_note_text, format_days,
                          is_evidence, issue_key, load_row_issues)

HERE = Path(__file__).parent
NULL = '\\N'

CROP_TEXT_FIELDS = ['sunlight', 'watering', 'storage', 'harvest_sign', 'failure_points']

# 農薬・商品名・薬剤を指す語。これらを含む対策・文章には、ラベル確認の注意書きが必須。
# 商品名や有効成分名は誤りやすい（例：オルトランはBT剤ではない）ため、出典なしでは載せない方針。
PESTICIDE_TERMS: tuple[str, ...] = (
    'オルトラン', 'スミチオン', 'バロック', 'マラチオン', 'マラソン', 'malathion', 'Malathion',
    'アセフェート', 'acephate', 'フェニトロチオン', 'fenitrothion', 'ダコニール', 'ベニカ', 'モスピラン',
    'アドマイヤー', 'トレボン', 'アファーム', 'ゼンターリ', 'Orthene', 'Sumithion', 'Baroque',
    'BT剤', '殺虫剤', '殺ダニ剤', '殺菌剤', '除草剤', '薬剤', '防除剤', '乳剤', '水和剤', '粒剤', 'フロアブル',
    'ダイアジノン', 'insecticide', 'miticide', 'fungicide', 'herbicide',
)
# 一般的な言及にも現れる弱い語（用語集の文章は対象外。対策・防除方法・作物の文章では検査する）
PESTICIDE_WEAK_TERMS: tuple[str, ...] = ('農薬', 'pesticide')
# 注意書きとして認める語句（日本語・英語）
CAUTION_PHRASES: tuple[str, ...] = ('ラベルの適用作物', 'registered crops')

# 関門：provisional=0（正式な行）に使う出典は、根拠に使える出典（sources.usable_as_evidence=1）に限り、
# 引用箇所（locator）が必須。統計データの出典（kind='statistics'）はこれらの表の根拠に使えない。親の行が仮なら子も仮
GATED_TABLES: tuple[str, ...] = ('crop_storage', 'trouble_causes', 'cause_conditions', 'remedies')


def load_csv(conn: sqlite3.Connection, table: str, path: Path) -> int:
    with open(path, encoding='utf-8', newline='') as f:
        r = csv.reader(f)
        header = next(r)
        rows = [[None if v == NULL else v for v in row] for row in r]
    ph = ','.join('?' * len(header))
    conn.executemany(f'INSERT INTO {table} ({",".join(header)}) VALUES ({ph})', rows)  # noqa: S608
    return len(rows)


def check_gate(conn: sqlite3.Connection) -> list[str]:
    """関門の検査。
    ・provisional=0 の行は、根拠に使える出典（usable_as_evidence=1）と引用箇所を持つ
    ・統計データの出典（kind='statistics'）は、原因・対策・保存方法・条件の根拠に付けられない
    ・親の行が仮（provisional=1）なのに、子が provisional=0 になっていない
    ・先人の智慧（wisdom=1）も、根拠に使える出典が必要
    """
    bad: list[str] = []
    for t in GATED_TABLES:
        for r in conn.execute(
                f'SELECT x.id, x.source_id FROM {t} x LEFT JOIN sources s ON s.id = x.source_id '  # noqa: S608
                'WHERE x.provisional = 0 AND (s.id IS NULL OR s.usable_as_evidence = 0)'):
            bad.append(f'{t} id={r["id"]}: provisional=0 なのに根拠に使える出典がない（source_id={r["source_id"]}）')
        for r in conn.execute(
                f'SELECT x.id, x.source_id FROM {t} x JOIN sources s ON s.id = x.source_id '  # noqa: S608
                "WHERE s.kind = 'statistics'"):
            bad.append(f'{t} id={r["id"]}: 統計データの出典（source_id={r["source_id"]}）は根拠に使えない')
    for t in ('crop_storage', 'remedies'):
        for r in conn.execute(
                f'SELECT x.id FROM {t} x LEFT JOIN sources s ON s.id = x.source_id '  # noqa: S608
                'WHERE x.wisdom = 1 AND (s.id IS NULL OR s.usable_as_evidence = 0)'):
            bad.append(f'{t} id={r["id"]}: wisdom=1 なのに根拠に使える出典がない')
    # 作物の文章欄の出典（crop_field_sources）：根拠にできるのは provisional=0・根拠に使える出典・引用箇所あり
    for r in conn.execute(
            'SELECT f.crop_id, f.field, f.source_id, f.provisional, s.usable_as_evidence AS u, s.kind AS kind '
            'FROM crop_field_sources f JOIN sources s ON s.id = f.source_id'):
        where = f'crop_field_sources crop_id={r["crop_id"]} field={r["field"]} source_id={r["source_id"]}'
        if r['kind'] == 'statistics':
            bad.append(f'{where}: 統計データの出典は作物の値の根拠に使えない')
        if not r['provisional'] and not r['u']:
            bad.append(f'{where}: provisional=0 なのに根拠に使える出典ではない')
    # 親が仮なら、子は provisional=0 にできない
    for r in conn.execute(
            'SELECT tc.id, t.provisional AS tp, c.provisional AS cp FROM trouble_causes tc '
            'JOIN troubles t ON t.id = tc.trouble_id JOIN causes c ON c.id = tc.cause_id '
            'WHERE tc.provisional = 0 AND (t.provisional = 1 OR c.provisional = 1)'):
        bad.append(f'trouble_causes id={r["id"]}: provisional=0 なのに親が仮（troubles.provisional={r["tp"]}・causes.provisional={r["cp"]}）')
    for t in ('remedies', 'cause_conditions'):
        for r in conn.execute(
                f'SELECT x.id FROM {t} x JOIN causes c ON c.id = x.cause_id '  # noqa: S608
                'WHERE x.provisional = 0 AND c.provisional = 1'):
            bad.append(f'{t} id={r["id"]}: provisional=0 なのに親の原因（causes）が仮')
    return bad


def _has_caution(text: str) -> bool:
    return any(p in text for p in CAUTION_PHRASES)


def check_pesticide(conn: sqlite3.Connection) -> list[str]:
    """農薬の検査：農薬・商品名・薬剤の語を含む対策・文章・防除方法には、ラベル確認の注意書きが必須。
    対策（remedies）は、さらに uses_pesticide=1 が必須（uses_pesticide=1 なら caution 必須は schema の CHECK）。"""
    bad: list[str] = []
    strong_weak = PESTICIDE_TERMS + PESTICIDE_WEAK_TERMS
    for r in conn.execute('SELECT id, text, caution, uses_pesticide FROM remedies'):
        full = f'{r["text"]} {r["caution"] or ""}'
        if any(w in full for w in strong_weak):
            if not r['uses_pesticide']:
                bad.append(f'remedies id={r["id"]}: 農薬の語があるのに uses_pesticide=1 ではない')
            if not _has_caution(full):
                bad.append(f'remedies id={r["id"]}: 農薬の語があるのに「ラベルの適用作物」の注意書きがない')
    for r in conn.execute('SELECT id, name, name_en FROM pest_controls'):
        full = f'{r["name"]} {r["name_en"] or ""}'
        if any(w in full for w in strong_weak) and not _has_caution(full):
            bad.append(f'pest_controls id={r["id"]}: 農薬の語があるのに注意書きがない')
    for r in conn.execute('SELECT id, section, text FROM chunks'):
        # 用語集は「農薬を使わない」のような一般的な言及を含むため、弱い語（農薬）は対象外
        words = PESTICIDE_TERMS if r['section'] == 'glossary' else strong_weak
        if any(w in r['text'] for w in words) and not _has_caution(r['text']):
            bad.append(f'chunks id={r["id"]}（{r["section"]}）: 農薬の語があるのに注意書きがない')
    return bad


def _issue_rows(conn: sqlite3.Connection, table: str, key: str) -> tuple[int | None, str | None]:
    """data_issues の row_key（自然キー）が指す行の数を返す。キーの書式が不正なら (None, 理由)。"""
    cols = {r[1] for r in conn.execute(f'PRAGMA table_info({table})')}  # noqa: S608
    try:
        parts = dict(p.split('=', 1) for p in key.split('|'))
    except ValueError:
        return None, f'row_key の書式が不正: {key}'
    if key != issue_key(**parts):
        return None, f'row_key が正規の形（列名の昇順・「列=値」を|でつなぐ）ではない: {key}'
    where: list[str] = []
    params: list[str] = []
    for col, val in parts.items():
        if table == 'climate_monthly' and col == 'region':
            where.append('region_id IN (SELECT id FROM regions WHERE name = ?)')
        elif col in cols:
            where.append(f'{col} = ?')
        else:
            return None, f'row_key の列 {col} が表 {table} にない'
        params.append(val)
    n = conn.execute(f'SELECT COUNT(*) FROM {table} WHERE ' + ' AND '.join(where), params).fetchone()[0]  # noqa: S608
    return n, None


def check_data_issues(conn: sqlite3.Connection) -> list[str]:
    """data_issues の整合：hide/note は指した先が実在して1行だけ、removed は実在しないこと。"""
    bad: list[str] = []
    for r in conn.execute('SELECT * FROM data_issues'):
        t = r['table_name']
        if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone():
            bad.append(f'data_issues id={r["id"]}: 表 {t} がない')
            continue
        n, err = _issue_rows(conn, t, r['row_key'])
        if err:
            bad.append(f'data_issues id={r["id"]}: {err}')
            continue
        if r['action'] == 'removed' and n:
            bad.append(f'data_issues id={r["id"]}: removed なのに {t} {r["row_key"]} が残っている')
        if r['action'] in ('hide', 'note') and n != 1:
            bad.append(f'data_issues id={r["id"]}: {t} {r["row_key"]} が{n}行に当たる（1行だけに当たる必要がある）')
        if r['action'] in ('hide', 'note'):
            cols = {c[1] for c in conn.execute(f'PRAGMA table_info({t})')}  # noqa: S608
            for c in (r['column_name'] or '').split(','):
                if c.strip() and c.strip() not in cols:
                    bad.append(f'data_issues id={r["id"]}: 列 {c.strip()} が表 {t} にない')
    return bad


def check_chunks_issues(conn: sqlite3.Connection) -> list[str]:
    """data_issues の hide に当たる文章欄から chunk が作られていないこと／note の chunk は仮で警告つきであること。"""
    bad: list[str] = []
    for r in conn.execute("SELECT * FROM data_issues WHERE table_name='crops' AND action IN ('hide','note')"):
        parts = dict(p.split('=', 1) for p in r['row_key'].split('|'))
        crop = conn.execute('SELECT id FROM crops WHERE name = ?', (parts.get('name'),)).fetchone()
        if not crop:
            continue
        for col in (c.strip() for c in (r['column_name'] or '').split(',') if c.strip()):
            lang = 'en' if col.endswith('_en') else 'ja'
            section = col[:-3] if col.endswith('_en') else col
            rows = conn.execute("SELECT provisional, has_source, warning FROM chunks WHERE ref_table='crops' AND ref_id=? "
                                'AND section=? AND lang=?', (crop[0], section, lang)).fetchall()
            if r['action'] == 'hide' and rows:
                bad.append(f'chunks: hide の {parts.get("name")} {col} から chunk が作られている（{len(rows)}件）')
            if r['action'] == 'note':
                for c in rows:
                    if not c['provisional'] or c['has_source'] or not c['warning']:
                        bad.append(f'chunks: note の {parts.get("name")} {col} の chunk が仮・警告つきになっていない')
    return bad


def check_hide_pairs(conn: sqlite3.Connection) -> list[str]:
    """文章欄の hide は、日英の両方を挙げるか、もう片方に note を付けること（片方だけ隠して他方が漏れるのを防ぐ）。"""
    bad: list[str] = []
    text_cols = set(CROP_TEXT_FIELDS)
    by_key: dict[str, dict[str, set[str]]] = {}
    for r in conn.execute("SELECT row_key, column_name, action FROM data_issues WHERE table_name='crops'"):
        d = by_key.setdefault(r['row_key'], {'hide': set(), 'note': set()})
        if r['action'] in d:
            d[r['action']] |= {c.strip() for c in (r['column_name'] or '').split(',') if c.strip()}
    for key, d in by_key.items():
        for col in d['hide']:
            base = col[:-3] if col.endswith('_en') else col
            if base not in text_cols:
                continue
            pair = base if col.endswith('_en') else base + '_en'
            if pair not in d['hide'] and pair not in d['note']:
                bad.append(f'data_issues crops {key}: {col} を hide にしているのに、対の {pair} が hide でも note でもない')
    return bad


def build_chunks(conn: sqlite3.Connection) -> int:
    """文章欄から chunks を作る。順序は決まっているので、同じCSVからは同じ結果になる。

    chunks.source_id は「根拠に使える出典（usable_as_evidence=1）」だけを入れる。
    provisional=1 の行や、根拠に使えない出典しかない行は source_id を空にし、has_source=0 にする。
    """
    out: list[tuple] = []
    usable = {r[0] for r in conn.execute('SELECT id FROM sources WHERE usable_as_evidence = 1')}

    def src(crop_id: int, field: str) -> tuple[int | None, str | None]:
        # provisional=0（対象列・引用箇所を確認済み）で、根拠に使える出典（statistics 以外）だけ。出典と引用箇所を返す
        r = conn.execute(
            'SELECT f.source_id, f.locator FROM crop_field_sources f JOIN sources s ON s.id = f.source_id '
            "WHERE f.crop_id=? AND f.field=? AND f.provisional=0 AND s.usable_as_evidence=1 AND s.kind <> 'statistics' "
            'ORDER BY f.source_id LIMIT 1', (crop_id, field)).fetchone()
        return (r[0], r[1]) if r else (None, None)

    def row(source_id, crop_id, lang, section, text, ref_table, ref_id, provisional=0, warning=None, locator=None):
        # 根拠にできる判定は vegbook_core.is_evidence の1か所だけ（親が仮かどうかは呼び出し側が provisional に含める）
        # 引用箇所（locator）は根拠にできる chunk だけに入れる
        ok = is_evidence(source_id in usable, provisional)
        sid = source_id if ok else None
        return (sid, crop_id, lang, section, text, 0, ref_table, ref_id, 1 if provisional else 0, 1 if ok else 0, warning,
                locator if ok else None)

    # 作物の文章欄：data_issues の hide の列からは chunk を作らない／note の列の chunk は仮（provisional=1・has_source=0）で警告つき
    crop_issues = load_row_issues(conn, 'crops')
    crop_names = {r[0]: r[1] for r in conn.execute('SELECT id, name FROM crops')}
    for r in conn.execute(f'SELECT id, name, {", ".join(CROP_TEXT_FIELDS)}, '
                          + ', '.join(f + '_en' for f in CROP_TEXT_FIELDS) + ' FROM crops ORDER BY id'):  # noqa: S608
        cid = r[0]
        marks = crop_issues.get(issue_key(name=r['name']), [])
        n = len(CROP_TEXT_FIELDS)
        for i, field in enumerate(CROP_TEXT_FIELDS):
            hidden = {c for m in marks if m['action'] == 'hide' for c in m['cols']}
            notes = [m['issue'] for m in marks if m['action'] == 'note' and {field, field + '_en'} & m['cols']]
            for lang, val, fld in (('ja', r[2 + i], field), ('en', r[2 + n + i], field + '_en')):
                if not (val and str(val).strip()) or fld in hidden:
                    continue
                if notes:
                    out.append(row(None, cid, lang, field, str(val).strip(), 'crops', cid, 1, '／'.join(notes)))
                else:
                    sid, loc = src(cid, fld)
                    out.append(row(sid, cid, lang, field, str(val).strip(), 'crops', cid, locator=loc))
    for r in conn.execute('SELECT id, crop_id, method, steps, duration_min_days, duration_max_days, '
                          'source_id, lang, wisdom, provisional, locator FROM crop_storage ORDER BY id'):
        label = STORAGE_METHODS.get(r['method'], r['method'])
        days = format_days(r['duration_min_days'], r['duration_max_days'])
        text = ('（先人の智慧）' if r['wisdom'] else '') + f'保存（{label}）：{r["steps"] or ""}' + (f'［{days}］' if days else '')
        # 作物の storage 欄に note があれば、保存方法の chunk にも警告を引き継ぐ（仮・根拠にしない）
        warn = crop_note_text(crop_issues, crop_names.get(r['crop_id']), STORAGE_NOTE_COLS)
        out.append(row(r['source_id'], r['crop_id'], r['lang'], 'storage_' + r['method'], text,
                       'crop_storage', r['id'], 1 if warn else r['provisional'], warn, r['locator']))
    for r in conn.execute('SELECT id, term, reading, plain_ja, plain_en FROM glossary ORDER BY id'):
        reading = f'（{r["reading"]}）' if r['reading'] else ''
        out.append(row(None, None, 'ja', 'glossary', f'{r["term"]}{reading}：{r["plain_ja"]}', 'glossary', r['id']))
        if r['plain_en']:
            out.append(row(None, None, 'en', 'glossary', f'{r["term"]}: {r["plain_en"]}', 'glossary', r['id']))
    cprov = {r[0]: r[1] for r in conn.execute('SELECT id, provisional FROM causes')}
    for t in conn.execute('SELECT * FROM troubles ORDER BY id'):
        tcs = conn.execute(
            'SELECT c.id, c.name, tc.source_id, tc.provisional, tc.locator FROM trouble_causes tc '
            'JOIN causes c ON c.id = tc.cause_id WHERE tc.trouble_id = ? ORDER BY c.id, tc.id', (t['id'],)).fetchall()
        section = 'trouble_' + t['phase']
        # 作物の failure_points・harvest_sign 欄に note があれば、困りごとの chunk にも警告を引き継ぐ
        # （文章欄から拾った仮の困りごとだけ。出典つきの行は文章欄に依らないので引き継がない）
        twarn = (crop_note_text(crop_issues, crop_names.get(t['crop_id']), TROUBLE_NOTE_COLS)
                 if t['provisional'] else None)
        if not tcs:   # 原因がまだつながっていない症状は、症状だけの chunk（仮）
            out.append(row(None, t['crop_id'], t['lang'], section, f'症状：{t["symptom"]}', 'troubles', t['id'], 1, twarn))
            continue
        # 困りごと×原因の単位で chunk を作る。has_source・provisional は、その原因の判定（is_evidence）と同じにする
        for cid in dict.fromkeys(c['id'] for c in tcs):
            mine = [c for c in tcs if c['id'] == cid]
            # 親の困りごと・親の原因が仮なら、つながりが provisional=0 でも根拠にしない
            evrows = [c for c in mine
                      if is_evidence(c['source_id'] in usable, c['provisional'], t['provisional'], cprov.get(cid, 1))]
            ev = [c['source_id'] for c in evrows]
            # 対策は、この原因の対策で、この困りごとの作物に当てはまるものだけ（crop_id が空は全作物向け）
            rem = conn.execute(
                'SELECT text, caution, provisional, source_id, locator FROM remedies WHERE cause_id = ? '
                'AND (crop_id IS NULL OR crop_id IS ?) ORDER BY id', (cid, t['crop_id'])).fetchall()
            if twarn:
                ev = []
            if ev:   # 根拠にできる chunk には、根拠にできる対策だけを入れる（仮の対策・出典のない対策は入れない）
                rem = [r for r in rem if is_evidence(r['source_id'] in usable, r['provisional'], cprov.get(cid, 1))]
            parts = [f'症状：{t["symptom"]}', f'原因：{mine[0]["name"]}']
            if rem:
                parts.append('対処：' + '／'.join(r['text'] for r in rem))
            cau = [r['caution'] for r in rem if r['caution']]
            if cau:
                parts.append('注意：' + '／'.join(cau))
            # 引用箇所：chunk の出典（いちばん小さい出典id）の原因の引用箇所と、同じ出典の対策の引用箇所
            # 注意：対策の本文は出典を問わず入るが、出典・引用箇所は chunk の出典の分だけ。別の出典の対策が混ざると
            # その対策の出典表示が落ちる（PDL1.0 などは出典の記載が条件）。2026-11-28時点のデータでは該当なし。
            # 原因の出典と対策の出典がずれる行を足すときは、原因を出典ごとに分けるか、ここで対策を出典で絞る。
            loc = None
            if ev:
                sid0 = min(ev)
                cl = list(dict.fromkeys(c['locator'] for c in evrows if c['source_id'] == sid0 and c['locator']))
                rl = list(dict.fromkeys(r['locator'] for r in rem if r['source_id'] == sid0 and r['locator']))
                loc = '原因：' + '／'.join(cl) + ('　対処：' + '／'.join(rl) if rl else '')
            out.append(row(min(ev) if ev else None, t['crop_id'], t['lang'], section,
                           '\n'.join(parts), 'troubles', t['id'], 0 if ev else 1, twarn, loc))
    conn.executemany(
        'INSERT INTO chunks (source_id, crop_id, lang, section, text, is_translation, ref_table, ref_id, '
        'provisional, has_source, warning, locator) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', out)
    conn.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
    return len(out)


def build(out: Path, data_dir: Path = HERE / 'data') -> dict[str, int]:
    tmp = out.with_name(out.name + '.building')
    if tmp.exists():
        raise SystemExit(f'一時ファイルが残っています。確認して手で片付けてください: {tmp}')
    conn = sqlite3.connect(tmp)
    conn.row_factory = sqlite3.Row
    counts: dict[str, int] = {}
    try:
        conn.executescript((HERE / 'schema.sql').read_text(encoding='utf-8'))
        for t in TABLES:
            p = data_dir / f'{t}.csv'
            if not p.exists():
                raise SystemExit(f'CSV がありません: {p}')
            counts[t] = load_csv(conn, t, p)
        counts['chunks'] = build_chunks(conn)
        conn.commit()
        # 検査に1つでも違反があればビルドを止める（既存の vegbook.db は壊れない）
        bad_fk = conn.execute('PRAGMA foreign_key_check').fetchall()
        problems = [f'外部キー違反: {tuple(b)}' for b in bad_fk]
        problems += check_gate(conn) + check_pesticide(conn) + check_data_issues(conn) + check_hide_pairs(conn) + check_chunks_issues(conn)
        if problems:
            raise SystemExit(f'ビルドを中止します（{len(problems)}件の検査違反）:\n  ' + '\n  '.join(problems[:30]))
        ok = conn.execute('PRAGMA integrity_check').fetchone()[0]
        if ok != 'ok':
            raise SystemExit(f'integrity_check 失敗: {ok}')
        conn.close()
        os.replace(tmp, out)
    except BaseException:
        conn.close()
        raise
    return counts


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='data/*.csv から vegbook.db を生成する')
    ap.add_argument('--out', type=Path, default=HERE / 'vegbook.db')
    ap.add_argument('--data', type=Path, default=HERE / 'data')
    a = ap.parse_args()
    for k, v in build(a.out, a.data).items():
        print(f'{k}: {v}行')
    print(f'生成しました: {a.out}')
