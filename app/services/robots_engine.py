"""Universal Robot execution engine"""
import logging
from typing import List, Dict, Any, Optional
import json
import re

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_SCRAPING_DEPS = True
except ImportError:
    HAS_SCRAPING_DEPS = False
    requests = None
    BeautifulSoup = None

try:
    from app.services.selenium_scraper import SeleniumScraper
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False
    SeleniumScraper = None

logger = logging.getLogger(__name__)


class RobotExecutionError(Exception):
    """Robot execution error"""
    pass


class RobotsEngine:
    """Engine for executing robot workflow specs"""
    
    @staticmethod
    def execute_workflow(
        url: str,
        workflow_spec: Dict[str, Any],
        schema: List[Dict[str, Any]],
        search_query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a robot workflow on a single URL
        
        Args:
            url: URL to scrape
            workflow_spec: Workflow DSL configuration
            schema: Field schema definitions
            search_query: Optional search query for interactive sites
        
        Returns:
            List of extracted rows (dicts with field values)
        """
        # Check if this is an interactive scraping workflow
        requires_interaction = workflow_spec.get("requires_interaction", False)
        search_box_selector = workflow_spec.get("search_box_selector")
        
        if requires_interaction or search_box_selector:
            # Use Selenium for interactive scraping
            if not HAS_SELENIUM:
                raise RobotExecutionError("Selenium not available. Install with: pip install selenium webdriver-manager")
            
            if not search_query:
                raise RobotExecutionError("search_query is required for interactive scraping")
            
            return RobotsEngine._execute_interactive_workflow(
                url, workflow_spec, schema, search_query
            )
        else:
            # Use simple HTTP requests
            return RobotsEngine._execute_simple_workflow(url, workflow_spec, schema)
    
    @staticmethod
    def _execute_interactive_workflow(
        url: str,
        workflow_spec: Dict[str, Any],
        schema: List[Dict[str, Any]],
        search_query: str
    ) -> List[Dict[str, Any]]:
        """Execute workflow using Selenium for interactive sites"""
        # Build Selenium config from workflow_spec
        selenium_config = {
            "url": url,
            "search_box_selector": workflow_spec.get("search_box_selector"),
            "submit_selector": workflow_spec.get("submit_selector"),
            "result_item_selector": workflow_spec.get("item_selector", ""),
            "fields": workflow_spec.get("fields", {}),
            "profile_link_selector": workflow_spec.get("profile_link_selector"),
            "wait_seconds": workflow_spec.get("wait_seconds", 5),
            "pagination": workflow_spec.get("pagination"),
        }
        
        with SeleniumScraper(headless=True) as scraper:
            results = scraper.scrape_with_search(
                query=search_query,
                config=selenium_config,
                max_results=workflow_spec.get("max_results")
            )
        
        # Map results to schema format
        mapped_results = []
        for result in results:
            mapped = {}
            for field_def in schema:
                field_name = field_def["name"]
                mapped[field_name] = result.get(field_name)
            mapped_results.append(mapped)
        
        return mapped_results
    
    @staticmethod
    def _execute_simple_workflow(
        url: str,
        workflow_spec: Dict[str, Any],
        schema: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute workflow using simple HTTP requests"""
        if not HAS_SCRAPING_DEPS:
            raise RobotExecutionError("Missing dependencies: requests and beautifulsoup4 required")
        
        try:
            # Fetch the page
            response = requests.get(url, timeout=30, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            response.raise_for_status()
            
            html = response.text
            soup = BeautifulSoup(html, "html.parser")
            
            # Get workflow configuration
            source_type = workflow_spec.get("source", "html_list_page")
            item_selector = workflow_spec.get("item_selector", "")
            fields_config = workflow_spec.get("fields", {})
            
            if not item_selector:
                # Single item page - extract one row
                return [RobotsEngine._extract_fields(soup, fields_config, schema)]
            
            # List page - find all items
            items = soup.select(item_selector)
            if not items:
                logger.warning(f"No items found with selector '{item_selector}' on {url}")
                return []
            
            rows = []
            for item in items:
                try:
                    row = RobotsEngine._extract_fields(item, fields_config, schema)
                    if row:
                        rows.append(row)
                except Exception as e:
                    logger.warning(f"Failed to extract row from item: {e}")
                    continue
            
            return rows
            
        except requests.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, 'response') else None
            if status_code == 403:
                raise RobotExecutionError(
                    f"Access forbidden (403): This website blocks automated scraping. "
                    f"Please check the site's Terms of Service and robots.txt. "
                    f"Only scrape sites that explicitly allow automated access."
                )
            elif status_code == 404:
                raise RobotExecutionError(f"Page not found (404): The URL does not exist.")
            elif status_code == 429:
                raise RobotExecutionError(
                    f"Rate limited (429): Too many requests. Please wait before trying again."
                )
            else:
                raise RobotExecutionError(f"HTTP error {status_code}: {str(e)}")
        except requests.RequestException as e:
            raise RobotExecutionError(f"Failed to fetch URL: {str(e)}")
        except Exception as e:
            raise RobotExecutionError(f"Execution error: {str(e)}")
    
    @staticmethod
    def _extract_fields(
        element: Any,
        fields_config: Dict[str, Any],
        schema: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract field values from a DOM element"""
        row = {}
        
        for field_def in schema:
            field_name = field_def["name"]
            field_type = field_def.get("type", "string")
            required = field_def.get("required", False)
            
            # Get field config
            field_config = fields_config.get(field_name, {})
            extract_type = field_config.get("type", "css_text")
            selector = field_config.get("selector", "")
            
            value = None
            
            if extract_type == "css_text":
                if selector:
                    found = element.select_one(selector)
                    if found:
                        value = found.get_text(strip=True)
                else:
                    value = element.get_text(strip=True)
            
            elif extract_type == "css_attr":
                attr_name = field_config.get("attr", "href")
                if selector:
                    found = element.select_one(selector)
                    if found:
                        value = found.get(attr_name, "")
                else:
                    value = element.get(attr_name, "")
            
            elif extract_type == "regex":
                text = element.get_text()
                pattern = field_config.get("pattern", "")
                if pattern:
                    match = re.search(pattern, text)
                    if match:
                        value = match.group(1) if match.groups() else match.group(0)
            
            elif extract_type == "static":
                value = field_config.get("value", "")
            
            # Type conversion
            if value is not None:
                if field_type == "number":
                    try:
                        # Try to extract number from text
                        num_match = re.search(r"[\d.]+", str(value))
                        if num_match:
                            value = float(num_match.group())
                        else:
                            value = None
                    except (ValueError, AttributeError):
                        value = None
                elif field_type == "boolean":
                    value = str(value).lower() in ("true", "1", "yes", "on")
            
            # Handle required fields
            if required and (value is None or value == ""):
                # Skip this row if required field is missing
                return None
            
            row[field_name] = value
        
        return row
    
    @staticmethod
    def test_workflow(
        url: str,
        workflow_spec: Dict[str, Any],
        schema: List[Dict[str, Any]],
        max_rows: int = 5
    ) -> Dict[str, Any]:
        """
        Test workflow on a single URL and return sample rows
        
        Args:
            url: URL to test
            workflow_spec: Workflow configuration
            schema: Field schema
            max_rows: Maximum rows to return
        
        Returns:
            Dict with 'rows' (list) and 'total' (int)
        """
        rows = RobotsEngine.execute_workflow(url, workflow_spec, schema)
        total = len(rows)
        
        return {
            "rows": rows[:max_rows],
            "total": total,
            "url": url,
        }

