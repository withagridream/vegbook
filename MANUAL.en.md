# vegbook User Manual

> 日本語版 → [MANUAL.md](MANUAL.md)

vegbook is an agricultural and home gardening crop database system, available in three ways:

| Method | Best for |
|---|---|
| **MCP** (Claude Code integration) | Pulling agricultural data through natural conversation with Claude Code |
| **CLI** (command line) | Quick lookups directly from a terminal |

---

## Table of Contents

1. [Using as MCP](#1-using-as-mcp)
   - 1.1 Installation
   - 1.2 Basic usage
   - 1.3 Getting the latest data
   - 1.4 Home gardener usage guide
   - 1.5 Farmer usage guide
2. [Using as CLI](#2-using-as-cli)
3. [Tool reference](#3-tool-reference)
4. [Refreshing the data](#4-refreshing-the-data)

---

## 1. Using as MCP

### 1.1 Installation

**Prerequisites**

- Python 3.10 or later
- Claude Code (CLI or Desktop App)

**Step 1: Clone the repository**

```bash
git clone https://github.com/withagridream/vegbook.git
cd vegbook
```

**Step 2: Create a virtual environment and install the MCP package**

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install mcp
```

**Step 3: Add vegbook to the configuration file**

The configuration file location differs between Claude Code CLI and Claude Desktop App.

#### Claude Code CLI (`.mcp.json`)

Create or edit `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "vegbook": {
      "type": "stdio",
      "command": "/absolute/path/to/vegbook/.venv/bin/python",
      "args": ["/absolute/path/to/vegbook/mcp_server.py"]
    }
  }
}
```

OS-specific examples:

**Linux / Raspberry Pi**
```json
{
  "mcpServers": {
    "vegbook": {
      "type": "stdio",
      "command": "/home/<username>/vegbook/.venv/bin/python",
      "args": ["/home/<username>/vegbook/mcp_server.py"]
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
      "command": "/Users/<username>/vegbook/.venv/bin/python",
      "args": ["/Users/<username>/vegbook/mcp_server.py"]
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
      "command": "C:\\Users\\<username>\\vegbook\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\<username>\\vegbook\\mcp_server.py"]
    }
  }
}
```

#### Claude Desktop App (`claude_desktop_config.json`)

Configuration file location:

| OS | Path |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

Add the `mcpServers` section to this file using the same format as the Claude Code CLI example above.

**Step 4: Restart Claude Code / Claude Desktop**

Restart the application to apply the configuration.

---

**Verify the setup**

Ask in the chat:

```
What vegetables can I plant this month?
```

If `vegbook_recommend` is called and returns a list of recommended crops, the setup is working.

**Claude Code CLI users can also run `/mcp` to verify:**

```
/mcp
```

You should see the `vegbook` server listed with 13 tools (`vegbook_search` through `vegbook_ask`).

---

### 1.1.1 Troubleshooting

**Tools are not recognized**

1. Verify that absolute paths are used in the configuration
2. Check that `mcp` is installed in the virtual environment's Python:
   ```bash
   /absolute/path/to/vegbook/.venv/bin/python -c "import mcp; print('OK')"
   ```
3. Fully quit and restart Claude Code / Claude Desktop

**`ModuleNotFoundError: No module named 'mcp'`**

The system Python is likely being used instead of the virtual environment's Python.  
Install `mcp` using the Python specified in `command`:

```bash
/absolute/path/to/vegbook/.venv/bin/pip install mcp
```

**`vegbook.db` not found error**

Verify that `vegbook.db` exists in the same directory as `mcp_server.py`:

```bash
ls /absolute/path/to/vegbook/vegbook.db
```

---

### 1.2 Basic usage

Just ask in natural language in the Claude Code chat — the relevant vegbook tool is called automatically.

| Example question | Tool used |
|---|---|
| "What should I plant this month?" | vegbook_recommend |
| "How do I grow tomatoes?" | vegbook_detail |
| "What beginner-friendly vegetables can I grow in a planter?" | vegbook_search |
| "What is crop rotation?" | vegbook_glossary |
| "What grows well next to eggplant?" | vegbook_companion |
| "What is the climate data for Kanto this month?" | vegbook_climate |
| "Show me tomato harvest statistics for the last 5 years" | vegbook_harvest_stats |

---

### 1.3 Getting the latest data

**Get this month's recommendations (auto-detects current month)**

```
What vegetables do you recommend planting this month?
```

`vegbook_recommend` uses the server-side system date, so it always returns current-month data.

**Get climate data**

```
Show me the average temperature and precipitation for Kanto Plain this month.
```

Returns the most recent 5 years by default. You can also specify a year:

```
Show me the climate data for Kanto Plain in May 2023.
```

**Get harvest statistics**

```
Show me tomato harvest statistics from 2020 onwards.
```

**Check for missing data (admin use)**

```
Run vegbook_diagnose to check for incomplete data.
```

Returns: crops missing companion plant entries, crops missing seed/seedling type.

---

### 1.4 Home gardener usage guide

#### Not sure what to plant this month?

```
What beginner-friendly vegetables can I grow in a planter in May?
```

`vegbook_search` filters by `environment=Planter` and `difficulty=1` and returns matching crops.

#### Want to use companion planting?

```
What plants grow well next to cherry tomatoes, and what should I avoid planting nearby?
```

`vegbook_companion` returns both good and bad pairings with explanations.

#### Want to know when to harvest or how to store your crop?

```
Tell me the full details for cucumber — especially the harvest signs and storage tips.
```

`vegbook_detail` returns harvest signs, storage methods, and common failure points.

#### Unfamiliar with agricultural terms?

```
Explain "crop rotation", "powdery mildew", and "thinning".
```

`vegbook_glossary` returns plain-language descriptions.

#### Looking for vegetables by difficulty level?

```
Show me all difficulty-1 (beginner-friendly) vegetables.
```

| Difficulty | Description |
|---|---|
| 1 | Low risk of failure even for beginners |
| 2 | Requires some attention |
| 3 | For experienced growers |

---

### 1.5 Farmer usage guide

#### Plan cultivation schedules with regional climate data

```
Show me the average temperature and precipitation for Kanto Plain in May, for the last 5 years.
```

Available regions: `関東平野 (Kanto Plain)` `近畿 (Kinki)` `九州北部 (Kyushu North)` `東北 (Tohoku)` `北海道 (Hokkaido)`

#### Understand harvest trends with production statistics

```
Show me the acreage, harvest volume, and shipment volume for tomatoes from 2010 to 2024.
```

`vegbook_harvest_stats` returns year-by-year statistics — useful for subsidy applications and business planning.

#### Use companion planting to manage replant problems

```
What companion plants help prevent replant problems for eggplant?
```

Useful for planning inter-cropping at field scale.

#### Add or update data (admin use)

Add a companion plant entry:

```
Add companion plant info for "水菜 (mizuna)" and "ニラ (chive)".
Effect: Antagonistic bacteria on chive roots suppress soil pathogens.
Relationship: positive.
```

Update a crop field:

```
Update the seed_or_seedling field for "ピーマン (bell pepper)" to "seedling".
```

Updatable fields:

| Field | Description |
|---|---|
| seed_or_seedling | Sow from seed or transplant seedling |
| planter_size | Recommended planter size |
| yield_per_plant | Yield per plant |
| storage | Storage method |
| harvest_sign | Signs the crop is ready to harvest |
| failure_points | Common mistakes to avoid |
| sunlight | Sunlight requirements |
| watering | Watering frequency |
| temp_min / temp_max | Suitable temperature range (°C) |
| sow_start / sow_end | Sowing season (month number) |
| harvest_start / harvest_end | Harvest season (month number) |
| days_to_harvest | Days from sowing to harvest |
| difficulty | Difficulty level (1–3) |

---

## 2. Using as CLI

Run `vegbook.py` directly from a terminal. No additional packages required (Python standard library only).

```bash
cd vegbook
```

### This month's recommendations

```bash
# Current month (auto-detected)
python vegbook.py recommend --lang en

# Specify a month
python vegbook.py recommend --month 7 --lang en
```

### Search crops

```bash
# Crops you can sow this month
python vegbook.py search --month 5 --lang en

# Filter by category
python vegbook.py search --category "Fruiting Vegetables" --lang en

# Filter by difficulty (1 = beginner-friendly)
python vegbook.py search --difficulty 1 --lang en

# Filter by growing environment
python vegbook.py search --environment Planter --lang en

# Combined filters
python vegbook.py search --month 5 --category "Leafy Vegetables" --difficulty 1 --lang en
```

Categories: `Fruiting Vegetables` `Leafy Vegetables` `Root Vegetables` `Herbs` `Legumes` `Tubers`  
Environments: `Field` `Planter` (currently the only two assigned to crops; `Balcony` `Hydroponics` `Indoors` exist as categories but return 0 results)

### Crop details

```bash
python vegbook.py detail Tomato --lang en
python vegbook.py detail Cucumber --lang en
python vegbook.py detail Radish --lang en
```

Shows: difficulty · sow/harvest months · temperature range · sunlight · watering · planter size · harvest signs · storage · common failure points

### Companion plants

```bash
python vegbook.py companion Tomato --lang en
python vegbook.py companion Eggplant --lang en
```

### Glossary lookup

```bash
# Show all terms
python vegbook.py glossary --lang en

# Search by keyword
python vegbook.py glossary --term mildew --lang en
python vegbook.py glossary --term nitrogen --lang en
python vegbook.py glossary --term rotation --lang en
```

### Japanese output

Omit `--lang en` (default is Japanese):

```bash
python vegbook.py recommend
python vegbook.py detail トマト
python vegbook.py companion ナス
```

---

## 3. Tool reference

All tools available via MCP:

| Tool | Function | Parameters |
|---|---|---|
| vegbook_search | Search crops by conditions | month(1-12), category, difficulty(1-3), environment, lang(ja/en) |
| vegbook_detail | Get full crop details (incl. sources, region, per-method storage) | name (Japanese, English, alias), lang |
| vegbook_recommend | Get recommended crops for the month (difficulty ≤ 2) | month (default: current month), lang |
| vegbook_companion | Get companion plants (good & bad pairings) | crop_name, lang |
| vegbook_glossary | Search agricultural glossary | query (keyword), lang |
| vegbook_climate | Get regional monthly climate data | region, year (default: last 5 years), month |
| vegbook_harvest_stats | Get national harvest statistics by crop | crop_name, start_year (default 2000), end_year |
| vegbook_diagnose | (compat) same as vegbook_db_check; diagnoses missing DB data, not crop problems | none |
| vegbook_trouble | "When you have a problem": symptom -> causes, conditions, remedies, sources | query, crop, lang, phase (growing/postharvest) |
| vegbook_ask | Search related information with sources (FTS5); storage keywords (refrigerate / dry / freeze ...) return per-method storage | query, crop, lang |
| vegbook_db_check | Diagnose missing data in the DB (formerly vegbook_diagnose) | none |
| vegbook_add_companion | Add a companion plant entry (disabled by default) | crop_name, companion_name, effect, is_positive, effect_en |
| vegbook_update_crop | Update a crop field (disabled by default) | crop_name, field, value |

### Available regions for vegbook_climate

| Query string | Region |
|---|---|
| 関東 or 関東平野 | Kanto Plain |
| 近畿 | Kinki |
| 九州 or 九州北部 | Kyushu North |
| 東北 | Tohoku |
| 北海道 | Hokkaido |

Region names must be given in Japanese (English names such as `Kanto` will not match).

### Enabling write tools

`vegbook_add_companion` and `vegbook_update_crop` are disabled by default. The database is opened read-only (`mode=ro`), and calling these tools returns a message explaining why they are disabled.
To enable them, set the environment variable `VEGBOOK_ALLOW_WRITE=1` when starting the MCP server. Example `.mcp.json`:

```json
{
  "mcpServers": {
    "vegbook": {
      "type": "stdio",
      "command": "/absolute/path/vegbook/.venv/bin/python",
      "args": ["/absolute/path/vegbook/mcp_server.py"],
      "env": { "VEGBOOK_ALLOW_WRITE": "1" }
    }
  }
}
```

When enabled, `vegbook.db` is modified directly (no history is kept and validation is limited). Make a backup copy of `vegbook.db` first.

### Known data issues (not yet fixed)

- `vegbook_harvest_stats`: values for 2014-2020 are withheld (a warning is returned) because of a suspected crop mix-up during import. Daikon 2007-08 and strawberry 2023 are also partly withheld.
- `vegbook_climate`: values for Kyushu North 2010/2011, Tohoku 2011, Hokkaido 2006 (precipitation) and 2011 are withheld because monthly columns appear shifted.
- The rows in `vegbook.db` themselves are not yet corrected. Do not rely on these figures until verified against the original sources.

---

## 4. Source of truth and building the database (2.0, in development)

**The source of truth is `data/*.csv` (one UTF-8 CSV per table) plus `schema.sql`. `vegbook.db` is a generated file.**
To fix data, edit the CSV and rebuild `vegbook.db` (do not edit the binary file directly, so that changes can be reviewed in diffs). Standard library only.

```bash
cd vegbook
python3 build_db.py                          # build vegbook.db from data/*.csv + schema.sql
python3 verify_roundtrip.py                  # round-trip check (DB -> CSV -> DB, chunks reproducibility); add --original old.db to also compare with the stage-1 DB
python3 check_questions.py                   # can the DB answer the questions in `questions`?
python3 export_csv.py [DB] [outdir]          # dump the DB to CSV (e.g. after collect_*.py)
```

- NULL is written as `\N`, an empty string as an empty field. Rows are in primary-key order.
- `chunks` (text for RAG) and the full-text index are generated by `build_db.py` (no CSV).
- Register sources in `sources` / `crop_field_sources`. Folklore without a source is not accepted (`tradition` requires the recording publication and the region).

### Source gate and build checks

`build_db.py` stops (the existing `vegbook.db` stays intact) on any of these:

- **Gate**: rows with `provisional=0` need a `source_id` and a `locator` (page / section / URL anchor), and the source must have `sources.usable_as_evidence=1` (default 0; only verified sources are set to 1; blanket-listed ids 5-9, fieldfresh and FAO tomato are 0). The same applies to `wisdom=1`.
- **chunks**: troubles are chunked per (trouble x cause); `has_source` / `provisional` equal that cause's `is_evidence` result, and an evidenced chunk contains only evidenced remedies. `crop_field_sources` also has a gate (`provisional`, `locator`; statistics forbidden; only `provisional=0` + usable counts).
- `locator` must not be blank (also required for `wisdom=1`); a source with `usable_as_evidence=1` needs `url` and `retrieved_at`.
- **Statistics sources** (`kind=statistics`: JMA, e-Stat) cannot back `trouble_causes`, `remedies`, `crop_storage` or `cause_conditions`.
- **A provisional parent makes the child provisional**: `trouble_causes` needs `troubles` and `causes` to be `provisional=0`; `remedies` / `cause_conditions` need their `causes` parent to be `provisional=0`.
- `evidence_count`, the acceptance check's `sourced` and `chunks.has_source` count only rows where the row and all parents are `provisional=0` and the source is usable. The judgement lives in one function, `vegbook_core.is_evidence()`.
- 0/1 columns and `lang` are restricted by CHECK constraints; any `PRAGMA foreign_key_check` violation stops the build.
- **Pesticides**: remedies / pest_controls / chunks that contain a pesticide or product word (`PESTICIDE_TERMS` in `build_db.py`) without the label caution ("ラベルの適用作物") stop the build. Product and active-ingredient names are not published without a source.
- Remedies containing a pesticide word (wettable powder, granules, emulsion, flowable, fungicide, etc.) must have `uses_pesticide=1` (and `uses_pesticide=1` requires `caution` by CHECK).
- `data_issues.row_key` (natural key) must hit exactly one row for hide/note, and none for removed.

### Provisional rows

Rows with `provisional=1` in troubles / causes / storage were cut mechanically out of crop text (the script that did so is not in this repository). **In stage 2c, never flip `provisional` to 0. Read the source and add a new sourced row (`provisional=0`), replacing the provisional one.** Clearly wrong provisional rows are recorded in `data/data_issues.csv` (`action=removed`) and dropped from the CSV.

### Targets to enter from primary sources in stage 2c

- **Known errors in the crops table**: values are not rewritten; they are marked in `data_issues` (`table_name=crops`, `row_key=name=<crop>`). `vegbook_detail` (and search / recommend) return `None` for `hide` columns with the reason in `warnings`, and keep the value for `note` columns while adding the reason to `warnings`. Re-check from primary sources in 2c, then remove the marks. hide: fava bean harvest_sign; note: days_to_harvest of chamomile / potato / burdock / corn, placeholder harvest months 1-12, missing autumn sowing (turnip, carrot), leafy greens' sow/harvest months, and ja/en number mismatches (64 crops, 117 columns).
- **Known limits (crops table)**: many companion pairs are registered in one direction only (the tool also looks up the reverse direction and marks it `registered_as='reverse'`); prices have no region or date.
- **Greening (solanine)**: potato "発芽・緑化する" (troubles 58, post-harvest) is a provisional row linked only to a storage cause. In 2c, re-enter symptom / cause / prevention from a primary (public) source with a locator, as new rows. Orphan provisional causes (44, 88, 92) are recorded in `data_issues`.

### Suspect values (data_issues) and symptom aliases (trouble_aliases)

- `data/data_issues.csv`: values suspected of import errors (table, natural-key `row_key`, column, issue, action). Rows are addressed by natural key (`crop_name=ダイコン|year=2007`, `month=3|region=九州北部|year=2010`), so a re-import that changes row ids cannot hide the wrong row; the build checks each key hits exactly one row. Values with `action=hide` are withheld by the MCP tools `vegbook_climate` / `vegbook_harvest_stats` with a warning (the data holds this, not code constants).
- `data/trouble_aliases.csv`: user wording -> formal symptom name (e.g. 実が割れる -> 裂果), used by symptom search.
- `chunks` carries `provisional` and `has_source` and returns them in search results.

### Retired scripts

`expand_crops.py` and `enrich_crops.py` are records of past imports; do not run them (`enrich_crops.py` overwrites text columns unconditionally and refuses to run without `VEGBOOK_LEGACY_OVERWRITE=1`). `build_glossary.py` and `enrich_*.py` are likewise no longer the source of truth.

### Importing external data

`collect_climate.py` (JMA, no key) and `collect_harvest.py` (e-Stat, API key) no longer write to `vegbook.db` or `data/*.csv`; they write `data/incoming/climate_monthly.csv` and `data/incoming/harvest_stats.csv` (they contact external servers, so the maintainer decides when to run them). To replace the source of truth: compare with the existing CSV by natural key (region_id+year+month / crop_name+year), replace values keeping `id`, append new rows with new ids, remove `data_issues` hides only after a human confirms, then build to a temporary DB, check, and swap.
**Some climate years and the harvest statistics for 2014-2020 are suspected to be mis-imported (known, not yet fixed). Re-import is planned for a later stage of 2.0.**

### Acceptance check (check_questions.py)

`data/questions.csv` (258 questions, 40+ per crop group, growing / post-harvest, with a mark for questions answered by traditional know-how) is fed to `vegbook_trouble` / `vegbook_ask`. Statuses: `sourced`, `provisional`, `link_missing`, `no_data`, `undecidable` (answered, but expected terms/method are empty), `fail` (answer does not fit the question: wrong crop, storage-only answer to a "why" question, or expected cause words missing). Each question has `qtype` (why/how/what), `expected_terms` and `origin`.

---

## License

### Code (MIT License)

```
MIT License

Copyright (c) 2026 withagridream

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

### Data

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

### Contact

Author: withagridream@gmail.com

---

## Disclaimer

- This database is provided as-is.
- The data in this database is limited to Japan.
- Accuracy and currency of data are not guaranteed. Use at your own risk for actual growing decisions.
