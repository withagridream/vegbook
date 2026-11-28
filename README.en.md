# vegbook

An agricultural and home gardening crop database system. Use it as a **Claude Code MCP tool**, or as a **CLI / Python / Node.js API**.

> 日本語版 → [README.md](README.md)  
> Full usage guide → [MANUAL.en.md](MANUAL.en.md)

---

## Use cases

**"I have no idea what to plant this month."**  
→ Ask Claude Code "What vegetables do you recommend this month?" — or run `recommend` from the CLI.

**"What should I plant next to my tomatoes?"**  
→ Use `companion` (or via MCP) to instantly look up good pairings and combinations to avoid.

**"What does 'crop rotation' actually mean?"**  
→ Use `glossary` to look up agricultural terms in plain language — no prior knowledge needed.

**"I want to find easy vegetables I can grow on my balcony."**  
→ Filter with `search --environment Planter --difficulty 1` and similar combinations.

**"I want to use this data in my own app or script."**  
→ `vegbook.db` is a standard SQLite3 file. Query it directly from Python, Node.js, or any language you prefer.

---

## About the Data

Agricultural database built from public sources: NARO (National Agriculture and Food Research Organization), MAFF (Ministry of Agriculture, Forestry and Fisheries) extension materials, Wikipedia (CC BY-SA), and home gardening field notes.

| Table | Records |
|---|---|
| Crops | 116 varieties |
| Fertilizer links | 92 |
| Pest & control links | 62 |
| Companion plants | 161 |
| Glossary terms | 52 |

> **Known data issues (not yet fixed)**
> - `vegbook_harvest_stats` withholds values for 2014-2020 (suspected crop mix-up during import). Daikon 2007-08 and strawberry 2023 are also partly withheld.
> - `vegbook_climate` withholds values for some region-years (Kyushu North 2010/2011, Tohoku 2011, Hokkaido 2006 [precipitation] and 2011) because monthly columns appear shifted.
> - The rows in `vegbook.db` themselves are not yet corrected. Do not rely on these figures until verified against the original sources.

---

## Requirements

**As MCP (Claude Code integration)**
- Python 3.10 or later
- Claude Code
- `pip install mcp`

**Write tools:** `vegbook_update_crop` and `vegbook_add_companion` are disabled by default (the database is opened read-only).
To enable them, set the environment variable `VEGBOOK_ALLOW_WRITE=1` when starting the MCP server (see "Enabling write tools" in MANUAL.en.md).

**As CLI**
- Python 3.8 or later
- No additional packages needed (standard library only)

---

## Installing Python (first-time users)

### Windows

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Click "Download Python 3.x.x"
3. Run the installer — **check "Add Python to PATH"** before clicking Install Now
4. Verify in Command Prompt (Win+R → `cmd`):
   ```
   python --version
   ```

### macOS

Open Terminal and run:

```bash
# Via Homebrew (recommended)
brew install python

# Or download the installer from python.org
# https://www.python.org/downloads/
```

### Linux (Ubuntu / Debian)

```bash
sudo apt update && sudo apt install python3
```

---

## Setup

```bash
git clone <repository URL>
cd vegbook
python vegbook.py --help
```

> On Windows, if `python` is not recognized, try `python3` instead.

---

## Commands

### This month's recommendations

```bash
python vegbook.py recommend --lang en
python vegbook.py recommend --month 7 --lang en
```

### Search crops

```bash
# Vegetables you can sow this month
python vegbook.py search --month 5 --lang en

# Filter by category
python vegbook.py search --category "Leafy Vegetables" --lang en

# Beginner-friendly (difficulty 1)
python vegbook.py search --difficulty 1 --lang en

# Combined filters
python vegbook.py search --month 5 --category "Fruiting Vegetables" --lang en
```

Categories: `Fruiting Vegetables` `Leafy Vegetables` `Root Vegetables` `Herbs` `Legumes` `Tubers`  
Environments: `Field` `Planter` (currently the only two assigned to crops; `Balcony` `Hydroponics` `Indoors` exist as categories but return 0 results)

### Crop detail

```bash
python vegbook.py detail Tomato --lang en
python vegbook.py detail Cucumber --lang en
```

Displays: difficulty · sow/harvest months · temperature range · sunlight · watering · planter size · crop rotation · common failures · harvest sign · storage · fertilizers · pests & controls · companion plants

### Companion plants

```bash
python vegbook.py companion Tomato --lang en
python vegbook.py companion Eggplant --lang en
```

