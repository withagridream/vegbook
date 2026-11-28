"""vegbook 共通部品（標準ライブラリのみ）。MCPサーバー（mcp_server.py）とCLI（vegbook.py）、
build_db.py が共有する。作物の名前解決は resolve_crop() の1か所に集約している。"""
import sqlite3

# 保存方法の固定値と表示名
STORAGE_METHODS: dict[str, str] = {
    'refrigerate': '冷蔵',
    'room': '常温・冷暗所',
    'freeze': '冷凍',
    'dry': '干す・乾燥',
    'pickle': '漬ける',
    'cure': 'キュアリング・追熟',
    'ground': '土中・囲い',
}
STORAGE_METHODS_EN: dict[str, str] = {
    'refrigerate': 'Refrigerate', 'room': 'Room temp / cool dark place', 'freeze': 'Freeze',
    'dry': 'Dry', 'pickle': 'Pickle', 'cure': 'Cure / ripen', 'ground': 'Store in ground',
}
# 質問文から保存方法を拾うための語
STORAGE_HINTS: dict[str, str] = {
    '冷蔵': 'refrigerate', '冷蔵庫': 'refrigerate', '野菜室': 'refrigerate',
    '常温': 'room', '冷暗所': 'room', '室温': 'room',
    '冷凍': 'freeze', '凍': 'freeze',
    '干す': 'dry', '干し': 'dry', '干した': 'dry', '乾燥': 'dry', 'ドライ': 'dry',
    '漬': 'pickle', '漬ける': 'pickle', '漬物': 'pickle',
    '追熟': 'cure', 'キュアリング': 'cure',
    '土に埋': 'ground', '土中': 'ground', '囲い': 'ground',
}

# 名前が複数の作物に当たったときの優先度（小さいほど優先）
_KIND_RANK = {'name': 0, 'name_en': 1, 'variant': 2, 'alias': 3, 'name_en_part': 4, 'name_en_shared': 5}


def kana_variants(text: str) -> list[str]:
    """カタカナ↔ひらがな両方の表記バリアントを返す（重複除去）。"""
    kata_to_hira = ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in text)
    hira_to_kata = ''.join(chr(ord(c) + 0x60) if 'ぁ' <= c <= 'ゖ' else c for c in text)
    seen: set[str] = set()
    result: list[str] = []
    for v in (text, kata_to_hira, hira_to_kata):
        if v not in seen:
            seen.add(v)
            result.append(v)
    return result


def resolve_crop(conn: sqlite3.Connection, name: str) -> dict:
    """作物名（正式名・英語名・別名・表記ゆれ。かな違いと大文字小文字は問わない）から作物を引く。

    戻り値:
      {'crop': Row|None, 'also': [他にも当たった作物名...], 'suggestions': [候補名...]}
    複数の作物に当たったときは、crop_aliases.kind の優先度（正式名＞英語名＞表記ゆれ＞別名＞
    英語名の一部＞他作物と重複する英語名）で1件に絞り、残りを also に入れる。
    """
    q = (name or '').strip()
    if not q:
        return {'crop': None, 'also': [], 'suggestions': []}
    # 全角英数字を半角に寄せる程度の正規化（標準ライブラリのみ）
    import unicodedata
    q = unicodedata.normalize('NFKC', q)
    # 全角括弧などは NFKC で半角になるため、正規化前の入力（ヤマイモ（長いも）など）の表記でも引く
    variants = list(dict.fromkeys(v.lower() for v in kana_variants(q) + kana_variants((name or '').strip())))
    ph = ','.join('?' * len(variants))
    rows = conn.execute(
        f'''SELECT a.crop_id, a.kind, c.name FROM crop_aliases a
            JOIN crops c ON c.id = a.crop_id
            WHERE lower(a.alias) IN ({ph})''',  # noqa: S608 – ph は ? のみ
        variants,
    ).fetchall()
    if rows:
        best: dict[int, tuple[int, str]] = {}
        for r in rows:
            rank = _KIND_RANK.get(r['kind'], 9)
            if r['crop_id'] not in best or rank < best[r['crop_id']][0]:
                best[r['crop_id']] = (rank, r['name'])
        ordered = sorted(best.items(), key=lambda kv: (kv[1][0], kv[0]))
        crop = conn.execute('SELECT * FROM crops WHERE id = ?', (ordered[0][0],)).fetchone()
        return {'crop': crop, 'also': [v[1] for _, v in ordered[1:]], 'suggestions': []}
    # 見つからないとき：部分一致の候補を返す
    sugg = conn.execute(
        'SELECT DISTINCT c.name FROM crop_aliases a JOIN crops c ON c.id = a.crop_id '
        'WHERE lower(a.alias) LIKE ? ORDER BY c.id LIMIT 5',
        (f'%{q.lower()}%',),
    ).fetchall()
    return {'crop': None, 'also': [], 'suggestions': [r['name'] for r in sugg]}


