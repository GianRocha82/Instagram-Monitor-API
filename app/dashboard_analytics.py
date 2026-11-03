"""
Dashboard Analytics Module - Computes metrics and prepares data for visualization
"""
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from datetime import datetime, timezone, timedelta
import json

from app.models import ProfileData, PostData, DashboardData, BR_TZ
from app.scraper import compute_compatibility, generate_insights

def calculate_engagement_rate(posts: List[PostData], followers: int) -> float:
    """Calcula taxa de engajamento: (likes + comments + shares + saves) / followers * 100"""
    if followers == 0:
        return 0.0
    
    total_interactions = sum(
        p.likes + p.comments + p.shares + p.saves 
        for p in posts
    )
    
    # Taxa média por post
    avg_interactions = total_interactions / len(posts) if posts else 0
    rate = (avg_interactions / followers) * 100
    return round(rate, 2)

def get_top_categories(posts: List[PostData], top_n: int = 5) -> List[Dict[str, Any]]:
    """Retorna top N categorias por total de interações."""
    cat_interactions = Counter()
    
    for post in posts:
        interactions = post.likes + post.comments + post.shares + post.saves
        cat_interactions[post.category] += interactions
    
    top = cat_interactions.most_common(top_n)
    return [
        {"category": cat, "interactions": count, "percentage": 0}  # percentage calculated later
        for cat, count in top
    ]

def get_timeline_data(posts: List[PostData]) -> List[Dict[str, Any]]:
    """Agrupa interações por mês/trimestre/ano para gráfico de linhas."""
    monthly = Counter()
    quarterly = Counter()
    yearly = Counter()
    
    for post in posts:
        try:
            dt = datetime.strptime(post.date_br, '%Y-%m-%d %H:%M:%S')
            month_key = dt.strftime('%Y-%m')
            quarter_key = f"{dt.year}-Q{(dt.month - 1) // 3 + 1}"
            year_key = str(dt.year)
            
            interactions = post.likes + post.comments + post.shares + post.saves
            monthly[month_key] += interactions
            quarterly[quarter_key] += interactions
            yearly[year_key] += interactions
        except:
            continue
    
    # Converter para formato de série temporal
    def format_series(counter: Counter, label: str) -> List[Dict[str, Any]]:
        return [
            {"period": k, "interactions": v, "granularity": label}
            for k, v in sorted(counter.items())
        ]
    
    return {
        "monthly": format_series(monthly, "month"),
        "quarterly": format_series(quarterly, "quarter"),
        "yearly": format_series(yearly, "year")
    }

def get_top_hashtags(posts: List[PostData], top_n: int = 20) -> List[Dict[str, Any]]:
    """Retorna top hashtags por frequência de uso."""
    hashtag_counter = Counter()
    hashtag_interactions = Counter()
    
    for post in posts:
        interactions = post.likes + post.comments + post.shares + post.saves
        for tag in post.hashtags:
            tag_lower = tag.lower()
            hashtag_counter[tag_lower] += 1
            hashtag_interactions[tag_lower] += interactions
    
    top_tags = hashtag_counter.most_common(top_n)
    return [
        {
            "hashtag": tag, 
            "count": count, 
            "total_interactions": hashtag_interactions[tag]
        }
        for tag, count in top_tags
    ]

def get_hashtag_timeline(posts: List[PostData], top_hashtags: List[str]) -> List[Dict[str, Any]]:
    """Retorna evolução das top hashtags ao longo do tempo (para gráfico de faixas)."""
    # Pegar top 10 hashtags
    top_tags = [h["hashtag"] for h in top_hashtags[:10]]
    
    monthly_hashtags = {tag: Counter() for tag in top_tags}
    
    for post in posts:
        try:
            dt = datetime.strptime(post.date_br, '%Y-%m-%d %H:%M:%S')
            month_key = dt.strftime('%Y-%m')
            interactions = post.likes + post.comments + post.shares + post.saves
            
            for tag in post.hashtags:
                tag_lower = tag.lower()
                if tag_lower in top_tags:
                    monthly_hashtags[tag_lower][month_key] += interactions
        except:
            continue
    
    # Formatar para stacked area chart
    result = []
    for tag in top_tags:
        series = monthly_hashtags[tag]
        for period, value in sorted(series.items()):
            result.append({
                "hashtag": tag,
                "period": period,
                "interactions": value
            })
    
    return result

def prepare_dashboard_data(
    company_profile: ProfileData,
    company_posts: List[PostData],
    target_profile: ProfileData,
    target_posts: List[PostData]
) -> DashboardData:
    """Prepara todos os dados necessários para o dashboard."""
    
    # 1. Taxa de engajamento
    engagement_rate = calculate_engagement_rate(target_posts, target_profile.followers)
    
    # 2. Top categorias
    top_categories = get_top_categories(target_posts, 5)
    total_cat_interactions = sum(c["interactions"] for c in top_categories)
    for cat in top_categories:
        cat["percentage"] = round((cat["interactions"] / total_cat_interactions * 100) if total_cat_interactions > 0 else 0, 1)
    
    # 3. Timeline
    timeline = get_timeline_data(target_posts)
    
    # 4. Compatibilidade
    compatibility = compute_compatibility(company_posts, target_posts)
    
    # 5. Top hashtags
    top_hashtags = get_top_hashtags(target_posts, 20)
    
    # 6. Hashtag timeline
    hashtag_timeline = get_hashtag_timeline(target_posts, top_hashtags)
    
    # 7. Insights
    total_interactions = sum(p.likes + p.comments + p.shares + p.saves for p in target_posts)
    insights = generate_insights(compatibility, engagement_rate, top_categories, total_interactions)
    
    return DashboardData(
        profile=target_profile,
        engagement_rate=engagement_rate,
        top_categories=top_categories,
        timeline_data=timeline,
        compatibility_score=compatibility,
        top_hashtags=top_hashtags,
        hashtag_timeline=hashtag_timeline,
        insights=insights
    )

def filter_dashboard_data(
    dashboard_data: DashboardData, 
    profile_filter: Optional[str] = None,
    months_filter: Optional[int] = None
) -> DashboardData:
    """Aplica filtros aos dados do dashboard."""
    # This would require re-filtering the original posts
    # For now, return as-is - filtering happens at scrape time
    return dashboard_data