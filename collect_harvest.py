"""e-Stat APIから野菜生産出荷統計（全国・作付面積・収穫量・出荷量）を取得してDBに保存する。

使い方:
    python3 collect_harvest.py <e-stat APIキー>
"""
import sqlite3
import urllib.request
import urllib.parse
import json
import re
import time
import sys
from datetime import date
from pathlib import Path

DB = Path(__file__).parent / 'vegbook.db'

STAT_CODE = '00500215'

# e-Stat cat01コード → vegbook DB の crop_name マッピング（集計単位のみ）
# 旧形式（3桁ゼロ埋め）と新形式（5桁）の両方を収録
CAT01_MAP = {
    # 旧形式コード
    '003': 'ダイコン', '007': 'カブ', '008': 'にんじん', '012': 'ゴボウ',
    '013': 'レンコン', '014': 'ジャガイモ', '017': 'サトイモ',
    '022': '白菜', '026': '小松菜', '027': 'キャベツ', '031': 'チンゲン菜',
    '032': 'ほうれん草', '033': 'フキ', '035': '春菊', '036': 'セロリ',
    '037': 'アスパラガス', '038': 'カリフラワー', '039': 'ブロッコリー',
    '040': 'レタス', '044': 'ネギ', '048': 'ニラ', '049': '玉ねぎ',
    '050': 'ニンニク', '052': 'きゅうり', '055': 'かぼちゃ', '056': 'ナス',
    '059': 'トマト', '062': 'ピーマン', '065': 'とうもろこし',
    '066': 'サヤインゲン', '067': 'さやえんどう', '068': 'そら豆',
    '069': 'エダマメ', '070': 'しょうが', '072': 'いちご',
    '073': 'メロン', '074': 'スイカ',
    # 新形式コード（5桁）
    '13010': 'ダイコン', '13020': 'カブ', '13030': 'にんじん',
    '13040': 'ゴボウ', '13060': 'レンコン', '13620': 'ジャガイモ',
    '13630': 'サトイモ', '13650': 'ヤマイモ（長いも）',
    '23110': '白菜', '23200': '小松菜', '23170': 'キャベツ',
    '23210': 'チンゲン菜', '23180': 'ほうれん草', '23220': 'フキ',
    '23240': '春菊', '23290': 'セロリ', '23360': 'アスパラガス',
    '23320': 'カリフラワー', '23330': 'ブロッコリー', '23340': 'レタス',
    '23190': 'ネギ', '23250': 'ニラ', '23660': '玉ねぎ', '23260': 'ニンニク',
    '33410': 'きゅうり', '33420': 'かぼちゃ', '33430': 'ナス',
    '33440': 'トマト', '33450': 'ピーマン', '33470': 'とうもろこし',
    '33510': 'サヤインゲン', '33520': 'さやえんどう', '33560': 'そら豆',
    '33550': 'エダマメ', '43670': 'しょうが',
    '54670': 'いちご', '54700': 'メロン', '54760': 'スイカ',
    # 3桁コード（平成26〜令和元年系）
    '130': 'ダイコン', '170': 'カブ', '180': 'にんじん',
    '220': 'ゴボウ', '230': 'レンコン', '240': 'ジャガイモ',
    '270': 'サトイモ', '300': 'ヤマイモ（長いも）',
    '320': '白菜', '360': '小松菜', '370': 'キャベツ',
    '410': 'チンゲン菜', '420': 'ほうれん草', '430': 'フキ',
    '450': '春菊', '470': 'セロリ', '480': 'アスパラガス',
    '490': 'カリフラワー', '500': 'ブロッコリー', '510': 'レタス',
    '550': 'ネギ', '590': 'ニラ', '600': '玉ねぎ', '610': 'ニンニク',
    '630': 'きゅうり', '660': 'かぼちゃ', '670': 'ナス',
    '700': 'トマト', '730': 'ピーマン', '760': 'とうもろこし',
    '770': 'サヤインゲン', '780': 'さやえんどう', '800': 'そら豆',
    '810': 'エダマメ', '820': 'しょうが',
    '840': 'いちご', '850': 'メロン', '860': 'スイカ',
    # 4桁コード（2019〜2024年系）
    '1003': 'ダイコン', '1007': 'カブ', '1008': 'にんじん',
    '1012': 'ゴボウ', '1013': 'レンコン', '1014': 'ジャガイモ',
    '1017': 'サトイモ', '1020': 'ヤマイモ（長いも）',
    '1022': '白菜', '1026': '小松菜', '1027': 'キャベツ',
    '1031': 'チンゲン菜', '1032': 'ほうれん草', '1033': 'フキ',
    '1035': '春菊', '1037': 'セロリ', '1038': 'アスパラガス',
    '1039': 'カリフラワー', '1040': 'ブロッコリー', '1041': 'レタス',
    '1045': 'ネギ', '1049': 'ニラ', '1050': '玉ねぎ', '1051': 'ニンニク',
    '1053': 'きゅうり', '1056': 'かぼちゃ', '1057': 'ナス',
    '1060': 'トマト', '1063': 'ピーマン', '1066': 'とうもろこし',
    '1067': 'サヤインゲン', '1068': 'さやえんどう', '1070': 'そら豆',
    '1071': 'エダマメ', '1072': 'しょうが',
    '1074': 'いちご', '1075': 'メロン', '1076': 'スイカ',
}

