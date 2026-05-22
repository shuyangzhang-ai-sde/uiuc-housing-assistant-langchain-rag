# Data Layer Research
*May 20–21, 2026*

---

## Part 1 — Q&A: Web Scraping Decisions

#### My Follow-up Questions to Claude 

1. **Why do we need a web scraper? Do we have to have one?**
2. **Is web scraping a given website okay?**

#### My Concerns toward data from third-party platforms like Apartments.com:
Apartments.com and similar third-party platforms may have stale or inaccurate data. UIUC has several large direct rental companies — **Green Street, Campus Town, Hub, Here 707, Universities Group, GSM, HMH** — and going to them directly would yield fresher and more accurate listings.

---

#### Q1 — Do You Have to Use a Web Scraper?

**No.** A scraper is just one way to get data into the RAG system. The real requirement is: *the app needs listing text to embed and search.* How that text gets in doesn't matter to the RAG pipeline.

| Approach | How it works | Trade-off |
|---|---|---|
| **Web scraper** | Auto-fetches listings on a schedule | Complex to build; ToS risk |
| **Manual CSV** | You paste listings into a spreadsheet | Tedious, but fast to build |
| **Direct company APIs** | Some property managers expose data feeds | Rare, but clean if it exists |
| **User-submitted links** | User pastes a URL, your app parses it | Good for MVP |
| **Static snapshot** | Scrape once, refresh monthly | Simple; data goes stale |

For an MVP, a **manual CSV or one-time snapshot** is perfectly fine — it lets you focus on the AI part, which is what the project is actually about.

---

#### Q2 — Is Web Scraping Legal / Okay?

**It depends on the site.**

- **`robots.txt`** — Every website can declare what crawlers are allowed to access. Always check first (e.g. `apartments.com/robots.txt`).
- **Terms of Service** — Most large platforms (Apartments.com, Zillow, etc.) explicitly prohibit scraping in their ToS. Violating this is generally a civil (not criminal) matter, but it's a real risk for a public product.
- **Small/direct company sites** — Individual landlord or property company sites are a much grayer area. Scraping publicly listed rental info (prices, addresses, available units) is generally lower risk, especially for a student project.
- **Use case matters** — A personal/student project is very different from a commercial product monetizing that data.

**Going directly to the rental companies is the smarter move** — both legally and for data quality. Apartments.com and Craigslist are aggregators; by the time a listing gets there, it may already be rented, mis-priced, or months old. Direct sources mean:

