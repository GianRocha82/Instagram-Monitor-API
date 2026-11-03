#!/usr/bin/env python3
"""Monitoramento contínuo de perfis públicos do Instagram usando Instaloader.
Aceita URL do perfil como input e realiza todo o processo automaticamente."""

import instaloader
import csv
import re
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Fuso horário de Brasília (UTC-3)
BR_TZ = timezone(timedelta(hours=-3))

# Categorias e palavras-chave para classificação
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

def extract_username_from_url(url):
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

def setup_instaloader():
    """Configura o objeto Instaloader."""
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
    return loader

def extract_hashtags(text):
    """Extrai hashtags de um texto, normalizando para minúsculas."""
    if not text:
        return []
    # Unicode-aware pattern: # followed by word characters including accented letters
    hashtag_pattern = re.compile(r'#[\w\u00C0-\u024F]+', re.UNICODE)
    tags = hashtag_pattern.findall(str(text))
    # Normalize to lowercase
    return [tag.lower() for tag in tags]

def classify_content(subtitles, hashtags):
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
    
    # Retorna a categoria com maior pontuação
    return max(scores, key=scores.get)

def convert_to_br_time(date_utc):
    """Converte datetime UTC para fuso horário de Brasília."""
    if date_utc is None:
        return datetime.now(BR_TZ).strftime('%Y-%m-%d %H:%M:%S')
    # Garante que o datetime tem timezone UTC
    if date_utc.tzinfo is None:
        date_utc = date_utc.replace(tzinfo=timezone.utc)
    br_time = date_utc.astimezone(BR_TZ)
    return br_time.strftime('%Y-%m-%d %H:%M:%S')

def get_post_data(post):
    """Extrai os dados relevantes de um post do Instagram."""
    # Data convertida para horário de Brasília
    date_br = convert_to_br_time(post.date_utc)
    
    # Tipo de post
    post_type = "video" if post.is_video else "image"
    if post.typename == "GraphSidecar":
        post_type = "carousel"
    
    # Autor
    user = post.owner_username
    
    # Legenda
    subtitles = post.caption if post.caption else ""
    
    # Descrição de acessibilidade
    image_description = post.accessibility_caption if post.accessibility_caption else ""
    
    # Métricas de engajamento
    likes = post.likes if post.likes else 0
    comments = post.comments if post.comments else 0
    views = post.video_view_count if post.is_video and post.video_view_count else 0
    
    # Shares e saves não estão disponíveis via API pública do Instagram
    # Retornamos 0 como placeholder
    shares = 0
    saves = 0
    
    # Ranking (timestamp UTC)
    rank = post.date_utc.timestamp() if post.date_utc else 0
    
    # Link do post
    link = f"https://www.instagram.com/{post.shortcode}/"
    
    # Hashtags
    hashtags_list = extract_hashtags(subtitles)
    
    # Classificação de categoria
    category = classify_content(subtitles, hashtags_list)
    
    data = {
        'date': date_br,
        'type': post_type,
        'user': user,
        'subtitles': subtitles,
        'image_description': image_description,
        'likes': likes,
        'comments': comments,
        'shares': shares,
        'saves': saves,
        'views': views,
        'rank': rank,
        'link': link,
        'category': category,
        '_hashtags_list': hashtags_list,  # Internal field for later processing
    }
    
    return data

# Global hashtag frequency tracker
_global_hashtag_freq = {}
_global_hashtag_ranking = []  # List of (hashtag_lower, count) sorted by frequency

def compute_global_hashtag_ranking(posts_data):
    """Computa o ranking global de hashtags por frequência (case-insensitive)."""
    global _global_hashtag_freq, _global_hashtag_ranking
    _global_hashtag_freq = {}
    for post_data in posts_data:
        hashtags = post_data.get('_hashtags_list', [])
        for tag in hashtags:
            tag_lower = tag.lower()
            _global_hashtag_freq[tag_lower] = _global_hashtag_freq.get(tag_lower, 0) + 1
    # Sort by frequency (descending), then alphabetically for ties
    _global_hashtag_ranking = sorted(_global_hashtag_freq.items(), key=lambda x: (-x[1], x[0]))