# cat02 コード → 項目種別（旧形式2桁・新形式3桁の両方）
CAT02_MAP = {
    '01': 'area',   '001': 'area',      # 作付面積（ha）
    '03': 'harvest', '003': 'harvest',  # 収穫量（t）
    '04': 'shipment', '004': 'shipment', # 出荷量（t）
}


def parse_year(label: str) -> int | None:
    """平成X年産 / 平．X年産 / 令和X年産 / 西暦YYYY年 → 西暦年に変換する。"""
    # 平成（表記ゆれを吸収: 平成・平．・平.）
    m = re.search(r'平[成．.]?(\d+)年', label)
    if m:
        return 1988 + int(m.group(1))
    # 令和元年
    if '令和元年' in label:
        return 2019
    # 令和X年
    m = re.search(r'令和(\d+)年', label)
    if m:
        return 2018 + int(m.group(1))
    # 西暦4桁
    m = re.search(r'(\d{4})年', label)
    if m:
        return int(m.group(1))
    return None


def get_meta(api_key: str, stats_id: str) -> dict:
    """統計表のメタ情報を取得し、パース情報を返す。

    Returns dict with:
      'time_map':  {time_code: year}   通常形式
      'cat02_map': {cat02_code: (indicator, year)}  cat02に年が埋め込まれた形式
      'mode': 'normal' | 'cat02_year'
    """
    params = urllib.parse.urlencode({'appId': api_key, 'lang': 'J', 'statsDataId': stats_id})
    url = f'https://api.e-stat.go.jp/rest/3.0/app/json/getMetaInfo?{params}'
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            data = json.load(r)
    except Exception as e:
        print(f'  メタ取得失敗 ({stats_id}): {e}')
        return {}

    class_objs = (
        data.get('GET_META_INFO', {})
            .get('METADATA_INF', {})
            .get('CLASS_INF', {})
            .get('CLASS_OBJ', [])
    )
    if isinstance(class_objs, dict):
        class_objs = [class_objs]

    time_map:  dict[str, int] = {}
    cat02_map: dict[str, tuple] = {}

    for cls in class_objs:
        cid   = cls.get('@id', '')
        items = cls.get('CLASS', [])
        if isinstance(items, dict):
            items = [items]

        if cid == 'time':
            for item in items:
                code  = item.get('@code', '')
                label = item.get('@name', '')
                year  = parse_year(label)
                if year and year >= 2000:
                    time_map[code] = year

        elif cid == 'cat02':
            # cat02に年が埋め込まれているか確認（例：「収穫量_2019年産」）
            for item in items:
                code  = item.get('@code', '')
                label = item.get('@name', '')
                year  = parse_year(label)
                if year is None:
                    continue
                if label.startswith('作付面積'):
                    cat02_map[code] = ('area', year)
                elif label.startswith('収穫量'):
                    cat02_map[code] = ('harvest', year)
                elif label.startswith('出荷量'):
                    cat02_map[code] = ('shipment', year)

    if cat02_map:
        return {'mode': 'cat02_year', 'cat02_map': cat02_map}
    elif time_map:
        return {'mode': 'normal', 'time_map': time_map}
    return {}


def fetch_data(api_key: str, stats_id: str) -> list[dict]:
    params = urllib.parse.urlencode({
        'appId': api_key, 'lang': 'J',
        'statsDataId': stats_id, 'limit': 100000,
    })
    url = f'https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData?{params}'
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            data = json.load(r)
        values = (
            data.get('GET_STATS_DATA', {})
                .get('STATISTICAL_DATA', {})
                .get('DATA_INF', {})
                .get('VALUE', [])
        )
        return values if isinstance(values, list) else [values]
    except Exception as e:
        print(f'  データ取得失敗 ({stats_id}): {e}')
        return []