def format_days(dmin: int | None, dmax: int | None) -> str:
    """日数を「約3〜5日」「約2週間」のような短い文字列にする。"""
    if dmin is None:
        return ''

    def one(d: int) -> str:
        if d % 365 == 0:
            return f'{d // 365}年'
        if d % 30 == 0 and d >= 30:
            return f'{d // 30}ヶ月'
        if d % 7 == 0 and d >= 7:
            return f'{d // 7}週間'
        return f'{d}日'
    if dmax is None:
        return f'{one(dmin)}以上'
    if dmin == dmax:
        return f'約{one(dmin)}'
    a, b = one(dmin), one(dmax)
    for u in ('年', 'ヶ月', '週間', '日'):   # 単位が同じなら「約2〜3ヶ月」のようにまとめる
        if a.endswith(u) and b.endswith(u):
            return f'約{a[:-len(u)]}〜{b}'
    return f'約{a}〜{b}'


# ── 出典・検索（vegbook_trouble / vegbook_ask の中身。標準ライブラリのみ）─────────
UNSOURCED = '出典未登録'

# 症状の言い回しをそろえるために末尾から外す語（照合用。DBの文章は変えない）
_SYMPTOM_TAILS = ('が発生しやすい', 'が多発する', 'になりやすい', 'しやすい', 'が出やすい', 'が出る', 'する', 'なる', 'になる')


def source_info(conn: sqlite3.Connection, source_id: int | None) -> dict | str:
    """出典IDから出典情報を返す。IDがなければ「出典未登録」。

    usable_as_evidence=False の出典（一括記載など、個別の値の根拠に使えないもの）は、
    出典の台帳には載っているが「根拠に使えない」ことを示す。
    """
    if source_id is None:
        return UNSOURCED
    r = conn.execute('SELECT id, title, publisher, url, license, usable_as_evidence FROM sources WHERE id = ?',
                     (source_id,)).fetchone()
    if not r:
        return UNSOURCED
    return {'id': r['id'], 'title': r['title'], 'publisher': r['publisher'], 'url': r['url'], 'license': r['license'],
            'usable_as_evidence': bool(r['usable_as_evidence'])}


def source_usable(source: dict | str | None) -> bool:
    """source_info の戻り値が「根拠に使える出典」か。"""
    return isinstance(source, dict) and bool(source.get('usable_as_evidence', False))


def is_evidence(source_usable_flag: bool, *provisionals: object) -> bool:
    """「根拠にできる」か：根拠に使える出典があり、行そのものと親の行（troubles・causes など）が
    すべて provisional=0。evidence_count・sourced・chunks.has_source の判定は、すべてこの1つの関数を通す。"""
    return bool(source_usable_flag) and not any(bool(p) for p in provisionals)


def _symptom_key(symptom: str) -> str:
    s = symptom.strip()
    for t in _SYMPTOM_TAILS:
        if s.endswith(t) and len(s) > len(t) + 1:
            return s[: -len(t)]
    return s


def trouble_alias_symptoms(conn: sqlite3.Connection, query: str) -> list[str]:
    """利用者の言い回し（実が割れる等）が含まれていれば、正式な症状名（裂果等）を返す。data/trouble_aliases.csv。"""
    import unicodedata
    q = unicodedata.normalize('NFKC', query)
    out: list[str] = []
    try:
        rows = conn.execute('SELECT alias, symptom FROM trouble_aliases ORDER BY length(alias) DESC, id').fetchall()
    except sqlite3.OperationalError:   # 古いDB（trouble_aliases がない）でも動く
        return out
    for r in rows:
        if unicodedata.normalize('NFKC', r['alias']) in q and r['symptom'] not in out:
            out.append(r['symptom'])
    return out


def issue_key(**parts: object) -> str:
    """data_issues.row_key（行の自然キー）を作る。「列=値」を | でつなぎ、列名の昇順に並べる。"""
    return '|'.join(f'{k}={parts[k]}' for k in sorted(parts))