def apply_hashtag_columns(posts_data):
    """Aplica as colunas de hashtag baseadas no ranking global de frequência."""
    # Always recompute for the current dataset
    compute_global_hashtag_ranking(posts_data)
    
    for post_data in posts_data:
        # Create case-insensitive lookup set
        hashtags_in_post = set(post_data.get('_hashtags_list', []))
        hashtags_lower = {tag.lower() for tag in hashtags_in_post}
        
        for rank, (tag_lower, count) in enumerate(_global_hashtag_ranking, 1):
            # Output lowercase hashtag from ranking
            post_data[f'hashtag_{rank}'] = tag_lower if tag_lower in hashtags_lower else ''
        # Remove internal field
        post_data.pop('_hashtags_list', None)

def get_fieldnames(post_data_list=None):
    """Retorna os fieldnames dinâmicos baseados nos dados."""
    base_fields = [
        'date', 'type', 'user', 'subtitles', 'image_description',
        'likes', 'comments', 'shares', 'saves', 'views',
        'rank', 'link', 'category'
    ]
    if post_data_list:
        max_hashtags = 0
        for row in post_data_list:
            if row:
                hashtag_count = len([k for k in row.keys() if k and k.startswith('hashtag_')])
                max_hashtags = max(max_hashtags, hashtag_count)
    else:
        max_hashtags = len(_global_hashtag_ranking) if _global_hashtag_ranking else 10
    hashtag_fields = [f'hashtag_{i}' for i in range(1, max_hashtags + 1)]
    return base_fields + hashtag_fields

def initialize_csv(output_csv, post_data_list=None):
    """Inicializa o arquivo CSV com o cabeçalho."""
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=get_fieldnames(post_data_list))
        writer.writeheader()
    print(f"Arquivo CSV criado: {output_csv}")

def append_post_to_csv(output_csv, post_data, post_data_list=None):
    """Adiciona um post ao arquivo CSV."""
    with open(output_csv, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=get_fieldnames(post_data_list))
        writer.writerow(post_data)