def search_target_tables(api_key: str) -> list[dict]:
    """全国集計表（2000年以降）をすべて検索して返す。"""
    keywords = ['全国の作付面積', '全国の作付面積・収穫量・出荷量']
    all_tables = []
    for kw in keywords:
        offset = 1
        while True:
            params = urllib.parse.urlencode({
                'appId': api_key, 'lang': 'J',
                'statsCode': STAT_CODE,
                'searchWord': kw,
                'limit': 100, 'startPosition': offset,
            })
            url = f'https://api.e-stat.go.jp/rest/3.0/app/json/getStatsList?{params}'
            try:
                with urllib.request.urlopen(url, timeout=20) as r:
                    data = json.load(r)
            except Exception as e:
                print(f'  表検索失敗: {e}')
                break

            tables = data.get('GET_STATS_LIST', {}).get('DATALIST_INF', {}).get('TABLE_INF', [])
            if isinstance(tables, dict):
                tables = [tables]
            if not tables:
                break
            all_tables.extend(tables)
            if len(tables) < 100:
                break
            offset += 100
            time.sleep(0.3)

    result = []
    for t in all_tables:
        survey = t.get('SURVEY_DATE', '')
        base_year = parse_year(t.get('STATISTICS_NAME', '') + ' ' + survey[:4] + '年')
        if base_year is None:
            try:
                base_year = int(survey[:4])
            except Exception:
                continue
        if base_year < 2000:
            continue
        title = t.get('TITLE', {}).get('$', '')
        if '全国の作付面積' in title and '収穫量' in title and '出荷量' in title:
            result.append({'id': t['@id'], 'title': title, 'survey': survey})

    # 重複排除
    seen = set()
    unique = []
    for t in result:
        if t['id'] not in seen:
            seen.add(t['id'])
            unique.append(t)
    return unique


def setup_table(conn: sqlite3.Connection) -> None:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS harvest_stats (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_name    TEXT NOT NULL,
            year         INTEGER NOT NULL,
            area_ha      REAL,
            harvest_t    REAL,
            shipment_t   REAL,
            source       TEXT DEFAULT 'e-Stat',
            UNIQUE(crop_name, year)
        )
    ''')
    conn.commit()


def main() -> None:
    if len(sys.argv) < 2:
        print('使い方: python3 collect_harvest.py <APIキー>')
        sys.exit(1)

    api_key = sys.argv[1]
    conn = sqlite3.connect(DB)
    setup_table(conn)

    print('対象表を検索中...')
    tables = search_target_tables(api_key)
    print(f'対象表: {len(tables)}件')

    inserted = 0
    skipped  = 0

    for tbl in tables:
        stats_id = tbl['id']
        print(f"  [{stats_id}] {tbl['title'][:40]}... ", end='', flush=True)

        meta = get_meta(api_key, stats_id)
        time.sleep(0.3)

        if not meta:
            print('（メタ情報なし・スキップ）')
            continue

        values = fetch_data(api_key, stats_id)
        time.sleep(0.5)

        mode     = meta.get('mode', '')
        time_map = meta.get('time_map', {})
        cat02_yr = meta.get('cat02_map', {})

        # {(crop_name, year): {area, harvest, shipment}}
        records: dict[tuple, dict] = {}

        for v in values:
            cat01 = v.get('@cat01', '')
            cat02 = v.get('@cat02', '')
            tcode = v.get('@time', '')

            crop_name = CAT01_MAP.get(cat01)
            if not crop_name:
                continue

            if mode == 'cat02_year':
                parsed = cat02_yr.get(cat02)
                if not parsed:
                    continue
                indicator, year = parsed
            else:
                indicator = CAT02_MAP.get(cat02)
                year      = time_map.get(tcode)
                if not (indicator and year):
                    continue

            val_str = v.get('$', '').replace(',', '').strip()
            try:
                val = float(val_str)
            except ValueError:
                continue

            key = (crop_name, year)
            if key not in records:
                records[key] = {'area': None, 'harvest': None, 'shipment': None}
            records[key][indicator] = val

        for (crop_name, year), vals in records.items():
            try:
                conn.execute(
                    '''INSERT OR IGNORE INTO harvest_stats
                       (crop_name, year, area_ha, harvest_t, shipment_t)
                       VALUES (?,?,?,?,?)''',
                    (crop_name, year, vals['area'], vals['harvest'], vals['shipment']),
                )
                if conn.execute('SELECT changes()').fetchone()[0]:
                    inserted += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f'    INSERT失敗 ({crop_name}/{year}): {e}')

        conn.commit()
        print(f'{len(records)}件処理')

    conn.close()
    print(f'\n挿入: {inserted}件 / スキップ（既存）: {skipped}件')

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM harvest_stats')
    print(f'harvest_stats 合計: {cur.fetchone()[0]}件')
    cur.execute('SELECT DISTINCT crop_name FROM harvest_stats ORDER BY crop_name')
    print('収録作物:', [r[0] for r in cur.fetchall()])
    cur.execute('SELECT MIN(year), MAX(year) FROM harvest_stats')
    print('年範囲:', cur.fetchone())
    conn.close()


if __name__ == '__main__':
    main()
