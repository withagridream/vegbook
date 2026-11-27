"""vegbook MCP サーバー（stdio方式）

Claude Code から直接呼び出せる農業データツール群。
tools:
  vegbook_search       - 作物検索（月・カテゴリ・難易度・環境）
  vegbook_detail       - 作物詳細取得
  vegbook_recommend    - 今月のおすすめ野菜
  vegbook_companion    - コンパニオンプランツ検索
  vegbook_glossary     - 農業用語検索
  vegbook_climate      - 地域別月別気候データ取得
  vegbook_harvest_stats - 作物別収穫量統計取得
  vegbook_diagnose     - DBの不足データの診断（互換用。vegbook_db_check と同じ）
  vegbook_db_check     - DBの不足データの診断（名前を中身に合わせた新名）
  vegbook_trouble      - 困りごと（症状→原因→条件→対策→出典）
  vegbook_ask          - 質問に関連する情報を出典つきで検索（FTS5）
  vegbook_add_companion - コンパニオンプランツの追加（既定で無効）
  vegbook_update_crop  - 作物フィールドの更新（既定で無効）

書き込み系ツールは、環境変数 VEGBOOK_ALLOW_WRITE=1 を設定して
起動したときだけ動く。それ以外は読み取り専用（mode=ro）で DB を開く。
"""
import os
import sqlite3
from datetime import date
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from vegbook_core import (
    STORAGE_METHODS, STORAGE_METHODS_EN, UNSOURCED, ask, kana_variants, resolve_crop,
    apply_crop_issues, issue_key, load_data_issues, load_row_issues, source_info, source_usable, storage_rows, trouble,
)

DB = Path(__file__).parent / 'vegbook.db'

__version__ = '2.0.0-dev'  # 2.0 開発中（リリース表記は段階2cの完了後に決める）

mcp = FastMCP('vegbook')


def _write_enabled() -> bool:
    """書き込み系ツールが有効か（環境変数 VEGBOOK_ALLOW_WRITE=1 のときだけ True）。"""
    return os.environ.get('VEGBOOK_ALLOW_WRITE') == '1'


_WRITE_DISABLED = {
    'error': 'このツールは既定で無効です（vegbook.db は読み取り専用で公開されています）。'
             '有効にするには、MCPサーバーの起動時に環境変数 VEGBOOK_ALLOW_WRITE=1 を設定してください。',
    'error_en': 'This tool is disabled by default (vegbook.db is read-only). '
                'Set the environment variable VEGBOOK_ALLOW_WRITE=1 when starting the MCP server to enable it.',
}


