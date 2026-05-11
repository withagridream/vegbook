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
→ `search --environment ベランダ --difficulty 1` のように複数条件で絞り込めます。

**「このデータを自分のアプリやスクリプトに組み込みたい」**  
→ `vegbook.db` は SQLite3 ファイルです。Python・Node.js・任意の言語から直接クエリを投げられます。

---

## データについて

農研機構・農林水産省普及資料・Wikipedia（CC BY-SA）および家庭菜園実践知見をもとに整備した農業データベースです。

| テーブル | 件数 |
|---|---|
| 作物（crops） | 100品種 |
| 肥料リンク | 92件 |
| 害虫・対策リンク | 62件 |
| コンパニオンプランツ | 161件 |
| 用語集 | 52語 |

---

## 必要環境

**MCP として使う場合**
- Python 3.10 以上
- Claude Code
- `pip install mcp`

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
栽培環境: `ほ場` `プランター` `ベランダ` `水耕栽培` `室内`

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
├── crops              作物メイン（30件）
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

## 免責事項

- 本データベースは現状のまま（as-is）提供します。
- データの正確性・最新性は保証しません。栽培の結果については自己責任でお願いします。
- 品種の追加・データの更新・バグ修正などは保証しません。Issue や Pull Request は歓迎しますが、対応を約束するものではありません。

---

## ライセンス

データ出典：農研機構・農林水産省・Wikipedia（CC BY-SA）および家庭菜園実践知見  
コード：MIT License
