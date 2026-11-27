# vegbook 取り扱い説明書

> English version → [MANUAL.en.md](MANUAL.en.md)

vegbook は農業・家庭菜園向けの作物データベースシステムです。以下の3つの方法で利用できます。

| 利用方法 | こんな人向け |
|---|---|
| **MCP**（Claude Code連携） | Claude Codeと会話しながら農業データを引き出したい |
| **CLI**（コマンドライン） | ターミナルから素早く調べたい |

---

## 目次

1. [MCPとして使う](#1-mcpとして使う)
   - 1.1 インストール方法
   - 1.2 基本的な使い方
   - 1.3 最新情報の取得方法
   - 1.4 家庭菜園向けの使い方
   - 1.5 農家向けの使い方
2. [CLIとして使う](#2-cliとして使う)
3. [ツール仕様一覧](#3-ツール仕様一覧)
4. [データのリフレッシュ](#4-データのリフレッシュ)

---

## 1. MCPとして使う

### 1.1 インストール方法

**前提条件**

- Python 3.10 以上
- Claude Code（CLI または Desktop App）

**Step 1: リポジトリをクローンする**

```bash
git clone https://github.com/withagridream/vegbook.git
cd vegbook
```

**Step 2: 仮想環境を作成して MCP パッケージをインストールする**

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install mcp
```

**Step 3: 設定ファイルに vegbook を追記する**

Claude Code CLI と Claude Desktop App で設定ファイルの場所が異なる。

#### Claude Code CLI（`.mcp.json`）

作業プロジェクトのルートに `.mcp.json` を作成または編集する。

```json
{
  "mcpServers": {
    "vegbook": {
      "type": "stdio",
      "command": "/絶対パス/vegbook/.venv/bin/python",
      "args": ["/絶対パス/vegbook/mcp_server.py"]
    }
  }
}
```

OS別の設定例：

**Linux / Raspberry Pi**
```json
{
  "mcpServers": {
    "vegbook": {
      "type": "stdio",
      "command": "/home/<ユーザー名>/vegbook/.venv/bin/python",
      "args": ["/home/<ユーザー名>/vegbook/mcp_server.py"]
    }
  }
}
```

**macOS**
```json
{
  "mcpServers": {
    "vegbook": {
      "type": "stdio",
      "command": "/Users/<ユーザー名>/vegbook/.venv/bin/python",
      "args": ["/Users/<ユーザー名>/vegbook/mcp_server.py"]
    }
  }
}
```

**Windows**
```json
{
  "mcpServers": {
    "vegbook": {
      "type": "stdio",
      "command": "C:\\Users\\<ユーザー名>\\vegbook\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\<ユーザー名>\\vegbook\\mcp_server.py"]
    }
  }
}
```

#### Claude Desktop App（`claude_desktop_config.json`）

設定ファイルの場所：

| OS | パス |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

上記ファイルに `mcpServers` セクションを追記する（形式は Claude Code CLI と同じ）。

**Step 4: Claude Code / Claude Desktop を再起動する**

設定を反映するために再起動する。

---

**動作確認**

チャットで以下を試す。

```
今月植えられる野菜を教えてください
```

`vegbook_recommend` ツールが呼ばれ、今月のおすすめ野菜一覧が返ってくれば成功。

**Claude Code CLI の場合は `/mcp` コマンドでも確認できる。**

```
/mcp
```

`vegbook` サーバーと13個のツール（`vegbook_search` 〜 `vegbook_ask`）が表示されれば正常に認識されている。

---

### 1.1.1 トラブルシューティング

**ツールが認識されない**

1. パスが正しいか確認する（絶対パスで指定しているか）
2. 仮想環境の `python` に `mcp` がインストールされているか確認する
   ```bash
   /絶対パス/vegbook/.venv/bin/python -c "import mcp; print('OK')"
   ```
3. Claude Code / Claude Desktop を完全に終了してから再起動する

**`ModuleNotFoundError: No module named 'mcp'` が出る**

仮想環境の `python` ではなくシステムの `python` を指定している可能性がある。  
`command` に指定したパスの python で mcp をインストールする。

```bash
/絶対パス/vegbook/.venv/bin/pip install mcp
```

**`vegbook.db` が見つからないエラーが出る**

`mcp_server.py` と同じディレクトリに `vegbook.db` が存在するか確認する。

```bash
ls /絶対パス/vegbook/vegbook.db
```

---

### 1.2 基本的な使い方

Claude Codeのチャットで自然な日本語で質問するだけで、vegbook のツールが自動的に呼び出される。

| 質問例 | 呼ばれるツール |
|---|---|
| 「今月何を植えれば良い？」 | vegbook_recommend |
| 「トマトの育て方を教えて」 | vegbook_detail |
| 「プランターで育てられる初心者向け野菜は？」 | vegbook_search |
| 「連作障害って何？」 | vegbook_glossary |
| 「ナスの隣に植えると良い野菜は？」 | vegbook_companion |
| 「関東の今月の気候データを見たい」 | vegbook_climate |
| 「トマトの収穫量の推移を知りたい」 | vegbook_harvest_stats |

---

### 1.3 最新情報の取得方法

**今月のおすすめを取得（自動で当月判定）**

```
今月のおすすめ野菜を教えて
```

`vegbook_recommend` はサーバー側でシステム日付を参照するため、常に当月のデータが返ってくる。

**気候データを取得**

```
関東平野の今月の平均気温と降水量を教えて
```

直近5年分のデータが返ってくる。特定の年を指定することも可能。

```
関東平野の2023年5月の気候データを教えて
```

**収穫量統計を取得**

```
トマトの2020年以降の収穫量統計を教えて
```

**DBの不足データを確認（管理者向け）**

```
vegbook_diagnose を実行して不足データを確認して
```

コンパニオンプランツ未登録の作物、種/苗情報が未設定の作物が一覧表示される。

---

### 1.4 家庭菜園向けの使い方

#### 今月何を植えるか迷ったとき

```
5月にプランターで育てられる初心者向けの野菜を教えて
```

`vegbook_search` が `environment=プランター` `difficulty=1` で絞り込み、候補を返す。

#### コンパニオンプランツを活用したい

```
ミニトマトの隣に植えると良い野菜と、植えてはいけない野菜を教えて
```

`vegbook_companion` が相性の良い・悪い組み合わせを、その理由（効果）とセットで返す。

#### 収穫のタイミングや保存方法を知りたい

```
きゅうりの詳細情報、特に収穫のサインと保存方法を教えて
```

`vegbook_detail` が収穫のサイン・保存方法・よくある失敗ポイントを返す。

#### 農業用語がわからない

```
「連作障害」「うどんこ病」「間引き」を調べたい
```

`vegbook_glossary` が平易な日本語で解説を返す。

#### 難易度別に野菜を選びたい

```
難易度1（初心者向け）の野菜を一覧で見せて
```

| 難易度 | 目安 |
|---|---|
| 1 | 初心者でも失敗しにくい |
| 2 | 少し注意が必要 |
| 3 | 経験者向け |

---

### 1.5 農家向けの使い方

#### 地域別気候データで栽培計画を立てる

```
関東平野の直近5年の5月の平均気温と降水量を教えて
```

利用可能な地域：`関東平野` `近畿` `九州北部` `東北` `北海道`

#### 収穫量統計でトレンドを把握する

```
トマトの2010年〜2024年の作付面積・収穫量・出荷量の推移を教えて
```

`vegbook_harvest_stats` が年別の統計データを返す。補助金申請・経営計画の参考として活用できる。

#### コンパニオンプランツで連作障害対策

```
ナスの連作障害対策になるコンパニオンプランツを教えて
```

圃場規模での混植設計にも活用できる。

#### データを追加・更新する（管理者向け）

コンパニオンプランツデータを追加：

```
「水菜」と「ニラ」のコンパニオン情報を追加してほしい。
効果：ニラの根に共生する拮抗菌が土壌病原菌を抑制する。相性良い。
```

作物の情報を更新：

```
「ピーマン」の seed_or_seedling を seedling に更新して
```

更新可能なフィールド一覧：

| フィールド名 | 意味 |
|---|---|
| seed_or_seedling | 種まき / 苗植え |
| planter_size | プランターサイズ |
| yield_per_plant | 1株あたりの収量 |
| storage | 保存方法 |
| harvest_sign | 収穫のサイン |
| failure_points | 失敗しやすいポイント |
| sunlight | 日照条件 |
| watering | 水やり頻度 |
| temp_min / temp_max | 適正気温（最低・最高） |
| sow_start / sow_end | 種まき時期（月） |
| harvest_start / harvest_end | 収穫時期（月） |
| days_to_harvest | 収穫までの日数 |
| difficulty | 難易度（1〜3） |

---

## 2. CLIとして使う

`vegbook.py` をターミナルから直接実行する。追加パッケージは不要（Python標準ライブラリのみ）。

```bash
cd vegbook
```

### 今月のおすすめ

```bash
# 今月のおすすめ（当月自動判定）
python vegbook.py recommend

# 月を指定
python vegbook.py recommend --month 7
```

### 作物を検索

```bash
# 今月植えられる野菜
python vegbook.py search --month 5

# カテゴリで絞り込み
python vegbook.py search --category 果菜類

# 難易度で絞り込み（1=初心者向け）
python vegbook.py search --difficulty 1

# 栽培環境で絞り込み
python vegbook.py search --environment プランター

# 複合条件
python vegbook.py search --month 5 --category 葉モノ野菜 --difficulty 1
```

カテゴリ一覧：`果菜類` `葉モノ野菜` `根菜類` `ハーブ` `豆類` `イモ類`  
栽培環境一覧：`ほ場` `プランター`（現在、作物に登録があるのはこの2つだけ。`ベランダ` `水耕栽培` `室内` は区分のみで、指定すると0件になる）

### 作物の詳細情報

```bash
python vegbook.py detail トマト
python vegbook.py detail きゅうり
python vegbook.py detail ラディッシュ
```

表示内容：難易度・種まき/収穫時期・適正気温・日照・水やり・プランターサイズ・収穫のサイン・保存方法・失敗しやすいポイント

### コンパニオンプランツ

```bash
python vegbook.py companion トマト
python vegbook.py companion ナス
```

### 農業用語を調べる

```bash
# 全用語を一覧表示
python vegbook.py glossary

# キーワードで検索
python vegbook.py glossary --term 連作
python vegbook.py glossary --term うどんこ
python vegbook.py glossary --term 間引き
```

### 英語で出力する

すべてのコマンドに `--lang en` を追加する。

```bash
python vegbook.py recommend --lang en
python vegbook.py detail Tomato --lang en
python vegbook.py companion Tomato --lang en
python vegbook.py search --month 5 --lang en
python vegbook.py glossary --term mildew --lang en
```

---

## 3. ツール仕様一覧

MCP経由で使えるツールの仕様一覧です。

| ツール名 | 機能 | パラメータ |
|---|---|---|
| vegbook_search | 作物を条件で検索 | month(1-12), category, difficulty(1-3), environment, lang(ja/en) |
| vegbook_detail | 作物の詳細情報を取得（出典・地域・保存方法を方法ごとに含む） | name（日本語または英語）, lang |
| vegbook_recommend | 今月のおすすめ野菜（難易度1-2）を取得 | month（省略時は当月）, lang |
| vegbook_companion | コンパニオンプランツ（相性○×）を取得（登録の向きを問わず両方向から引く） | crop_name, lang |
| vegbook_glossary | 農業用語を検索 | query（キーワード）, lang |
| vegbook_climate | 地域別月別気候データを取得 | region, year（省略時は直近5年）, month |
| vegbook_harvest_stats | 作物別収穫量統計を取得 | crop_name, start_year（デフォルト2000）, end_year |
| vegbook_diagnose | （互換用）vegbook_db_check と同じ。栽培の診断ではなくDBの不足診断 | なし |
| vegbook_trouble | 「◯◯に困ったら」症状から原因・条件・対策・出典を返す | query, crop, lang, phase(growing/postharvest) |
| vegbook_ask | 質問に関連する情報を出典つきで検索（FTS5）。保存方法の語は方法ごとに返す | query, crop, lang |
| vegbook_db_check | DBの不足データを診断（旧 vegbook_diagnose） | なし |
| vegbook_add_companion | コンパニオンプランツを追加（既定で無効） | crop_name, companion_name, effect, is_positive, effect_en |
| vegbook_update_crop | 作物フィールドを更新（既定で無効） | crop_name, field, value |

### vegbook_climate の地域名一覧

| 指定文字列 | 対象地域 |
|---|---|
| 関東 または 関東平野 | 関東平野 |
| 近畿 | 近畿 |
| 九州 または 九州北部 | 九州北部 |
| 東北 | 東北 |
| 北海道 | 北海道 |

地域名は日本語で指定する（`Kanto` などの英語名では見つからない）。

### 書き込み系ツールを有効にする

`vegbook_add_companion` と `vegbook_update_crop` は、既定では無効になっている。DB は読み取り専用（`mode=ro`）で開き、呼び出すと「無効です」という理由を返す。
有効にするには、MCP サーバーの起動時に環境変数 `VEGBOOK_ALLOW_WRITE=1` を設定する。`.mcp.json` の例：

```json
{
  "mcpServers": {
    "vegbook": {
      "type": "stdio",
      "command": "/絶対パス/vegbook/.venv/bin/python",
      "args": ["/絶対パス/vegbook/mcp_server.py"],
      "env": { "VEGBOOK_ALLOW_WRITE": "1" }
    }
  }
}
```

有効にすると `vegbook.db` が直接書き換わる（履歴は残らず、値の検証も限定的）。書き換える前に `vegbook.db` のコピーを取っておくこと。

### データ上の注意（既知の不具合・未修正）

- `vegbook_harvest_stats`：2014〜2020年は、別の作物の値が入っている疑いがあるため値を返さない（警告を返す）。ダイコン2007〜08年・いちご2023年も一部の値を返さない。
- `vegbook_climate`：九州北部2010・2011、東北2011、北海道2006（降水量）・2011は、月の値がずれている疑いがあるため値を返さない。
- いずれも `vegbook.db` の行は未修正。原典で確認できるまで、記事や計画の根拠にしないこと。

---

## 4. データの正本とビルド（2.0 開発中）

**正本は `data/*.csv`（テーブルごとのUTF-8 CSV）と `schema.sql`。`vegbook.db` は生成物です。**
データを直すときは CSV を編集してから `vegbook.db` を作り直します（バイナリの `vegbook.db` を直接編集しません。差分をレビューできるようにするためです）。標準ライブラリだけで動きます。

```bash
cd vegbook
python3 build_db.py                          # data/*.csv + schema.sql から vegbook.db を生成
python3 verify_roundtrip.py                  # 往復一致の検査（DB→CSV→DB・chunksの再現性）。--original 元のDB を付けると段階1までのDBとも比べる
python3 check_questions.py                   # 答えるべき問い（questions）に答えられるかの検収
python3 export_csv.py [DB] [出力先] [--force]  # DB を CSV に書き出す。出力先が data/（正本）のときは --force がないと止まる
```

- NULL は `\N`、空文字列は空欄で書きます。行は主キー順です。
- `chunks`（RAG用の文章）と全文検索索引は `build_db.py` が生成します（CSVはありません）。
- 出典は `sources` / `crop_field_sources` に登録します。出典のない「言い伝え」は入れません（`tradition` は記録した資料と地域が必須）。

### 出典の関門とビルドの検査

次のどれかに違反すると `build_db.py` は止まります（既存の `vegbook.db` は壊れません）。

- **関門**：`provisional=0` の行（正式な行）は `source_id` と引用箇所 `locator`（ページ・節・URLのアンカー）が必須で、その出典は `sources.usable_as_evidence=1`（個別の値の根拠に使える出典）でなければなりません。`wisdom=1` も同じです。`usable_as_evidence` の既定は0で、確認した出典だけを明示的に1にします（一括記載の id 5〜9・fieldfresh・FAO トマトは0）。
- **統計データの出典**（`kind=statistics`。気象庁・e-Stat）は、`trouble_causes`・`remedies`・`crop_storage`・`cause_conditions` の根拠に付けられません。
- **親が仮なら子も仮**：`trouble_causes` は親の `troubles`・`causes` が、`remedies`・`cause_conditions` は親の `causes` が、すべて `provisional=0` でなければ `provisional=0` にできません。
- `evidence_count`（よくある原因かの裏付けの件数）・検収の `sourced`・`chunks.has_source` は、「行も親の行もすべて `provisional=0` で、根拠に使える出典がある」ものだけで数えます。判定は `vegbook_core.is_evidence()` の1か所だけです。
- 0/1の列（provisional・wisdom・uses_pesticide・is_positive など）と `lang`（ja/en）は CHECK で制限しています。外部キー違反（`PRAGMA foreign_key_check`）があれば止まります。
- **chunks**：困りごとは「困りごと×原因」の単位で作ります。`has_source`・`provisional` は、その原因の判定（`is_evidence`）と同じで、根拠にできる chunk には根拠にできる対策だけを入れます。作物の文章欄の出典（`crop_field_sources`）も、`provisional=0`・根拠に使える出典（statistics 以外）・`locator` ありのものだけが根拠になります（既存の行は provisional=1）。
- **引用箇所と出典の台帳**：`locator` は空白だけでは通りません。`wisdom=1` の行にも必須です。`usable_as_evidence=1` の出典は `url` と `retrieved_at` が必須です。
- **農薬**：対策（remedies）・防除方法（pest_controls）・chunks に、農薬の商品名・薬剤の語（`build_db.py` の `PESTICIDE_TERMS`・`PESTICIDE_WEAK_TERMS`。水和剤・粒剤・乳剤・フロアブル・農薬・殺虫剤・殺菌剤・除草剤・ダイアジノン・fungicide など）があるのに「ラベルの適用作物」の注意書きがなければ止まります。対策（remedies）は、さらに `uses_pesticide=1` が必須です（`uses_pesticide=1` なら `caution` 必須は CHECK）。商品名・有効成分名は出典なしでは載せません。語の列挙は素通りしうるので、新しい語は見つけ次第 `PESTICIDE_TERMS` に足します。
- `data_issues` の `row_key`（自然キー）が指す先が、hide・note は1行だけ存在し、removed は存在しないことを確かめます。

### 仮の行の扱い

困りごと・原因・保存方法などの `provisional=1` の行は、作物の文章を機械的に切り出した**仮の行**です（切り出したスクリプトはリポジトリにありません）。
**段階2cでは、仮の行の `provisional` を0に切り替えません。出典を見て、出典つきの新しい行（`provisional=0`）として入れ、仮の行は置き換えます。**
明らかに誤った仮の行は、`data/data_issues.csv` に `action=removed` で記録したうえで CSV から外します。

### 段階2cで一次資料から入れる対象

- **緑化（ソラニン）**：ジャガイモの「発芽・緑化する」（troubles 58・収穫後）は、仮の行のまま原因（収穫後の保存の高温・光）だけがつながっています。2cで一次資料（公的資料）から、症状・原因・予防（光を当てない・低温の限度）を出典と引用箇所つきの新しい行として入れ直します。仮の行の `provisional` は0にしません。
- 孤立した仮の原因（causes 44・88・92）は、2cで整理します（`data_issues` に記録済み）。
- **作物の表（crops）の既知の誤り**：値は書き換えず、`data_issues`（`table_name=crops`・`row_key=name=作物名`）に印を付けています。`vegbook_detail`（と `vegbook_search`・`vegbook_recommend`）は、`hide` の列を `None` にして `warnings` に理由を入れ、`note` の列は値を返したまま `warnings` に理由を入れます。2cで一次資料から確かめ直し、直したら印を外します。
  - hide：そら豆の `harvest_sign`・`harvest_sign_en`（同じ作物の失敗ポイントと矛盾する疑い）
  - note：カモミール・ジャガイモ・ゴボウ・とうもろこしの `days_to_harvest`（播種・収穫月や本文と合わない疑い）／収穫月が1〜12月の仮置き（ほうれん草・ダイコン・キャベツ・ネギ・白菜・豆苗・かいわれ大根）／カブ・にんじんの播種月（秋まきの抜け）／小松菜・チンゲン菜・水菜・パクチョイの播種・収穫月（播種の時期ごとの区別がない）／日英の数字の食い違い（64作物・117列。数字の集合を日英で比べて機械的に抽出。英語欄は翻訳ではなく別に書かれた文章）
- **既知の制約（作物の表）**：コンパニオンは161件のうち多くが片方向にしか登録されていません（`vegbook_companion` は逆向きも引いて `registered_as='reverse'` と示しますが、効果の説明文は登録した側から見た書き方です）。価格（`price_min`・`price_max`）には地域も時点もありません（取得日は `fetched_at` のみ）。地域は `region_id=1`（関東平野）が一部の作物だけで、他は未指定です。

### 疑いのある値（data_issues）と症状の言い換え（trouble_aliases）

- `data/data_issues.csv`：取り込み不良などが疑われる値（表名・行の自然キー `row_key`・列・問題・対処）。`action=hide` の値は MCP の `vegbook_climate` / `vegbook_harvest_stats` が返さず、警告文を付けます（コードの定数ではなくデータが持ちます）。行は自然キー（収穫統計は `crop_name=ダイコン|year=2007`、気候は `month=3|region=九州北部|year=2010`）で指すので、取り込み直しで行idが変わっても別の行を隠すことはありません。ビルドが「指した先が1行だけ存在するか」を照合します。
- `data/trouble_aliases.csv`：利用者の言い回し→正式な症状名（例：実が割れる→裂果、すが入る→す入り、二股→又根）。`vegbook_trouble` / `vegbook_ask` の症状検索で使います。
- `chunks` には `provisional`（仮の行由来か）と `has_source`（根拠に使える出典があるか）が付き、検索結果に出ます。

### 引退したスクリプト

`expand_crops.py`・`build_glossary.py`・`enrich_crops.py`・`enrich_en.py`・`enrich_companions.py`・`enrich_companion_en.py` は過去の取り込み記録です。
正本は `data/*.csv` なので、どれも実行するとエラーで止まり「正本は data/*.csv」と表示します（生成物の vegbook.db を直接書き換えないため）。

### 外部データの取り込み

`collect_climate.py`（気象庁・キー不要）と `collect_harvest.py`（e-Stat・APIキー必要）は、`vegbook.db` にも `data/*.csv` にも直接書かず、
`data/incoming/climate_monthly.csv`（`region_id,year,month,avg_temp,precipitation`）・`data/incoming/harvest_stats.csv`（`crop_name,year,area_ha,harvest_t,shipment_t,source`）に書き出します（外部通信が発生するので、実行は管理者が決めます）。
正本への差し替え手順：
1. 書き出されたCSVを、既存の `data/climate_monthly.csv`・`data/harvest_stats.csv` と自然キー（気候：region_id+year+month／収穫統計：crop_name+year）で突き合わせて目で確かめる
2. 置き換える行は `id` を保ったまま値だけ差し替え、新しい行は末尾に `id` を振って追加する（`INSERT OR IGNORE` のように壊れた行を放置しない）
3. 疑いが晴れた行の `data_issues` の hide を人が外す
4. `python3 build_db.py --out 一時DB` で検査を通してから `vegbook.db` に差し替える
5. **2014〜2020年の hide の見直し（2b の取り込み直しのあと必ず行う）**：`data_issues.csv` の収穫統計 hide（`crop_name=…|year=2014`〜`2020`）は、品目コード表のずれの疑いで、取り込み前の値が別の作物のものかもしれないという理由で隠しています。取り込み直した値について、(a) 作物ごとに 2013→2014 と 2020→2021 で値が不連続になっていないか、(b) e-Stat の原典の表と数点を目で突き合わせ、(c) 面積×単収と収穫量が合うか、を確かめます。直っている作物・年だけ hide の行を外し（行ごとに判断。一括で外さない）、直っていないものは残します。ダイコン2007・2008、いちご2023、気候の hide も同じ手順で見直します
**気候データの一部の年と収穫統計の2014〜2020年は取り込み不良の疑いがあります（既知・未修正）。取り込み直しは 2.0 の次の段階で行います。**

### 検収（check_questions.py）

`data/questions.csv`（258問・作物群ごとに40問以上。栽培中と収穫後、「先人の智慧」で答えるべき問いの印つき。問いの型 `qtype`（why/how/what）・期待する原因の語 `expected_terms`（検収の目安で、出典のある事実ではない）・出どころ `origin` つき）を、
`vegbook_trouble` / `vegbook_ask` に投げて、原因と出典が返ったかを一覧にします。
判定は `sourced`（根拠にできる出典つきで答えられた）/ `provisional`（仮の答え）/ `link_missing`（関連記述はあるが原因につながっていない）/ `no_data`（データがない）/ `fail`（不合格：返った症状の作物が問いと違う `crop_mismatch`・「なぜ」の問いに保存方法しか返らない `why_storage_only`・期待する語が原因の名前にない `expected_terms_missing`・期待する保存方法が返らない `expected_method_missing`・方法の理由の語がない `reason_missing`）/ `undecidable`（判定不能：答えは返ったが期待語・期待する保存方法が空）。
問いの型 `qtype` は why（原因）/ how（方法）/ what（事実）/ reason（方法の理由。なぜ干すか等）。期待語は原因の名前だけと照合します（reason と先人の智慧は対策文・保存手順も見る）。`expected_method` は答えに返ってほしい保存方法です。

---

## ライセンス

### コード（MIT License）

```
MIT License

Copyright (c) 2026 withagridream@gmail.com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### データ

データの出典は `data/sources.csv` が正です（`usable_as_evidence` が「根拠に使えるか」）。

| id | 出典 | 根拠に使えるか |
|---|---|---|
| 1 | fieldfresh（スケジュール表。播種・収穫月の出所） | 使えない（利用許諾なし・転載方針未確認。公的資料で入れ替える予定） |
| 2 | FAO Crop Information: Tomato | 使えない（どの列の出典か未特定・ライセンス未確認） |
| 3・4 | 気象庁（気候）・e-Stat（収穫統計） | 使えない（統計データ `kind=statistics`。取得日の記録がなく、原因・対策・保存方法・作物の値の根拠には付けられない。政府標準利用規約・原文は未確認） |
| 5〜9 | 農研機構・農林水産省・Wikipedia（CC BY-SA）・FAO・家庭菜園実践知見（READMEなどへの一括記載） | 使えない（個別の値との対応・引用箇所が確かめられない） |

**ライセンス：データのライセンスは未定です（管理者の判断待ち）。** LICENSE ファイルはありません。「二次利用・改変は自由」とは言えません（出典1・7の利用条件が未解決のため）。

### 連絡先

Author: withagridream@gmail.com

---

## 免責事項

- データは現状のまま（as-is）提供します。
- 当該データは日本国のものに限定されています。
- データの正確性・最新性は保証しません。栽培の結果については自己責任でお願いします。
