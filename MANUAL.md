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

`vegbook` サーバーと10個のツール（`vegbook_search` 〜 `vegbook_update_crop`）が表示されれば正常に認識されている。

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
| 「ベランダで育てられる初心者向け野菜は？」 | vegbook_search |
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
5月にベランダで育てられる初心者向けの野菜を教えて
```

`vegbook_search` が `environment=ベランダ` `difficulty=1` で絞り込み、候補を返す。

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
python vegbook.py search --environment ベランダ

# 複合条件
python vegbook.py search --month 5 --category 葉モノ野菜 --difficulty 1
```

カテゴリ一覧：`果菜類` `葉モノ野菜` `根菜類` `ハーブ` `豆類` `イモ類`  
栽培環境一覧：`ほ場` `プランター` `ベランダ` `水耕栽培` `室内`

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
| vegbook_detail | 作物の詳細情報を取得 | name（日本語または英語）, lang |
| vegbook_recommend | 今月のおすすめ野菜（難易度1-2）を取得 | month（省略時は当月）, lang |
| vegbook_companion | コンパニオンプランツ（相性○×）を取得 | crop_name, lang |
| vegbook_glossary | 農業用語を検索 | query（キーワード）, lang |
| vegbook_climate | 地域別月別気候データを取得 | region, year（省略時は直近5年）, month |
| vegbook_harvest_stats | 作物別収穫量統計を取得 | crop_name, start_year（デフォルト2000）, end_year |
| vegbook_diagnose | DBの不足データを診断 | なし |
| vegbook_add_companion | コンパニオンプランツを追加 | crop_name, companion_name, effect, is_positive, effect_en |
| vegbook_update_crop | 作物フィールドを更新 | crop_name, field, value |

### vegbook_climate の地域名一覧

| 指定文字列 | 対象地域 |
|---|---|
| 関東 または 関東平野 | 関東平野 |
| 近畿 | 近畿 |
| 九州 または 九州北部 | 九州北部 |
| 東北 | 東北 |
| 北海道 | 北海道 |

---

## 4. データのリフレッシュ

vegbook.db のデータは以下のスクリプトで更新・補完できます。  
実行前に必ず仮想環境を有効化してください（`mcp` パッケージが必要なスクリプトがあります）。

```bash
cd vegbook
source .venv/bin/activate
```

### スクリプト一覧と実行順序

DB を一から再構築する場合は以下の順で実行してください。  
部分更新の場合は該当スクリプトのみ実行すれば問題ありません。

| 順序 | スクリプト | 内容 | 外部依存 |
|---|---|---|---|
| 1 | `build_glossary.py` | 用語集テーブルの作成・データ投入 | なし |
| 2 | `expand_crops.py` | 作物品種の追加（既存品種はスキップ） | なし |
| 3 | `enrich_crops.py` | 作物詳細データの補完（気温・日照・水やり等） | なし |
| 4 | `enrich_companions.py` | コンパニオンプランツデータの補完 | なし |
| 5 | `enrich_en.py` | 作物・カテゴリ等の英語データ投入 | なし |
| 6 | `enrich_companion_en.py` | コンパニオンプランツ英語データ投入 | なし |
| 7 | `collect_climate.py` | 気象庁から気候データを取得・更新 | 気象庁（公開データ・キー不要） |
| 8 | `collect_harvest.py` | e-Stat から収穫量統計を取得・更新 | **e-Stat API キー必要** |

### 各スクリプトの実行方法

**用語集の再構築**

```bash
python build_glossary.py
```

**作物品種の追加**

```bash
python expand_crops.py
```

**作物詳細データの補完**

```bash
python enrich_crops.py
```

**コンパニオンプランツの補完**

```bash
python enrich_companions.py
python enrich_companion_en.py
```

**英語データの投入**

```bash
python enrich_en.py
```

**気候データの更新（気象庁・APIキー不要）**

```bash
python collect_climate.py
```

**収穫量統計の更新（e-Stat API キーが必要）**

```bash
python collect_harvest.py <あなたご自身のAPIキー>
```

e-Stat API キーの取得：[https://www.e-stat.go.jp/api/](https://www.e-stat.go.jp/api/)（無料・要登録）

### リフレッシュ後の確認

スクリプト実行後は `vegbook_diagnose` ツールで不足データがないか確認することを推奨します。

Claude Code から：

```
vegbook_diagnose を実行して不足データを確認して
```

または MCP ツールを直接呼び出す：

```python
# Python から直接確認
import sqlite3
from pathlib import Path

DB = Path("vegbook.db")
conn = sqlite3.connect(DB)
no_companion = conn.execute(
    "SELECT COUNT(*) FROM crops WHERE id NOT IN (SELECT DISTINCT crop_id FROM companion_plants)"
).fetchone()[0]
no_seed = conn.execute(
    "SELECT COUNT(*) FROM crops WHERE seed_or_seedling IS NULL"
).fetchone()[0]
conn.close()
print(f"コンパニオン未登録: {no_companion}件 / seed_type未設定: {no_seed}件")
```

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

農研機構・農林水産省・Wikipedia（CC BY-SA）および家庭菜園実践知見を元に整備。  
データの二次利用・改変は出典を明記のうえ自由に行えます。

### 連絡先

Author: withagridream@gmail.com

---

## 免責事項

- データは現状のまま（as-is）提供します。
- 当該データは日本国のものに限定されています。
- データの正確性・最新性は保証しません。栽培の結果については自己責任でお願いします。
