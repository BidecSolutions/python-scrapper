"""CLI entry point for lead scraper (optional)."""

import argparse

from app.core.logging import logger
from app.scraper.crawler import SimpleCrawler
from app.services.export_service import export_to_csv, export_to_json
from app.services.lead_service import LeadService
from app.sources.google_places import GooglePlacesSource
from app.sources.web_search import WebSearchSource


def main() -> None:
    parser = argparse.ArgumentParser(description="Lead scraper CLI")
    parser.add_argument("--niche", required=True, help="e.g. 'dentist clinic'")
    parser.add_argument("--location", required=False, help="e.g. 'Karachi'")
    parser.add_argument("--out", required=True, help="Output file (CSV or JSON)")
    parser.add_argument("--max-results", type=int, default=50, help="Maximum number of leads")
    parser.add_argument("--max-pages", type=int, default=5, help="Maximum pages per website")
    parser.add_argument("--format", choices=["csv", "json"], default="csv", help="Output format")
    args = parser.parse_args()

    sources = []
    try:
        sources.append(GooglePlacesSource())
        logger.info("Google Places source enabled")
    except Exception as e:
        logger.warning("Google Places source disabled: %s", e)

    try:
        sources.append(WebSearchSource())
        logger.info("Web Search source enabled")
    except Exception as e:
        logger.warning("Web Search source disabled: %s", e)

    if not sources:
        logger.error("No sources available. Please set at least one API key.")
        return

    crawler = SimpleCrawler(max_pages=args.max_pages)
    service = LeadService(sources=sources, crawler=crawler)

    logger.info("Searching for leads: %s in %s", args.niche, args.location or "any location")
    leads = service.search_leads(
        niche=args.niche,
        location=args.location,
        max_results=args.max_results,
    )

    if args.format == "csv":
        export_to_csv(leads, args.out)
    else:
        export_to_json(leads, args.out)

    logger.info("Saved %s leads to %s", len(leads), args.out)
    print(f"Saved {len(leads)} leads to {args.out}")


if __name__ == "__main__":
    main()

