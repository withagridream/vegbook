# vegbook データベーススキーマ

`vegbook.db` は SQLite3 ファイルです。追加パッケージなしで Python・Node.js・任意の言語から直接クエリを投げられます。

---

## テーブル一覧

| テーブル | 説明 | 件数 |
|---|---|---|
| `crops` | 作物メイン | 100 |
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
| `seed_or_seedling` | TEXT | `seed` / `seedling` / `both` |
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
| `name` | TEXT | 栽培環境（日本語）例: ほ場, プランター, ベランダ, 水耕栽培, 室内 |
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
```

---

## ライセンス

データ出典: 農研機構・農林水産省・Wikipedia（CC BY-SA）および家庭菜園実践知見  
コード: MIT License — Copyright (c) 2026 withagridream@gmail.com
