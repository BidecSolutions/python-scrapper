"""Lead Health Score Service - Calculates data completeness and freshness scores"""
from typing import Dict, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.core.orm import LeadORM


class HealthScoreCalculator:
    """Calculates health score for leads based on data completeness and freshness"""
    
    # Score weights (total = 100)
    WEIGHTS = {
        "has_email": 20,
        "email_verified": 25,
        "has_phone": 10,
        "has_website": 10,
        "has_address": 5,
        "recently_updated": 20,  # Updated in last 30 days
        "no_bounce_flags": 10,  # No bounces/spam flags
    }
    
    @staticmethod
    def calculate(lead: LeadORM, email_verification_status: Optional[str] = None) -> Dict:
        """
        Calculate health score for a lead.
        
        Returns:
            {
                "score": 0-100,
                "breakdown": {
                    "has_email": {"points": 20, "max": 20, "reason": "Email found"},
                    ...
                },
                "grade": "A" | "B" | "C" | "D" | "F",
                "recommendations": ["Add phone number", ...]
            }
        """
        breakdown = {}
        total_score = 0
        recommendations = []
        
        # 1. Has email (20 points)
        has_email = bool(lead.emails and len(lead.emails) > 0)
        if has_email:
            breakdown["has_email"] = {
                "points": HealthScoreCalculator.WEIGHTS["has_email"],
                "max": HealthScoreCalculator.WEIGHTS["has_email"],
                "reason": f"Email found ({len(lead.emails)} address{'es' if len(lead.emails) > 1 else ''})",
                "status": "good"
            }
            total_score += HealthScoreCalculator.WEIGHTS["has_email"]
        else:
            breakdown["has_email"] = {
                "points": 0,
                "max": HealthScoreCalculator.WEIGHTS["has_email"],
                "reason": "No email address",
                "status": "missing"
            }
            recommendations.append("Add email address")
        
        # 2. Email verified (25 points) - only if email exists
        if has_email:
            # Check verification status
            is_verified = False
            if email_verification_status:
                is_verified = email_verification_status in ["valid", "risky"]  # Risky still counts as verified
            elif hasattr(lead, "email_records") and lead.email_records:
                # Check if any email record is verified
                for email_record in lead.email_records:
                    if hasattr(email_record, "verification_status"):
                        if email_record.verification_status in ["valid", "risky"]:
                            is_verified = True
                            break
            
            if is_verified:
                breakdown["email_verified"] = {
                    "points": HealthScoreCalculator.WEIGHTS["email_verified"],
                    "max": HealthScoreCalculator.WEIGHTS["email_verified"],
                    "reason": "Email verified",
                    "status": "good"
                }
                total_score += HealthScoreCalculator.WEIGHTS["email_verified"]
            else:
                breakdown["email_verified"] = {
                    "points": 0,
                    "max": HealthScoreCalculator.WEIGHTS["email_verified"],
                    "reason": "Email not verified",
                    "status": "warning"
                }
                if has_email:
                    recommendations.append("Verify email address")
        else:
            breakdown["email_verified"] = {
                "points": 0,
                "max": HealthScoreCalculator.WEIGHTS["email_verified"],
                "reason": "No email to verify",
                "status": "na"
            }
        
        # 3. Has phone (10 points)
        has_phone = bool(lead.phones and len(lead.phones) > 0)
        if has_phone:
            breakdown["has_phone"] = {
                "points": HealthScoreCalculator.WEIGHTS["has_phone"],
                "max": HealthScoreCalculator.WEIGHTS["has_phone"],
                "reason": f"Phone found ({len(lead.phones)} number{'s' if len(lead.phones) > 1 else ''})",
                "status": "good"
            }
            total_score += HealthScoreCalculator.WEIGHTS["has_phone"]
        else:
            breakdown["has_phone"] = {
                "points": 0,
                "max": HealthScoreCalculator.WEIGHTS["has_phone"],
                "reason": "No phone number",
                "status": "missing"
            }
            recommendations.append("Add phone number")
        
        # 4. Has website (10 points)
        has_website = bool(lead.website and lead.website.strip())
        if has_website:
            breakdown["has_website"] = {
                "points": HealthScoreCalculator.WEIGHTS["has_website"],
                "max": HealthScoreCalculator.WEIGHTS["has_website"],
                "reason": "Website available",
                "status": "good"
            }
            total_score += HealthScoreCalculator.WEIGHTS["has_website"]
        else:
            breakdown["has_website"] = {
                "points": 0,
                "max": HealthScoreCalculator.WEIGHTS["has_website"],
                "reason": "No website",
                "status": "missing"
            }
            recommendations.append("Add website URL")
        
        # 5. Has address (5 points)
        has_address = bool(lead.address and lead.address.strip())
        if has_address:
            breakdown["has_address"] = {
                "points": HealthScoreCalculator.WEIGHTS["has_address"],
                "max": HealthScoreCalculator.WEIGHTS["has_address"],
                "reason": "Address available",
                "status": "good"
            }
            total_score += HealthScoreCalculator.WEIGHTS["has_address"]
        else:
            breakdown["has_address"] = {
                "points": 0,
                "max": HealthScoreCalculator.WEIGHTS["has_address"],
                "reason": "No address",
                "status": "missing"
            }
        
        # 6. Recently updated (20 points)
        if lead.updated_at:
            # Handle timezone-aware and naive datetimes
            updated_at = lead.updated_at
            if updated_at.tzinfo is not None:
                updated_at = updated_at.replace(tzinfo=None)
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            days_since_update = (now - updated_at).days
            if days_since_update <= 30:
                breakdown["recently_updated"] = {
                    "points": HealthScoreCalculator.WEIGHTS["recently_updated"],
                    "max": HealthScoreCalculator.WEIGHTS["recently_updated"],
                    "reason": f"Updated {days_since_update} day{'s' if days_since_update != 1 else ''} ago",
                    "status": "good"
                }
                total_score += HealthScoreCalculator.WEIGHTS["recently_updated"]
            elif days_since_update <= 90:
                # Partial points for 30-90 days
                points = int(HealthScoreCalculator.WEIGHTS["recently_updated"] * (1 - (days_since_update - 30) / 60))
                breakdown["recently_updated"] = {
                    "points": points,
                    "max": HealthScoreCalculator.WEIGHTS["recently_updated"],
                    "reason": f"Updated {days_since_update} days ago (stale)",
                    "status": "warning"
                }
                total_score += points
                recommendations.append("Update lead information")
            else:
                breakdown["recently_updated"] = {
                    "points": 0,
                    "max": HealthScoreCalculator.WEIGHTS["recently_updated"],
                    "reason": f"Not updated in {days_since_update} days",
                    "status": "missing"
                }
                recommendations.append("Update lead information")
        else:
            breakdown["recently_updated"] = {
                "points": 0,
                "max": HealthScoreCalculator.WEIGHTS["recently_updated"],
                "reason": "Never updated",
                "status": "missing"
            }
        
        # 7. No bounce flags (10 points)
        # Check if lead has any bounce/spam flags
        has_bounce_flags = False
        if hasattr(lead, "email_records") and lead.email_records:
            for email_record in lead.email_records:
                if hasattr(email_record, "verification_status"):
                    if email_record.verification_status in ["invalid", "bounced"]:
                        has_bounce_flags = True
                        break
        
        if not has_bounce_flags:
            breakdown["no_bounce_flags"] = {
                "points": HealthScoreCalculator.WEIGHTS["no_bounce_flags"],
                "max": HealthScoreCalculator.WEIGHTS["no_bounce_flags"],
                "reason": "No bounce or spam flags",
                "status": "good"
            }
            total_score += HealthScoreCalculator.WEIGHTS["no_bounce_flags"]
        else:
            breakdown["no_bounce_flags"] = {
                "points": 0,
                "max": HealthScoreCalculator.WEIGHTS["no_bounce_flags"],
                "reason": "Has bounce or invalid email flags",
                "status": "warning"
            }
            recommendations.append("Fix invalid email addresses")
        
        # Calculate grade
        if total_score >= 90:
            grade = "A"
        elif total_score >= 75:
            grade = "B"
        elif total_score >= 60:
            grade = "C"
        elif total_score >= 40:
            grade = "D"
        else:
            grade = "F"
        
        return {
            "score": round(total_score, 1),
            "max_score": 100,
            "breakdown": breakdown,
            "grade": grade,
            "recommendations": recommendations,
        }
    
    @staticmethod
    def calculate_batch(leads: list[LeadORM], db: Session) -> Dict[int, Dict]:
        """Calculate health scores for multiple leads"""
        results = {}
        for lead in leads:
            # Get email verification status if available
            email_status = None
            if hasattr(lead, "email_records") and lead.email_records:
                # Get most recent verification status
                for email_record in sorted(lead.email_records, key=lambda x: x.created_at if hasattr(x, "created_at") else datetime.min, reverse=True):
                    if hasattr(email_record, "verification_status"):
                        email_status = email_record.verification_status
                        break
            
            results[lead.id] = HealthScoreCalculator.calculate(lead, email_status)
        
        return results