def save_to_xlsx(output_csv, output_xlsx):
    """Converte o CSV para XLSX."""
    import openpyxl
    
    csv_data = []
    with open(output_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            csv_data.append(row)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Plan1"
    
    headers = get_fieldnames(csv_data)
    for col_idx, header in enumerate(headers, 1):
        ws.cell(row=1, column=col_idx, value=header)
    
    for row_idx, row in enumerate(csv_data, 2):
        for col_idx, header in enumerate(headers, 1):
            value = row.get(header, '')
            if header in ['likes', 'comments', 'shares', 'saves', 'views']:
                value = int(value) if value else 0
            elif header == 'rank':
                value = float(value) if value else 0
            ws.cell(row=row_idx, column=col_idx, value=value)
    
    wb.save(output_xlsx)
    print(f"Arquivo XLSX criado: {output_xlsx}")

def post_type_str(is_video, typename):
    if typename == "GraphSidecar":
        return "carousel"
    return "video" if is_video else "image"

def monitor_profile(profile_url, max_posts=100):
    """Função principal de monitoramento."""
    profile_name = extract_username_from_url(profile_url)
    if not profile_name:
        print(f"Erro: Não foi possível extrair username da URL: {profile_url}")
        return False
    
    print(f"\n{'='*60}")
    print(f"MONITORAMENTO DE PERFIL: {profile_name}")
    print(f"{'='*60}")
    print(f"URL: {profile_url}")
    print(f"Limite de posts: {max_posts}")
    print()
    
    base_dir = Path.cwd() / profile_name
    output_csv = base_dir / "posts_monitor.csv"
    output_xlsx = base_dir / "Monitoramento.xlsx"
    
    loader = setup_instaloader()
    
    try:
        profile = instaloader.Profile.from_username(loader.context, profile_name)
        print(f"Perfil carregado: @{profile.username}")
        print(f"Posts totais: {profile.mediacount}")
        print(f"Seguidores: {profile.followers}")
        print(f"Seguindo: {profile.followees}")
        print(f"Biografia: {profile.biography[:100]}..." if profile.biography else "Sem biografia")
        print()
        
        posts_data = []
        posts_processed = 0
        
        for post in profile.get_posts():
            if posts_processed >= max_posts:
                print(f"\nLimite de {max_posts} posts alcançado.")
                break
            
            post_data = get_post_data(post)
            posts_data.append(post_data)
            
            print(f"[{posts_processed + 1:3d}] {post.shortcode} | {post_type_str(post.is_video, post.typename):8s} | "
                  f"Likes: {str(post.likes):>6s} | Comments: {str(post.comments):>5s} | "
                  f"Views: {str(post.video_view_count if post.is_video else 0):>6s} | "
                  f"Cat: {post_data['category']:12s} | "
                  f"{post.date_utc.astimezone(BR_TZ).strftime('%Y-%m-%d %H:%M') if post.date_utc else 'N/A'}")
            
            posts_processed += 1
        
        if posts_processed == 0:
            print("Nenhum post encontrado.")
            return False
        
        # Compute global hashtag ranking and apply columns
        apply_hashtag_columns(posts_data)
        
        # Salvar CSV
        initialize_csv(output_csv, posts_data)
        for post_data in posts_data:
            append_post_to_csv(output_csv, post_data, posts_data)
        
        print(f"\n✓ {posts_processed} posts salvos em: {output_csv}")
        
        # Salvar XLSX
        save_to_xlsx(output_csv, output_xlsx)
        print(f"✓ Planilha Excel salva em: {output_xlsx}")
        
        # Resumo de categorias
        categories_count = {}
        for post_data in posts_data:
            cat = post_data.get('category', 'outros')
            categories_count[cat] = categories_count.get(cat, 0) + 1
        
        if categories_count:
            print(f"\nDistribuição por categoria:")
            for cat, count in sorted(categories_count.items(), key=lambda x: x[1], reverse=True):
                print(f"  {cat}: {count}")
        
        # Resumo de hashtags (global frequency)
        if _global_hashtag_ranking:
            print(f"\nTop 10 hashtags mais usadas (global):")
            for tag, count in _global_hashtag_ranking[:10]:
                print(f"  {tag}: {count}")
        
        return True
        
    except instaloader.exceptions.ProfileNotExistsException:
        print(f"Erro: Perfil @{profile_name} não encontrado ou é privado.")
        return False
    except instaloader.exceptions.LoginRequiredException:
        print("Erro: Login necessário. O perfil pode ser privado ou exigir autenticação.")
        print("Dica: Use 'instaloader --login=SEU_USUARIO --session-file=sessao @perfil' para criar sessão.")
        return False
    except Exception as e:
        print(f"Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

def update_existing_profiles():
    """Atualiza os perfis já monitorados com os novos campos."""
    base_dir = Path.cwd()
    profiles = ["fc_horacio", "midiabeijaflor"]
    
    for profile_name in profiles:
        profile_dir = base_dir / profile_name
        csv_file = profile_dir / "posts_monitor.csv"
        xlsx_file = profile_dir / "Monitoramento.xlsx"
        
        if not csv_file.exists():
            print(f"Arquivo não encontrado: {csv_file}")
            continue
        
        print(f"\nAtualizando {profile_name}...")
        
        # Ler CSV existente
        csv_data = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                csv_data.append(row)
        
        if not csv_data:
            print(f"  Nenhum dado em {csv_file}")
            continue
        
        # Atualizar cada linha com novos campos
        for row in csv_data:
            # Converter data de UTC para Brasília se necessário
            if 'date' in row and row['date']:
                try:
                    dt_utc = datetime.strptime(row['date'], '%Y-%m-%d %H:%M:%S UTC')
                    dt_utc = dt_utc.replace(tzinfo=timezone.utc)
                    dt_br = dt_utc.astimezone(BR_TZ)
                    row['date'] = dt_br.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass  # Manter data original se falhar
            
            # Adicionar campos faltantes com valores padrão
            row.setdefault('comments', '0')
            row.setdefault('shares', '0')
            row.setdefault('saves', '0')
            row.setdefault('category', 'outros')
            
            # Extrair hashtags do subtitles para reclassificar categoria
            subtitles = row.get('subtitles', '')
            hashtags_list = extract_hashtags(subtitles)
            row['category'] = classify_content(subtitles, hashtags_list)
            row['_hashtags_list'] = hashtags_list  # Internal field for global ranking
            
            # Remove the old 'hashtags' field since we no longer use it
            row.pop('hashtags', None)
        
        # Compute global hashtag ranking and apply columns
        apply_hashtag_columns(csv_data)
        
        # Reescrever CSV atualizado
        initialize_csv(csv_file, csv_data)
        for row in csv_data:
            append_post_to_csv(csv_file, row, csv_data)
        
        # Regerar XLSX
        save_to_xlsx(csv_file, xlsx_file)
        
        print(f"  ✓ {len(csv_data)} posts atualizados")
        print(f"  CSV: {csv_file}")
        print(f"  XLSX: {xlsx_file}")

def main():
    print("🔍 MONITORAMENTO DE PERFIS INSTAGRAM")
    print("=" * 60)
    print("Insira a URL do perfil do Instagram para monitorar.")
    print("Exemplos aceitos:")
    print("  https://www.instagram.com/fc_horacio/")
    print("  https://www.instagram.com/midiabeijaflor/?utm_source=...")
    print("  fc_horacio")
    print("=" * 60)
    
    # Menu de opções
    print("\nOpções:")
    print("  1 - Monitorar novo perfil")
    print("  2 - Atualizar perfis existentes (fc_horacio, midiabeijaflor)")
    print("  3 - Ambos")
    
    while True:
        choice = input("\n📋 Escolha uma opção [1]: ").strip()
        if not choice or choice == "1":
            mode = "new"
            break
        elif choice == "2":
            mode = "update"
            break
        elif choice == "3":
            mode = "both"
            break
        print("⚠️  Opção inválida. Digite 1, 2 ou 3.")
    
    if mode in ["new", "both"]:
        # Input da URL
        while True:
            profile_url = input("\n📎 URL do perfil: ").strip()
            if profile_url:
                break
            print("⚠️  URL não pode ser vazia. Tente novamente.")
        
        # Input do limite de posts
        while True:
            max_posts_input = input("📊 Máximo de posts a coletar [100]: ").strip()
            if not max_posts_input:
                max_posts = 100
                break
            try:
                max_posts = int(max_posts_input)
                if max_posts > 0:
                    break
                print("⚠️  Deve ser um número positivo.")
            except ValueError:
                print("⚠️  Digite um número válido.")
        
        success = monitor_profile(profile_url, max_posts)
        
        if success:
            profile_name = extract_username_from_url(profile_url)
            print(f"\n{'='*60}")
            print(f"✅ MONITORAMENTO CONCLUÍDO COM SUCESSO!")
            print(f"📁 Pasta do perfil: ./{profile_name}/")
            print(f"📄 CSV: ./{profile_name}/posts_monitor.csv")
            print(f"📊 Excel: ./{profile_name}/Monitoramento.xlsx")
            print(f"{'='*60}")
        else:
            print(f"\n❌ Monitoramento falhou. Verifique os erros acima.")
    
    if mode in ["update", "both"]:
        print(f"\n{'='*60}")
        print("ATUALIZANDO PERFIS EXISTENTES")
        print(f"{'='*60}")
        update_existing_profiles()
        print(f"\n✅ Atualização concluída!")

if __name__ == "__main__":
    main()