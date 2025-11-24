"""Social Content Intelligence Service - Analyze social posts for insights"""
import logging
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from collections import Counter
import re

from app.core.orm_v2 import (
    SocialPostORM, SocialInsightORM, EntityORM, EntityType
)
from app.services.contrastive_embeddings import ContrastiveEmbeddingService

logger = logging.getLogger(__name__)


class SocialIntelligenceService:
    """Service for analyzing social media content"""
    
    def __init__(self):
        self.embedding_service = ContrastiveEmbeddingService()
    
    def ingest_post(
        self,
        db: Session,
        organization_id: int,
        entity_id: int,
        platform: str,
        post_id: str,
        text: str,
        created_at: datetime,
        metrics: Dict[str, Any],
        url: Optional[str] = None
    ) -> SocialPostORM:
        """Ingest a social media post"""
        # Check if post already exists
        existing = db.query(SocialPostORM).filter(
            SocialPostORM.organization_id == organization_id,
            SocialPostORM.platform == platform,
            SocialPostORM.post_id == post_id
        ).first()
        
        if existing:
            return existing
        
        # Analyze post
        topics = self._extract_topics(text)
        sentiment = self._classify_sentiment(text)
        embedding = self.embedding_service.generate_embedding(text)
        
        post = SocialPostORM(
            organization_id=organization_id,
            entity_id=entity_id,
            platform=platform,
            post_id=post_id,
            url=url,
            text=text,
            created_at_post=created_at,
            metrics=metrics,
            topics=topics,
            sentiment=sentiment,
            embedding=embedding
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        
        return post
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract topics from post text (simple keyword-based for now)"""
        # Common business topics
        topic_keywords = {
            "digital_marketing": ["marketing", "digital", "seo", "advertising", "campaign"],
            "patient_experience": ["patient", "care", "experience", "satisfaction"],
            "hiring": ["hiring", "job", "career", "team", "recruiting"],
            "software": ["software", "technology", "digital", "automation", "system"],
            "operations": ["operations", "efficiency", "process", "workflow"],
            "growth": ["growth", "expansion", "scaling", "revenue"],
        }
        
        text_lower = text.lower()
        found_topics = []
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                found_topics.append(topic)
        
        return found_topics[:5]  # Limit to 5 topics
    
    def _classify_sentiment(self, text: str) -> str:
        """Classify sentiment (simple rule-based for now)"""
        positive_words = ["great", "excellent", "amazing", "love", "happy", "success", "win"]
        negative_words = ["bad", "terrible", "disappointed", "fail", "problem", "issue", "challenge"]
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            return "positive"
        elif neg_count > pos_count:
            return "negative"
        else:
            return "neutral"
    
    def generate_insights(
        self,
        db: Session,
        entity_id: int,
        organization_id: int,
        days: int = 90
    ) -> SocialInsightORM:
        """Generate aggregated insights for an entity"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all posts
        posts = db.query(SocialPostORM).filter(
            SocialPostORM.organization_id == organization_id,
            SocialPostORM.entity_id == entity_id,
            SocialPostORM.created_at_post >= cutoff_date
        ).all()
        
        if not posts:
            # Return empty insight
            insight = SocialInsightORM(
                organization_id=organization_id,
                entity_id=entity_id,
                posts_per_month=0.0,
                avg_engagement=0.0,
                topic_distribution={},
                sentiment_distribution={}
            )
            db.add(insight)
            db.commit()
            return insight
        
        # Calculate metrics
        days_span = max(1, (datetime.utcnow() - cutoff_date).days)
        posts_per_month = (len(posts) / days_span) * 30
        
        # Average engagement
        total_engagement = 0
        for post in posts:
            metrics = post.metrics or {}
            engagement = (
                metrics.get("likes", 0) +
                metrics.get("comments", 0) +
                metrics.get("shares", 0)
            )
            total_engagement += engagement
        
        avg_engagement = total_engagement / len(posts) if posts else 0.0
        
        # Topic distribution
        all_topics = []
        for post in posts:
            if post.topics:
                all_topics.extend(post.topics)
        topic_counter = Counter(all_topics)
        topic_distribution = dict(topic_counter)
        dominant_topics = [topic for topic, _ in topic_counter.most_common(5)]
        
        # Sentiment distribution
        sentiments = [post.sentiment for post in posts if post.sentiment]
        sentiment_counter = Counter(sentiments)
        total_sentiments = len(sentiments) or 1
        sentiment_distribution = {
            sentiment: count / total_sentiments
            for sentiment, count in sentiment_counter.items()
        }
        
        # Classify growth stage and dominant pain
        growth_stage = self._classify_growth_stage(posts, topic_distribution)
        dominant_pain = self._classify_dominant_pain(topic_distribution)
        
        # Generate summary using LLM (optional)
        summary = self._generate_summary(posts, topic_distribution, sentiment_distribution)
        
        # Update or create insight
        insight = db.query(SocialInsightORM).filter(
            SocialInsightORM.organization_id == organization_id,
            SocialInsightORM.entity_id == entity_id
        ).first()
        
        if insight:
            insight.posts_per_month = posts_per_month
            insight.avg_engagement = avg_engagement
            insight.topic_distribution = topic_distribution
            insight.dominant_topics = dominant_topics
            insight.sentiment_distribution = sentiment_distribution
            insight.growth_stage = growth_stage
            insight.dominant_pain = dominant_pain
            insight.summary = summary
            insight.updated_at = datetime.utcnow()
        else:
            insight = SocialInsightORM(
                organization_id=organization_id,
                entity_id=entity_id,
                posts_per_month=posts_per_month,
                avg_engagement=avg_engagement,
                topic_distribution=topic_distribution,
                dominant_topics=dominant_topics,
                sentiment_distribution=sentiment_distribution,
                growth_stage=growth_stage,
                dominant_pain=dominant_pain,
                summary=summary
            )
            db.add(insight)
        
        db.commit()
        db.refresh(insight)
        return insight
    
    def _classify_growth_stage(
        self,
        posts: List[SocialPostORM],
        topic_distribution: Dict[str, int]
    ) -> str:
        """Classify growth stage based on content"""
        if not posts:
            return "unknown"
        
        # Simple heuristics
        growth_keywords = topic_distribution.get("growth", 0)
        hiring_keywords = topic_distribution.get("hiring", 0)
        
        if growth_keywords > 3 or hiring_keywords > 2:
            return "scaling"
        elif len(posts) < 5:
            return "early"
        else:
            return "mature"
    
    def _classify_dominant_pain(self, topic_distribution: Dict[str, int]) -> Optional[str]:
        """Classify dominant pain point"""
        if not topic_distribution:
            return None
        
        # Map topics to pain points
        pain_map = {
            "hiring": "hiring",
            "digital_marketing": "lead_gen",
            "operations": "ops",
            "software": "software",
            "patient_experience": "reputation",
        }
        
        # Find most common topic
        if topic_distribution:
            top_topic = max(topic_distribution.items(), key=lambda x: x[1])[0]
            return pain_map.get(top_topic, "unknown")
        
        return None
    
    def _generate_summary(
        self,
        posts: List[SocialPostORM],
        topic_distribution: Dict[str, int],
        sentiment_distribution: Dict[str, float]
    ) -> str:
        """Generate human-readable summary"""
        if not posts:
            return "No recent social media activity."
        
        dominant_topics = [topic for topic, _ in sorted(topic_distribution.items(), key=lambda x: x[1], reverse=True)[:3]]
        dominant_sentiment = max(sentiment_distribution.items(), key=lambda x: x[1])[0] if sentiment_distribution else "neutral"
        
        summary_parts = [
            f"Posted {len(posts)} times in the last 90 days.",
            f"Mostly posting about: {', '.join(dominant_topics) if dominant_topics else 'various topics'}.",
            f"Overall sentiment: {dominant_sentiment}.",
        ]
        
        return " ".join(summary_parts)

