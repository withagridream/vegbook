"""気象庁から5地域の月別平均気温・降水量（2000年〜）を取得して data/incoming/climate_monthly.csv に書く。

DB（vegbook.db）には直接書かない（INSERT OR IGNORE では壊れた行が置き換わらないため）。
取り込み直しの手順は main() の docstring と MANUAL.md 第4章を参照。
"""
import csv
import urllib.request
import re
import time
from datetime import date
from pathlib import Path

OUT = Path(__file__).parent / 'data' / 'incoming' / 'climate_monthly.csv'

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


def main() -> None:
    """取得した値を data/incoming/climate_monthly.csv に書く（vegbook.db にも data/climate_monthly.csv にも直接書かない）。

    取り込み直しの手順：
      1. このスクリプトを実行する（外部通信あり：気象庁）
      2. data/incoming/climate_monthly.csv（region_id,year,month,avg_temp,precipitation）を data/climate_monthly.csv と見比べる
         （自然キー region_id+year+month で突き合わせる。既存の行は「壊れた行は置き換え、同じ値は据え置き」を目で確かめる）
      3. 置き換える行は id を保ったまま値だけ差し替え、新しい行は末尾に id を振って追加する
      4. data_issues.csv は region・year・month の自然キーで指しているので、取り込み直しで id が変わっても対応は崩れない。
         疑いが晴れた行の hide は削除する（削除は人が決める）
      5. python3 build_db.py --out 一時DB → 検査が通ったら vegbook.db に差し替える
    """
    rows: list[tuple] = []
    skipped = 0
    for region_id, (label, prec_no, block_no) in STATIONS.items():
        print(f'\n[{label}] region_id={region_id}')
        for year in range(START_YEAR, END_YEAR + 1):
            print(f'  {year}年 ', end='', flush=True)
            temps = fetch_monthly(prec_no, block_no, year, 'a1')
            time.sleep(0.5)
            precips = fetch_monthly(prec_no, block_no, year, 'p5')
            time.sleep(0.5)
            for month in range(1, 13):
                t, p = temps[month - 1], precips[month - 1]
                if t is None and p is None:
                    skipped += 1
                    continue
                rows.append((region_id, year, month, t, p))
            print('完了')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['region_id', 'year', 'month', 'avg_temp', 'precipitation'])
        for r in rows:
            w.writerow(['\\N' if v is None else v for v in r])
    print(f'\n書き出し: {len(rows)}行 / データなし: {skipped}件 → {OUT}')


if __name__ == '__main__':
    main()
