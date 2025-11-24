# Doctor Scraper & ML Pipeline

A simple end-to-end Python pipeline for scraping doctor data and training ML models.

## ⚠️ Legal & Ethical Warning

**These tools are for LEGITIMATE use only on sites that explicitly allow scraping.**

- Always check `robots.txt` and Terms of Service
- Never use anti-detection techniques to bypass blocks
- See `ANTI_DETECTION_WARNING.md` for detailed legal information
- You are responsible for compliance with all laws

### ⚠️ YELLOWPAGES SPECIFICALLY FORBIDDEN

**DO NOT scrape YellowPages:**
- ❌ Explicitly forbidden in Terms of Service
- ❌ Will result in 403 errors
- ❌ Legal risk if violated
- ✅ Use `google_places_scraper.py` instead (legal alternative)

See `YELLOWPAGES_WARNING.md` for details.

## 🎯 Recommended Solution

**For production use, see `complete_solution.py`:**

This implements the **API-First Architecture** with:
- ✅ Google Places API (primary source)
- ✅ BetterDoctor API (secondary source)
- ✅ Intelligent deduplication algorithm
- ✅ Quality scoring
- ✅ Multi-source aggregation

**Quick start:**
```bash
pip install googlemaps requests
python complete_solution.py
```

See `SOLUTION_ARCHITECTURE.md` for complete architecture details.

---

## Quick Start (Single File)

For a simple, single-file solution, use `generic_doctor_bot.py`:

```bash
# 1. Install dependencies
pip install selenium webdriver-manager beautifulsoup4

# 2. Edit generic_doctor_bot.py
#    - Update site_config with your target site
#    - Set CSS selectors for search box, results, fields

# 3. Run it
python generic_doctor_bot.py
```

This single file includes everything: scraping, auto-detection, CSV saving.

## Advanced Features (Use Responsibly)

For sites that allow scraping but have basic anti-bot measures, see `advanced_scraper.py`:

- Anti-detection techniques
- Human-like behavior simulation
- Browser fingerprinting spoofing
- Proxy support

**⚠️ CRITICAL**: Only use on sites that explicitly allow scraping. See `ANTI_DETECTION_WARNING.md` for legal details.

## Full Pipeline (Multi-File)

For the complete pipeline with ML training, use the multi-file structure:

## ⚠️ Legal Notice

**Only use this on websites that explicitly allow automated scraping!**

- Always check `robots.txt` (e.g., `https://example.com/robots.txt`)
- Review the site's Terms of Service
- Many sites (YellowPages, LinkedIn, etc.) explicitly forbid scraping
- You are responsible for compliance with all applicable laws

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install Chrome browser** (required for Selenium)

3. **Configure your site:**
   - Open `collect_data.py`
   - Update `SITE_CONFIG` with:
     - A website URL that allows scraping
     - Correct CSS selectors for that site
     - Field mappings for data extraction

## Usage

### 1. Collect Data

Scrape doctors and save to CSV:

```bash
python collect_data.py
```

- Enter search queries (e.g., "orthopedic doctor", "cardiologist")
- Data is saved to `doctors_data.csv`
- Run multiple times to build your dataset

### 2. Train Model

Train a model to predict doctor specialty:

```bash
python train_model.py
```

This will:
- Load data from `doctors_data.csv`
- Train a text classification model
- Save model to `specialty_model.joblib`
- Show performance metrics

### 3. Make Predictions

Test the trained model:

```bash
python train_model.py predict
```

Or in Python:
```python
import joblib

model = joblib.load("specialty_model.joblib")
le = joblib.load("label_encoder.joblib")

pred = model.predict(["Dr. John Smith, Heart Clinic, 123 Main St"])
specialty = le.inverse_transform(pred)[0]
print(specialty)  # e.g., "Cardiologist"
```

## Project Structure

```
doctor_bot/
├── scraper.py          # Core scraping logic with auto-detection
├── collect_data.py     # CLI tool to scrape and save CSV
├── train_model.py      # ML model training and prediction
├── requirements.txt    # Python dependencies
├── README.md          # This file
├── doctors_data.csv    # Generated: scraped data
├── specialty_model.joblib      # Generated: trained model
└── label_encoder.joblib        # Generated: label encoder
```

## Customization

### Adding More Fields

Edit `SITE_CONFIG["fields"]` in `collect_data.py`:

```python
"fields": {
    "name": ".doctor-name",
    "specialty": ".doctor-specialty",
    "phone": ".doctor-phone",
    "address": ".doctor-address",
    "email": ".doctor-email",  # Add new field
    "rating": ".doctor-rating"  # Add new field
}
```

### Changing the Model

Edit `train_model.py` to:
- Use different algorithms (Random Forest, SVM, etc.)
- Predict different targets (location, rating, etc.)
- Add feature engineering
- Use embeddings instead of TF-IDF

### Auto-Detection

The scraper can auto-detect search boxes if you don't provide `search_box_selector`. It looks for:
- `input[type='search']`
- Inputs with "search", "query", "keyword" in name/id/placeholder

## Troubleshooting

**403 Forbidden Error:**
- Site blocks automated access
- Use a different site that allows scraping

**No Results Found:**
- Check CSS selectors are correct
- Verify site structure hasn't changed
- Try different search terms

**Model Performance Poor:**
- Collect more data (aim for 100+ samples per class)
- Check data quality (noise, missing values)
- Try different features or algorithms

## Example Workflow

```bash
# 1. Collect data
python collect_data.py
# Enter: "orthopedic doctor"
# Enter: "cardiologist"
# Enter: "dermatologist"
# ... (collect 50-100+ samples)

# 2. Train model
python train_model.py

# 3. Test predictions
python train_model.py predict
```

## Next Steps

- Add more sophisticated models (neural networks, embeddings)
- Implement data validation and cleaning
- Add support for multiple sites
- Create a simple web interface
- Export to different formats (JSON, Excel)

