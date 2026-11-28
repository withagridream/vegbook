# vegbook データベーススキーマ

`vegbook.db` は SQLite3 ファイルです。追加パッケージなしで Python・Node.js・任意の言語から直接クエリを投げられます。

---

## テーブル一覧

| テーブル | 説明 | 件数 |
|---|---|---|
| `crops` | 作物メイン | 116 |
| `crop_categories` | カテゴリマスタ | 6 |
| `grow_environments` | 栽培環境マスタ | 5 |
| `fertilizers` | 肥料マスタ | 9 |
| `pests` | 害虫マスタ | 7 |
| `pest_controls` | 害虫対策マスタ | 10 |
| `crop_fertilizers` | 作物×肥料（多対多） | 92 |
| `crop_pests` | 作物×害虫×対策（多対多） | 62 |
| `companion_plants` | コンパニオンプランツ（自己参照） | 161 |
| `glossary` | 農業用語集 | 52 |
| `regions` | 地域マスタ | 5 |
| `climate_monthly` | 地域別月別気候データ | 1,560 |
| `harvest_stats` | 作物別収穫量統計（e-Stat） | 927 |

---

## vegbook 2.0（開発中）で追加したテーブル

正本は `data/*.csv` と `schema.sql`。`vegbook.db` は `build_db.py` で生成する（手順は MANUAL.md 第4章）。
2.0 は従来の図鑑データ（上の13テーブル）を壊さず、その上に「困ったときに引ける」層と出典の層を積む。

| テーブル | 説明 | 件数 |
|---|---|---|
| `sources` | 出典の台帳（kind・license・retrieved_at・checksum・usable_as_evidence） | 9 |
| `crop_field_sources` | 作物の値（列）ごとの出典。`field='*'` は行全体（対象列は未特定）。`provisional`（既定1）・`locator`。根拠にできるのは provisional=0・根拠に使える出典・locator ありだけ | 117 |
| `dataset_sources` | テーブル全体の出典（気候・収穫統計） | 2 |
| `crop_aliases` | 名前解決用の別名・表記ゆれ・英語名 | 428 |
| `crop_storage` | 保存方法（方法ごとに1行） | 174（すべて仮抽出） |
| `crop_soil` | 土の項目（pH範囲・水はけ・土質・用土配合・NPK）。スキーマのみ | 0 |
| `troubles` | 困りごと（症状。phase = growing / postharvest） | 171（すべて仮抽出） |
| `causes` | 原因（category つき） | 93（すべて仮抽出） |
| `trouble_causes` | 症状と原因の多対多（出典の件数で「よくある原因か」を裏付ける） | 181（すべて仮抽出） |
| `cause_conditions` | 原因を作物データの値につなぐ条件 | 45（すべて仮抽出） |
| `remedies` | 予防・対策（農薬を使う対策は caution 必須） | 9（すべて仮抽出） |
| `questions` | 答えるべき問い（検収の基準。`check_questions.py` で使う。qtype・expected_terms・expected_method・origin つき） | 258 |
| `data_issues` | 疑いのある値（取り込み不良など）の台帳。行は自然キー（`row_key`）で指す | 348 |
| `trouble_aliases` | 症状の言い換え表（実が割れる→裂果 など。症状検索で使う） | 46 |
| `chunks` / `chunks_fts` | RAG用の文章と全文検索索引（FTS5 trigram）。`build_db.py` が生成 | 生成物 |

「仮抽出」は、既存の `failure_points`・`storage` などの文章から機械的に拾った行で、`provisional=1`・出典未登録の印が付く。
推測では値を足していない。

### sources（出典）