def load_data_issues(conn: sqlite3.Connection, table: str) -> dict[str, tuple[set[str], str]]:
    """data_issues（疑いのある値の台帳）から、値を返さない行を {row_key: (列の集合, 警告文)} で返す。action='hide' のみ。
    row_key は issue_key() で作った自然キー（harvest_stats: crop_name・year／climate_monthly: month・region・year）。"""
    try:
        rows = conn.execute("SELECT row_key, column_name, issue FROM data_issues WHERE table_name=? AND action='hide'",
                            (table,)).fetchall()
    except sqlite3.OperationalError:   # 古いDB（data_issues がない）でも動く
        return {}
    return {r['row_key']: ({c.strip() for c in (r['column_name'] or '').split(',') if c.strip()}, r['issue'])
            for r in rows}


def load_row_issues(conn: sqlite3.Connection, table: str) -> dict[str, list[dict]]:
    """data_issues から、表の行ごとの印（hide=値を返さない / note=値は返すが警告を付ける）を
    {row_key: [{'action', 'cols', 'issue'}, ...]} で返す。作物の表（crops）の警告に使う。"""
    try:
        rows = conn.execute("SELECT row_key, column_name, issue, action FROM data_issues "
                            "WHERE table_name=? AND action IN ('hide','note') ORDER BY id", (table,)).fetchall()
    except sqlite3.OperationalError:   # 古いDB（data_issues がない）でも動く
        return {}
    out: dict[str, list[dict]] = {}
    for r in rows:
        out.setdefault(r['row_key'], []).append(
            {'action': r['action'], 'issue': r['issue'],
             'cols': {c.strip() for c in (r['column_name'] or '').split(',') if c.strip()}})
    return out


def crop_note_text(issues: dict[str, list[dict]], crop_name: str | None, cols: set[str]) -> str | None:
    """作物の data_issues の note のうち、列 cols に当たるものの理由を「／」でつないで返す（なければ None）。
    保存方法・困りごとなど、作物の文章欄から作った情報へ警告を引き継ぐために使う。"""
    if not crop_name:
        return None
    notes = [m['issue'] for m in issues.get(issue_key(name=crop_name), []) if m['action'] == 'note' and m['cols'] & cols]
    return '／'.join(dict.fromkeys(notes)) or None


# 警告の引き継ぎ先：保存方法は storage の欄、困りごとは failure_points・harvest_sign の欄の印を引き継ぐ
STORAGE_NOTE_COLS = {'storage', 'storage_en'}
TROUBLE_NOTE_COLS = {'failure_points', 'failure_points_en', 'harvest_sign', 'harvest_sign_en'}


def crop_marks(crop_name: str, issues: dict[str, list[dict]], shown: dict[str, str],
               other: dict[str, str] | None = None) -> dict[str, dict[str, list[str]]]:
    """作物の data_issues の印を、出力のキーごとにまとめる。{出力キー: {'hide': [理由...], 'note': [理由...]}}。
    hide は shown（表示している列）だけが対象。note は shown に加えて other（別言語の列）も対象。
    shown・other は {DBの列名: 出力のキー}。"""
    other = other or {}
    out: dict[str, dict[str, list[str]]] = {}
    for m in issues.get(issue_key(name=crop_name), []):
        for col in sorted(m['cols']):
            key = shown.get(col) or (other.get(col) if m['action'] == 'note' else None)
            if key:
                lst = out.setdefault(key, {'hide': [], 'note': []})[m['action']]
                if m['issue'] not in lst:
                    lst.append(m['issue'])
    return out


def apply_crop_issues(item: dict, crop_name: str, issues: dict[str, list[dict]], shown: dict[str, str],
                      other: dict[str, str] | None = None) -> dict:
    """作物の返り値 item に data_issues の印を反映する。
    ・hide の列：出力のキーを None にして、warnings に理由を入れる
    ・note の列：値は返したまま、warnings に理由を入れる
    """
    warnings: list[str] = []
    for key, mk in crop_marks(crop_name, issues, shown, other).items():
        if key not in item:
            continue
        if mk['hide']:
            item[key] = None
        warnings += [f'{key}: {r}（値は返していません）' for r in mk['hide']]
        warnings += [f'{key}: {r}' for r in mk['note']]
    if warnings:
        item['warnings'] = list(dict.fromkeys(warnings))
    return item


