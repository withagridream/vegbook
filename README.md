# vegbook

いっしょに作物を育てる喜びを共有しましょう！ withagridream@gmail.com

家庭菜園・農業向けの作物データベースシステムです。**Claude Code の MCP ツール**として、または**CLI・Python/Node.js API** として利用できます。

> English version → [README.en.md](README.en.md)  
> 詳細な使い方 → [MANUAL.md](MANUAL.md)

---

## こんなときに使えます

**「今月、何を植えればいいかわからない」**  
→ Claude Code に「今月のおすすめ野菜を教えて」と聞くだけ。または `recommend` コマンドを実行。

**「トマトの隣に何を植えるといいの？」**  
→ `companion` コマンド（または MCP 経由）で、相性の良い組み合わせ・避けるべき組み合わせをすぐに調べられます。

**「連作障害ってなに？」**  
→ `glossary` コマンドで農業用語をわかりやすい言葉で調べられます。初心者でも安心です。

**「ベランダで育てられる難易度の低い野菜を探したい」**  
→ `search --environment プランター --difficulty 1` のように複数条件で絞り込めます。

**「このデータを自分のアプリやスクリプトに組み込みたい」**  
→ `vegbook.db` は SQLite3 ファイルです。Python・Node.js・任意の言語から直接クエリを投げられます。

---

## データについて

農研機構・農林水産省普及資料・Wikipedia（CC BY-SA）および家庭菜園実践知見をもとに整備した農業データベースです。

| テーブル | 件数 |
|---|---|
| 作物（crops） | 116品種 |
| 肥料リンク | 92件 |
| 害虫・対策リンク | 62件 |
| コンパニオンプランツ | 161件 |
| 用語集 | 52語 |

> **データ上の注意（既知の不具合・未修正）**
> - 収穫量統計（`vegbook_harvest_stats`）の2014〜2020年は、別の作物の値が入っている疑いがあるため値を返しません（ダイコン2007〜08年・いちご2023年も一部の値を返しません）。
> - 気候データ（`vegbook_climate`）の一部の地域・年（九州北部2010・2011、東北2011、北海道2006〈降水量〉・2011）は、月の値がずれている疑いがあるため値を返しません。
> - いずれも `vegbook.db` の行そのものは未修正です。原典で確認できるまで、記事や計画の根拠にしないでください。

---

## 必要環境

**MCP として使う場合**
- Python 3.10 以上
- Claude Code
- `pip install mcp`

**書き込み系ツールについて**：`vegbook_update_crop`・`vegbook_add_companion` は、既定では無効です（DB は読み取り専用で開きます）。
有効にするには、MCP サーバーの起動時に環境変数 `VEGBOOK_ALLOW_WRITE=1` を設定してください（設定例は MANUAL.md の「書き込み系ツールを有効にする」）。

**CLI として使う場合**
- Python 3.8 以上
- 追加パッケージ不要（標準ライブラリのみ）

---

## Python のインストール（初めての方）

### Windows