| カラム | 型 | 説明 |
|---|---|---|
| `id` | INTEGER PK | |
| `title` / `publisher` / `url` | TEXT | 資料名・発行者・URL |
| `license` | TEXT | 利用条件（確認できていないものはその旨を書く） |
| `retrieved_at` / `checksum` | TEXT | 取得日・ファイルのハッシュ |
| `note` | TEXT | 確認できていること・できていないこと |
| `kind` | TEXT | `official`=公的資料 / `research`=研究機関 / `seed_company`=種苗会社 / `tradition`=地域の慣行・伝承の記録 / `author`=作者の公開記事（URLのみ。本文は取り込まない）/ `statistics`=統計データ（気候・収穫統計。原因・対策・保存方法の根拠に付けられない）/ `other` |
| `usable_as_evidence` | INTEGER | 1=個別の値の根拠に使える / 0=使えない（一括記載・列未特定・利用許諾なし・ライセンス未確認）。既定は0。`evidence_count`・`sourced`・`has_source` は1の出典だけで数える |
| `region` | TEXT | 地域。`tradition` では必須（記録した資料 publisher も必須。出典なしの言い伝えは入れない） |

### crop_storage（保存方法）

方法（`method`）は次の固定値。1つの作物に方法ごとに行を持てる。

| method | 意味 |
|---|---|
| `refrigerate` | 冷蔵 |
| `room` | 常温・冷暗所 |
| `freeze` | 冷凍 |
| `dry` | 干す・乾燥 |
| `pickle` | 漬ける |
| `cure` | キュアリング・追熟 |
| `ground` | 土中・囲い |

| カラム | 説明 |
|---|---|
| `steps` | 手順・説明（文章） |
| `duration_min_days` / `duration_max_days` | 日持ちの日数（下限・上限。「以上」は上限NULL） |
| `temp_c_min` / `temp_c_max` | 保存温度（℃） |
| `caution` | 注意 |
| `source_id` | 出典（仮抽出の行は NULL） |
| `lang` | 文章の言語 |
| `provisional` | 1=既存の `crops.storage` から機械的に切り出した仮の行 |
| `wisdom` | 1=「先人の智慧」（やぐら干し・土中保存・吊り干しなど、慣行・伝承の工夫）。`source_id` 必須 |
| `locator` | 引用箇所（ページ・節・URLのアンカー）。`provisional=0` なら必須（`trouble_causes`・`cause_conditions`・`remedies` も同じ） |

既存の `crops.storage`（日英）は消さずに残している。

### 困りごと（症状 → 原因 → 条件 → 予防・対策 → 出典）

```
troubles ── trouble_causes ── causes ── cause_conditions   （作物データの列と結合）
                  │              └──── remedies             （農薬を使う対策は caution 必須）
                  └─ source_id（同じ症状・原因に付く出典の件数＝よくある原因かの裏付け）
```

- `cause_conditions.field` が `crops.temp_max` のような「テーブル.列」で `value` が NULL のときは、
  利用者の実測値をその作物の列の値と比べる（例：気温 > `crops.temp_max`）。
  `soil_ph`・`storage_temp_c`・`air_temp_c` で `value` があるときは、実測値を `value` と比べる。
- `causes.category`：温度 / 水分 / 日照 / 土・pH / 肥料過多・不足 / 病気 / 害虫 / 生理障害 / 収穫時期 / 保存温度・湿度 / エチレン / 傷 / その他
- 関門：`provisional=0` の行は `source_id`・`locator` が必須で、出典は `usable_as_evidence=1` かつ `kind` が `statistics` でないこと。親の行（`troubles`・`causes`）が仮なら、子（`trouble_causes`・`remedies`・`cause_conditions`）も仮のまま（ビルドが検査）。
- 農薬の語を含む対策は `uses_pesticide=1` が必須で、`uses_pesticide=1` なら `caution` 必須（CHECK）。
- 頻度は推測で書かない。「よくある原因か」は、同じ (症状, 原因) に付く出典の件数（`vegbook_trouble` の `evidence_count`）で見る。

### data_issues（疑いのある値の台帳）

