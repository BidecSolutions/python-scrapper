"""Advanced duplicate detection and merging for leads"""
import re
from typing import List, Dict, Set, Tuple
from urllib.parse import urlparse
from app.core.models import Lead


def normalize_domain(url: str) -> str:
    """Normalize domain for comparison"""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        # Remove www.
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except:
        return url.lower()


def normalize_name(name: str) -> str:
    """Normalize business name for comparison"""
    if not name:
        return ""
    # Lowercase, remove common suffixes, strip whitespace
    name = name.lower().strip()
    # Remove common business suffixes
    suffixes = [" inc", " inc.", " llc", " ltd", " ltd.", " corp", " corp.", " pvt", " pvt."]
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    return name


def normalize_phone(phone: str) -> str:
    """Normalize phone number for comparison"""
    if not phone:
        return ""
    # Remove all non-digit characters except +
    normalized = re.sub(r'[^\d+]', '', phone)
    # Remove leading + if present for comparison
    if normalized.startswith('+'):
        normalized = normalized[1:]
    # Take last 10 digits (for US numbers) or keep as is
    if len(normalized) > 10:
        normalized = normalized[-10:]
    return normalized


class DuplicateDetector:
    """Detect and merge duplicate leads from different sources"""
    
    @staticmethod
    def find_duplicates(leads: List[Lead]) -> Dict[int, List[int]]:
        """
        Find duplicate leads and return a mapping of lead_id -> [duplicate_ids]
        
        Returns:
            Dict mapping each lead's index to list of duplicate indices
        """
        duplicates: Dict[int, List[int]] = {}
        processed: Set[int] = set()
        
        for i, lead1 in enumerate(leads):
            if i in processed:
                continue
                
            duplicates[i] = []
            
            for j, lead2 in enumerate(leads[i+1:], start=i+1):
                if j in processed:
                    continue
                    
                if DuplicateDetector._are_duplicates(lead1, lead2):
                    duplicates[i].append(j)
                    processed.add(j)
            
            if duplicates[i]:
                processed.add(i)
            else:
                # No duplicates found, remove from dict
                del duplicates[i]
        
        return duplicates
    
    @staticmethod
    def _are_duplicates(lead1: Lead, lead2: Lead) -> bool:
        """Check if two leads are duplicates"""
        # Method 1: Same domain (normalized)
        domain1 = normalize_domain(lead1.website or "")
        domain2 = normalize_domain(lead2.website or "")
        if domain1 and domain2 and domain1 == domain2:
            return True
        
        # Method 2: Same name + same phone
        name1 = normalize_name(lead1.name or "")
        name2 = normalize_name(lead2.name or "")
        if name1 and name2 and name1 == name2:
            # Check if they share a phone number
            phones1 = {normalize_phone(p) for p in (lead1.phones or [])}
            phones2 = {normalize_phone(p) for p in (lead2.phones or [])}
            if phones1 and phones2 and phones1 & phones2:
                return True
            
            # Check if they share an email
            emails1 = {e.lower() for e in (lead1.emails or [])}
            emails2 = {e.lower() for e in (lead2.emails or [])}
            if emails1 and emails2 and emails1 & emails2:
                return True
        
        # Method 3: Same phone + same city (if both have phone and city)
        if lead1.phones and lead2.phones and lead1.city and lead2.city:
            phones1 = {normalize_phone(p) for p in lead1.phones}
            phones2 = {normalize_phone(p) for p in lead2.phones}
            if phones1 & phones2 and lead1.city.lower() == lead2.city.lower():
                return True
        
        return False
    
    @staticmethod
    def merge_leads(leads: List[Lead]) -> Lead:
        """Merge multiple duplicate leads into one"""
        if not leads:
            raise ValueError("Cannot merge empty list")
        if len(leads) == 1:
            return leads[0]
        
        # Start with the first lead
        merged = Lead(
            id=leads[0].id,
            name=leads[0].name,
            niche=leads[0].niche,
            website=leads[0].website,
            emails=list(leads[0].emails or []),
            phones=list(leads[0].phones or []),
            address=leads[0].address,
            source=leads[0].source,
            city=leads[0].city,
            country=leads[0].country,
        )
        
        # Collect all sources
        sources = {leads[0].source}
        
        # Merge data from other leads
        for lead in leads[1:]:
            # Merge emails
            merged.emails = list(set(merged.emails) | set(lead.emails or []))
            
            # Merge phones
            merged.phones = list(set(merged.phones) | set(lead.phones or []))
            
            # Use best name (longest, most complete)
            if lead.name and (not merged.name or len(lead.name) > len(merged.name)):
                merged.name = lead.name
            
            # Use best website (prefer https, longer domain)
            if lead.website:
                if not merged.website:
                    merged.website = lead.website
                elif lead.website.startswith("https://") and not merged.website.startswith("https://"):
                    merged.website = lead.website
            
            # Use best address (longest)
            if lead.address and (not merged.address or len(lead.address) > len(merged.address)):
                merged.address = lead.address
            
            # Use best city/country
            if lead.city and not merged.city:
                merged.city = lead.city
            if lead.country and not merged.country:
                merged.country = lead.country
            
            # Collect source
            if lead.source:
                sources.add(lead.source)
        
        # Update source to show all sources
        merged.source = ", ".join(sorted(sources))
        
        return merged