1. [https://www.python.org/downloads/](https://www.python.org/downloads/) を開く
2. 「Download Python 3.x.x」ボタンをクリック
3. インストーラーを起動し、**「Add Python to PATH」にチェックを入れてから** Install Now をクリック
4. インストール完了後、コマンドプロンプト（Win+R → `cmd`）で確認：
   ```
   python --version
   ```

### macOS

ターミナルを開いて以下を実行：

```bash
# Homebrew 経由（推奨）
brew install python

# または python.org からインストーラーをダウンロード
# https://www.python.org/downloads/
```

### Linux（Ubuntu / Debian 系）

```bash
sudo apt update && sudo apt install python3
```

---

## セットアップ

```bash
git clone <このリポジトリのURL>
cd vegbook
python vegbook.py --help
```

> Windows の場合、`python` が認識されないときは `python3` に置き換えてください。

---

## コマンド一覧

### 今月のおすすめ

```bash
python vegbook.py recommend
python vegbook.py recommend --month 7
```

### 作物を検索

```bash
# 今月植えられる野菜
python vegbook.py search --month 5

# カテゴリで絞り込み
python vegbook.py search --category 果菜類

# 難易度1（初心者向け）
python vegbook.py search --difficulty 1

# 複合条件
python vegbook.py search --month 5 --category 葉モノ野菜 --difficulty 1
```

カテゴリ一覧: `果菜類` `葉モノ野菜` `根菜類` `ハーブ` `豆類` `イモ類`  
栽培環境: `ほ場` `プランター`（現在、作物に登録があるのはこの2つだけ。`ベランダ` `水耕栽培` `室内` は区分のみで、指定すると0件になります）

### 作物の詳細

```bash
python vegbook.py detail トマト
python vegbook.py detail きゅうり
```

表示内容: 難易度・種まき/収穫時期・適正気温・日照・水やり・プランターサイズ・連作障害・失敗しやすい点・収穫のサイン・保存方法・肥料・害虫と対策・コンパニオンプランツ

### コンパニオンプランツ

```bash
python vegbook.py companion トマト
python vegbook.py companion ナス
```

### 用語集

```bash
# 全用語を表示
python vegbook.py glossary

# キーワード検索
python vegbook.py glossary --term 連作
python vegbook.py glossary --term うどんこ
```

---

## 英語表示

すべてのコマンドに `--lang en` を追加すると英語で出力されます。

```bash
python vegbook.py recommend --month 5 --lang en
python vegbook.py detail Tomato --lang en
python vegbook.py companion Tomato --lang en
python vegbook.py glossary --term mildew --lang en
```

---

## データベース構造

```
vegbook.db（SQLite3）
├── crops              作物メイン（116件）
├── crop_categories    カテゴリマスタ
├── grow_environments  栽培環境マスタ
├── fertilizers        肥料マスタ
├── pests              害虫マスタ
├── pest_controls      害虫対策マスタ
├── crop_fertilizers   作物×肥料（多対多）
├── crop_pests         作物×害虫×対策（多対多）
├── companion_plants   コンパニオンプランツ（自己参照）
└── glossary           用語集（52語）
```

詳細なスキーマ定義 → [schema.md](schema.md)

---

## vegbook 2.0（開発中）

いまの vegbook は「図鑑」です。2.0 は、その上に **「どういう困ったときに使えるか」** を積みます（既存の図鑑データは壊さず、土台として残します）。

- **困ったら**：`vegbook_trouble`（症状 → 原因 → 条件 → 予防・対策 → 出典）、`vegbook_ask`（質問に関連する情報を出典つきで検索）
- **先人の智慧**：やぐら干し・土中保存・吊り干しなどの慣行・伝承の工夫を、出典（記録した資料・地域）つきで持てる形にしました。出典なしの言い伝えは入れません
- **出典**：`sources` に出典の台帳（公的資料・研究機関・種苗会社・地域の慣行の記録・作者の記事の別）。値ごとの出典は `crop_field_sources`
- **保存方法**：冷蔵・常温・冷凍・干す・漬ける・追熟・土中を方法ごとに持つ `crop_storage`
- **正本**：`data/*.csv` と `schema.sql`。`vegbook.db` は `build_db.py` で生成します（MANUAL.md 第4章）
- **検収**：`data/questions.csv`（258問）に答えられるかを `check_questions.py` で測ります

> **開発中の注意**：困りごと・原因・保存方法の行は、いまは既存の文章から機械的に拾った**仮の行（出典未登録）**です。「出典未登録」と表示されるものは、原典で確かめるまで根拠にしないでください。土の項目（pH・用土・NPK）はテーブルだけで、中身は未登録です。仮の行は、段階2cで**出典を見たうえで新しい行（provisional=0・出典つき）として入れ直す**前提です。仮の行の `provisional` を0に書き換えて「出典あり」にしてはいけません（仮の行を作ったスクリプトはリポジトリにありません）。一括記載の出典（`sources` の `usable_as_evidence=0`）は、個別の値の根拠に使えません。リリース表記（v2.0.0）は、出典付きの充填が終わってから決めます。

---

## 免責事項

- 本データベースは現状のまま（as-is）提供します。
- データの正確性・最新性は保証しません。栽培の結果については自己責任でお願いします。
- 品種の追加・データの更新・バグ修正などは保証しません。Issue や Pull Request は歓迎しますが、対応を約束するものではありません。

---

## ライセンス

データの出典は `data/sources.csv` が正です（`usable_as_evidence` が「根拠に使えるか」）。

| id | 出典 | 根拠に使えるか |
|---|---|---|
| 1 | fieldfresh（スケジュール表。播種・収穫月の出所） | 使えない（利用許諾なし・転載方針未確認。公的資料で入れ替える予定） |
| 2 | FAO Crop Information: Tomato | 使えない（どの列の出典か未特定・ライセンス未確認） |
| 3・4 | 気象庁（気候）・e-Stat（収穫統計） | 使えない（統計データ `kind=statistics`。取得日の記録がなく、原因・対策・保存方法・作物の値の根拠には付けられない。政府標準利用規約・原文は未確認） |
| 5〜9 | 農研機構・農林水産省・Wikipedia（CC BY-SA）・FAO・家庭菜園実践知見（READMEなどへの一括記載） | 使えない（個別の値との対応・引用箇所が確かめられない） |

**ライセンス：データのライセンスは未定です（管理者の判断待ち）。** LICENSE ファイルはありません。「二次利用・改変は自由」とは言えません（出典1・7の利用条件が未解決のため）。

コード：MIT License