| カラム | 説明 |
|---|---|
| `table_name` | 対象の表 |
| `row_key` | 行の自然キー。「列=値」を `|` でつなぎ列名の昇順。収穫統計 `crop_name=ダイコン|year=2007`／気候 `month=3|region=九州北部|year=2010`（region は regions.name）／用語集 `term=BT剤`／その他 `id=行id` |
| `column_name` | 対象の列（`,`区切り） |
| `issue` | 利用者に見せる警告文・問題の説明 |
| `action` | `hide`=値を返さない（行は残す）/ `removed`=CSVから外した（記録のみ）/ `note`=注意書きのみ |

ビルドが、hide・note は指した先が1行だけ存在し、removed は存在しないことを照合する。

### trouble_aliases（症状の言い換え）

`alias`（利用者の言い回し）→ `symptom`（正式な症状名）。`vegbook_trouble` / `vegbook_ask` の症状検索で使う。

### questions（検収の問い）

`qtype`：`why`=原因 / `how`=方法 / `what`=事実 / `reason`=方法の理由。`expected_terms`=原因の名前に含まれていてほしい語（`;`区切り・2文字以上）、
`expected_method`=返ってほしい保存方法（`crop_storage.method`）、`origin`=問いの出どころ。期待語・期待方法が空の問いは検収で「判定不能」。

### chunks（RAG用の文章。生成物）

`source_id`・`provisional`・`has_source`：根拠にできる行（行も親も provisional=0・根拠に使える出典あり）のときだけ `source_id` が入り `has_source=1`。

`locator`：根拠の引用箇所。`has_source=1` のときだけ入る。困りごとの chunk は「原因：（原因の引用箇所）　対処：（同じ出典の対策の引用箇所）」の形。

### crop_aliases（名前解決）

`kind`：`name`=正式名 / `name_en`=英語名 / `name_en_shared`=他の作物と重複する英語名（Bell Pepper・Taro・Turnip の2件目。曖昧なときの優先度は最低）/
`name_en_part`=英語名の一部 / `variant`=表記ゆれ（漢字・かな違い）/ `alias`=別名。
名前解決は `vegbook_core.resolve_crop()` の1か所に集約している（かな違い・大文字小文字は問わない）。

### crop_soil（スキーマのみ）

作物ごとの適正pH範囲（`ph_min`・`ph_max`）、水はけ/保水の好み、合う土質、プランター用土の配合の目安、NPK要求の目安。
各値に `*_source_id` を持つ。値は出典付きで入れる。

---

## テーブル定義

### crops（作物メイン）

| カラム | 型 | 説明 |
|---|---|---|
| `id` | INTEGER PK | |
| `name` | TEXT | 作物名（日本語） |
| `name_en` | TEXT | 作物名（英語） |
| `category_id` | INTEGER FK | → crop_categories.id |
| `region_id` | INTEGER FK | → regions.id |
| `environment_id` | INTEGER FK | → grow_environments.id |
| `difficulty` | INTEGER | 難易度（1=初心者, 2=中級, 3=上級） |
| `days_to_harvest` | INTEGER | 収穫までの日数 |
| `sow_start` | INTEGER | 種まき開始月 |
| `sow_end` | INTEGER | 種まき終了月 |
| `harvest_start` | INTEGER | 収穫開始月 |
| `harvest_end` | INTEGER | 収穫終了月 |
| `sunlight` | TEXT | 日照条件（日本語） |
| `sunlight_en` | TEXT | 日照条件（英語） |
| `watering` | TEXT | 水やり頻度（日本語） |
| `watering_en` | TEXT | 水やり頻度（英語） |
| `temp_min` | REAL | 適正最低気温（℃） |
| `temp_max` | REAL | 適正最高気温（℃） |
| `seed_or_seedling` | TEXT | 自由記述（`seed`・`seedling`・`both` の3値に正規化していない。実際は46種類の値が混ざる）。今後正規化する対象 |
| `price_min` | INTEGER | 種・苗の最低価格（円） |
| `price_max` | INTEGER | 種・苗の最高価格（円） |
| `planter_size` | TEXT | プランターサイズ目安 |
| `rotation_years` | INTEGER | 連作回避年数 |
| `yield_per_plant` | TEXT | 1株あたりの収量目安 |
| `storage` | TEXT | 保存方法（日本語） |
| `storage_en` | TEXT | 保存方法（英語） |
| `harvest_sign` | TEXT | 収穫のサイン（日本語） |
| `harvest_sign_en` | TEXT | 収穫のサイン（英語） |
| `failure_points` | TEXT | 失敗しやすいポイント（日本語） |
| `failure_points_en` | TEXT | 失敗しやすいポイント（英語） |
| `source_url` | TEXT | データ出典URL |
| `fetched_at` | TEXT | データ取得日時 |

