# Introduction

A collection of web scrapers designed to extract grocery product data from major UK retailers.


Here’s a **cleaned-up and README-friendly version** of your example — formatted clearly, documented, and simplified for readability:

---

# 🧩 Example: Scrape Ocado Product Data

```python
import logging
import time
from surquest.utils.scrappers.ocado import Scraper, DataHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

start_time = time.perf_counter()

scraper = Scraper()
categories = scraper.fetch_categories()

total_categories = len(categories)
logging.info(f"Found {total_categories} categories to process.")

for idx, category in enumerate(categories, start=1):
    category_name = category.get("fullURLPath", "unknown").lower()
    category_id = category.get("id")

    logging.info(f"[{idx}/{total_categories}] Starting category: {category_name}")

    cat_start = time.perf_counter()
    try:
        # Step 1️⃣ Get product IDs
        product_ids, _ = scraper.get_products(category_id=category_id)
        logging.info(f"  → Retrieved {len(product_ids)} product IDs")

        # Step 2️⃣ Fetch product details
        product_details = scraper.get_product_details(product_ids=product_ids)
        data = list(product_details.values())
        logging.info(f"  → Fetched details for {len(data)} products")

        # Step 3️⃣ Save to file
        output_path = f"./ocado/uk/products.{category_name}.jsonl"
        DataHandler.save_as_jsonlines(data=data, file_path=output_path)
        logging.info(f"  ✅ Saved {len(data)} products to {output_path}")

    except Exception as e:
        logging.error(f"  ❌ Failed category {category_name}: {e}")

    finally:
        elapsed = time.perf_counter() - cat_start
        logging.info(f"  ⏱ Completed {category_name} in {elapsed:.2f}s\n")

total_time = time.perf_counter() - start_time
logging.info(f"🎉 Finished scraping all {total_categories} categories in {total_time:.2f}s")
```

## 🧠 Notes

* **`Scraper`** handles token initialization, session cookies, and API requests.
* **`get_products(category_id)`** retrieves product IDs and summaries for a given category.
* **`get_product_details(product_ids)`** fetches extended product metadata.
* **`DataHandler.save_as_jsonlines()`** writes results as a `.jsonl` file — one JSON object per line, ideal for large datasets.

✅ Example output files:

```
./ocado/uk/products.drinks.jsonl  
./ocado/uk/products.fruit-vegetables.jsonl  
```

---

# 🛒 Example: Scrape Tesco Online

The **Tesco Online Scraper** is a utility for extracting product data and taxonomy information directly from Tesco’s online store API.
It allows automated collection of product listings across all categories (“facets”) for a given region.

## 📦 Features

* Fetches complete taxonomy (category) structure for a Tesco region (e.g. `uk`, `ie`).
* Iterates through each facet and scrapes associated product listings.
* Saves product data locally in the efficient [JSON Lines](https://jsonlines.org/) format.
* Includes robust logging and error handling for long-running scrapes.

## 🚀 Usage Example

```python
import os
import logging
from surquest.utils.scrappers.tesco import Scraper, DataHandler


# --- Configuration ---
REGION = "uk"
API_KEY = "TvOSZJHlEk0pjniDGQFAc9Q59WGAR4dA"
OUTPUT_DIR = f"../data/{REGION}"


# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# --- Helper Functions ---
def ensure_output_dir(path: str) -> None:
    """Ensure that the output directory exists."""
    os.makedirs(path, exist_ok=True)


# --- Main Script ---
logging.info(f"Initializing Tesco scraper for region '{REGION}'...")
scraper = Scraper(api_key=API_KEY, region=REGION)
ensure_output_dir(OUTPUT_DIR)

logging.info("Fetching taxonomy data...")
taxonomy_data = scraper.fetch_taxonomy()
if not taxonomy_data or not taxonomy_data[0].get("data", {}).get("taxonomy"):
    logging.warning("No taxonomy data found. Exiting.")
    exit()

facets = taxonomy_data[0]["data"]["taxonomy"]
logging.info(f"Found {len(facets)} facets to process.")

for facet in facets:
    facet_name = facet.get("name", "unknown").lower().replace(" ", "-")
    facet_id = facet.get("id")

    if not facet_id:
        logging.warning(f"Skipping facet '{facet_name}' — missing ID.")
        continue

    logging.info(f"Fetching data for facet: {facet_name}")

    try:
        products = scraper.fetch_facet_products(facet_id, size=100)
        if not products:
            logging.warning(f"No products found for facet '{facet_name}'.")
            continue

        output_file = os.path.join(OUTPUT_DIR, f"products.{facet_name}.jsonl")
        DataHandler.save_as_jsonlines(data=products, file_path=output_file)

        logging.info(f"✅ Saved {len(products)} products to {output_file}")
    except Exception as e:
        logging.error(f"❌ Error fetching products for facet '{facet_name}': {e}")

logging.info("🎉 All facets processed successfully.")
```

## 🧩 How It Works

1. **Initialization** – The script authenticates using the provided API key and region.
2. **Taxonomy Fetch** – It retrieves the hierarchical list of product categories.
3. **Product Extraction** – For each category (facet), it queries and downloads available products.
4. **Data Storage** – All scraped products are saved as `.jsonl` files, one per facet.

## 📁 Output

Each facet (category) will produce one JSON Lines file inside the specified output directory:

```
../data/uk/
├── products.fruit.jsonl
├── products.vegetables.jsonl
├── products.meat.jsonl
└── ...
```

Each line represents a single product record.

## ⚙️ Configuration

| Variable     | Description                       | Example                              |
| ------------ | --------------------------------- | ------------------------------------ |
| `REGION`     | Tesco region to scrape            | `"uk"`, `"cz"`, `"hu"`, `"sk"`       |
| `API_KEY`    | API key for Tesco’s internal API  | `"TvOSZJHlEk0pjniDGQFAc9Q59WGAR4dA"` |
| `OUTPUT_DIR` | Local path for storing the output | `"../data/uk"`                       |

---

## 🧠 Notes

* Ensure you have access to the Tesco API for the specified region.
* API keys are region-specific and may expire or be rate-limited.
* Large regions can produce tens of thousands of product entries — consider running the script in a controlled environment.