def _trigrams(text: str) -> set[str]:
    t = ''.join(text.split())
    return {t[i:i + 3] for i in range(len(t) - 2)}


def detect_crop(conn: sqlite3.Connection, text: str) -> sqlite3.Row | None:
    """文章に含まれる作物名（別名・表記ゆれ含む）のうち最も長いものから作物を返す。"""
    import unicodedata
    t = unicodedata.normalize('NFKC', text).lower()
    forms = [v.lower() for v in kana_variants(t)]
    best: tuple[int, int] | None = None   # (別名の長さ, crop_id)
    for r in conn.execute('SELECT crop_id, alias FROM crop_aliases'):
        a = r['alias'].lower()
        if len(a) < 2:
            continue
        if any(a in f for f in forms) or any(v in t for v in kana_variants(a)):
            if best is None or len(a) > best[0]:
                best = (len(a), r['crop_id'])
    if not best:
        return None
    return conn.execute('SELECT * FROM crops WHERE id = ?', (best[1],)).fetchone()


def _crop_value(conn: sqlite3.Connection, crop_id: int | None, field: str) -> float | None:
    """'crops.temp_max' のような列参照を、その作物の値に解決する。"""
    if crop_id is None or '.' not in field:
        return None
    table, col = field.split('.', 1)
    if table == 'crops' and col in ('temp_min', 'temp_max', 'days_to_harvest'):
        return conn.execute(f'SELECT {col} FROM crops WHERE id = ?', (crop_id,)).fetchone()[0]  # noqa: S608
    if table == 'crop_soil' and col in ('ph_min', 'ph_max'):
        r = conn.execute(f'SELECT {col} FROM crop_soil WHERE crop_id = ?', (crop_id,)).fetchone()  # noqa: S608
        return r[0] if r else None
    if table == 'crop_storage' and col in ('temp_c_min', 'temp_c_max'):
        agg = 'MIN' if col.endswith('min') else 'MAX'
        return conn.execute(f'SELECT {agg}({col}) FROM crop_storage WHERE crop_id = ?', (crop_id,)).fetchone()[0]  # noqa: S608
    return None


def _cause_detail(conn: sqlite3.Connection, trouble_id: int, row: sqlite3.Row, crop_id: int | None,
                  trouble_provisional: bool = True) -> dict:
    cid = row['cause_id']
    srcs = conn.execute(
        'SELECT source_id, MIN(provisional) AS provisional FROM trouble_causes '
        'WHERE trouble_id=? AND cause_id=? AND source_id IS NOT NULL GROUP BY source_id',
        (trouble_id, cid)).fetchall()
    sources = []
    evidence = 0   # 根拠にできる出典の件数（provisional=0 かつ 根拠に使える出典）
    for s in srcs:
        info = source_info(conn, s['source_id'])
        if isinstance(info, dict):
            info = {**info, 'provisional': bool(s['provisional'])}
        sources.append(info)
        # 行（trouble_causes）・親の困りごと・親の原因のどれかが仮なら、根拠に数えない
        if is_evidence(source_usable(info), s['provisional'], trouble_provisional, row['provisional']):
            evidence += 1
    conds = []
    for k in conn.execute('SELECT * FROM cause_conditions WHERE cause_id=? AND (crop_id IS NULL OR crop_id=?)',
                          (cid, crop_id if crop_id is not None else row['crop_id'])):
        d = {'field': k['field'], 'op': k['op'], 'value': k['value'], 'unit': k['unit'],
             'provisional': bool(k['provisional'])}
        if k['value'] is None:
            d['crop_value'] = _crop_value(conn, crop_id if crop_id is not None else row['crop_id'], k['field'])
        conds.append(d)
    rems = []
    for m in conn.execute('SELECT * FROM remedies WHERE cause_id=? AND (crop_id IS NULL OR crop_id=?)',
                          (cid, crop_id if crop_id is not None else row['crop_id'])):
        rems.append({'kind': m['kind'], 'text': m['text'], 'caution': m['caution'],
                     'uses_pesticide': bool(m['uses_pesticide']), 'source': source_info(conn, m['source_id']),
                     'provisional': bool(m['provisional']), 'wisdom': bool(m['wisdom'])})
    return {
        'cause': row['name'], 'category': row['category'],
        'evidence_count': evidence,                 # 根拠にできる出典の件数（仮の行・根拠に使えない出典は数えない。0なら裏付けなし）
        'sources': sources or UNSOURCED,
        'provisional': bool(row['provisional']) or bool(row['tc_provisional']),
        'conditions': conds, 'remedies': rems,
    }