---

### crop_categories（カテゴリマスタ）

| カラム | 型 | 説明 |
|---|---|---|
| `id` | INTEGER PK | |
| `name` | TEXT | カテゴリ名（日本語）例: 果菜類, 葉モノ野菜, 根菜類, ハーブ, 豆類, イモ類 |
| `name_en` | TEXT | カテゴリ名（英語）例: Fruiting Vegetables, Leafy Vegetables |

---

### grow_environments（栽培環境マスタ）

| カラム | 型 | 説明 |
|---|---|---|
| `id` | INTEGER PK | |
| `name` | TEXT | 栽培環境（日本語）例: ほ場, プランター, ベランダ, 水耕栽培, 室内（現在、作物に登録があるのは ほ場・プランター のみ） |
| `name_en` | TEXT | 栽培環境（英語）例: Field, Planter, Balcony, Hydroponics, Indoors |

---

### fertilizers（肥料マスタ）

| カラム | 型 | 説明 |
|---|---|---|
| `id` | INTEGER PK | |
| `name` | TEXT | 肥料名（日本語） |
| `name_en` | TEXT | 肥料名（英語） |
| `availability` | INTEGER | 入手しやすさ（1=容易〜3=専門店） |

---

### pests（害虫マスタ）

| カラム | 型 | 説明 |
|---|---|---|
| `id` | INTEGER PK | |
| `name` | TEXT | 害虫・病害名（日本語） |
| `name_en` | TEXT | 害虫・病害名（英語） |
| `season` | TEXT | 発生しやすい季節 |
| `description` | TEXT | 説明 |

---

### pest_controls（害虫対策マスタ）

| カラム | 型 | 説明 |
|---|---|---|
| `id` | INTEGER PK | |
| `name` | TEXT | 対策名（日本語） |
| `name_en` | TEXT | 対策名（英語） |
| `type` | TEXT | 対策種別（物理, 農薬, 天敵など） |
| `availability` | INTEGER | 入手しやすさ（1=容易〜3=専門店） |

---

### crop_fertilizers（作物×肥料）

| カラム | 型 | 説明 |
|---|---|---|
| `id` | INTEGER PK | |
| `crop_id` | INTEGER FK | → crops.id |
| `fertilizer_id` | INTEGER FK | → fertilizers.id |
| `ratio` | TEXT | 施肥量・割合の目安 |

---

### crop_pests（作物×害虫×対策）

| カラム | 型 | 説明 |
|---|---|---|
| `id` | INTEGER PK | |
| `crop_id` | INTEGER FK | → crops.id |
| `pest_id` | INTEGER FK | → pests.id |
| `control_id` | INTEGER FK | → pest_controls.id |
| `notes` | TEXT | 補足事項 |

---

### companion_plants（コンパニオンプランツ）

| カラム | 型 | 説明 |
|---|---|---|
| `id` | INTEGER PK | |
| `crop_id` | INTEGER FK | → crops.id（主作物） |
| `companion_id` | INTEGER FK | → crops.id（相手作物） |
| `effect` | TEXT | 効果・理由（日本語） |
| `effect_en` | TEXT | 効果・理由（英語） |
| `is_positive` | INTEGER | 1=相性良い, 0=相性悪い |

---

### glossary（農業用語集）

| カラム | 型 | 説明 |
|---|---|---|
| `id` | INTEGER PK | |
| `term` | TEXT UNIQUE | 用語（日本語） |
| `reading` | TEXT | 読み仮名 |
| `plain_ja` | TEXT | わかりやすい説明（日本語） |
| `plain_en` | TEXT | わかりやすい説明（英語） |
| `category` | TEXT | カテゴリ（栽培, 病害虫, 土壌, 農業技術など） |

