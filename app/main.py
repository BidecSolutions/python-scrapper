"""CLI entry point for lead scraper"""
import argparse
from app.scraper.crawler import SimpleCrawler
from app.services.lead_service import LeadService
from app.services.export_service import export_to_csv, export_to_json
from app.sources.google_places import GooglePlacesSource
from app.sources.web_search import WebSearchSource
from app.core.logging import logger


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="Lead scraper MVP")
    parser.add_argument("--niche", required=True, help="e.g. 'dentist clinic'")
    parser.add_argument("--location", required=False, help="e.g. 'Karachi'")
    parser.add_argument("--out", required=True, help="Output file (CSV or JSON)")
    parser.add_argument("--max-results", type=int, default=50, help="Maximum number of leads")
    parser.add_argument("--max-pages", type=int, default=5, help="Maximum pages per website")
    parser.add_argument("--format", choices=["csv", "json"], default="csv", help="Output format")
    
    args = parser.parse_args()

    # Initialize sources
    sources = []
    
    # Add Google Places source
    try:
        sources.append(GooglePlacesSource())
        logger.info("Google Places source enabled")
    except ValueError as e:
        logger.warning(f"Google Places source disabled: {e}")
    
    # Add Web Search source
    try:
        sources.append(WebSearchSource())
        logger.info("Web Search source enabled")
    except Exception as e:
        logger.warning(f"Web Search source disabled: {e}")
    
    if not sources:
        logger.error("No sources available! Please set at least one API key.")
        return
    
    # Initialize crawler and service
    crawler = SimpleCrawler(max_pages=args.max_pages)
    service = LeadService(sources=sources, crawler=crawler)

    # Search for leads
    logger.info(f"Searching for leads: {args.niche} in {args.location or 'any location'}")
    leads = service.search_leads(
        niche=args.niche,
        location=args.location,
        max_results=args.max_results,
    )

    # Export results
    if args.format == "csv":
        export_to_csv(leads, args.out)
    else:
        export_to_json(leads, args.out)

    logger.info(f"Saved {len(leads)} leads to {args.out}")
    print(f"Saved {len(leads)} leads to {args.out}")


if __name__ == "__main__":
    main()

