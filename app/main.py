"""
Main FastAPI Application - Instagram Monitor API
"""
import os
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Form
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import HttpUrl

from app.models import (
    ProfileInput, ProfileData, PostData, DashboardData, JobStatus,
    TimeRange, CollectionMode, MonitoringMode, INSTAGRAM_COLORS, BR_TZ
)
from app.scraper import (
    extract_username_from_url, setup_instaloader, scrape_profile,
    filter_posts_by_date, scrape_profile_first_posts
)
from app.excel_generator import save_to_excel, load_from_excel, generate_filename
from app.dashboard_analytics import prepare_dashboard_data

# Job storage (in-memory for simplicity, use Redis in production)
jobs: Dict[str, JobStatus] = {}

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
FRONTEND_DIR = BASE_DIR / "frontend"
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Instagram Monitor API iniciada")
    print(f"📁 Diretório de dados: {DATA_DIR}")
    yield
    # Shutdown
    print("👋 Instagram Monitor API finalizada")

app = FastAPI(
    title="Instagram Monitor API",
    description="API para monitoramento de engajamento de perfis estratégicos no Instagram",
    version="1.0.0",
    lifespan=lifespan
)

# Static files and templates
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
templates = Jinja2Templates(directory=str(FRONTEND_DIR))

def update_job(job_id: str, status: str, progress: int, message: str, 
               result: Optional[Dict] = None, error: Optional[str] = None):
    """Atualiza status do job."""
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status=status,
        progress=progress,
        message=message,
        result=result,
        error=error
    )

async def run_monitoring_job(job_id: str, input_data: ProfileInput):
    """Executa o job de monitoramento em background."""
    try:
        update_job(job_id, "running", 5, "Iniciando coleta de dados...")
        
        # Setup Instaloader
        loader = setup_instaloader(
            username=input_data.instagram_username if input_data.collection_mode == CollectionMode.PRIVATE_PROFILE else None,
            password=input_data.instagram_password if input_data.collection_mode == CollectionMode.PRIVATE_PROFILE else None
        )
        
        # 1. Raspar perfil da empresa (primeiros 25 posts para base temática - SEM filtro de data)
        update_job(job_id, "running", 10, "Coletando dados da empresa contratante...")
        company_username = extract_username_from_url(str(input_data.company_url))
        if not company_username:
            raise ValueError("URL da empresa inválida")
        
        company_profile, company_posts = scrape_profile_first_posts(
            loader, company_username, max_posts=25
        )
        update_job(job_id, "running", 25, f"Empresa @{company_username}: {len(company_posts)} posts coletados (base temática)")
        
        # 2. Raspar perfis estratégicos
        all_target_profiles = []
        all_target_posts = []
        
        for i, profile_url in enumerate(input_data.profiles):
            username = extract_username_from_url(str(profile_url))
            if not username:
                continue
            
            progress = 25 + int((i / len(input_data.profiles)) * 60)
            update_job(job_id, "running", progress, f"Coletando @{username}...")
            
            profile, posts = scrape_profile(
                loader, username, max_posts=100, time_range=input_data.time_range
            )
            all_target_profiles.append(profile)
            all_target_posts.append((profile, posts))
            
            update_job(job_id, "running", progress + 5, f"@{username}: {len(posts)} posts coletados")
        
        # 3. Gerar arquivos Excel e dashboards
        update_job(job_id, "running", 85, "Gerando relatórios e dashboards...")
        
        output_path = Path(input_data.output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = []
        for profile, posts in all_target_posts:
            # Salvar Excel
            excel_file = save_to_excel(
                profile, posts, output_path, 
                input_data.time_range.value, company_profile
            )
            
            # Preparar dashboard
            dashboard = prepare_dashboard_data(
                company_profile, company_posts, profile, posts
            )
            
            results.append({
                "profile": profile.username,
                "excel_file": str(excel_file),
                "dashboard": dashboard.model_dump()
            })
        
        # 4. Se monitoramento semanal, agendar (simulado - em produção usaria cron/APScheduler)
        if input_data.monitoring_mode == MonitoringMode.WEEKLY_30_DAYS:
            update_job(job_id, "running", 95, "Configurando monitoramento semanal por 30 dias...")
            # TODO: Implementar agendamento real com APScheduler
        
        update_job(job_id, "completed", 100, "Monitoramento concluído com sucesso!", {
            "company": company_profile.username,
            "profiles_monitored": len(results),
            "results": results
        })
        
    except Exception as e:
        update_job(job_id, "failed", 0, f"Erro: {str(e)}", error=str(e))
        print(f"Job {job_id} falhou: {e}")

# ==================== API ENDPOINTS ====================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Página principal - Interface de input."""
    # Read the HTML file directly and inject the template variables
    html_path = FRONTEND_DIR / "index.html"
    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Simple template variable replacement
    time_ranges_html = "".join([
        f'<option value="{tr.value}" {"selected" if tr.value == "30" else ""}>Últimos {tr.value} dias</option>'
        for tr in TimeRange
    ])
    
    html_content = html_content.replace(
        '{% for tr in time_ranges %}\n                        <label class="mode-card" data-value="{{ tr.value }}">\n                            <input type="radio" name="time_range" value="{{ tr.value }}" {% if tr.value == "30" %}checked{% endif %}>\n                            <div class="font-semibold text-lg">{{ tr.label }}</div>\n                            <div class="text-sm text-gray-400 mt-1">Período de análise</div>\n                        </label>\n                        {% endfor %}',
        time_ranges_html
    )
    
    # Replace DATA_DIR
    html_content = html_content.replace('{{ DATA_DIR }}', str(DATA_DIR).replace('\\', '\\\\'))
    
    return HTMLResponse(content=html_content)

@app.post("/api/start-monitoring")
async def start_monitoring(background_tasks: BackgroundTasks, input_data: ProfileInput):
    """Inicia job de monitoramento."""
    job_id = str(uuid.uuid4())[:8]
    
    # Validar caminho de saída
    output_path = Path(input_data.output_path)
    if not output_path.exists():
        try:
            output_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise HTTPException(400, f"Caminho de saída inválido: {e}")
    
    # Criar job
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        message="Job criado, iniciando..."
    )
    
    # Executar em background
    background_tasks.add_task(run_monitoring_job, job_id, input_data)
    
    return {"job_id": job_id, "status": "started"}

