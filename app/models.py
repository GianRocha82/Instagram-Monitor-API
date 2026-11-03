"""
Instagram Monitor API - Core configuration and models
"""
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, HttpUrl, Field
from enum import Enum

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Brasilia timezone (UTC-3)
BR_TZ = timezone(timedelta(hours=-3))

# Instagram colors
INSTAGRAM_COLORS = {
    "primary": "#E1306C",
    "primary_dark": "#C13584",
    "primary_light": "#F77737",
    "gradient_start": "#F58529",
    "gradient_mid": "#DD2A7B",
    "gradient_end": "#8134AF",
    "bg_dark": "#1A1A1A",
    "bg_card": "#262626",
    "bg_hover": "#2E2E2E",
    "text_primary": "#FFFFFF",
    "text_secondary": "#A8A8A8",
    "text_muted": "#8E8E8E",
    "border": "#3A3A3A",
    "success": "#00BA7C",
    "warning": "#FFB300",
    "error": "#ED4956",
}

class TimeRange(str, Enum):
    DAYS_30 = "30"
    DAYS_90 = "90"
    DAYS_180 = "180"

class CollectionMode(str, Enum):
    PRIVATE_PROFILE = "private"
    PUBLIC_ONLY = "public"

class MonitoringMode(str, Enum):
    ONE_TIME = "once"
    WEEKLY_30_DAYS = "weekly"

class ProfileInput(BaseModel):
    """Input model for profile monitoring request"""
    company_url: HttpUrl = Field(..., description="URL do perfil da empresa contratante")
    profiles: List[HttpUrl] = Field(..., min_length=1, description="Lista de perfis a monitorar")
    time_range: TimeRange = Field(default=TimeRange.DAYS_30, description="Intervalo de dias para análise")
    collection_mode: CollectionMode = Field(default=CollectionMode.PUBLIC_ONLY, description="Modo de coleta")
    monitoring_mode: MonitoringMode = Field(default=MonitoringMode.ONE_TIME, description="Modo de monitoramento")
    output_path: str = Field(..., description="Caminho onde salvar o CSV")
    instagram_username: Optional[str] = Field(None, description="Username do Instagram (para modo privado)")
    instagram_password: Optional[str] = Field(None, description="Senha do Instagram (para modo privado)")

class ProfileData(BaseModel):
    """Instagram profile data"""
    username: str
    user_id: int
    full_name: str
    biography: str
    followers: int
    followees: int
    mediacount: int
    profile_pic_url: str
    is_verified: bool
    is_private: bool

class PostData(BaseModel):
    """Instagram post data"""
    shortcode: str
    post_id: int
    date_utc: datetime
    date_br: str
    is_video: bool
    typename: str
    post_type: str  # image, video, carousel
    caption: str
    likes: int
    comments: int
    views: int
    shares: int
    saves: int
    hashtags: List[str]
    category: str
    url: str

class DashboardData(BaseModel):
    """Data for dashboard visualization"""
    profile: ProfileData
    engagement_rate: float
    top_categories: List[Dict[str, Any]]
    timeline_data: Dict[str, List[Dict[str, Any]]]  # Changed from List to Dict
    compatibility_score: float
    top_hashtags: List[Dict[str, Any]]
    hashtag_timeline: List[Dict[str, Any]]
    insights: List[str]

class JobStatus(BaseModel):
    """Job tracking"""
    job_id: str
    status: str  # pending, running, completed, failed
    progress: int
    message: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None