def search_troubles(conn: sqlite3.Connection, query: str, crop_id: int | None = None,
                    phase: str | None = None, limit: int = 5) -> list[dict]:
    """症状の語句が質問文に含まれる（または大きく重なる）困りごとを返す。症状→原因→条件→対策→出典。"""
    import unicodedata
    q = unicodedata.normalize('NFKC', query)
    qf = [v for v in kana_variants(q)]
    alias_forms = trouble_alias_symptoms(conn, query)   # 言い換え→正式な症状名（実が割れる→裂果 など）
    qtri = _trigrams(q)
    sql = 'SELECT t.*, c.name AS crop_name FROM troubles t LEFT JOIN crops c ON c.id = t.crop_id WHERE 1=1'
    params: list = []
    if crop_id is not None:
        sql += ' AND (t.crop_id = ? OR t.crop_id IS NULL)'
        params.append(crop_id)
    if phase:
        sql += ' AND t.phase = ?'
        params.append(phase)
    scored: list[tuple[int, int, sqlite3.Row]] = []
    for t in conn.execute(sql, params):
        key = _symptom_key(unicodedata.normalize('NFKC', t['symptom']))
        score = 0
        if len(key) >= 2 and any(key in f for f in qf):
            score = 10 + len(key)
        elif len(q) >= 2 and any(f in key for f in qf):
            score = 5 + len(q)
        elif any(len(a) >= 2 and (a in key or (len(key) >= 2 and key in a)) for a in alias_forms):
            score = 8 + len(key)     # 言い換え表で当たったもの（直接一致よりは低い）
        else:
            shared = len(qtri & _trigrams(key))
            if shared >= 2:
                score = shared
        if score:
            if crop_id is not None and t['crop_id'] == crop_id:
                score += 3
            scored.append((score, t['id'], t))
    scored.sort(key=lambda x: (-x[0], x[1]))
    out = []
    issues = load_row_issues(conn, 'crops')
    for _, _, t in scored[:limit]:
        causes = conn.execute(
            '''SELECT c.*, tc.cause_id, MIN(tc.provisional) AS tc_provisional, MIN(tc.crop_id) AS crop_id
               FROM trouble_causes tc JOIN causes c ON c.id = tc.cause_id
               WHERE tc.trouble_id = ? GROUP BY tc.cause_id ORDER BY tc.cause_id''', (t['id'],)).fetchall()
        warning = crop_note_text(issues, t['crop_name'], TROUBLE_NOTE_COLS)   # 作物の文章欄の印を引き継ぐ
        item = {
            'symptom': t['symptom'], 'phase': t['phase'], 'crop': t['crop_name'],
            'provisional': bool(t['provisional']),
            'causes': [_cause_detail(conn, t['id'], c, crop_id if crop_id is not None else t['crop_id'],
                                     bool(t['provisional'])) for c in causes],
            'warning': warning,
        }
        for c in item['causes']:
            c['warning'] = warning
            if warning:
                c['evidence_count'] = 0   # 元の文章欄に疑いがあるので、根拠に数えない
        out.append(item)
    return out


def _fts_query(text: str) -> str | None:
    """FTS5 trigram 用の検索式。3文字ずつ切った断片のOR（質問文のどこかが重なる文章を拾う）。"""
    tri = sorted(_trigrams(text))
    if not tri:
        return None
    return ' OR '.join('"' + t.replace('"', '""') + '"' for t in tri[:40])