def _conn(write: bool = False) -> sqlite3.Connection:
    """DB 接続を返す。write=False（既定）は読み取り専用（mode=ro）。"""
    mode = 'rw' if write else 'ro'
    conn = sqlite3.connect(f'{DB.as_uri()}?mode={mode}', uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _in_month_sql(start: str, end: str) -> str:
    """月 m が [start, end] に入る条件のSQL断片（プレースホルダ4個: m, m, m, m）。

    start > end（例：11〜2月）は年をまたぐ範囲として扱う。
    """
    return (f'(({start} <= {end} AND {start} <= ? AND {end} >= ?)'
            f' OR ({start} > {end} AND ({start} <= ? OR {end} >= ?)))')


# 取り込み不良の疑いがあるデータ（DBの行は未修正。応急処置として値を返さない）
# 対象の行・列・警告文は data/data_issues.csv（DBの data_issues 表）が持つ。action='hide' の行の列は None にして返す。
# 出力のキー名（avg_temp_c など）とDBの列名の対応
_CLIMATE_COLS = {'avg_temp': 'avg_temp_c', 'precipitation': 'precipitation_mm'}

# 作物の表（crops）の列と、各ツールの出力キーの対応。data_issues の印（hide・note）を warnings に反映する。
# shown=その言語で表示している列、other=別言語の列（note のときだけ対象にする）
_TEXT_COLS = ('sunlight', 'watering', 'storage', 'harvest_sign', 'failure_points')
_NUM_COLS = {'days_to_harvest': 'days_to_harvest', 'temp_min': 'temp_min', 'temp_max': 'temp_max',
             'sow_start': 'sow_months', 'sow_end': 'sow_months',
             'harvest_start': 'harvest_months', 'harvest_end': 'harvest_months'}


def _detail_colmaps(lang: str, row: sqlite3.Row | None = None) -> tuple[dict[str, str], dict[str, str]]:
    """英語の出力で _en 列が空のとき、日本語欄の値に戻して出している。その場合は日本語の列も「表示している列」に数える
    （日本語欄が hide なら、戻さず None と警告にするため）。"""
    ja = {c: c for c in _TEXT_COLS}
    en = {c + '_en': c for c in _TEXT_COLS}
    shown, other = (en, ja) if lang == 'en' else (ja, en)
    shown = dict(shown)
    if lang == 'en' and row is not None:
        for c in _TEXT_COLS:
            if not row[c + '_en']:
                shown[c] = c
    return {**_NUM_COLS, **shown}, other


_LIST_COLS = {'days_to_harvest': 'days_to_harvest', 'harvest_start': 'harvest', 'harvest_end': 'harvest'}


def _ambiguity(res: dict) -> dict:
    """名前が複数の作物に当たったとき（Taro＝サトイモ・タロイモ など）、候補をすべて返す。"""
    if not res['also']:
        return {}
    return {'candidates': [res['crop']['name'], *res['also']],
            'candidates_note': '入力した名前は複数の作物に当たります。先頭の作物の結果を返しています。'
                               '別の作物なら、候補の名前（日本語）で指定し直してください。'}


_kana_variants = kana_variants  # 互換用の別名（実体は vegbook_core.kana_variants）


# ── ① 作物検索 ──────────────────────────────────────────────────────
@mcp.tool()
def vegbook_search(
    month: int | None = None,
    category: str | None = None,
    difficulty: int | None = None,
    environment: str | None = None,
    lang: str = 'ja',
) -> list[dict]:
    """作物を条件で検索する。

    Args:
        month:       播種または収穫が含まれる月（1〜12）
        category:    カテゴリ名（果菜類・葉モノ野菜・根菜類・ハーブ・豆類・イモ類）
        difficulty:  難易度（1=簡単 2=普通 3=難しい）
        environment: 栽培環境（ほ場・プランター・ベランダ・水耕栽培・室内）
        lang:        出力言語（ja / en）
    """
    conn = _conn()
    query = '''
        SELECT c.id, c.name, c.name_en, c.difficulty, c.days_to_harvest,
               c.sow_start, c.sow_end, c.harvest_start, c.harvest_end,
               cc.name AS category, cc.name_en AS category_en,
               ge.name AS environment, ge.name_en AS environment_en
        FROM crops c
        JOIN crop_categories cc ON c.category_id = cc.id
        LEFT JOIN grow_environments ge ON c.environment_id = ge.id
        WHERE 1=1
    '''
    params: list = []

    if month is not None:
        query += (' AND (' + _in_month_sql('c.sow_start', 'c.sow_end')
                  + ' OR ' + _in_month_sql('c.harvest_start', 'c.harvest_end') + ')')
        params += [month] * 8
    if category:
        query += ' AND cc.name LIKE ?'
        params.append(f'%{category}%')
    if difficulty is not None:
        query += ' AND c.difficulty = ?'
        params.append(difficulty)
    if environment:
        query += ' AND ge.name LIKE ?'
        params.append(f'%{environment}%')

    query += ' ORDER BY c.difficulty, c.name'
    rows = conn.execute(query, params).fetchall()
    issues = load_row_issues(conn, 'crops')
    conn.close()

    results = []
    for r in rows:
        if lang == 'en':
            results.append({
                'id': r['id'],
                'name': r['name_en'] or r['name'],
                'category': r['category_en'],
                'difficulty': r['difficulty'],
                'days_to_harvest': r['days_to_harvest'],
                'sow': f"{r['sow_start']}-{r['sow_end']}月",
                'harvest': f"{r['harvest_start']}-{r['harvest_end']}月",
                'environment': r['environment_en'],
            })
        else:
            results.append({
                'id': r['id'],
                'name': r['name'],
                'category': r['category'],
                'difficulty': r['difficulty'],
                'days_to_harvest': r['days_to_harvest'],
                'sow': f"{r['sow_start']}-{r['sow_end']}月",
                'harvest': f"{r['harvest_start']}-{r['harvest_end']}月",
                'environment': r['environment'],
            })
    cols = {'days_to_harvest': 'days_to_harvest', 'sow_start': 'sow', 'sow_end': 'sow',
            'harvest_start': 'harvest', 'harvest_end': 'harvest'}
    return [apply_crop_issues(it, r['name'], issues, cols) for it, r in zip(results, rows)]


# ── ② 作物詳細 ──────────────────────────────────────────────────────
def _detail_extras(conn: sqlite3.Connection, row: sqlite3.Row, lang: str) -> dict:
    """出典・地域・保存方法（方法ごと）を詳細に添える。"""
    region = None
    if row['region_id'] is not None:
        r = conn.execute('SELECT name FROM regions WHERE id = ?', (row['region_id'],)).fetchone()
        region = r['name'] if r else None
    srcs = conn.execute(
        'SELECT field, source_id, provisional FROM crop_field_sources WHERE crop_id = ? ORDER BY source_id, field',
        (row['id'],)
    ).fetchall()
    grouped: dict[int, list[str]] = {}
    confirmed: dict[int, bool] = {}   # 出典ごとに、引用箇所の確認済み（provisional=0）の列が1つでもあるか
    for x in srcs:
        grouped.setdefault(x['source_id'], []).append(x['field'])
        confirmed[x['source_id']] = confirmed.get(x['source_id'], False) or x['provisional'] == 0
    sources = [{'fields': f, 'source': source_info(conn, sid), 'provisional': not confirmed[sid]}
               for sid, f in grouped.items()]
    storage = storage_rows(conn, row['id'])
    for st in storage:
        if lang == 'en':
            st['method_label'] = STORAGE_METHODS_EN.get(st['method'], st['method'])
    return {
        'region': region,
        'region_note': None if region else '地域の指定なし（登録時に地域を区別していない値。全国共通とは限りません）',
        'sources': sources or UNSOURCED,
        'sources_note': ('列ごとの出典。ここに載っていない列は出典未登録です。'
                         'usable_as_evidence=false の出典（一括記載・列未特定・利用許諾なしなど）は、個別の値の根拠に使えません。'
                         if sources else None),
        # 根拠に使える出典が、引用箇所の確認済み（provisional=0）で付いているときだけ True
        'has_usable_source': any(source_usable(x['source']) and not x['provisional'] for x in sources),
        'storage_methods': storage,
    }


@mcp.tool()
def vegbook_detail(name: str, lang: str = 'ja') -> dict:
    """作物の詳細情報を取得する。

    Args:
        name: 作物名（日本語・英語・別名・表記ゆれ。ひらがな/カタカナどちらでも可）
        lang: 出力言語（ja / en）

    出典（sources）・地域（region）・保存方法（storage_methods。方法ごと）も返す。
    """
    conn = _conn()
    res = resolve_crop(conn, name)
    if not res['crop']:
        conn.close()
        return {'error': f'Crop "{name}" not found.', 'suggestions': res['suggestions']}
    row = conn.execute(
        '''SELECT c.*, cc.name AS category, cc.name_en AS category_en,
                  ge.name AS environment, ge.name_en AS environment_en
           FROM crops c
           JOIN crop_categories cc ON c.category_id = cc.id
           LEFT JOIN grow_environments ge ON c.environment_id = ge.id
           WHERE c.id = ?''',
        (res['crop']['id'],),
    ).fetchone()
    extras = _detail_extras(conn, row, lang)
    issues = load_row_issues(conn, 'crops')
    conn.close()

    if lang == 'en':
        out = {
            'name': row['name_en'] or row['name'],
            'name_ja': row['name'],
            'category': row['category_en'],
            'difficulty': row['difficulty'],
            'days_to_harvest': row['days_to_harvest'],
            'sow_months': f"{row['sow_start']}-{row['sow_end']}",
            'harvest_months': f"{row['harvest_start']}-{row['harvest_end']}",
            'sunlight': row['sunlight_en'] or row['sunlight'],
            'watering': row['watering_en'] or row['watering'],
            'temp_min': row['temp_min'],
            'temp_max': row['temp_max'],
            'seed_or_seedling': row['seed_or_seedling'],
            'planter_size': row['planter_size'],
            'yield_per_plant': row['yield_per_plant'],
            'storage': row['storage_en'] or row['storage'],
            'harvest_sign': row['harvest_sign_en'] or row['harvest_sign'],
            'failure_points': row['failure_points_en'] or row['failure_points'],
        }
    else:
        out = {
            'name': row['name'],
            'name_en': row['name_en'],
            'category': row['category'],
            'difficulty': row['difficulty'],
            'days_to_harvest': row['days_to_harvest'],
            'sow_months': f"{row['sow_start']}-{row['sow_end']}月",
            'harvest_months': f"{row['harvest_start']}-{row['harvest_end']}月",
            'sunlight': row['sunlight'],
            'watering': row['watering'],
            'temp_min': row['temp_min'],
            'temp_max': row['temp_max'],
            'seed_or_seedling': row['seed_or_seedling'],
            'planter_size': row['planter_size'],
            'yield_per_plant': row['yield_per_plant'],
            'storage': row['storage'],
            'harvest_sign': row['harvest_sign'],
            'failure_points': row['failure_points'],
        }
    if res['also']:
        out['also_matches'] = res['also']
    out.update(_ambiguity(res))
    out.update(extras)
    shown, other = _detail_colmaps(lang, row)
    return apply_crop_issues(out, row['name'], issues, shown, other)


# ── ③ 今月のおすすめ ────────────────────────────────────────────────
@mcp.tool()
def vegbook_recommend(month: int | None = None, lang: str = 'ja') -> list[dict]:
    """今月（または指定月）に播種できる難易度1〜2の作物を返す。

    Args:
        month: 対象月（省略時は今月）
        lang:  出力言語（ja / en）
    """
    if month is None:
        month = date.today().month

    conn = _conn()
    rows = conn.execute(
        '''SELECT c.id, c.name, c.name_en, c.difficulty, c.days_to_harvest,
                  c.harvest_start, c.harvest_end,
                  cc.name AS category, cc.name_en AS category_en
           FROM crops c
           JOIN crop_categories cc ON c.category_id = cc.id
           WHERE ''' + _in_month_sql('c.sow_start', 'c.sow_end') + '''
             AND c.difficulty <= 2
           ORDER BY c.difficulty, c.days_to_harvest''',
        (month, month, month, month),
    ).fetchall()
    issues = load_row_issues(conn, 'crops')
    conn.close()

    results = []
    for r in rows:
        if lang == 'en':
            results.append({
                'name': r['name_en'] or r['name'],
                'category': r['category_en'],
                'difficulty': r['difficulty'],
                'days_to_harvest': r['days_to_harvest'],
                'harvest': f"{r['harvest_start']}-{r['harvest_end']}月",
            })
        else:
            results.append({
                'name': r['name'],
                'category': r['category'],
                'difficulty': r['difficulty'],
                'days_to_harvest': r['days_to_harvest'],
                'harvest': f"{r['harvest_start']}-{r['harvest_end']}月",
            })
    return [apply_crop_issues(it, r['name'], issues, _LIST_COLS) for it, r in zip(results, rows)]


# ── ④ コンパニオンプランツ ──────────────────────────────────────────
@mcp.tool()
def vegbook_companion(crop_name: str, lang: str = 'ja') -> dict:
    """指定作物のコンパニオンプランツ（相性の良い・悪い組み合わせ）を返す。

    Args:
        crop_name: 作物名（日本語・英語・別名・表記ゆれ）
        lang:      出力言語（ja / en）

    登録の向きは問わず両方向から引く。相手の側にだけ登録がある組み合わせは
    registered_as='reverse' と示す（効果の説明文は登録した側の作物から見た書き方）。
    """
    conn = _conn()
    res = resolve_crop(conn, crop_name)
    crop = res['crop']
    if not crop:
        conn.close()
        return {'error': f'Crop "{crop_name}" not found.', 'suggestions': res['suggestions']}

    rows = conn.execute(
        '''SELECT c2.id AS oid, c2.name, c2.name_en, cp.effect, cp.effect_en, cp.is_positive, 'direct' AS d
           FROM companion_plants cp JOIN crops c2 ON cp.companion_id = c2.id
           WHERE cp.crop_id = ?
           UNION ALL
           SELECT c1.id AS oid, c1.name, c1.name_en, cp.effect, cp.effect_en, cp.is_positive, 'reverse' AS d
           FROM companion_plants cp JOIN crops c1 ON cp.crop_id = c1.id
           WHERE cp.companion_id = ?''',
        (crop['id'], crop['id']),
    ).fetchall()
    conn.close()

    good, bad = [], []
    seen: set[int] = set()
    for r in sorted(rows, key=lambda x: (x['d'] != 'direct', not x['is_positive'], x['name'])):
        if r['oid'] in seen:      # 両方向に登録がある相手は、正方向の登録を優先して1回だけ出す
            continue
        seen.add(r['oid'])
        entry = {
            'name': (r['name_en'] or r['name']) if lang == 'en' else r['name'],
            'effect': (r['effect_en'] or r['effect']) if lang == 'en' else r['effect'],
            'registered_as': r['d'],
        }
        (good if r['is_positive'] else bad).append(entry)
    out = {
        'crop': (crop['name_en'] or crop['name']) if lang == 'en' else crop['name'],
        'good_companions': good,
        'bad_companions': bad,
    }
    if res['also']:
        out['also_matches'] = res['also']
    out.update(_ambiguity(res))
    return out


# ── ⑤ 農業用語検索 ──────────────────────────────────────────────────
@mcp.tool()
def vegbook_glossary(query: str, lang: str = 'ja') -> list[dict]:
    """農業用語を検索する。

    Args:
        query: 検索キーワード（用語名・読み・カテゴリ）
        lang:  出力言語（ja / en）
    """
    conn = _conn()
    # カタカナ・ひらがな両方の表記で検索する
    variants = _kana_variants(query)
    cond = ' OR '.join(['term LIKE ? OR reading LIKE ? OR plain_ja LIKE ? OR plain_en LIKE ?'] * len(variants))
    params = [f'%{v}%' for v in variants for _ in range(4)]
    rows = conn.execute(
        f'''SELECT DISTINCT term, reading, plain_ja, plain_en, category
           FROM glossary
           WHERE {cond}
           ORDER BY term''',  # noqa: S608 – cond は固定文字列のみ
        params,
    ).fetchall()
    conn.close()

    results = []
    for r in rows:
        if lang == 'en':
            results.append({
                'term': r['term'],
                'reading': r['reading'],
                'description': r['plain_en'] or r['plain_ja'],
                'category': r['category'],
            })
        else:
            results.append({
                'term': r['term'],
                'reading': r['reading'],
                'description': r['plain_ja'],
                'category': r['category'],
            })
    return results


# ── ⑥ 気候データ ────────────────────────────────────────────────────
@mcp.tool()
def vegbook_climate(
    region: str,
    year: int | None = None,
    month: int | None = None,
) -> list[dict]:
    """地域別の月別平均気温・降水量を返す。

    Args:
        region: 地域名（関東平野・近畿・九州北部・東北・北海道）または部分一致
        year:   対象年（省略時は直近5年）
        month:  対象月（省略時は全月）
    """
    conn = _conn()

    # 地域IDを取得
    reg = conn.execute(
        'SELECT id, name FROM regions WHERE name LIKE ?', (f'%{region}%',)
    ).fetchone()
    if not reg:
        conn.close()
        return [{'error': f'Region "{region}" not found. Available (Japanese names only / 日本語名で指定): 関東平野, 近畿, 九州北部, 東北, 北海道'}]

    query = '''
        SELECT id, year, month, avg_temp, precipitation
        FROM climate_monthly
        WHERE region_id = ?
    '''
    params: list = [reg['id']]

    if year is not None:
        query += ' AND year = ?'
        params.append(year)
    else:
        # 直近5年（今年ではなく、この地域のデータにある最新の年から数える。今年の値はまだ入っていないため）
        latest = conn.execute('SELECT MAX(year) FROM climate_monthly WHERE region_id = ?', (reg['id'],)).fetchone()[0]
        query += ' AND year >= ?'
        params.append((latest if latest is not None else date.today().year) - 4)

    if month is not None:
        query += ' AND month = ?'
        params.append(month)

    query += ' ORDER BY year, month'
    rows = conn.execute(query, params).fetchall()
    issues = load_data_issues(conn, 'climate_monthly')
    conn.close()

    results = []
    for r in rows:
        item = {
            'region': reg['name'],
            'year': r['year'],
            'month': r['month'],
            'avg_temp_c': r['avg_temp'],
            'precipitation_mm': r['precipitation'],
        }
        key = issue_key(region=reg['name'], year=r['year'], month=r['month'])   # 自然キー（行idは使わない）
        if key in issues:
            cols, note = issues[key]
            for col in cols:
                item[_CLIMATE_COLS.get(col, col)] = None
            item['warning'] = note
        results.append(item)
    return results


# ── ⑦ 収穫量統計 ────────────────────────────────────────────────────
@mcp.tool()
def vegbook_harvest_stats(
    crop_name: str,
    start_year: int = 2000,
    end_year: int | None = None,
) -> list[dict]:
    """作物別の全国収穫量統計（作付面積・収穫量・出荷量）を返す。

    Args:
        crop_name:  作物名（日本語。カタカナ・ひらがなどちらでも可）
        start_year: 開始年（デフォルト2000年）
        end_year:   終了年（省略時は最新年）
    """
    if end_year is None:
        end_year = date.today().year

    conn = _conn()
    # 作物名は別名・表記ゆれも受け付ける（解決できなければ入力のかな違いで直接探す）
    res = resolve_crop(conn, crop_name)
    _v = [res['crop']['name']] if res['crop'] else _kana_variants(crop_name)
    _ph = ','.join('?' * len(_v))
    rows = conn.execute(
        f'''SELECT id, crop_name, year, area_ha, harvest_t, shipment_t
           FROM harvest_stats
           WHERE crop_name IN ({_ph}) AND year >= ? AND year <= ?
           ORDER BY crop_name, year''',  # noqa: S608 – _ph は ? のみ
        (*_v, start_year, end_year),
    ).fetchall()
    issues = load_data_issues(conn, 'harvest_stats')
    conn.close()

    if not rows:
        return [{'error': f'No harvest data found for "{crop_name}".'}]

    results = []
    for r in rows:
        item = {
            'crop_name': r['crop_name'],
            'year': r['year'],
            'area_ha': r['area_ha'],
            'harvest_t': r['harvest_t'],
            'shipment_t': r['shipment_t'],
        }
        key = issue_key(crop_name=r['crop_name'], year=r['year'])   # 自然キー（行idは使わない）
        if key in issues:
            cols, note = issues[key]
            for col in cols:
                item[col] = None
            item['warning'] = note
        results.append(item)
    return results


# ── ⑧ 不足データ診断 ────────────────────────────────────────────────
def _db_check() -> dict:
    conn = _conn()
    no_companion = conn.execute(
        '''SELECT id, name FROM crops
           WHERE id NOT IN (SELECT DISTINCT crop_id FROM companion_plants)
             AND id NOT IN (SELECT DISTINCT companion_id FROM companion_plants)
           ORDER BY id''').fetchall()
    no_seed_type = conn.execute(
        'SELECT id, name FROM crops WHERE seed_or_seedling IS NULL ORDER BY id').fetchall()
    no_storage = conn.execute(
        'SELECT id, name FROM crops WHERE id NOT IN (SELECT crop_id FROM crop_storage) ORDER BY id').fetchall()
    n_crops = conn.execute('SELECT COUNT(*) FROM crops').fetchone()[0]
    # 根拠に使える出典（usable_as_evidence=1）が、引用箇所の確認済み（provisional=0）で付いた作物だけを数える。
    # 使えない出典だけの作物は別に数える
    n_srcd = conn.execute(
        'SELECT COUNT(DISTINCT f.crop_id) FROM crop_field_sources f JOIN sources s ON s.id = f.source_id '
        'WHERE s.usable_as_evidence = 1 AND f.provisional = 0').fetchone()[0]
    n_any = conn.execute('SELECT COUNT(DISTINCT crop_id) FROM crop_field_sources').fetchone()[0]
    troubles = conn.execute(
        'SELECT COUNT(*), SUM(provisional) FROM troubles').fetchone()
    conn.close()
    return {
        'companion_missing': [{'id': r['id'], 'name': r['name']} for r in no_companion],
        'companion_missing_count': len(no_companion),
        'seed_type_missing': [{'id': r['id'], 'name': r['name']} for r in no_seed_type],
        'seed_type_missing_count': len(no_seed_type),
        'storage_missing_count': len(no_storage),
        'crops_with_any_source': n_srcd,                      # 根拠に使える出典が付いた作物
        'crops_with_unusable_source_only': n_any - n_srcd,   # 出典の記載はあるが根拠に使えないものだけ
        'crops_without_source': n_crops - n_srcd,
        'troubles_total': troubles[0], 'troubles_provisional': troubles[1] or 0,
    }


@mcp.tool()
def vegbook_db_check() -> dict:
    """DB の不足データを診断してレポートする（旧名 vegbook_diagnose）。

    検出する内容: コンパニオン登録が0件（どちら向きにも）の作物 / seed_or_seedling が NULL の作物 /
    保存方法が未登録の作物 / 出典が1つも付いていない作物の数 / 困りごとの件数（仮抽出の数）。
    ※ 栽培の診断（症状の原因）ではない。症状から原因を引くには vegbook_trouble を使う。
    """
    return _db_check()


@mcp.tool()
def vegbook_diagnose() -> dict:
    """（互換用）vegbook_db_check と同じ。名前は「DBの不足データ診断」の意味で、栽培の診断ではない。

    症状から原因を調べるには vegbook_trouble / vegbook_ask を使う。
    """
    return _db_check()


# ── ⑪ 困りごと・質問検索 ────────────────────────────────────────────
@mcp.tool()
def vegbook_trouble(query: str, crop: str | None = None, lang: str = 'ja', phase: str | None = None) -> dict:
    """「◯◯に困ったら」：症状から、原因（複数）・条件・予防/対策・出典を返す。

    Args:
        query: 症状や困りごと（例：「実が割れる」「葉が黄色い」「すが入る」）
        crop:  作物名（省略可。日本語・英語・別名・表記ゆれ）
        lang:  出力言語（ja / en）
        phase: growing（栽培中）/ postharvest（収穫後）。省略時は両方

    出典のない項目は「出典未登録」と明示する。provisional=true は既存の文章から機械的に
    拾った仮の項目で、根拠として使う前に原典で確かめる必要がある。
    農薬を使う対策には必ず caution（登録のある作物にだけ使う等）が付く。
    """
    conn = _conn()
    out = trouble(conn, query, crop, lang, phase)
    conn.close()
    return out


@mcp.tool()
def vegbook_ask(query: str, crop: str | None = None, lang: str = 'ja') -> dict:
    """質問に関連する情報を、出典つきで返す（困りごと・保存方法・関連する文章を全文検索）。

    Args:
        query: 質問（例：「大根 干す」「トマト 冷蔵庫」「アブラムシ」「トマト 保存」）
        crop:  作物名（省略時は質問文から探す）
        lang:  出力言語（ja / en）。文章検索の対象言語

    保存方法の語（冷蔵・常温・冷凍・干す・漬ける・追熟・土に埋める）が含まれると、
    その作物の保存方法（crop_storage）を方法ごとに返す。登録がなければ「未登録」と返す。
    出典のないものは「出典未登録」と明示する。
    """
    conn = _conn()
    out = ask(conn, query, crop, lang)
    conn.close()
    return out


# ── ⑨ コンパニオンプランツ追加 ──────────────────────────────────────
@mcp.tool()
def vegbook_add_companion(
    crop_name: str,
    companion_name: str,
    effect: str,
    is_positive: bool,
    effect_en: str = '',
) -> dict:
    """コンパニオンプランツのデータを追加する。

    Args:
        crop_name:      主作物名（日本語）
        companion_name: 相性の相手作物名（日本語）
        effect:         効果の説明（日本語）
        is_positive:    True=相性良い / False=相性悪い
        effect_en:      効果の説明（英語・省略可）

    既定では無効。環境変数 VEGBOOK_ALLOW_WRITE=1 で起動したときだけ動く。
    """
    if not _write_enabled():
        return dict(_WRITE_DISABLED)
    conn = _conn(write=True)

    r1 = resolve_crop(conn, crop_name)
    crop = r1['crop']
    if not crop:
        conn.close()
        return {'error': f'Crop "{crop_name}" not found.', 'suggestions': r1['suggestions']}
    r2 = resolve_crop(conn, companion_name)
    companion = r2['crop']
    if not companion:
        conn.close()
        return {'error': f'Companion crop "{companion_name}" not found.', 'suggestions': r2['suggestions']}

    # 重複チェック
    existing = conn.execute(
        'SELECT id FROM companion_plants WHERE crop_id = ? AND companion_id = ?',
        (crop['id'], companion['id']),
    ).fetchone()
    if existing:
        conn.close()
        return {'error': f'"{crop_name}" × "{companion_name}" is already registered (id={existing["id"]}).'}

    conn.execute(
        '''INSERT INTO companion_plants(crop_id, companion_id, effect, is_positive, effect_en)
           VALUES (?, ?, ?, ?, ?)''',
        (crop['id'], companion['id'], effect, 1 if is_positive else 0, effect_en),
    )
    conn.commit()
    new_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()

    return {
        'status': 'added',
        'id': new_id,
        'crop': crop_name,
        'companion': companion_name,
        'is_positive': is_positive,
        'effect_ja': effect,
        'effect_en': effect_en,
    }


# ── ⑩ 作物フィールド更新 ─────────────────────────────────────────────
# 値の検証ルール：整数の範囲 / 実数の範囲 / 文字列の最大長
_INT_RANGE = {
    'sow_start': (1, 12), 'sow_end': (1, 12), 'harvest_start': (1, 12), 'harvest_end': (1, 12),
    'difficulty': (1, 3), 'days_to_harvest': (1, 1000),
}
_REAL_RANGE = {'temp_min': (-30.0, 60.0), 'temp_max': (-30.0, 60.0)}
_TEXT_MAX = 2000


def _validate_value(conn: sqlite3.Connection, crop_id: int, field: str, value: str):
    """更新値を検証して、DB に入れる型（int / float / str）にして返す。不正なら ValueError。"""
    if field in _INT_RANGE:
        lo, hi = _INT_RANGE[field]
        try:
            f = float(str(value).strip())
        except ValueError:
            raise ValueError(f'整数で指定してください（{lo}〜{hi}）') from None
        if f != int(f) or not lo <= int(f) <= hi:
            raise ValueError(f'{lo}〜{hi} の整数で指定してください')
        return int(f)
    if field in _REAL_RANGE:
        lo, hi = _REAL_RANGE[field]
        try:
            f = float(str(value).strip())
        except ValueError:
            raise ValueError(f'数値で指定してください（{lo}〜{hi}）℃') from None
        if not lo <= f <= hi:
            raise ValueError(f'{lo}〜{hi} の範囲で指定してください')
        row = conn.execute('SELECT temp_min, temp_max FROM crops WHERE id = ?', (crop_id,)).fetchone()
        tmin = f if field == 'temp_min' else row['temp_min']
        tmax = f if field == 'temp_max' else row['temp_max']
        if tmin is not None and tmax is not None and tmin >= tmax:
            raise ValueError(f'temp_min（{tmin}）は temp_max（{tmax}）より小さくしてください')
        return f
    text = str(value).strip()
    if not text:
        raise ValueError('空の値は指定できません')
    if len(text) > _TEXT_MAX:
        raise ValueError(f'{_TEXT_MAX}文字以内で指定してください')
    return text


# 更新を許可するフィールドのホワイトリスト
_UPDATABLE_FIELDS = {
    'seed_or_seedling', 'planter_size', 'yield_per_plant',
    'storage', 'harvest_sign', 'failure_points',
    'sunlight', 'watering', 'temp_min', 'temp_max',
    'sow_start', 'sow_end', 'harvest_start', 'harvest_end',
    'days_to_harvest', 'difficulty',
}


@mcp.tool()
def vegbook_update_crop(crop_name: str, field: str, value: str) -> dict:
    """作物の指定フィールドを更新する。

    Args:
        crop_name: 作物名（日本語または英語）
        field:     更新するフィールド名。指定可能:
                   seed_or_seedling / planter_size / yield_per_plant /
                   storage / harvest_sign / failure_points /
                   sunlight / watering / temp_min / temp_max /
                   sow_start / sow_end / harvest_start / harvest_end /
                   days_to_harvest / difficulty
        value:     設定する値

    既定では無効。環境変数 VEGBOOK_ALLOW_WRITE=1 で起動したときだけ動く。
    """
    if not _write_enabled():
        return dict(_WRITE_DISABLED)
    if field not in _UPDATABLE_FIELDS:
        return {
            'error': f'Field "{field}" cannot be updated.',
            'allowed_fields': sorted(_UPDATABLE_FIELDS),
        }

    conn = _conn(write=True)
    res = resolve_crop(conn, crop_name)
    crop = res['crop']
    if not crop:
        conn.close()
        return {'error': f'Crop "{crop_name}" not found.', 'suggestions': res['suggestions']}

    # 値の検証（型・範囲）。通らなければ書き込まない
    try:
        value = _validate_value(conn, crop['id'], field, value)
    except ValueError as e:
        conn.close()
        return {'error': f'Invalid value for "{field}": {e}', 'field': field, 'value': value}

    conn.execute(
        f'UPDATE crops SET {field} = ? WHERE id = ?',  # noqa: S608 – field はホワイトリスト済み
        (value, crop['id']),
    )
    conn.commit()
    conn.close()

    return {
        'status': 'updated',
        'crop_name': crop['name'],
        'field': field,
        'value': value,
    }


if __name__ == '__main__':
    mcp.run(transport='stdio')