### Glossary

```bash
# Show all terms
python vegbook.py glossary --lang en

# Search by keyword
python vegbook.py glossary --term mildew --lang en
python vegbook.py glossary --term nitrogen --lang en
```

---

## Japanese output

All commands default to Japanese. Omit `--lang en` for Japanese output.

```bash
python vegbook.py recommend --month 5
python vegbook.py detail トマト
python vegbook.py companion トマト
```

---

## Database schema

```
vegbook.db (SQLite3)
├── crops              Main crop table (116 records)
├── crop_categories    Category master
├── grow_environments  Growing environment master
├── fertilizers        Fertilizer master
├── pests              Pest master
├── pest_controls      Pest control master
├── crop_fertilizers   Crop × Fertilizer (many-to-many)
├── crop_pests         Crop × Pest × Control (many-to-many)
├── companion_plants   Companion plants (self-referencing)
└── glossary           Glossary (52 terms, JP + EN)
```

Full schema → [schema.md](schema.md)

---

## vegbook 2.0 (in development)

Today's vegbook is a "field guide". 2.0 adds a layer on top of it: **"what can I use it for when I'm in trouble?"** (the existing guide data is kept as the foundation).

- **When in trouble**: `vegbook_trouble` (symptom -> causes -> conditions -> remedies -> sources) and `vegbook_ask` (search related information with sources)
- **Traditional know-how**: practices such as hanging-drying daikon, storing in soil, or hanging onions can be recorded with a source (the publication and the region). Folklore without a source is not accepted
- **Sources**: a ledger in `sources` (official / research / seed company / tradition / author's articles); per-value sources in `crop_field_sources`
- **Storage**: `crop_storage` holds refrigerate / room / freeze / dry / pickle / cure / in-ground per method
- **Source of truth**: `data/*.csv` + `schema.sql`; `vegbook.db` is generated by `build_db.py` (MANUAL.en.md, section 4)
- **Acceptance check**: `check_questions.py` measures how many of the 258 questions in `data/questions.csv` can be answered

> **Note (in development):** the trouble / cause / storage rows are currently **provisional rows extracted mechanically from existing text, with no source registered**. Do not rely on anything marked "出典未登録" (no source) until verified against the original. The soil tables (pH, potting mix, NPK) exist but are empty. Provisional rows are meant to be **replaced in stage 2c by new rows (provisional=0, with a source) entered after reading the source**; never flip a provisional row to 0 to make it look sourced (the script that created the provisional rows is not in this repository). Blanket-listed sources (`usable_as_evidence=0` in `sources`) cannot back individual values. The release label (v2.0.0) will be decided after sourced data has been filled in.

---

## Disclaimer

- This database is provided as-is.
- Accuracy and currency of the data are not guaranteed. Use at your own risk for actual growing decisions.
- No commitment is made to add new crop varieties, update existing data, or fix issues. Issues and Pull Requests are welcome, but responses are not guaranteed.

---

## License

The source of truth for data sources is `data/sources.csv` (`usable_as_evidence` says whether a source may back a value).

| id | Source | Usable as evidence? |
|---|---|---|
| 1 | fieldfresh (schedule table; origin of sowing/harvest months) | No (no usage permission, reprint policy unchecked; to be replaced with public sources) |
| 2 | FAO Crop Information: Tomato | No (columns it covers are unidentified, license unchecked) |
| 3, 4 | JMA (climate), e-Stat (harvest statistics) | No (statistics, `kind=statistics`; no retrieval date recorded; cannot back causes, remedies, storage or crop values; Government Standard Terms of Use, original text unchecked) |
| 5-9 | NARO, MAFF, Wikipedia (CC BY-SA), FAO, home-gardening field notes (blanket mentions in README etc.) | No (cannot be tied to individual values or passages) |

**License**: code is under the MIT License; data (the author-created parts of `data/*.csv` and `vegbook.db`) is under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/ ; attribution required). See `LICENSE` for the full text. Not covered by CC BY 4.0:
- Data derived from JMA and e-Stat (`climate_monthly`, `harvest_stats`): follow their terms of use (Government Standard Terms of Use); cite the source and state that the data was processed (some values are withheld as suspected import errors).
- Sowing/harvest month data derived from fieldfresh (source id=1; 29 crops): rights unverified, to be replaced with public sources.
- FAO-derived data (source id=2): status unverified.

Code: MIT License (see `LICENSE`)