def _like_escape(text: str) -> str:
    """LIKE の % と _ （と \\）をふつうの文字として扱うためのエスケープ（ESCAPE '\\' と組で使う）。"""
    return text.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def search_chunks(conn: sqlite3.Connection, query: str, crop_id: int | None = None, lang: str = 'ja',
                  limit: int = 8, sections: tuple[str, ...] | None = None) -> list[dict]:
    """chunks を全文検索して出典つきで返す。

    1回目（AND）：空白で区切った語のうち3文字以上は trigram の断片のOR（質問文のどこかが重なる文章）を語ごとに
      AND で絞る。2文字以下の語は、3文字以上の語があるときは絞り込みに使わず順位付けだけに使い（含む語が多い順）、
      3文字以上の語がないときは部分一致（LIKE。% と _ はエスケープ）のANDで絞る。
    2回目（OR）：1回目が0件なら、空白を詰めた全体の trigram のOR（3文字未満なら語ごとの部分一致のOR）に戻す
      （「連作 障害 対策」のように2文字語が並ぶ質問でも拾えるように）。
    """
    import unicodedata
    tokens = unicodedata.normalize('NFKC', query).split()
    if not tokens:
        return []
    filt = ' AND ch.lang = ?'
    params: list = [lang]
    if crop_id is not None:
        filt += ' AND (ch.crop_id = ? OR ch.crop_id IS NULL)'
        params.append(crop_id)
    if sections:
        filt += ' AND ch.section IN (' + ','.join('?' * len(sections)) + ')'
        params += list(sections)
    long_tokens = [t for t in tokens if len(t) >= 3]
    short_tokens = [t for t in tokens if len(t) < 3]

    def like_of(ts: list[str]) -> list[str]:
        return [f'%{_like_escape(t)}%' for t in ts]

    def run(match: str | None, must: list[str], rank: list[str]) -> list[sqlite3.Row]:
        """match=FTS の式（なし可）、must=すべて含む語（LIKE）、rank=含む数で並べ替えるだけの語（LIKE）。"""
        cond = ''.join(" AND ch.text LIKE ? ESCAPE '\\'" for _ in must)
        order = ('(' + ' + '.join("(ch.text LIKE ? ESCAPE '\\')" for _ in rank) + ') DESC, ') if rank else ''
        base = ('SELECT ch.*, bm25(chunks_fts) AS score FROM chunks_fts JOIN chunks ch ON ch.id = chunks_fts.rowid '
                'WHERE chunks_fts MATCH ?' if match else 'SELECT ch.*, 0 AS score FROM chunks ch WHERE 1=1')
        sql = f'{base}{filt}{cond} ORDER BY {order}score, ch.id LIMIT ?'  # noqa: S608 – 固定文字列だけを連結
        args = ([match] if match else []) + params + like_of(must) + like_of(rank) + [limit]
        return conn.execute(sql, args).fetchall()

    fqs = [fq for fq in (_fts_query(t) for t in long_tokens) if fq]
    if fqs:
        rows = run(' AND '.join(f'({fq})' for fq in fqs), [], short_tokens)
    else:
        rows = run(None, short_tokens, [])
    if not rows and len(tokens) > 1:
        joined = ''.join(tokens)
        fq = _fts_query(joined) if len(joined) >= 3 else None
        if fq:
            rows = run(fq, [], [])
        else:   # 全体が2文字以下：語ごとの部分一致のOR
            cond = ' OR '.join("ch.text LIKE ? ESCAPE '\\'" for _ in tokens)
            rows = conn.execute(f'SELECT ch.*, 0 AS score FROM chunks ch WHERE ({cond}){filt} ORDER BY ch.id LIMIT ?',  # noqa: S608
                                like_of(tokens) + params + [limit]).fetchall()
    out = []
    for r in rows:
        crop = conn.execute('SELECT name FROM crops WHERE id=?', (r['crop_id'],)).fetchone() if r['crop_id'] else None
        out.append({'crop': crop['name'] if crop else None, 'section': r['section'], 'lang': r['lang'],
                    'text': r['text'], 'source': source_info(conn, r['source_id']),
                    'provisional': bool(r['provisional']), 'has_source': bool(r['has_source']),
                    'warning': r['warning']})
    return out


def storage_rows(conn: sqlite3.Connection, crop_id: int, methods: list[str] | None = None) -> list[dict]:
    sql = 'SELECT * FROM crop_storage WHERE crop_id = ?'
    params: list = [crop_id]
    if methods:
        sql += ' AND method IN (' + ','.join('?' * len(methods)) + ')'
        params += methods
    out = []
    cname = conn.execute('SELECT name FROM crops WHERE id = ?', (crop_id,)).fetchone()
    warning = crop_note_text(load_row_issues(conn, 'crops'), cname['name'] if cname else None, STORAGE_NOTE_COLS)
    for r in conn.execute(sql + ' ORDER BY id', params):
        src = source_info(conn, r['source_id'])
        out.append({'method': r['method'], 'method_label': STORAGE_METHODS.get(r['method'], r['method']),
                    'steps': r['steps'], 'duration': format_days(r['duration_min_days'], r['duration_max_days']) or None,
                    'duration_min_days': r['duration_min_days'], 'duration_max_days': r['duration_max_days'],
                    'temp_c_min': r['temp_c_min'], 'temp_c_max': r['temp_c_max'], 'caution': r['caution'],
                    'source': src, 'provisional': bool(r['provisional']),
                    'has_source': is_evidence(source_usable(src), r['provisional']) and not warning,
                    'wisdom': bool(r['wisdom']), 'warning': warning})
    return out


