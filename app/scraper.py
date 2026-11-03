"""
Instagram Scraper Module - Extends monitor_instagram_universal.py functionality
"""
import instaloader
import re
import os
import csv
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

from app.models import BR_TZ, ProfileData, PostData, TimeRange

# Categories from universal script
CATEGORIES = {
    "notícias": [
        "notícia", "noticias", "jornal", "reportagem", "breaking", "urgente",
        "política", "governo", "prefeito", "vereador", "deputado", "senador",
        "eleição", "votação", "projeto de lei", "decreto", "medida provisória",
        "oficial", "comunicado", "nota oficial", "ascom", "assessoria"
    ],
    "esportes": [
        "futebol", "campeonato", "copa", "liga", "time", "seleção", "jogo",
        "partida", "gol", "vitória", "derrota", "empate", "classificação",
        "artilheiro", "goleiro", "zagueiro", "meia", "atacante", "técnico",
        "treino", "estádio", "arena", "intermunicipal", "amador", "profissional",
        "basquete", "vôlei", "handebol", "atletismo", "natação", "esporte",
        "torcida", "torcedor", "arquibancada", "camisa", "uniforme"
    ],
    "curiosidades": [
        "curiosidade", "curioso", "interessante", "sabia", "você sabia",
        "fato", "dado", "estranho", "bizarro", "incrível", "surpreendente",
        "história", "lenda", "mito", "falso", "verdade", "mistério",
        "ciência", "tecnologia", "inovação", "descoberta", "pesquisa"
    ],
    "festas": [
        "festa", "festas", "evento", "show", "concerto", "festival",
        "carnaval", "são joão", "são pedro", "natal", "réveillon", "ano novo",
        "formatura", "casamento", "aniversário", "baile", "micareta",
        "arraiá", "quadrilha", "forró", "piseiro", "vaquejada", "rodeio",
        "expo", "exposição", "feira", "festança", "comemoração"
    ],
    "cultura": [
        "cultura", "cultural", "arte", "artista", "museu", "teatro", "cinema",
        "livro", "leitura", "poesia", "música", "músico", "banda", "cantor",
        "dança", "bailarino", "coreografia", "patrimônio", "histórico",
        "tradição", "folclore", "artesanato", "pintura", "escultura",
        "exposição", "vernissage", "galeria", "biblioteca", "academia"
    ],
    "religião": [
        "igreja", "missa", "culto", "deus", "jesus", "cristo", "bíblia",
        "oração", "fé", "crente", "evangélico", "católico", "espírito",
        "santo", "santa", "padre", "pastor", "bispo", "paróquia",
        "comunidade", "grupo de oração", "louvor", "adoração", "benção"
    ],
    "educação": [
        "escola", "colégio", "universidade", "faculdade", "curso", "aula",
        "professor", "aluno", "estudante", "educação", "ensino", "aprendizado",
        "formatura", "diploma", "certificado", "vestibular", "enem",
        "bolsa", "prouni", "fies", "pró-reitoria", "reitoria", "campus"
    ],
    "saúde": [
        "saúde", "hospital", "clínica", "médico", "enfermeiro", "paciente",
        "tratamento", "doença", "vacina", "vacinação", "campanha", "prevenção",
        "exame", "consulta", "cirurgia", "emergência", "samu", "ups",
        "psf", "acs", "agente de saúde", "vigilância", "epidemiologia"
    ],
    "economia": [
        "economia", "emprego", "trabalho", "vaga", "contratação", "empresa",
        "comércio", "indústria", "agronegócio", "produtor", "feira livre",
        "mercado", "preço", "inflação", "investimento", "crédito", "financiamento",
        "banco", "caixa", "bradesco", "itau", "santander", "banco do brasil"
    ],
    "turismo": [
        "turismo", "viagem", "passeio", "destino", "hotel", "pousada",
        "praia", "serra", "cachoeira", "trilha", "parque", "mirante",
        "roteiro", "guia", "hospedagem", "gastronomia", "restaurante",
        "prato típico", "culinária", "artesão", "souvenir", "artesanato"
    ],
    "meio ambiente": [
        "meio ambiente", "natureza", "floresta", "mata", "rio", "lago",
        "represa", "nascentes", "preservação", "conservação", "sustentabilidade",
        "reciclagem", "lixo", "poluição", "queimada", "desmatamento",
        "biodiversidade", "fauna", "flora", "espécie", "ameaçada"
    ],
    "segurança": [
        "polícia", "bombeiro", "guarda", "segurança", "crime", "roubo",
        "furto", "assalto", "homicídio", "tráfico", "droga", "prisão",
        "flagrante", "inquérito", "delegacia", "ministério público",
        "justiça", "tribunal", "fórum", "advogado", "defensor"
    ],
    "infraestrutura": [
        "obra", "construção", "reforma", "asfalto", "pavimentação", "rua",
        "avenida", "ponte", "viaduto", "túnel", "saneamento", "esgoto",
        "água", "energia", "iluminação", "poste", "rede", "internet",
        "transporte", "ônibus", "metrô", "trem", "ciclovia", "calçada"
    ]
}