@app.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    """Consulta status do job."""
    if job_id not in jobs:
        raise HTTPException(404, "Job não encontrado")
    return jobs[job_id]

@app.get("/api/dashboard/{profile_name}")
async def get_dashboard(profile_name: str, time_range: str = "30"):
    """Retorna dados do dashboard para um perfil."""
    # Buscar arquivo Excel mais recente do perfil
    pattern = f"{profile_name}_{time_range}dias_*.xlsx"
    files = list(DATA_DIR.glob(pattern))
    
    if not files:
        # Tentar no output_path personalizado se fornecido
        raise HTTPException(404, f"Dados não encontrados para @{profile_name}")
    
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    data = load_from_excel(latest_file)
    
    if not data["postagens"]:
        raise HTTPException(404, "Nenhum dado de postagens encontrado")
    
    # Reconstruir objetos para analytics
    posts = [PostData(**p) for p in data["postagens"]]
    profile = ProfileData(**data["metadados"]) if data["metadados"] else None
    
    # Se não tem perfil completo, criar básico
    if not profile:
        profile = ProfileData(
            username=profile_name,
            user_id=posts[0].get("id_perfil", 0) if posts else 0,
            full_name="",
            biography="",
            followers=0,
            followees=0,
            mediacount=len(posts),
            profile_pic_url="",
            is_verified=False,
            is_private=False
        )
    
    # Calcular métricas básicas
    from app.dashboard_analytics import (
        calculate_engagement_rate, get_top_categories, get_timeline_data,
        get_top_hashtags, get_hashtag_timeline
    )
    
    engagement_rate = calculate_engagement_rate(posts, profile.followers)
    top_categories = get_top_categories(posts)
    timeline = get_timeline_data(posts)
    top_hashtags = get_top_hashtags(posts)
    hashtag_timeline = get_hashtag_timeline(posts, top_hashtags)
    
    return {
        "profile": profile.model_dump(),
        "engagement_rate": engagement_rate,
        "top_categories": top_categories,
        "timeline": timeline,
        "top_hashtags": top_hashtags,
        "hashtag_timeline": hashtag_timeline,
        "posts_count": len(posts),
        "file": str(latest_file)
    }

@app.get("/api/download/{profile_name}")
async def download_excel(profile_name: str, time_range: str = "30"):
    """Download do arquivo Excel."""
    pattern = f"{profile_name}_{time_range}dias_*.xlsx"
    files = list(DATA_DIR.glob(pattern))
    
    if not files:
        raise HTTPException(404, "Arquivo não encontrado")
    
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    return FileResponse(
        latest_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=latest_file.name
    )

@app.get("/api/list-profiles")
async def list_profiles():
    """Lista perfis monitorados disponíveis."""
    files = list(DATA_DIR.glob("*.xlsx"))
    profiles = {}
    
    for f in files:
        # Parse filename: {profile}_{timerange}_{date}.xlsx
        name = f.stem
        parts = name.split("_")
        if len(parts) >= 2:
            profile_name = parts[0]
            time_range = parts[1] if len(parts) > 1 else "unknown"
            if profile_name not in profiles:
                profiles[profile_name] = []
            profiles[profile_name].append({
                "time_range": time_range,
                "file": f.name,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            })
    
    return {"profiles": profiles}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(BR_TZ).isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)