---

### regions（地域マスタ）

| カラム | 型 | 説明 |
|---|---|---|
| `id` | INTEGER PK | |
| `name` | TEXT | 地域名（例: 関東平野, 近畿, 九州北部, 東北, 北海道） |
| `lat` | REAL | 代表地点の緯度 |
| `lon` | REAL | 代表地点の経度 |
| `pref` | TEXT | 代表都道府県 |

---

### climate_monthly（地域別月別気候データ）

| カラム | 型 | 説明 |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `region_id` | INTEGER FK | → regions.id |
| `year` | INTEGER | 年 |
| `month` | INTEGER | 月（1〜12） |
| `avg_temp` | REAL | 月平均気温（℃） |
| `precipitation` | REAL | 月降水量（mm） |

- UNIQUE 制約: `(region_id, year, month)`
- データ出典: 気象庁公開データ（APIキー不要）

---

### harvest_stats（作物別収穫量統計）

| カラム | 型 | 説明 |
|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | |
| `crop_name` | TEXT | 作物名（日本語） |
| `year` | INTEGER | 年 |
| `area_ha` | REAL | 作付面積（ha） |
| `harvest_t` | REAL | 収穫量（t） |
| `shipment_t` | REAL | 出荷量（t） |
| `source` | TEXT | データ出典（デフォルト: `e-Stat`） |

- UNIQUE 制約: `(crop_name, year)`
- データ出典: e-Stat API（農林水産省）

---

## インデックス一覧

| インデックス名 | テーブル | カラム | 用途 |
|---|---|---|---|
| `idx_crops_name` | crops | name | 日本語名検索 |
| `idx_crops_name_en` | crops | name_en | 英語名検索 |
| `idx_crops_sow` | crops | sow_start, sow_end | 種まき時期検索 |
| `idx_crops_harvest` | crops | harvest_start, harvest_end | 収穫時期検索 |
| `idx_crops_category` | crops | category_id | カテゴリ絞り込み |
| `idx_crops_env` | crops | environment_id | 栽培環境絞り込み |
| `idx_crops_difficulty` | crops | difficulty | 難易度絞り込み |
| `idx_companions_pair` | companion_plants | crop_id, companion_id | コンパニオン検索（重複防止） |
| `idx_crop_fert_crop` | crop_fertilizers | crop_id | 作物ごとの肥料取得 |
| `idx_crop_pests_crop` | crop_pests | crop_id | 作物ごとの害虫取得 |
| `idx_glossary_cat` | glossary | category | カテゴリ検索 |
| `idx_glossary_reading` | glossary | reading | 読み仮名検索 |
| `idx_regions_name` | regions | name | 地域名検索 |

---

## ER図（概略）

```
crop_categories ──┐
grow_environments ─┤
                   ▼
regions ──────── crops ────────── crop_fertilizers ── fertilizers
                   │
                   ├──────────── crop_pests ─┬─ pests
                   │                         └─ pest_controls
                   │
                   └──────────── companion_plants（自己参照）

regions ─────── climate_monthly

harvest_stats（作物名文字列で管理、crops との JOIN 不要）

glossary（独立テーブル）

── 2.0 で追加 ──
sources ─┬─ crop_field_sources ── crops
         ├─ dataset_sources（climate_monthly / harvest_stats）
         └─ crop_storage / crop_soil / trouble_causes / cause_conditions / remedies
crops ── crop_aliases / crop_storage / crop_soil / troubles ── trouble_causes ── causes
chunks（生成物）＋ chunks_fts（FTS5 trigram）
```

---

## ライセンス

データ出典: `data/sources.csv` が正（README のデータの項を参照）。ライセンスはコード MIT・データ CC BY 4.0（例外あり。`LICENSE` を参照）。  
コード: MIT License — Copyright (c) 2026 withagridream@gmail.com
