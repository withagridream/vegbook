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
→ Filter with `search --environment Balcony --difficulty 1` and similar combinations.

**"I want to use this data in my own app or script."**  
→ `vegbook.db` is a standard SQLite3 file. Query it directly from Python, Node.js, or any language you prefer.

---

## About the Data

Agricultural database built from public sources: NARO (National Agriculture and Food Research Organization), MAFF (Ministry of Agriculture, Forestry and Fisheries) extension materials, Wikipedia (CC BY-SA), and home gardening field notes.

| Table | Records |
|---|---|
| Crops | 100 varieties |
| Fertilizer links | 92 |
| Pest & control links | 62 |
| Companion plants | 161 |
| Glossary terms | 52 |

---

## Requirements

**As MCP (Claude Code integration)**
- Python 3.10 or later
- Claude Code
- `pip install mcp`

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
Environments: `Field` `Planter` `Balcony` `Hydroponics` `Indoors`

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
├── crops              Main crop table (30 records)
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

## Disclaimer

- This database is provided as-is.
- Accuracy and currency of the data are not guaranteed. Use at your own risk for actual growing decisions.
- No commitment is made to add new crop varieties, update existing data, or fix issues. Issues and Pull Requests are welcome, but responses are not guaranteed.

---

## License

Data sources: NARO, MAFF, Wikipedia (CC BY-SA), and home gardening field notes.  
Code: MIT License