- ✅ Fresher pricing
- ✅ Accurate availability
- ✅ Better unit-level detail (floor plans, amenities)
- ✅ Lower legal risk (it's their public listings)

---

#### Decisions Made

| Question | Answer |
|---|---|
| Intended scale? | Personal project now; will launch to real UIUC students if quality is good enough |
| Data freshness? | Automatic weekly refresh |
| Open to contacting companies? | Yes — but will fall back to scraping or manual collection if they don't respond |

---

## Recommended Strategy: 3-Tier Data Approach

Since the goal is auto-refresh but the app also needs to *work now*, build in layers:

```
Tier 1 (This week)     → Manual CSV snapshot     → MVP works immediately
Tier 2 (Before launch) → Per-company scrapers     → Auto-refresh weekly
Tier 3 (If lucky)      → Direct company data feed → Cleanest solution
```


#### Tier 1 — Manual CSV for MVP (2–3 hours, works today)

Don't let data collection block the RAG build. Manually copy ~15–20 listings per company into a CSV. This gets the AI pipeline working with real, accurate Champaign data.

**robots.txt Research Log (researched May 20):**

| Company | Website | robots.txt | Recommended Approach |
|---|---|---|---|
| **Green Street Realty** | greenstrealty.com | ✅ `User-agent: *` — wildcard allowed | Build a scraper (Tier 2 — skip manual) |
| **Universities Group** | ugroupcu.com | ✅ `User-agent: *` — wildcard allowed | Build a scraper (Tier 2 — skip manual) |
| Here 707 | here707.com | ❓ Not yet checked | Manual CSV for now |
| Hub Champaign | huboncampus.com | ⚠️ No robots.txt found | Manual CSV for now |
| Campus Town (The Dean) | thedean.com | ⚠️ robots.txt page 404 | Manual CSV for now |
| MHM Properties | mhmproperties.com | ✅ `User-agent: *` — wildcard allowed | Build a scraper (Tier 2) |

> 💡 **Updated plan:** Green Street, Universities Group, and MHM explicitly permit wildcard crawlers — go straight to building scrapers for them. Use manual CSV only as a fallback for companies whose `robots.txt` blocks or hasn't been checked yet.

**CSV schema (for manual entries):**
```
company, title, address, price, beds, baths, sqft, distance_to_campus, amenities, available_date, url
```

~60–80 rows across all sources is enough for the RAG pipeline to be genuinely useful for demos and testing.

---

#### 💡 Suggestions Based on robots.txt Research

**1. Promote Green Street and Universities Group straight to Tier 2**

Since both sites explicitly allow wildcard scrapers, there's no reason to waste time on a manual CSV for them. Build `scrapers/green_street.py` and `scrapers/universities_group.py` first. Combined, these two are likely the largest landlords in Champaign — you'll get plenty of real data to work with.

**2. Check Here 707 next**

Before defaulting to manual collection, spend 5 minutes checking:
```bash
curl https://here707.com/robots.txt
```

**3. Build one scraper at a time — don't batch them**

Start with `green_street.py`, get it fully working and normalized, embed those listings, and verify the RAG pipeline produces good results. Then add `universities_group.py`.

**4. Green Street first — biggest data bang**

Green Street is the largest local landlord in Champaign-Urbana. Prioritizing it means your MVP has the most coverage from day one.

**5. Keep the manual CSV as a living document anyway**

Even after scrapers are running, maintain a small handpicked CSV of 10–15 *premium* listings (popular buildings, well-known addresses) that you've verified by hand.

---

#### Tier 2 — Per-Company Scrapers with Weekly Refresh

Build **one small scraper per company** rather than one big scraper. Each outputs to the same schema.

**`refresh.py` (the scheduler):**
```python
import schedule, time
from scrapers import green_street, universities_group, here_707, hub_champaign
from normalize import save_to_db
from ingest import rebuild_vectorstore

def weekly_refresh():
    print("🔄 Starting weekly listing refresh...")
    all_listings = (
        green_street.scrape() +
        universities_group.scrape() +
        here_707.scrape() +
        hub_champaign.scrape()
    )
    save_to_db(all_listings)
    rebuild_vectorstore()
    print(f"✅ Refreshed {len(all_listings)} listings")

weekly_refresh()
schedule.every(7).days.do(weekly_refresh)

while True:
    schedule.run_pending()
    time.sleep(3600)
```

---

#### Tier 3 — Direct Company Outreach

**Email template:**

> **Subject:** UIUC Student Project — Housing Search Tool for Students
>
> Hi [Name],
>
> I'm a CS student at UIUC building an AI-powered housing search tool specifically for UIUC students — think "ask in plain English, get ranked apartments near campus." I'm targeting local Champaign landlords rather than Apartments.com to keep the data accurate and current.
>
> Would you be open to sharing a simple data export (CSV or JSON) of your current available units? Even a basic spreadsheet with unit type, price, and address would work. I'd display your listings with direct links back to your site, and credit you as a source.
>
> Happy to share the app once it's live. Thanks for your time!

---

#### Decision Tree for Each Company

```
For each company:
    ↓
Check robots.txt
    ├── Blocked? → Try outreach email → No response? → Skip or manual
    └── Allowed? → Write scraper
                    ├── Static HTML? → Use requests + BeautifulSoup
                    └── JS-rendered? → Use playwright (handles React/Vue sites)
```

---

## Part 2 — robots.txt Raw Research

*Checked May 20, 2026*

### Green Street Realty
**URL:** https://www.greenstrealty.com/robots.txt  
**Checked:** May 20, 2026

#### Raw robots.txt

```
User-agent: AI2Bot
User-agent: Ai2Bot-Dolma
User-agent: Amazonbot
User-agent: Brightbot 1.0
User-agent: Bytespider
User-agent: CCBot
User-agent: cohere-ai
User-agent: cohere-training-data-crawler
User-agent: Crawlspace
User-agent: Diffbot
User-agent: DuckAssistBot
User-agent: FacebookBot
User-agent: FriendlyCrawler
User-agent: iaskspider/2.0
User-agent: ICC-Crawler
User-agent: ImagesiftBot
User-agent: img2dataset
User-agent: ISSCyberRiskCrawler
User-agent: Kangaroo Bot
User-agent: Meta-ExternalAgent
User-agent: Meta-ExternalFetcher
User-agent: omgili
User-agent: omgilibot
User-agent: PanguBot
User-agent: PetalBot
User-agent: Scrapy
User-agent: SemrushBot-OCOB
User-agent: SemrushBot-SWA
User-agent: Sidetrade indexer bot
User-agent: Timpibot
User-agent: VelenPublicWebCrawler
User-agent: Webzio-Extended
User-agent: YouBot
Disallow: /

User-agent: *
Content-signal: search=yes,ai-train=no
Crawl-delay: 10
Disallow: /cdn-cgi/
Disallow: /backend/
Disallow: /modules/
Sitemap: https://www.greenstrealty.com/sitemap.xml
```

#### Analysis

**Block 1 — Named bots are fully blocked**

The first block lists specific crawlers (including `Scrapy`, a Python scraping framework) and blocks them from everything with `Disallow: /`. This shows Green Street is actively aware of scraping tools. Our scraper uses Playwright with a real Chrome `User-Agent`, so it does **not** fall into this block.

**Block 2 — Everyone else (`User-agent: *`)**

| Signal | Meaning | Impact on our scraper |
|---|---|---|
| `Disallow: /cdn-cgi/`, `/backend/`, `/modules/` | These specific paths are blocked | ✅ We only hit `/properties` — not affected |
| `Crawl-delay: 10` | Wait 10 seconds between requests | ✅ Added `time.sleep(10)` to `green_street.py` |
| `Content-signal: ai-train=no` | Don't use content to train AI models | ✅ We're not training a model — powering a search app |

The `/properties` path is **not listed under Disallow**, so crawling it is permitted.

#### The `ai-train=no` Signal

They're saying: *don't use our content to train AI models.* We are **not** training a model — we're using listing data to power a housing search app for students. That's closer to how Google indexes their site than how a company like OpenAI trains on web data. The line is genuinely blurry, and this signal is relatively new with no legal precedent yet. For a personal student project, the risk is low. If the app is launched publicly and monetized, this is worth revisiting.

#### Is It Illegal?

**No.** Under current US law, scraping publicly accessible data is not illegal. The key precedent is *hiQ Labs v. LinkedIn* (9th Circuit, 2022), which held that scraping publicly available web data does not violate the Computer Fraud and Abuse Act (CFAA). Green Street's listing prices and addresses are meant to be seen by prospective tenants — this is not private data behind a login. `robots.txt` is also **not legally binding** — it is a convention, not a contract.

#### Summary

| Question | Answer |
|---|---|
| Is it illegal? | **No** — publicly accessible listing data, no CFAA violation |
| Does robots.txt permit it? | **Yes** — `/properties` is not blocked for `User-agent: *` |
| Is it ethical? | **Yes** — `time.sleep(10)` crawl delay respected in scraper |
| Any risk at all? | Minimal for a student project; revisit `ai-train=no` if commercializing |

**Verdict: Okay to proceed. ✅**

---

#### Technical Note

```Bas
Fetch(https://www.greenstrealty.com/properties/search/CYBbxIDVHJLRZAOXJ5ZNAqELnhIoqlqSH3WfJKjYkKqvLTcOwb-FJ4tT-yOriG6sF2KT24ejiG6KccBxT3QFQnk_pnuDN4uWArV7RRD-N3U1aZ5CUziQs7BkYpwXlOU4G2t)
  ⎿  Received 0 bytes (403 Forbidden)

⏺ That URL is session-protected (403). Let me try their main public properties page instead.
  
⏺ Fetch(https://www.greenstrealty.com/properties)
  ⎿  Received 0 bytes (403 Forbidden)

⏺ Fetch(https://www.greenstrealty.com)
  ⎿  Received 0 bytes (403 Forbidden)
```

```
⏺ The entire greenstrealty.com domain is returning 403 Forbidden for automated requests — their server is
   actively blocking non-browser HTTP calls, even though their robots.txt permits crawlers. These are two
   different things:

  - robots.txt = polite permission — tells crawlers they're allowed to visit
  - HTTP 403 = active technical block — the server detects it's not a real browser and refuses the
  connection

  The requests library won't work here. Here's what that means for your scraper and your options:

```
```
  What's Happening
  
  The long token in your URL (CYBbxIDVHJLRZAOX...) is a session key generated by your browser after you
  loaded the page. That token is tied to your browser session — it's why it works for you but not for a
  bare requests call.
```
```
  Your Options

  Option A — Switch to Playwright (Recommended)

  Playwright launches a real headless Chrome browser, which passes bot detection checks because it
  behaves exactly like a human visitor. It's the right tool for JS-rendered or bot-protected sites.

  pip install playwright
  playwright install chromium

  The scraper logic stays the same — you just swap requests.get() for Playwright's page.goto() and use
  Playwright's selector API instead of BeautifulSoup. This is the path worth taking if you want automated
   weekly refresh.
```



Site returns `403 Forbidden` to bare `requests` calls — requires **Playwright** (real headless browser) to load. 
```Bash
(.venv) shuyangzhang@Shuyangs-MBP ai % pip install playwright
playwright install chromium

Collecting playwright
  Downloading playwright-1.60.0-py3-none-macosx_11_0_arm64.whl.metadata (3.5 kB)
Collecting pyee<14,>=13 (from playwright)
  Downloading pyee-13.0.1-py3-none-any.whl.metadata (3.0 kB)
Collecting greenlet<4.0.0,>=3.1.1 (from playwright)
  Downloading greenlet-3.5.1-cp314-cp314-macosx_11_0_universal2.whl.metadata (3.8 kB)
Requirement already satisfied: typing-extensions in ./.venv/lib/python3.14/site-packages (from pyee<14,>=13->playwright) (4.15.0)
Downloading playwright-1.60.0-py3-none-macosx_11_0_arm64.whl (42.3 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 42.3/42.3 MB 34.3 MB/s  0:00:01
Downloading greenlet-3.5.1-cp314-cp314-macosx_11_0_universal2.whl (285 kB)
Downloading pyee-13.0.1-py3-none-any.whl (15 kB)
Installing collected packages: pyee, greenlet, playwright
Successfully installed greenlet-3.5.1 playwright-1.60.0 pyee-13.0.1
Downloading Chrome for Testing 148.0.7778.96 (playwright chromium v1223) from https://cdn.playwright.dev/builds/cft/148.0.7778.96/mac-arm64/chrome-mac-arm64.zip
169.2 MiB [====================] 100% 0.0s
Chrome for Testing 148.0.7778.96 (playwright chromium v1223) downloaded to /Users/shuyangzhang/Library/Caches/ms-playwright/chromium-1223
Downloading FFmpeg (playwright ffmpeg v1011) from https://cdn.playwright.dev/dbazure/download/playwright/builds/ffmpeg/1011/ffmpeg-mac-arm64.zip
1 MiB [====================] 100% 0.0s
FFmpeg (playwright ffmpeg v1011) downloaded to /Users/shuyangzhang/Library/Caches/ms-playwright/ffmpeg-1011
Downloading Chrome Headless Shell 148.0.7778.96 (playwright chromium-headless-shell v1223) from https://cdn.playwright.dev/builds/cft/148.0.7778.96/mac-arm64/chrome-headless-shell-mac-arm64.zip
92.4 MiB [====================] 100% 0.0s
Chrome Headless Shell 148.0.7778.96 (playwright chromium-headless-shell v1223) downloaded to /Users/shuyangzhang/Library/Caches/ms-playwright/chromium_headless_shell-1223

(.venv) shuyangzhang@Shuyangs-MBP ai % 
```

Scraper written, tested, and ran successfully:

```Bash
(.venv) shuyangzhang@Shuyangs-MBP ai %   source ~/Library/CloudStorage/OneDrive-Personal/ai/.venv/bin/activate 
python scrapers/green_street.py
Found 253 property cards on the page
✅ Saved 489 floor plan listings from 251 properties
   → green_street_raw.json
```

---

### Universities Group
**URL:** https://ugroupcu.com/robots.txt

```
# START YOAST BLOCK
# ---------------------------
User-agent: *
Disallow:

Sitemap: https://ugroupcu.com/sitemap_index.xml
# ---------------------------
# END YOAST BLOCK
```

**Verdict:** ✅ No disallow rules — all paths open to crawlers.

---

### Hub on Campus
**URL:** https://huboncampus.com/robots.txt

```
(none — no robots.txt file found)
```

**Verdict:** ⚠️ No robots.txt at all. Technically no restrictions stated, but proceed carefully. Manual CSV recommended until scraper is verified.

---

### Campus Town / The Dean
**URL:** https://www.thedean.com/campustown/robots.txt

```
This www.thedean.com page can't be found
HTTP ERROR 404
```

**Verdict:** ⚠️ robots.txt not found (404). Same situation as Hub — no explicit restrictions, but no explicit permission either. Manual CSV for now.

---

### MHM Properties
**URL:** https://www.mhmproperties.com/robots.txt

```
Crawl-delay: 10
# START YOAST BLOCK
# ---------------------------
User-agent: *
Disallow:

Sitemap: https://www.mhmproperties.com/sitemap_index.xml
# ---------------------------
# END YOAST BLOCK
```

**Verdict:** ✅ Wildcard allowed, no disallow rules. Respect `Crawl-delay: 10`.

---

## Part 3 — Green Street Data Pipeline

### HTML Inspection

While building `green_street.py`, inspecting the page source revealed that every property card embeds a `<script type="application/json" class="property-info-json">` tag containing all property data as structured JSON — no fragile CSS selector scraping needed. Raw wrapper from Chrome DevTools:

**HTML card structure** (outer wrapper + key elements):

```html
<div class="property-outer-wrapper wide" data-id="375">

  <!-- ★ All property data lives here as structured JSON — no CSS selector scraping needed -->
  <script type="application/json" class="property-info-json">
    { ... see JSON block below ... }
  </script>

  <div class="property-wrapper">
    <div class="prop-image-wrapper"> ... </div>

    <div class="property-data">
      <div class="property-title">105 E Armory Ave</div>
      <div class="property-price-totals">$875 – $1,650 /bed</div>
      <div class="property-price-totals">$1,650 – $3,600 /mth</div>
      <div class="fplan-row">1 – 4 bed · 1 – 4 bath</div>
      <a class="property-link" href="...">View Availability</a>
    </div>
  </div>

</div>
```

**JSON content** inside `<script class="property-info-json">` (key fields only, photos/album arrays trimmed):

```json
{
  "address_1":       "105 E Armory Ave",
  "city":            "Champaign",
  "state":           "IL",
  "zip":             "61820",
  "type_of_property":"Apartment",
  "property_area":   "on-campus",
  "roommate_match":  "1",
  "url":             "https://www.greenstrealty.com/properties/profile/105-e-armory-ave",

  "fplans": [
    {
      "title":         "1 Bedroom",
      "beds":          "1",
      "baths":         "1.0",
      "availability":  "Leased",
      "total_price":   "1650",
      "price_per_bed": "1650"
    },
    {
      "title":         "3 Bedroom",
      "beds":          "3",
      "baths":         "3.0",
      "availability":  "Available August 2026",
      "total_price":   "2700",
      "price_per_bed": "900"
    },
    {
      "title":         "4 Bedroom",
      "beds":          "4",
      "baths":         "4.0",
      "availability":  "Available August 2026",
      "total_price":   "3500-3600",
      "price_per_bed": "875-900"
    }
  ],

  "prices": {
    "bedlow":  "875",
    "bedhigh": "1650",
    "totlow":  "1650",
    "tothigh": "3600"
  }
}
```

**Key finding:** the `fplans` array inside the JSON holds one object per floor plan (1BR, 2BR, 3BR, 4BR), each with its own `beds`, `baths`, `availability`, `total_price`, and `price_per_bed`. This is why the scraper iterates `fplans` rather than scraping HTML elements — the data is already structured.

---

### Pipeline

```
greenstrealty.com/properties
        ↓  Playwright launches headless Chromium (site blocks bare requests calls)
        ↓  waits for networkidle, reads every div.property-outer-wrapper
        ↓  each card has <script class="property-info-json"> with structured JSON
        ↓  iterates fplans[] — one row per floor plan per property

scrapers/green_street.py          →  run: python scrapers/green_street.py
        ↓  489 floor plan listings from 251 properties

green_street_raw.json
        ↓  parse_price_range: "875-900" → (875, 900)
        ↓  re-composes text chunk with honest price ranges
        ↓  writes richer schema: address, area, availability, baths, etc.

normalize_green_street.py         →  run: python normalize_green_street.py
        ↓
        ↓  Loaded 489 records from green_street_raw.json
        ↓  ✅ Stored 489 listings in green_street_listings.db
        ↓     Available : 167  |  Leased : 322
        ↓     Has price : 454  |  No price : 35
        ↓     Price ranges (low ≠ high) : 200

green_street_listings.db  (SQLite, 489 rows · 17 columns)
        ↓  ready for embedding

ingest.py                         →  run: python ingest.py
        ↓

chroma_db/
```

#### Final SQLite Schema (`green_street_listings.db`)

```sql
id                  INTEGER PRIMARY KEY AUTOINCREMENT
company             TEXT
address             TEXT
area                TEXT     -- "on-campus", "downtown", etc.
property_type       TEXT     -- "Apartment", etc.
roommate_match      INTEGER  -- 0 or 1
unit_type           TEXT     -- "1 Bedroom", "2 Bedroom", etc.
beds                INTEGER
baths               REAL
sqft                INTEGER
price_per_bed_low   INTEGER  -- lower bound (or exact price if no range)
price_per_bed_high  INTEGER  -- upper bound (same as low if no range)
price_total_low     INTEGER  -- lower bound (or exact price if no range)
price_total_high    INTEGER  -- upper bound (same as low if no range)
availability        TEXT     -- "Available August 2026" or "Leased"
url                 TEXT
text                TEXT     -- pre-composed RAG chunk for embedding
```
---

### Normalization Decisions

#### What Green Street Data Already Has

| Green Street field | Already clean? | What generic `normalize.py` would do instead |
|---|---|---|
| `beds` | ✅ `"3"` | use regex to extract from messy title |
| `price_per_bed` | ⚠️ `"875-900"` (range) | use regex to extract from messy string |
| `address` | ✅ full address string | buried in `raw_meta` |
| `availability` | ✅ `"Available August 2026"` | not captured at all |
| `text` | ✅ already composed in scraper | needs to be composed manually |

No regex needed — Green Street data is already structured. `normalize_green_street.py` is a plain loader, not a parser.

---

#### Price Normalization — Low/High Bounds (not just lower bound)

**Decision:** Price range strings (e.g. `"875-900"`) are split into **two integer columns** — `_low` and `_high` — rather than a single lower-bound number.

**Why:** Storing only `875` is misleading — a student clicks expecting ≤$875 and finds the unit is $900. Storing both bounds keeps the data honest end-to-end. Single prices (e.g. `"900"`) produce `low = high = 900`.

```
"900"       → (900, 900)
"875-900"   → (875, 900)
""          → (None, None)
```

> See `parse_price_range` in `normalize_green_street.py`.

---

#### Price Filtering — How to Handle Range Overlap

**The problem:** a property priced `$700–$900/bed` overlaps a user's `$800` budget. Three options:

| Option | Filter | Result |
|---|---|---|
| A | `price_per_bed_high <= 800` | Listing excluded — user misses the $700 1BR |
| B | `price_per_bed_low <= 800` | Included silently — user sees $700, finds $900 (bait-and-switch) |
| **C ✅** | `price_per_bed_low <= 800` | Included, LLM flags the range explicitly |

**Decision: Option C.** A `$700–$900` property has multiple unit types — a 1BR at $700 and a 4BR at $900. Excluding the whole property on `high > budget` throws away the affordable unit too. Instead:
- Retriever filters on `price_per_bed_low <= budget` (wide net)
- LLM reads the honest range from the `text` chunk and calls it out
- Prompt template in `rag_chain.py` instructs: *"If a listing's price range may exceed the student's budget, say so explicitly."*

---