def method_hints(text: str) -> list[str]:
    found: list[str] = []
    for k, m in STORAGE_HINTS.items():
        if k in text and m not in found:
            found.append(m)
    return found


def ask(conn: sqlite3.Connection, query: str, crop: str | None = None, lang: str = 'ja', limit: int = 8) -> dict:
    """質問に関連する情報を、出典つきで返す（構造化された困りごと・保存方法・関連する文章）。"""
    crop_row = None
    note: list[str] = []
    if crop:
        res = resolve_crop(conn, crop)
        crop_row = res['crop']
        if not crop_row:
            return {'query': query, 'error': f'Crop "{crop}" not found.', 'suggestions': res['suggestions']}
    else:
        crop_row = detect_crop(conn, query)
    crop_id = crop_row['id'] if crop_row else None
    hints = method_hints(query)
    result: dict = {'query': query, 'crop': crop_row['name'] if crop_row else None}
    if hints:
        result['storage_methods_asked'] = [STORAGE_METHODS[h] for h in hints]
    if crop_row is not None and (hints or any(k in query for k in ('保存', '日持ち', '長持ち', '何日', 'いつまで'))):
        rows = storage_rows(conn, crop_id, hints or None)
        result['storage'] = rows
        if hints and not rows:
            note.append(f'{crop_row["name"]}の「{"・".join(STORAGE_METHODS[h] for h in hints)}」の保存方法は未登録です。')
    result['troubles'] = search_troubles(conn, query, crop_id)
    rest = query
    if crop_row is not None:
        for a in [r['alias'] for r in conn.execute('SELECT alias FROM crop_aliases WHERE crop_id=?', (crop_id,))]:
            for v in kana_variants(a):
                rest = rest.replace(v, '')
    result['passages'] = search_chunks(conn, rest if rest.strip() else query, crop_id, lang, limit)
    if not (result['troubles'] or result.get('storage') or result['passages']):
        note.append('該当する情報がありません（データ未登録）。')
    if any(not p['has_source'] for p in result['passages']) or any(
            c['evidence_count'] == 0 for t in result['troubles'] for c in t['causes']):
        note.append('根拠にできる出典がない項目（「出典未登録」または仮の行）は、確認できていません。記事や判断の根拠にする前に原典で確かめてください。')
    if any(p.get('warning') for p in result['passages']):
        note.append('warning の付いた文章は、疑いのある値（日英の食い違いなど）を含みます。原典で確かめてください。')
    if note:
        result['note'] = note
    return result


def trouble(conn: sqlite3.Connection, query: str, crop: str | None = None, lang: str = 'ja',
            phase: str | None = None) -> dict:
    """vegbook_trouble の中身。症状→原因（複数）→条件→対策→出典を返す。"""
    crop_row = None
    if crop:
        res = resolve_crop(conn, crop)
        crop_row = res['crop']
        if not crop_row:
            return {'error': f'Crop "{crop}" not found.', 'suggestions': res['suggestions']}
    else:
        crop_row = detect_crop(conn, query)
    crop_id = crop_row['id'] if crop_row else None
    troubles = search_troubles(conn, query, crop_id, phase)
    out: dict = {'query': query, 'crop': crop_row['name'] if crop_row else None, 'troubles': troubles}
    if not troubles:
        out['related_passages'] = search_chunks(
            conn, query, crop_id, lang, 3, ('failure_points', 'harvest_sign', 'trouble_growing', 'trouble_postharvest'))
        out['note'] = ('該当する困りごとが登録されていません（原因とのつながりが未登録）。'
                       '関連しそうな既存の記述を related_passages に示します。')
    elif any(c['evidence_count'] == 0 for t in troubles for c in t['causes']):
        out['note'] = '根拠にできる出典がない原因（「出典未登録」または仮の行）は、確認できていません。記事や判断の根拠にする前に原典で確かめてください。'
    return out