def extract_username_from_url(url: str) -> Optional[str]:
    """Extrai o username de uma URL do Instagram."""
    patterns = [
        r'instagram\.com/([^/?#]+)',
        r'^([a-zA-Z0-9._]+)$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url.strip())
        if match:
            username = match.group(1).rstrip('/')
            return username
    return None

def setup_instaloader(username: Optional[str] = None, password: Optional[str] = None, session_file: Optional[str] = None):
    """Configura o objeto Instaloader com login opcional."""
    loader = instaloader.Instaloader(
        quiet=True,
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
    )
    
    if session_file and Path(session_file).exists():
        loader.load_session_from_file(username, session_file)
    elif username and password:
        loader.login(username, password)
        # Save session for future use
        session_dir = Path.home() / ".instaloader_sessions"
        session_dir.mkdir(exist_ok=True)
        loader.save_session_to_file(session_dir / f"{username}.session")
    
    return loader

def extract_hashtags(text: str) -> List[str]:
    """Extrai hashtags de um texto, normalizando para minúsculas."""
    if not text:
        return []
    hashtag_pattern = re.compile(r'#[\w\u00C0-\u024F]+', re.UNICODE)
    tags = hashtag_pattern.findall(str(text))
    return [tag.lower() for tag in tags]

def classify_content(subtitles: str, hashtags: List[str]) -> str:
    """Classifica o conteúdo baseado em legendas e hashtags."""
    text = (subtitles or "").lower()
    tag_text = " ".join(hashtags).lower()
    combined = f"{text} {tag_text}"
    
    scores = {}
    for category, keywords in CATEGORIES.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            scores[category] = score
    
    if not scores:
        return "outros"
    
    return max(scores, key=scores.get)

def convert_to_br_time(date_utc: datetime) -> str:
    """Converte datetime UTC para fuso horário de Brasília."""
    if date_utc is None:
        return datetime.now(BR_TZ).strftime('%Y-%m-%d %H:%M:%S')
    if date_utc.tzinfo is None:
        date_utc = date_utc.replace(tzinfo=timezone.utc)
    br_time = date_utc.astimezone(BR_TZ)
    return br_time.strftime('%Y-%m-%d %H:%M:%S')

def get_post_type(is_video: bool, typename: str) -> str:
    if typename == "GraphSidecar":
        return "carousel"
    return "video" if is_video else "image"

def get_post_data(post) -> PostData:
    """Extrai os dados relevantes de um post do Instagram."""
    date_br = convert_to_br_time(post.date_utc)
    post_type = get_post_type(post.is_video, post.typename)
    
    caption = post.caption if post.caption else ""
    hashtags_list = extract_hashtags(caption)
    category = classify_content(caption, hashtags_list)
    
    likes = post.likes if post.likes else 0
    comments = post.comments if post.comments else 0
    views = post.video_view_count if post.is_video and post.video_view_count else 0
    shares = 0  # Not available via public API
    saves = 0   # Not available via public API
    
    return PostData(
        shortcode=post.shortcode,
        post_id=post.mediaid,
        date_utc=post.date_utc,
        date_br=date_br,
        is_video=post.is_video,
        typename=post.typename,
        post_type=post_type,
        caption=caption,
        likes=likes,
        comments=comments,
        views=views,
        shares=shares,
        saves=saves,
        hashtags=hashtags_list,
        category=category,
        url=f"https://www.instagram.com/p/{post.shortcode}/"
    )

def get_profile_data(profile) -> ProfileData:
    """Extrai dados do perfil."""
    return ProfileData(
        username=profile.username,
        user_id=profile.userid,
        full_name=profile.full_name or "",
        biography=profile.biography or "",
        followers=profile.followers if profile.followers else 0,
        followees=profile.followees if profile.followees else 0,
        mediacount=profile.mediacount if profile.mediacount else 0,
        profile_pic_url=profile.profile_pic_url or "",
        is_verified=profile.is_verified,
        is_private=profile.is_private
    )

def filter_posts_by_date(posts: List[PostData], time_range: TimeRange) -> List[PostData]:
    """Filtra posts pelo intervalo de tempo selecionado."""
    now = datetime.now(timezone.utc)
    days_map = {
        TimeRange.DAYS_30: 30,
        TimeRange.DAYS_90: 90,
        TimeRange.DAYS_180: 180,
    }
    days = days_map.get(time_range, 30)
    cutoff = now - timedelta(days=days)

    filtered = []
    for post in posts:
        post_date = post.date_utc
        # Ensure both datetimes are timezone-aware for comparison
        if post_date.tzinfo is None:
            post_date = post_date.replace(tzinfo=timezone.utc)
        if post_date >= cutoff:
            filtered.append(post)
    return filtered

def scrape_profile(loader: instaloader.Instaloader, username: str, max_posts: int = 100, 
                   time_range: TimeRange = TimeRange.DAYS_30, 
                   progress_callback=None) -> Tuple[ProfileData, List[PostData]]:
    """Raspa um perfil do Instagram filtrando por intervalo de tempo."""
    try:
        profile = instaloader.Profile.from_username(loader.context, username)
        profile_data = get_profile_data(profile)
        
        posts_data = []
        posts_processed = 0
        
        for post in profile.get_posts():
            if posts_processed >= max_posts:
                break
            
            post_data = get_post_data(post)
            posts_data.append(post_data)
            posts_processed += 1
            
            if progress_callback:
                progress_callback(posts_processed, max_posts, f"Coletando posts de @{username}")
        
        # Filtrar por data
        posts_data = filter_posts_by_date(posts_data, time_range)
        
        return profile_data, posts_data
        
    except instaloader.exceptions.ProfileNotExistsException:
        raise ValueError(f"Perfil @{username} não encontrado ou é privado.")
    except instaloader.exceptions.LoginRequiredException:
        raise ValueError("Login necessário. O perfil pode ser privado ou exigir autenticação.")
    except Exception as e:
        raise RuntimeError(f"Erro ao raspar @{username}: {str(e)}")


def scrape_profile_first_posts(loader: instaloader.Instaloader, username: str, max_posts: int = 25, 
                                progress_callback=None) -> Tuple[ProfileData, List[PostData]]:
    """Raspa os primeiros N posts de um perfil (sem filtro de data) - usado para base temática da empresa."""
    try:
        profile = instaloader.Profile.from_username(loader.context, username)
        profile_data = get_profile_data(profile)
        
        posts_data = []
        posts_processed = 0
        
        for post in profile.get_posts():
            if posts_processed >= max_posts:
                break
            
            post_data = get_post_data(post)
            posts_data.append(post_data)
            posts_processed += 1
            
            if progress_callback:
                progress_callback(posts_processed, max_posts, f"Coletando posts de @{username}")
        
        # NÃO filtra por data - pega os primeiros N posts mais recentes
        return profile_data, posts_data
        
    except instaloader.exceptions.ProfileNotExistsException:
        raise ValueError(f"Perfil @{username} não encontrado ou é privado.")
    except instaloader.exceptions.LoginRequiredException:
        raise ValueError("Login necessário. O perfil pode ser privado ou exigir autenticação.")
    except Exception as e:
        raise RuntimeError(f"Erro ao raspar @{username}: {str(e)}")

def compute_compatibility(company_posts: List[PostData], target_posts: List[PostData]) -> float:
    """Calcula o grau de compatibilidade entre perfis baseado em categorias e hashtags."""
    if not company_posts or not target_posts:
        return 0.0
    
    # Categorias da empresa
    company_cats = Counter(p.category for p in company_posts)
    target_cats = Counter(p.category for p in target_posts)
    
    # Similaridade de categorias (Jaccard ponderado)
    all_cats = set(company_cats.keys()) | set(target_cats.keys())
    cat_intersection = sum(min(company_cats.get(c, 0), target_cats.get(c, 0)) for c in all_cats)
    cat_union = sum(max(company_cats.get(c, 0), target_cats.get(c, 0)) for c in all_cats)
    cat_similarity = cat_intersection / cat_union if cat_union > 0 else 0
    
    # Hashtags da empresa
    company_tags = Counter()
    for p in company_posts:
        company_tags.update(p.hashtags)
    
    target_tags = Counter()
    for p in target_posts:
        target_tags.update(p.hashtags)
    
    # Similaridade de hashtags
    all_tags = set(company_tags.keys()) | set(target_tags.keys())
    tag_intersection = sum(min(company_tags.get(t, 0), target_tags.get(t, 0)) for t in all_tags)
    tag_union = sum(max(company_tags.get(t, 0), target_tags.get(t, 0)) for t in all_tags)
    tag_similarity = tag_intersection / tag_union if tag_union > 0 else 0
    
    # Peso: 60% categorias, 40% hashtags
    compatibility = (cat_similarity * 0.6 + tag_similarity * 0.4) * 100
    return round(compatibility, 1)

def generate_insights(compatibility: float, engagement_rate: float, 
                      top_categories: List[Dict], total_interactions: int) -> List[str]:
    """Gera insights baseados na análise."""
    insights = []
    
    if compatibility >= 70:
        insights.append(f"✅ Alta compatibilidade ({compatibility}%) — forte alinhamento temático com a empresa")
    elif compatibility >= 40:
        insights.append(f"⚠️ Compatibilidade moderada ({compatibility}%) — alinhamento parcial, avaliar nichos específicos")
    else:
        insights.append(f"❌ Baixa compatibilidade ({compatibility}%) — perfis com temáticas divergentes")
    
    if engagement_rate >= 5:
        insights.append(f"🔥 Excelente taxa de engajamento ({engagement_rate:.1f}%) — audiência muito ativa")
    elif engagement_rate >= 2:
        insights.append(f"👍 Boa taxa de engajamento ({engagement_rate:.1f}%) — audiência engajada")
    elif engagement_rate >= 1:
        insights.append(f"📊 Taxa de engajamento média ({engagement_rate:.1f}%) — dentro do esperado para o nicho")
    else:
        insights.append(f"📉 Baixa taxa de engajamento ({engagement_rate:.1f}%) — pode indicar audiência menos ativa")
    
    if top_categories:
        top_cat = top_categories[0]
        insights.append(f"🎯 Temática principal: {top_cat['category']} ({top_cat['interactions']} interações)")
    
    if total_interactions > 10000:
        insights.append("📈 Alto volume de interações — bom alcance potencial para campanhas")
    elif total_interactions > 1000:
        insights.append("📊 Volume moderado de interações — adequado para micro-influência")
    else:
        insights.append("📉 Baixo volume de interações — considerar perfis com maior alcance")
    
    # Verificar consistência temporal
    insights.append("💡 Recomendação: Avaliar histórico de parcerias e autenticidade do engajamento antes de fechar contrato")
    
    return insights