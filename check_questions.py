"""答えるべき問い（data/questions.csv）を vegbook_trouble / vegbook_ask の中身に投げて、
答え（原因と出典）が返ったか・空だったか・的外れだったかを一覧にする検収スクリプト（標準ライブラリのみ）。

使い方:
    python3 check_questions.py [--db vegbook.db] [--verbose] [--csv 結果CSV]

判定（1問ごと）:
  sourced      答えが返り、根拠にできる出典が付いている（provisional=0 かつ 根拠に使える出典）  ← 答えられた
  provisional  答えは返ったが、仮の行・出典未登録・根拠に使えない出典のみ                      ← 仮の答え（根拠にできない）
  link_missing 関連する既存の記述はあるが、原因につながっていない                             ← 理由：つながりがない
  no_data      該当するデータがない                                                          ← 理由：データがない
  fail         答えが返ったが、問いに合っていない（不合格。理由は下の3つ）
                 crop_mismatch          返った症状の作物（作物群）が、問いの作物（作物群）と違う
                 why_storage_only       「なぜ」の問い（why）に、保存方法しか返らなかった（原因がない）
                 expected_terms_missing 期待する原因の語（questions.expected_terms）が原因の名前に1つも含まれない
                 expected_method_missing 期待する保存方法（questions.expected_method）が返らない
                 reason_missing         方法の理由（reason）の問いで、理由の語が答えにない
  undecidable  答えは返ったが、期待語・期待する保存方法が空で、合っているか判定できない（合格にしない）
問いの型（qtype）：why=原因を問う / how=方法を問う / what=事実・定義・期間を問う。
検収の基準。公的資料による出典つきの入力の進み具合は sourced の件数で見る。
"""
import argparse
import csv
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

from vegbook_core import ask, trouble, _trigrams

HERE = Path(__file__).parent
REL_SECTIONS = {'growing': ('failure_points', 'harvest_sign', 'watering', 'sunlight', 'trouble_growing'),
                'postharvest': ('storage', 'trouble_postharvest')}
ORDER = ['sourced', 'provisional', 'link_missing', 'no_data', 'fail', 'undecidable']
FAIL_REASONS = ['crop_mismatch', 'why_storage_only', 'expected_terms_missing', 'expected_method_missing', 'reason_missing']


def _crop_category(conn: sqlite3.Connection, crop_name: str | None) -> str | None:
    if not crop_name:
        return None
    r = conn.execute('SELECT cc.name FROM crops c JOIN crop_categories cc ON cc.id = c.category_id WHERE c.name = ?',
                     (crop_name,)).fetchone()
    return r[0] if r else None


def _crop_ok(conn: sqlite3.Connection, tr: dict, asked_crop: str | None, group: str | None) -> bool:
    """返った症状の作物が問いに合うか。作物を問わない症状（crop が空）は合う扱い。"""
    if tr['crop'] is None:
        return True
    if asked_crop:                       # 問いの作物（質問文から検出した作物を含む）と同じ作物か
        return tr['crop'] == asked_crop
    return _crop_category(conn, tr['crop']) == group   # 作物を問わない問い：作物群が同じか


def _terms_hit(text: str, terms: list[str]) -> bool:
    return any(t in text for t in terms)


def _fail(code: str, msg: str) -> tuple[str, str]:
    return 'fail', f'fail:{code}:{msg}'


