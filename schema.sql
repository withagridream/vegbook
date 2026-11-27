-- vegbook スキーマ定義（正本）
-- vegbook.db は build_db.py が data/*.csv とこのファイルから生成する。
-- 列の並びは従来の vegbook.db（後から ALTER で足した列が末尾）に合わせてある。

PRAGMA foreign_keys = OFF;

-- ── マスタ ─────────────────────────────────────────────
CREATE TABLE regions (
    id    INTEGER PRIMARY KEY,
    name  TEXT NOT NULL,
    lat   REAL,
    lon   REAL,
    pref  TEXT
);
CREATE TABLE crop_categories (
    id    INTEGER PRIMARY KEY,
    name  TEXT NOT NULL,
    name_en          TEXT
);
CREATE TABLE grow_environments (
    id    INTEGER PRIMARY KEY,
    name  TEXT NOT NULL,
    name_en         TEXT
);
CREATE TABLE fertilizers (
    id           INTEGER PRIMARY KEY,
    name         TEXT NOT NULL,
    availability INTEGER,
    name_en          TEXT
);
CREATE TABLE pests (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    season      TEXT,
    description TEXT,
    name_en          TEXT
);
CREATE TABLE pest_controls (
    id           INTEGER PRIMARY KEY,
    name         TEXT NOT NULL,
    type         TEXT,
    availability INTEGER,
    name_en          TEXT
);

-- ── 作物 ───────────────────────────────────────────────
CREATE TABLE crops (
    id               INTEGER PRIMARY KEY,
    name             TEXT NOT NULL,
    category_id      INTEGER REFERENCES crop_categories(id),
    region_id        INTEGER REFERENCES regions(id),
    environment_id   INTEGER REFERENCES grow_environments(id),
    difficulty       INTEGER,
    days_to_harvest  INTEGER,
    sow_start        INTEGER,
    sow_end          INTEGER,
    harvest_start    INTEGER,
    harvest_end      INTEGER,
    sunlight         TEXT,
    watering         TEXT,
    temp_min         REAL,
    temp_max         REAL,
    seed_or_seedling TEXT,
    price_min        INTEGER,
    price_max        INTEGER,
    planter_size     TEXT,
    rotation_years   INTEGER,
    yield_per_plant  TEXT,
    storage          TEXT,
    harvest_sign     TEXT,
    failure_points   TEXT,
    source_url       TEXT,
    fetched_at       TEXT,
    name_en          TEXT,
    watering_en      TEXT,
    sunlight_en      TEXT,
    failure_points_en TEXT,
    harvest_sign_en  TEXT,
    storage_en       TEXT
);
CREATE TABLE crop_fertilizers (
    id            INTEGER PRIMARY KEY,
    crop_id       INTEGER REFERENCES crops(id),
    fertilizer_id INTEGER REFERENCES fertilizers(id),
    ratio         TEXT
);
CREATE TABLE companion_plants (
    id           INTEGER PRIMARY KEY,
    crop_id      INTEGER REFERENCES crops(id),
    companion_id INTEGER REFERENCES crops(id),
    effect       TEXT,
    is_positive  INTEGER,
    effect_en TEXT,
    CHECK (is_positive IS NULL OR is_positive IN (0,1))
);
CREATE TABLE crop_pests (
    id         INTEGER PRIMARY KEY,
    crop_id    INTEGER REFERENCES crops(id),
    pest_id    INTEGER REFERENCES pests(id),
    control_id INTEGER REFERENCES pest_controls(id),
    notes      TEXT
);
CREATE TABLE glossary (
    id       INTEGER PRIMARY KEY,
    term     TEXT NOT NULL UNIQUE,
    reading  TEXT,
    plain_ja TEXT NOT NULL,
    category TEXT,
    plain_en         TEXT
);

-- ── 気候・統計 ─────────────────────────────────────────
CREATE TABLE climate_monthly (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id    INTEGER NOT NULL,
    year         INTEGER NOT NULL,
    month        INTEGER NOT NULL,
    avg_temp     REAL,
    precipitation REAL,
    UNIQUE(region_id, year, month),
    FOREIGN KEY(region_id) REFERENCES regions(id)
);
CREATE TABLE harvest_stats (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_name    TEXT NOT NULL,
    year         INTEGER NOT NULL,
    area_ha      REAL,
    harvest_t    REAL,
    shipment_t   REAL,
    source       TEXT DEFAULT 'e-Stat',
    UNIQUE(crop_name, year)
);

-- ── 出典 ───────────────────────────────────────────────
-- 出典の台帳。note に「確認できていること／できていないこと」を書く。
CREATE TABLE sources (
    id           INTEGER PRIMARY KEY,
    title        TEXT NOT NULL,
    publisher    TEXT,
    url          TEXT,
    license      TEXT,
    retrieved_at TEXT,
    checksum     TEXT,
    note         TEXT,
    -- kind: official=公的資料 / research=研究機関 / seed_company=種苗会社 /
    --       tradition=地域の慣行・伝承の記録 / author=作者の公開記事（URLのみ。本文は取り込まない）/
    --       statistics=統計データ（気候・収穫統計。原因・対策・保存方法の根拠には使えない）/ other=その他
    kind         TEXT NOT NULL DEFAULT 'other'
                 CHECK (kind IN ('official','research','seed_company','tradition','author','statistics','other')),
    region       TEXT,   -- 地域（tradition では必須。どの地域の慣行かを書く）
    -- usable_as_evidence: 1=個別の値の根拠に使える出典 / 0=使えない（一括記載・列未特定・利用許諾なし・
    -- ライセンス未確認など、個別の値との対応や引用箇所が確かめられないもの）。
    -- 既定は0（確認した出典だけを明示的に1にする）。evidence_count・sourced の判定は 1 のものだけで数える。
    usable_as_evidence INTEGER NOT NULL DEFAULT 0 CHECK (usable_as_evidence IN (0,1)),
    -- 出典なしの言い伝えは入れない：tradition は、記録した資料（publisher）と地域（region）を必須にする
    CHECK (kind <> 'tradition' OR (publisher IS NOT NULL AND publisher <> '' AND region IS NOT NULL AND region <> '')),
    -- 根拠に使える出典（usable_as_evidence=1）は、資料を特定できる url と取得日 retrieved_at が必須
    CHECK (usable_as_evidence = 0 OR (url IS NOT NULL AND trim(url) <> '' AND retrieved_at IS NOT NULL AND trim(retrieved_at) <> '')),
    -- 作者の記事は URL のみ持つ
    CHECK (kind <> 'author' OR (url IS NOT NULL AND url <> ''))
);
-- 作物の値（列）ごとの出典。field='*' は「行全体に付いた出典URLで、対象列は未特定」の意味。
-- provisional=1（既定）は「対象列・引用箇所が未確認の記載」。根拠にできるのは provisional=0 かつ
-- 根拠に使える出典（statistics 以外）かつ locator あり、のものだけ（chunks.has_source もこれで決まる）。
CREATE TABLE crop_field_sources (
    crop_id   INTEGER NOT NULL REFERENCES crops(id),
    field     TEXT NOT NULL,
    source_id INTEGER NOT NULL REFERENCES sources(id),
    provisional INTEGER NOT NULL DEFAULT 1 CHECK (provisional IN (0,1)),
    locator   TEXT,   -- 引用箇所（ページ・節・URLのアンカー）。provisional=0 なら必須
    PRIMARY KEY (crop_id, field, source_id),
    CHECK (provisional = 1 OR (locator IS NOT NULL AND trim(locator) <> ''))
);
-- テーブル全体の出典（気候・収穫統計など）
CREATE TABLE dataset_sources (
    table_name TEXT NOT NULL,
    source_id  INTEGER NOT NULL REFERENCES sources(id),
    note       TEXT,
    PRIMARY KEY (table_name, source_id)
);

-- ── 名前解決 ───────────────────────────────────────────
-- kind: name=正式名 / name_en=英語名 / name_en_shared=他の作物と重複する英語名（曖昧時の優先度は低い）
--       name_en_part=英語名を / や括弧で分けた一部 / variant=表記ゆれ（漢字・かな違い）/ alias=別名
CREATE TABLE crop_aliases (
    id      INTEGER PRIMARY KEY,
    crop_id INTEGER NOT NULL REFERENCES crops(id),
    alias   TEXT NOT NULL,
    lang    TEXT NOT NULL CHECK (lang IN ('ja','en')),
    kind    TEXT NOT NULL,
    UNIQUE(crop_id, alias)
);
CREATE INDEX idx_crop_aliases_alias ON crop_aliases(alias);

-- ── 保存方法（方法ごとに1行）──────────────────────────
-- method: refrigerate=冷蔵 / room=常温・冷暗所 / freeze=冷凍 / dry=干す・乾燥 /
--         pickle=漬ける / cure=キュアリング・追熟 / ground=土中・囲い
-- provisional=1 は crops.storage の文章から機械的に切り出した仮の行（source_id は空）。
-- 出典付きの行は provisional=0 で入れる（段階2c）。
CREATE TABLE crop_storage (
    id                INTEGER PRIMARY KEY,
    crop_id           INTEGER NOT NULL REFERENCES crops(id),
    method            TEXT NOT NULL CHECK (method IN
                      ('refrigerate','room','freeze','dry','pickle','cure','ground')),
    steps             TEXT,
    duration_min_days INTEGER,
    duration_max_days INTEGER,
    temp_c_min        REAL,
    temp_c_max        REAL,
    caution           TEXT,
    source_id         INTEGER REFERENCES sources(id),
    lang              TEXT NOT NULL DEFAULT 'ja' CHECK (lang IN ('ja','en')),
    provisional       INTEGER NOT NULL DEFAULT 0 CHECK (provisional IN (0,1)),
    -- wisdom=1 は「先人の智慧」（やぐら干し・土中保存・吊り干しなど、慣行・伝承の工夫）。
    -- 出典（source_id）が必須。出典なしの言い伝えは入れない。
    wisdom            INTEGER NOT NULL DEFAULT 0 CHECK (wisdom IN (0,1)),
    -- locator: 引用箇所（ページ・節・URLのアンカーなど）。provisional=0 なら必須
    locator           TEXT,
    CHECK (wisdom = 0 OR (source_id IS NOT NULL AND locator IS NOT NULL AND trim(locator) <> '')),
    -- 関門：provisional=0（出典付きの正式な行）は source_id と引用箇所を空にできない
    CHECK (provisional = 1 OR (source_id IS NOT NULL AND locator IS NOT NULL AND trim(locator) <> ''))
);
CREATE INDEX idx_crop_storage_crop ON crop_storage(crop_id);

-- ── 土（スキーマのみ。値は段階2cで出典付きで入れる）────
CREATE TABLE crop_soil (
    crop_id                  INTEGER PRIMARY KEY REFERENCES crops(id),
    ph_min                   REAL,
    ph_max                   REAL,
    ph_source_id             INTEGER REFERENCES sources(id),
    drainage                 TEXT,   -- 水はけ/保水の好み
    water_retention          TEXT,
    drainage_source_id       INTEGER REFERENCES sources(id),
    soil_type                TEXT,   -- 合う土質
    soil_type_source_id      INTEGER REFERENCES sources(id),
    container_mix            TEXT,   -- プランター用土の配合の目安
    container_mix_source_id  INTEGER REFERENCES sources(id),
    n_level                  TEXT,   -- 窒素の要求の目安
    p_level                  TEXT,   -- リン酸
    k_level                  TEXT,   -- カリ
    npk_source_id            INTEGER REFERENCES sources(id),
    note                     TEXT
);

-- ── 困りごと：症状 → 原因（複数）→ 条件 → 予防・対策 → 出典 ──────────
-- phase: growing=栽培中 / postharvest=収穫後。provisional=1 は既存の文章から機械的に拾った仮の行
-- （出典未登録）。出典付きの行は provisional=0・source_id あり（段階2c）。
CREATE TABLE troubles (
    id               INTEGER PRIMARY KEY,
    symptom          TEXT NOT NULL,
    symptom_reading  TEXT,
    phase            TEXT NOT NULL CHECK (phase IN ('growing','postharvest')),
    crop_id          INTEGER REFERENCES crops(id),   -- NULL は作物を問わない症状
    category         TEXT,
    lang             TEXT NOT NULL DEFAULT 'ja' CHECK (lang IN ('ja','en')),
    provisional      INTEGER NOT NULL DEFAULT 0 CHECK (provisional IN (0,1)),
    origin           TEXT
);
-- 原因。category は 温度/水分/日照/土・pH/肥料過多・不足/病気/害虫/生理障害/収穫時期/
-- 保存温度・湿度/エチレン/傷/その他 のいずれか
CREATE TABLE causes (
    id               INTEGER PRIMARY KEY,
    name             TEXT NOT NULL,
    category         TEXT NOT NULL CHECK (category IN ('温度','水分','日照','土・pH','肥料過多・不足',
                     '病気','害虫','生理障害','収穫時期','保存温度・湿度','エチレン','傷','その他')),
    description      TEXT,
    provisional      INTEGER NOT NULL DEFAULT 0 CHECK (provisional IN (0,1)),
    origin           TEXT
);
-- 症状と原因の多対多。「よくある原因か」は、同じ (trouble_id, cause_id) に付く出典（source_id）の件数で
-- 裏付ける。頻度を推測で書かない（likelihood_note は出典に書かれた表現の引用用）。
CREATE TABLE trouble_causes (
    id               INTEGER PRIMARY KEY,
    trouble_id       INTEGER NOT NULL REFERENCES troubles(id),
    cause_id         INTEGER NOT NULL REFERENCES causes(id),
    crop_id          INTEGER REFERENCES crops(id),
    likelihood_note  TEXT,
    source_id        INTEGER REFERENCES sources(id),
    provisional      INTEGER NOT NULL DEFAULT 0 CHECK (provisional IN (0,1)),
    -- locator: 引用箇所（ページ・節・URLのアンカーなど）。provisional=0 なら必須
    locator          TEXT,
    -- 関門：provisional=0 は source_id と引用箇所が必須（根拠に使える出典か・親が仮でないかは build_db.py が検査する）
    CHECK (provisional = 1 OR (source_id IS NOT NULL AND locator IS NOT NULL AND trim(locator) <> ''))
);
CREATE INDEX idx_trouble_causes_trouble ON trouble_causes(trouble_id);
CREATE INDEX idx_trouble_causes_cause ON trouble_causes(cause_id);
-- 原因を作物データの値とつなぐ条件。
--  ・field が 'crops.temp_max' のような「テーブル.列」で value が NULL のとき：
--    利用者の実測値を、その作物のその列の値と op で比べる（例：気温 > crops.temp_max）
--  ・field が 'soil_ph' 'storage_temp_c' 'air_temp_c' で value があるとき：実測値を value と op で比べる
--  結合できる列：crops.temp_min/temp_max、crop_soil.ph_min/ph_max、crop_storage.temp_c_min/temp_c_max ほか
CREATE TABLE cause_conditions (
    id               INTEGER PRIMARY KEY,
    cause_id         INTEGER NOT NULL REFERENCES causes(id),
    crop_id          INTEGER REFERENCES crops(id),
    field            TEXT NOT NULL,
    op               TEXT NOT NULL CHECK (op IN ('<','<=','>','>=','=','!=')),
    value            REAL,
    unit             TEXT,
    source_id        INTEGER REFERENCES sources(id),
    provisional      INTEGER NOT NULL DEFAULT 0 CHECK (provisional IN (0,1)),
    locator          TEXT,   -- 引用箇所。provisional=0 なら必須
    CHECK (provisional = 1 OR (source_id IS NOT NULL AND locator IS NOT NULL AND trim(locator) <> ''))
);
CREATE INDEX idx_cause_conditions_cause ON cause_conditions(cause_id);
-- 予防・対策。uses_pesticide=1（農薬を使う対策）の行は caution が必須
-- （「登録のある作物にだけ使う」「ラベルの使用方法を守る」など）。
CREATE TABLE remedies (
    id               INTEGER PRIMARY KEY,
    cause_id         INTEGER NOT NULL REFERENCES causes(id),
    kind             TEXT NOT NULL CHECK (kind IN ('prevention','treatment')),
    text             TEXT NOT NULL,
    caution          TEXT,
    uses_pesticide   INTEGER NOT NULL DEFAULT 0 CHECK (uses_pesticide IN (0,1)),
    crop_id          INTEGER REFERENCES crops(id),
    source_id        INTEGER REFERENCES sources(id),
    lang             TEXT NOT NULL DEFAULT 'ja' CHECK (lang IN ('ja','en')),
    provisional      INTEGER NOT NULL DEFAULT 0 CHECK (provisional IN (0,1)),
    -- wisdom=1 は「先人の智慧」（寒起こし・やぐら干しなど）。出典（source_id）が必須。
    wisdom           INTEGER NOT NULL DEFAULT 0 CHECK (wisdom IN (0,1)),
    locator          TEXT,   -- 引用箇所。provisional=0 なら必須
    -- 農薬を使う対策（uses_pesticide=1）は注意書き必須。農薬の語を含む対策に uses_pesticide=1 が付いているかは build_db.py が検査する
    CHECK (uses_pesticide = 0 OR (caution IS NOT NULL AND caution <> '')),
    CHECK (wisdom = 0 OR (source_id IS NOT NULL AND locator IS NOT NULL AND trim(locator) <> '')),
    CHECK (provisional = 1 OR (source_id IS NOT NULL AND locator IS NOT NULL AND trim(locator) <> ''))
);
CREATE INDEX idx_remedies_cause ON remedies(cause_id);

-- ── 答えるべき問い（検収の基準。data/questions.csv）────
CREATE TABLE questions (
    id              INTEGER PRIMARY KEY,
    question        TEXT NOT NULL,
    phase           TEXT NOT NULL CHECK (phase IN ('growing','postharvest')),
    crop            TEXT,
    crop_group      TEXT,
    expected_tables TEXT,
    wisdom          INTEGER NOT NULL DEFAULT 0 CHECK (wisdom IN (0,1)),   -- 1=「先人の智慧」で答えるべき問い
    -- qtype: why=原因を問う / how=やり方・方法を問う / what=事実・定義・期間などを問う /
    --        reason=方法の理由を問う（なぜ干す・なぜ吊るす等。方法と理由の語の両方が答えに要る）
    qtype           TEXT NOT NULL CHECK (qtype IN ('why','how','what','reason')),
    -- expected_terms: 答え（原因の名前）に含まれていてほしい語。;区切り。どれか1つが含まれれば合格。2文字以上。
    -- 検収の目安であり、出典のある事実ではない。期待語・期待方法がどちらも空の問いは「判定不能」として別に数える
    expected_terms  TEXT,
    -- origin: 問いの出どころ（誰がどの段階で作ったか）
    origin          TEXT,
    -- expected_method: 答えに含まれていてほしい保存方法（crop_storage.method。;区切り。どれか1つで合格）
    expected_method TEXT
);

-- ── 疑いのある値（取り込み不良など）の台帳。data/data_issues.csv ──────────
-- row_key は行の自然キー（取り込み直しで行idが変わっても同じ行を指す）。「列=値」を | でつなぎ、列名の昇順に並べる。
--   harvest_stats   : crop_name=ダイコン|year=2007
--   climate_monthly : month=3|region=九州北部|year=2010   （region は regions.name）
--   crops           : name=そら豆
--   glossary        : term=BT剤 / それ以外の表: id=行id（removed は実在しない行のid）
-- ビルドで「hide・note は指した先が1行だけ存在する／removed は存在しない」を照合する。
-- action: hide=値を返さない（行は残す）/ removed=行をCSVから外した（記録のみ）/ note=注意書きのみ
-- column_name は ','区切りで複数指定できる。issue は利用者に見せる警告文。
CREATE TABLE data_issues (
    id          INTEGER PRIMARY KEY,
    table_name  TEXT NOT NULL,
    row_key     TEXT NOT NULL,
    column_name TEXT,
    issue       TEXT NOT NULL,
    action      TEXT NOT NULL CHECK (action IN ('hide','removed','note')),
    UNIQUE(table_name, row_key, action, column_name)
);
CREATE INDEX idx_data_issues_table ON data_issues(table_name, row_key);

-- ── 症状の言い換え表（利用者の言い回し → 正式な症状名）。data/trouble_aliases.csv ──
CREATE TABLE trouble_aliases (
    id      INTEGER PRIMARY KEY,
    alias   TEXT NOT NULL UNIQUE,
    symptom TEXT NOT NULL
);

-- ── RAG用の文章（build_db.py が上記の表から生成する。CSVは持たない）──
CREATE TABLE chunks (
    id             INTEGER PRIMARY KEY,
    source_id      INTEGER REFERENCES sources(id),
    crop_id        INTEGER REFERENCES crops(id),
    lang           TEXT NOT NULL CHECK (lang IN ('ja','en')),
    section        TEXT NOT NULL,
    text           TEXT NOT NULL,
    is_translation INTEGER NOT NULL DEFAULT 0 CHECK (is_translation IN (0,1)),
    ref_table      TEXT,
    ref_id         INTEGER,
    -- provisional=1: 元の行が仮抽出（または根拠にできない）。has_source=1: 根拠に使える出典がある
    provisional    INTEGER NOT NULL DEFAULT 0 CHECK (provisional IN (0,1)),
    has_source     INTEGER NOT NULL DEFAULT 0 CHECK (has_source IN (0,1))
);
CREATE INDEX idx_chunks_crop ON chunks(crop_id);
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    text, content='chunks', content_rowid='id', tokenize='trigram'
);

-- ── 索引 ───────────────────────────────────────────────
CREATE INDEX idx_crops_sow       ON crops(sow_start, sow_end);
CREATE INDEX idx_crops_harvest   ON crops(harvest_start, harvest_end);
CREATE INDEX idx_crops_category  ON crops(category_id);
CREATE INDEX idx_crops_env       ON crops(environment_id);
CREATE INDEX idx_crop_fert_crop  ON crop_fertilizers(crop_id);
CREATE INDEX idx_crop_pests_crop ON crop_pests(crop_id);
CREATE INDEX idx_glossary_cat    ON glossary(category);
CREATE INDEX idx_crops_name      ON crops(name);
CREATE INDEX idx_crops_name_en   ON crops(name_en);
CREATE INDEX idx_crops_difficulty ON crops(difficulty);
CREATE INDEX idx_companions_pair ON companion_plants(crop_id, companion_id);
CREATE INDEX idx_regions_name    ON regions(name);
CREATE INDEX idx_glossary_reading ON glossary(reading);
