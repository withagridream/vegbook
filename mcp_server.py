"""vegbook MCP サーバー（stdio方式）

Claude Code から直接呼び出せる農業データツール群。
tools:
  vegbook_search       - 作物検索（月・カテゴリ・難易度・環境）
  vegbook_detail       - 作物詳細取得
  vegbook_recommend    - 今月のおすすめ野菜
  vegbook_companion    - コンパニオンプランツ検索
  vegbook_glossary     - 農業用語検索
  vegbook_climate      - 地域別月別気候データ取得
  vegbook_harvest      - 作物別収穫量統計取得
  vegbook_diagnose     - 不足データの診断レポート
  vegbook_add_companion - コンパニオンプランツの追加
  vegbook_update_crop  - 作物フィールドの更新
"""
import sqlite3
from datetime import date
from pathlib import Path

from mcp.server.fastmcp import FastMCP

DB = Path(__file__).parent / 'vegbook.db'

mcp = FastMCP('vegbook')


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


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
        query += ' AND (c.sow_start <= ? AND c.sow_end >= ? OR c.harvest_start <= ? AND c.harvest_end >= ?)'
        params += [month, month, month, month]
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
    return results


# ── ② 作物詳細 ──────────────────────────────────────────────────────
@mcp.tool()
def vegbook_detail(name: str, lang: str = 'ja') -> dict:
    """作物の詳細情報を取得する。

    Args:
        name: 作物名（日本語または英語）
        lang: 出力言語（ja / en）
    """
    conn = _conn()
    row = conn.execute(
        '''SELECT c.*, cc.name AS category, cc.name_en AS category_en,
                  ge.name AS environment, ge.name_en AS environment_en
           FROM crops c
           JOIN crop_categories cc ON c.category_id = cc.id
           LEFT JOIN grow_environments ge ON c.environment_id = ge.id
           WHERE c.name = ? OR c.name_en = ?''',
        (name, name),
    ).fetchone()
    conn.close()

    if not row:
        return {'error': f'Crop "{name}" not found.'}

    if lang == 'en':
        return {
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
        return {
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
           WHERE c.sow_start <= ? AND c.sow_end >= ?
             AND c.difficulty <= 2
           ORDER BY c.difficulty, c.days_to_harvest''',
        (month, month),
    ).fetchall()
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
    return results


# ── ④ コンパニオンプランツ ──────────────────────────────────────────
@mcp.tool()
def vegbook_companion(crop_name: str, lang: str = 'ja') -> dict:
    """指定作物のコンパニオンプランツ（相性の良い・悪い組み合わせ）を返す。

    Args:
        crop_name: 作物名（日本語または英語）
        lang:      出力言語（ja / en）
    """
    conn = _conn()

    # 作物IDを取得
    crop = conn.execute(
        'SELECT id, name, name_en FROM crops WHERE name = ? OR name_en = ?',
        (crop_name, crop_name),
    ).fetchone()

    if not crop:
        conn.close()
        return {'error': f'Crop "{crop_name}" not found.'}

    rows = conn.execute(
        '''SELECT c2.name, c2.name_en, cp.effect, cp.effect_en, cp.is_positive
           FROM companion_plants cp
           JOIN crops c2 ON cp.companion_id = c2.id
           WHERE cp.crop_id = ?
           ORDER BY cp.is_positive DESC, c2.name''',
        (crop['id'],),
    ).fetchall()
    conn.close()

    good = []
    bad  = []
    for r in rows:
        entry = {
            'name': (r['name_en'] or r['name']) if lang == 'en' else r['name'],
            'effect': (r['effect_en'] or r['effect']) if lang == 'en' else r['effect'],
        }
        if r['is_positive']:
            good.append(entry)
        else:
            bad.append(entry)

    return {
        'crop': (crop['name_en'] or crop['name']) if lang == 'en' else crop['name'],
        'good_companions': good,
        'bad_companions': bad,
    }


# ── ⑤ 農業用語検索 ──────────────────────────────────────────────────
@mcp.tool()
def vegbook_glossary(query: str, lang: str = 'ja') -> list[dict]:
    """農業用語を検索する。

    Args:
        query: 検索キーワード（用語名・読み・カテゴリ）
        lang:  出力言語（ja / en）
    """
    conn = _conn()
    rows = conn.execute(
        '''SELECT term, reading, plain_ja, plain_en, category
           FROM glossary
           WHERE term LIKE ? OR reading LIKE ? OR plain_ja LIKE ? OR plain_en LIKE ?
           ORDER BY term''',
        (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'),
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
        return [{'error': f'Region "{region}" not found. Available: Kanto-Plain, Kinki, Kyushu-North, Tohoku, Hokkaido'}]

    query = '''
        SELECT year, month, avg_temp, precipitation
        FROM climate_monthly
        WHERE region_id = ?
    '''
    params: list = [reg['id']]

    if year is not None:
        query += ' AND year = ?'
        params.append(year)
    else:
        # 直近5年
        max_year = date.today().year
        query += ' AND year >= ?'
        params.append(max_year - 4)

    if month is not None:
        query += ' AND month = ?'
        params.append(month)

    query += ' ORDER BY year, month'
    rows = conn.execute(query, params).fetchall()
    conn.close()

    return [
        {
            'region': reg['name'],
            'year': r['year'],
            'month': r['month'],
            'avg_temp_c': r['avg_temp'],
            'precipitation_mm': r['precipitation'],
        }
        for r in rows
    ]


# ── ⑦ 収穫量統計 ────────────────────────────────────────────────────
@mcp.tool()
def vegbook_harvest_stats(
    crop_name: str,
    start_year: int = 2000,
    end_year: int | None = None,
) -> list[dict]:
    """作物別の全国収穫量統計（作付面積・収穫量・出荷量）を返す。

    Args:
        crop_name:  作物名（vegbookのcropsテーブルと同じ名称）
        start_year: 開始年（デフォルト2000年）
        end_year:   終了年（省略時は最新年）
    """
    if end_year is None:
        end_year = date.today().year

    conn = _conn()
    rows = conn.execute(
        '''SELECT year, area_ha, harvest_t, shipment_t
           FROM harvest_stats
           WHERE crop_name = ? AND year >= ? AND year <= ?
           ORDER BY year''',
        (crop_name, start_year, end_year),
    ).fetchall()
    conn.close()

    if not rows:
        return [{'error': f'No harvest data found for "{crop_name}".'}]

    return [
        {
            'crop_name': crop_name,
            'year': r['year'],
            'area_ha': r['area_ha'],
            'harvest_t': r['harvest_t'],
            'shipment_t': r['shipment_t'],
        }
        for r in rows
    ]


# ── ⑧ 不足データ診断 ────────────────────────────────────────────────
@mcp.tool()
def vegbook_diagnose() -> dict:
    """DBの不足データを診断してレポートする。

    以下を検出する:
    - companion_plantsに主作物として未登録の作物
    - seed_or_seedling が NULL の作物
    """
    conn = _conn()

    # companion_plantsに未登録の作物
    no_companion = conn.execute(
        '''SELECT id, name FROM crops
           WHERE id NOT IN (SELECT DISTINCT crop_id FROM companion_plants)
           ORDER BY id''',
    ).fetchall()

    # seed_or_seedling が NULL の作物
    no_seed_type = conn.execute(
        'SELECT id, name FROM crops WHERE seed_or_seedling IS NULL ORDER BY id',
    ).fetchall()

    conn.close()

    return {
        'companion_missing': [
            {'id': r['id'], 'name': r['name']} for r in no_companion
        ],
        'companion_missing_count': len(no_companion),
        'seed_type_missing': [
            {'id': r['id'], 'name': r['name']} for r in no_seed_type
        ],
        'seed_type_missing_count': len(no_seed_type),
    }


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
    """
    conn = _conn()

    crop = conn.execute(
        'SELECT id FROM crops WHERE name = ? OR name_en = ?',
        (crop_name, crop_name),
    ).fetchone()
    if not crop:
        conn.close()
        return {'error': f'Crop "{crop_name}" not found.'}

    companion = conn.execute(
        'SELECT id FROM crops WHERE name = ? OR name_en = ?',
        (companion_name, companion_name),
    ).fetchone()
    if not companion:
        conn.close()
        return {'error': f'Companion crop "{companion_name}" not found.'}

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
    """
    if field not in _UPDATABLE_FIELDS:
        return {
            'error': f'Field "{field}" cannot be updated.',
            'allowed_fields': sorted(_UPDATABLE_FIELDS),
        }

    conn = _conn()
    crop = conn.execute(
        'SELECT id, name FROM crops WHERE name = ? OR name_en = ?',
        (crop_name, crop_name),
    ).fetchone()
    if not crop:
        conn.close()
        return {'error': f'Crop "{crop_name}" not found.'}

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