def judge(conn: sqlite3.Connection, q: sqlite3.Row) -> tuple[str, str]:
    """1問を判定する。戻り値は (判定, 理由)。fail の理由は「fail:理由コード:説明」の形。

    期待語（expected_terms）の照合は原因の名前だけで行う（対策文は見ない）。
    例外：方法の理由（reason）と先人の智慧（wisdom=1）は、対策文・保存方法の手順も見る。
    期待語も期待する保存方法も空の問いは、答えが返っても合格にせず undecidable（判定不能）にする。
    出典つき（sourced）は、出典のある原因（保存方法）そのものが期待語に当たるときだけ（仮の行で当たった合格は provisional）。
    """
    crop = q['crop']
    qt = q['qtype']
    t = trouble(conn, q['question'], crop, 'ja', q['phase'])
    a = ask(conn, q['question'], crop, 'ja')
    if 'error' in t:
        return 'no_data', f'作物名を解決できない: {crop}'
    asked_crop = t['crop']               # 解決された作物名（問いの作物、または質問文から検出した作物）
    trs = t['troubles']
    matched = [tr for tr in trs if _crop_ok(conn, tr, asked_crop, q['crop_group'])]
    causes = [c for tr in matched for c in tr['causes']]
    storage = a.get('storage') or []
    terms = [x for x in (q['expected_terms'] or '').split(';') if x]
    methods = [x for x in (q['expected_method'] or '').split(';') if x]

    def names(cs: list[dict]) -> str:
        return ''.join(c['cause'] for c in cs)

    def wide(cs: list[dict], st: list[dict]) -> str:   # 原因の名前＋対策文＋保存方法の手順・注意
        return (names(cs) + ''.join(r['text'] for c in cs for r in c['remedies'])
                + ''.join((s['steps'] or '') + (s['caution'] or '') for s in st))

    def done(status: str, why: str) -> tuple[str, str]:
        if status in ('sourced', 'provisional') and not terms and not methods:
            return 'undecidable', '期待語・期待する保存方法が空のため、答えが合っているか判定できない'
        return status, why

    # 保存方法の行が返ったとき（why 以外の問いの答えになる）
    if qt != 'why' and storage:
        if methods and not any(s['method'] in methods for s in storage):
            got = '・'.join(sorted({s['method'] for s in storage}))
            return _fail('expected_method_missing', f'期待する保存方法（{"・".join(methods)}）が返らない（返った方法: {got}）')
        use = [s for s in storage if not methods or s['method'] in methods]
        if qt == 'reason' and terms and not _terms_hit(wide(causes, use), terms):
            return _fail('reason_missing', f'方法は返ったが、理由の語（{"・".join(terms[:4])}…）がない')
        ev = [s for s in use if s['has_source']]
        # 方法の理由（reason）は、出典のある保存方法の側で理由の語に当たるときだけ出典つきにする
        if ev and qt == 'reason' and terms and not _terms_hit(wide(causes, ev), terms):
            ev = []
        if ev:
            return done('sourced', f'保存方法{len(ev)}件（出典あり）')
        return done('provisional', f'保存方法{len(use)}件（出典未登録・仮抽出）')
    if causes:
        text = wide(causes, []) if (qt == 'reason' or q['wisdom']) else names(causes)
        if terms and not _terms_hit(text, terms):
            code = 'reason_missing' if qt == 'reason' else 'expected_terms_missing'
            return _fail(code, f'原因{len(causes)}件の名前に期待する語（{"・".join(terms[:4])}…）がない')
        # 出典つき（sourced）は、出典のある原因そのものが期待語に当たるときだけ。
        # 期待語には仮の原因で当たり、出典は別の原因にある、という合格を出さない
        ev = [c for c in causes if c['evidence_count'] > 0]
        ev_text = wide(ev, []) if (qt == 'reason' or q['wisdom']) else names(ev)
        if ev and (not terms or _terms_hit(ev_text, terms)):
            return done('sourced', f'原因{len(ev)}件（出典あり）')
        if ev:
            return done('provisional', f'原因{len(causes)}件（出典つきの原因{len(ev)}件は期待する語に当たらない・残りは仮抽出）')
        return done('provisional', f'原因{len(causes)}件（出典未登録・仮抽出）')
    if trs and not matched:
        return _fail('crop_mismatch', f'返った症状{len(trs)}件の作物が問いと違う（{trs[0]["crop"]}など）')
    if qt == 'why' and storage:
        return _fail('why_storage_only', f'原因の問いに保存方法{len(storage)}件しか返らない')
    # 関連する文章があるか（質問と3文字の重なりが2つ以上あるもの）
    qtri = _trigrams(q['question'])
    rel = [p for p in a.get('passages', []) if p['section'] in REL_SECTIONS[q['phase']]
           and len(qtri & _trigrams(p['text'])) >= 2]
    if rel:
        return 'link_missing', '関連する既存の記述はあるが、症状→原因につながっていない'
    return 'no_data', '該当するデータがない'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--db', type=Path, default=HERE / 'vegbook.db')
    ap.add_argument('--verbose', action='store_true', help='1問ずつ表示')
    ap.add_argument('--csv', type=Path, help='結果をCSVに書く')
    a = ap.parse_args()
    conn = sqlite3.connect(f'{a.db.resolve().as_uri()}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    qs = conn.execute('SELECT * FROM questions ORDER BY id').fetchall()
    res = []
    for q in qs:
        st, why = judge(conn, q)
        res.append((q, st, why))
        if a.verbose:
            print(f'{q["id"]:>3} [{st:<12}] {q["crop_group"]}/{q["phase"]}/{q["crop"] or "-"}: {q["question"]}  … {why}')
    order = ORDER
    print('\n=== 作物群 × 判定 ===')
    print(f'{"作物群":<10}' + ''.join(f'{o:>14}' for o in order) + f'{"計":>6}')
    by = defaultdict(Counter)
    for q, st, _ in res:
        by[q['crop_group']][st] += 1
    for g, cnt in by.items():
        print(f'{g:<10}' + ''.join(f'{cnt[o]:>14}' for o in order) + f'{sum(cnt.values()):>6}')
    tot = Counter(st for _, st, _ in res)
    print(f'{"全体":<10}' + ''.join(f'{tot[o]:>14}' for o in order) + f'{len(res):>6}')
    print('\n=== 段階（栽培中/収穫後）===')
    for ph in ('growing', 'postharvest'):
        c = Counter(st for q, st, _ in res if q['phase'] == ph)
        print(f'{ph:<12}' + ' '.join(f'{o}={c[o]}' for o in order))
    wis = [(q, st) for q, st, _ in res if q['wisdom']]
    cw = Counter(st for _, st in wis)
    print(f'\n=== 「先人の智慧」で答えるべき問い: {len(wis)}件 ===  ' + ' '.join(f'{o}={cw[o]}' for o in order))
    fails = Counter(why.split(':')[1] for _, st, why in res if st == 'fail')
    print('\n=== 不合格（fail）の内訳 ===  ' + ' '.join(f'{k}={fails[k]}' for k in FAIL_REASONS))
    print('=== 問いの型 × 判定 ===')
    for qt in ('why', 'how', 'what', 'reason'):
        c = Counter(st for q, st, _ in res if q['qtype'] == qt)
        print(f'{qt:<8}' + ' '.join(f'{o}={c[o]}' for o in order))
    print(f'\n答えられた（出典つき）: {tot["sourced"]} / 仮の答え: {tot["provisional"]} / '
          f'つながりがなく答えられない: {tot["link_missing"]} / データがなく答えられない: {tot["no_data"]} / '
          f'不合格: {tot["fail"]} / 判定不能: {tot["undecidable"]}（全{len(res)}問）')
    if a.csv:
        with open(a.csv, 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f, lineterminator='\n')
            w.writerow(['id', 'crop_group', 'phase', 'crop', 'wisdom', 'qtype', 'question', 'status', 'reason'])
            for q, st, why in res:
                w.writerow([q['id'], q['crop_group'], q['phase'], q['crop'] or '', q['wisdom'], q['qtype'], q['question'], st, why])
    return 0


if __name__ == '__main__':
    sys.exit(main())
