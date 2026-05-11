"""気象庁から5地域の月別平均気温・降水量（2000年〜）を取得してDBに保存する。"""
import sqlite3
import urllib.request
import re
import time
from datetime import date
from pathlib import Path

DB = Path(__file__).parent / 'vegbook.db'

# 気象庁の観測所コード（地域IDに対応）
STATIONS = {
    1: ('関東平野/東京', 44, 47662),
    2: ('近畿/大阪',    62, 47772),
    3: ('九州北部/福岡', 82, 47807),
    4: ('東北/仙台',    34, 47590),
    5: ('北海道/札幌',  14, 47412),
}

START_YEAR = 2000
END_YEAR   = date.today().year


def fetch_monthly(prec_no: int, block_no: int, year: int, view: str) -> list[float | None]:
    """気象庁の月別値ページから12ヶ月分の数値を返す。取得失敗は None。"""
    url = (
        f'https://www.data.jma.go.jp/obd/stats/etrn/view/monthly_s3.php'
        f'?prec_no={prec_no}&block_no={block_no}&year={year}&month=&day=&view={view}'
    )
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=20) as r:
            html = r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f'  取得失敗 ({year}/{view}): {e}')
        return [None] * 12

    rows = re.findall(r'class="mtx"[^>]*>(.*?)</tr>', html, re.DOTALL)
    for row in rows:
        nums = re.findall(r'>([-\d.]+)<', row)
        if not nums:
            continue
        # 先頭が対象年なら月別データが続く
        try:
            if int(nums[0]) == year and len(nums) >= 13:
                return [float(v) for v in nums[1:13]]
        except ValueError:
            continue
    return [None] * 12


def setup_table(conn: sqlite3.Connection) -> None:
    conn.execute('''
        CREATE TABLE IF NOT EXISTS climate_monthly (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            region_id    INTEGER NOT NULL,
            year         INTEGER NOT NULL,
            month        INTEGER NOT NULL,
            avg_temp     REAL,
            precipitation REAL,
            UNIQUE(region_id, year, month),
            FOREIGN KEY(region_id) REFERENCES regions(id)
        )
    ''')
    conn.commit()


def main() -> None:
    conn = sqlite3.connect(DB)
    setup_table(conn)

    total_inserted = 0
    total_skipped  = 0

    for region_id, (label, prec_no, block_no) in STATIONS.items():
        print(f'\n[{label}] region_id={region_id}')
        for year in range(START_YEAR, END_YEAR + 1):
            print(f'  {year}年 ', end='', flush=True)
            temps  = fetch_monthly(prec_no, block_no, year, 'a1')
            time.sleep(0.5)
            precips = fetch_monthly(prec_no, block_no, year, 'p5')
            time.sleep(0.5)

            for month in range(1, 13):
                t = temps[month - 1]
                p = precips[month - 1]
                if t is None and p is None:
                    total_skipped += 1
                    continue
                try:
                    conn.execute(
                        '''INSERT OR IGNORE INTO climate_monthly
                           (region_id, year, month, avg_temp, precipitation)
                           VALUES (?,?,?,?,?)''',
                        (region_id, year, month, t, p),
                    )
                    if conn.execute('SELECT changes()').fetchone()[0]:
                        total_inserted += 1
                    else:
                        total_skipped += 1
                except Exception as e:
                    print(f'INSERT失敗: {e}')
            conn.commit()
            print('完了')

    conn.close()
    print(f'\n挿入: {total_inserted}件 / スキップ（既存・データなし）: {total_skipped}件')

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM climate_monthly')
    print(f'climate_monthly 合計: {cur.fetchone()[0]}件')
    conn.close()


if __name__ == '__main__':
    main()
