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

You should see the `vegbook` server listed with 10 tools (`vegbook_search` through `vegbook_update_crop`).

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
| "What beginner-friendly vegetables can I grow on a balcony?" | vegbook_search |
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
What beginner-friendly vegetables can I grow on a balcony in May?
```

`vegbook_search` filters by `environment=Balcony` and `difficulty=1` and returns matching crops.

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
python vegbook.py search --environment Balcony --lang en

# Combined filters
python vegbook.py search --month 5 --category "Leafy Vegetables" --difficulty 1 --lang en
```

Categories: `Fruiting Vegetables` `Leafy Vegetables` `Root Vegetables` `Herbs` `Legumes` `Tubers`  
Environments: `Field` `Planter` `Balcony` `Hydroponics` `Indoors`

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
| vegbook_detail | Get full crop details | name (Japanese or English), lang |
| vegbook_recommend | Get recommended crops for the month (difficulty ≤ 2) | month (default: current month), lang |
| vegbook_companion | Get companion plants (good & bad pairings) | crop_name, lang |
| vegbook_glossary | Search agricultural glossary | query (keyword), lang |
| vegbook_climate | Get regional monthly climate data | region, year (default: last 5 years), month |
| vegbook_harvest_stats | Get national harvest statistics by crop | crop_name, start_year (default 2000), end_year |
| vegbook_diagnose | Diagnose missing data in the DB | none |
| vegbook_add_companion | Add a companion plant entry | crop_name, companion_name, effect, is_positive, effect_en |
| vegbook_update_crop | Update a crop field | crop_name, field, value |

### Available regions for vegbook_climate

| Query string | Region |
|---|---|
| 関東 or 関東平野 | Kanto Plain |
| 近畿 | Kinki |
| 九州 or 九州北部 | Kyushu North |
| 東北 | Tohoku |
| 北海道 | Hokkaido |

---

## 4. Refreshing the data

The data in `vegbook.db` can be updated and supplemented using the scripts below.  
Activate the virtual environment before running (some scripts require the `mcp` package):

```bash
cd vegbook
source .venv/bin/activate
```

### Scripts and recommended execution order

When rebuilding the DB from scratch, run the scripts in the order below.  
For partial updates, run only the relevant script.

| Order | Script | Description | External dependency |
|---|---|---|---|
| 1 | `build_glossary.py` | Create glossary table and insert data | None |
| 2 | `expand_crops.py` | Add crop varieties (skips existing entries) | None |
| 3 | `enrich_crops.py` | Fill in crop details (temperature, sunlight, watering, etc.) | None |
| 4 | `enrich_companions.py` | Supplement companion plant data | None |
| 5 | `enrich_en.py` | Insert English data for crops, categories, etc. | None |
| 6 | `enrich_companion_en.py` | Insert English descriptions for companion plants | None |
| 7 | `collect_climate.py` | Fetch and update climate data from JMA | JMA public data (no key required) |
| 8 | `collect_harvest.py` | Fetch and update harvest statistics from e-Stat | **e-Stat API key required** |

### How to run each script

**Rebuild glossary**

```bash
python build_glossary.py
```

**Add crop varieties**

```bash
python expand_crops.py
```

**Fill in crop details**

```bash
python enrich_crops.py
```

**Supplement companion plant data**

```bash
python enrich_companions.py
python enrich_companion_en.py
```

**Insert English data**

```bash
python enrich_en.py
```

**Update climate data (JMA, no API key required)**

```bash
python collect_climate.py
```

**Update harvest statistics (e-Stat API key required)**

```bash
python collect_harvest.py <your-api-key>
```

Get your e-Stat API key at: [https://www.e-stat.go.jp/api/](https://www.e-stat.go.jp/api/) (free, registration required)

### Verify after refresh

After running any script, it is recommended to check for missing data using `vegbook_diagnose`.

Via Claude Code:

```
Run vegbook_diagnose to check for incomplete data.
```

Or check directly in Python:

```python
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
print(f"Missing companion entries: {no_companion}  /  Missing seed type: {no_seed}")
```

---

## License

### Code (MIT License)

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

### Data

Built from NARO (National Agriculture and Food Research Organization), MAFF (Ministry of Agriculture, Forestry and Fisheries), Wikipedia (CC BY-SA), and home gardening field notes.  
Secondary use and modification of the data is permitted with attribution.

### Contact

Author: withagridream@gmail.com

---

## Disclaimer

- This database is provided as-is.
- The data in this database is limited to Japan.
- Accuracy and currency of data are not guaranteed. Use at your own risk for actual growing decisions.
