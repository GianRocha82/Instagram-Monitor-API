"""
CSV/Excel Generator Module - Creates multi-sheet output as specified
"""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import Counter

import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.models import ProfileData, PostData, BR_TZ
from app.scraper import CATEGORIES

def generate_filename(profile_name: str, time_range: str) -> str:
    """Gera nome do arquivo: {nome do perfil}_{tempo de raspagem}"""
    time_labels = {
        "30": "30dias",
        "90": "90dias", 
        "180": "180dias"
    }
    time_label = time_labels.get(time_range, f"{time_range}dias")
    timestamp = datetime.now(BR_TZ).strftime('%Y%m%d')
    return f"{profile_name}_{time_label}_{timestamp}"

def create_postagens_sheet(posts: List[PostData], profile: ProfileData) -> List[Dict[str, Any]]:
    """
    Cria a tabela 'Postagens' com as colunas especificadas:
    id_perfil, nome_perfil, id_postagem, data_postagem, tipo_postagem,
    legenda_postagem, numero_likes, numero_views, numero_republicado,
    numero_compartilhamento, numero_comentarios, hashtags
    """
    rows = []
    for post in posts:
        # Hashtags em minúsculas, separadas por vírgula
        hashtags_str = ", ".join(post.hashtags) if post.hashtags else ""
        
        row = {
            "id_perfil": profile.user_id,
            "nome_perfil": profile.username,
            "id_postagem": post.post_id,
            "data_postagem": post.date_br,
            "tipo_postagem": post.post_type,
            "legenda_postagem": post.caption,
            "numero_likes": post.likes,
            "numero_views": post.views,
            "numero_republicado": post.shares,  # shares = republicado
            "numero_compartilhamento": post.saves,  # saves = compartilhamento
            "numero_comentarios": post.comments,
            "hashtags": hashtags_str
        }
        rows.append(row)
    return rows

def create_hashtags_sheet(posts: List[PostData], profile: ProfileData) -> List[Dict[str, Any]]:
    """
    Cria a tabela 'Hashtags' com colunas: id_perfil, id_postagem, hashtag_n
    Cada coluna hashtag_n contém apenas a hashtag naquela posição (baseada no ranking global)
    """
    if not posts:
        return []
    
    # Calcular ranking global de hashtags por frequência
    global_hashtag_freq = Counter()
    for post in posts:
        for tag in post.hashtags:
            global_hashtag_freq[tag.lower()] += 1
    
    # Ordenar por frequência (desc), depois alfabética
    global_ranking = sorted(global_hashtag_freq.items(), key=lambda x: (-x[1], x[0]))
    
    rows = []
    for post in posts:
        # Criar lookup case-insensitive das hashtags do post
        post_hashtags_lower = {tag.lower() for tag in post.hashtags}
        
        row = {
            "id_perfil": profile.user_id,
            "id_postagem": post.post_id
        }
        
        # Para cada hashtag no ranking global, preencher se o post a tem
        for rank, (tag_lower, count) in enumerate(global_ranking, 1):
            row[f"hashtag_{rank}"] = tag_lower if tag_lower in post_hashtags_lower else ""
        
        rows.append(row)
    
    return rows, [tag for tag, _ in global_ranking]

def create_conteudo_sheet(posts: List[PostData], profile: ProfileData) -> List[Dict[str, Any]]:
    """
    Cria a tabela 'Conteudo' com: id_perfil, id_postagem, tematica_conteudo
    """
    rows = []
    for post in posts:
        row = {
            "id_perfil": profile.user_id,
            "id_postagem": post.post_id,
            "tematica_conteudo": post.category
        }
        rows.append(row)
    return rows

def save_to_excel(profile: ProfileData, posts: List[PostData], output_path: Path, 
                  time_range: str, company_profile: Optional[ProfileData] = None) -> Path:
    """
    Salva os dados em arquivo Excel com 3 abas: Postagens, Hashtags, Conteudo
    """
    filename = generate_filename(profile.username, time_range)
    output_file = output_path / f"{filename}.xlsx"
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Gerar dados para cada aba
    postagens_data = create_postagens_sheet(posts, profile)
    hashtags_data, hashtag_ranking = create_hashtags_sheet(posts, profile)
    conteudo_data = create_conteudo_sheet(posts, profile)
    
    # Criar workbook
    wb = openpyxl.Workbook()
    
    # Estilos
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="E1306C", end_color="E1306C", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # ABA 1: Postagens
    ws1 = wb.active
    ws1.title = "Postagens"
    
    if postagens_data:
        headers = list(postagens_data[0].keys())
        # Escrever cabeçalho
        for col_idx, header in enumerate(headers, 1):
            cell = ws1.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
        
        # Escrever dados
        for row_idx, row_data in enumerate(postagens_data, 2):
            for col_idx, header in enumerate(headers, 1):
                cell = ws1.cell(row=row_idx, column=col_idx, value=row_data.get(header, ""))
                cell.border = thin_border
                if header in ["numero_likes", "numero_views", "numero_republicado", "numero_compartilhamento"]:
                    cell.number_format = '#,##0'
        
        # Ajustar largura das colunas
        for col_idx, header in enumerate(headers, 1):
            ws1.column_dimensions[get_column_letter(col_idx)].width = min(max(len(header) + 2, 15), 50)
        # Coluna legenda mais larga
        legenda_idx = headers.index("legenda_postagem") + 1
        ws1.column_dimensions[get_column_letter(legenda_idx)].width = 80
    
    # ABA 2: Hashtags
    ws2 = wb.create_sheet("Hashtags")
    
    if hashtags_data:
        headers = list(hashtags_data[0].keys())
        for col_idx, header in enumerate(headers, 1):
            cell = ws2.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
        
        for row_idx, row_data in enumerate(hashtags_data, 2):
            for col_idx, header in enumerate(headers, 1):
                cell = ws2.cell(row=row_idx, column=col_idx, value=row_data.get(header, ""))
                cell.border = thin_border
        
        for col_idx in range(1, len(headers) + 1):
            ws2.column_dimensions[get_column_letter(col_idx)].width = 18
    
    # ABA 3: Conteudo
    ws3 = wb.create_sheet("Conteudo")
    
    if conteudo_data:
        headers = list(conteudo_data[0].keys())
        for col_idx, header in enumerate(headers, 1):
            cell = ws3.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
        
        for row_idx, row_data in enumerate(conteudo_data, 2):
            for col_idx, header in enumerate(headers, 1):
                cell = ws3.cell(row=row_idx, column=col_idx, value=row_data.get(header, ""))
                cell.border = thin_border
        
        for col_idx, header in enumerate(headers, 1):
            ws3.column_dimensions[get_column_letter(col_idx)].width = max(len(header) + 2, 20)
        # Coluna tematica mais larga
        tematica_idx = headers.index("tematica_conteudo") + 1
        ws3.column_dimensions[get_column_letter(tematica_idx)].width = 30
    
    # ABA 4: Metadados (informações do perfil e empresa)
    ws4 = wb.create_sheet("Metadados")
    
    meta_data = [
        ["Campo", "Valor"],
        ["Perfil Analisado", f"@{profile.username}"],
        ["Nome Completo", profile.full_name],
        ["ID Perfil", profile.user_id],
        ["Seguidores", profile.followers],
        ["Seguindo", profile.followees],
        ["Total de Posts", profile.mediacount],
        ["Verificado", "Sim" if profile.is_verified else "Não"],
        ["Privado", "Sim" if profile.is_private else "Não"],
        ["Biografia", profile.biography],
        ["Foto do Perfil", profile.profile_pic_url],
        ["", ""],
        ["Período de Análise", f"Últimos {time_range} dias"],
        ["Posts Coletados", len(posts)],
        ["Data da Coleta", datetime.now(BR_TZ).strftime('%Y-%m-%d %H:%M:%S')],
    ]
    
    if company_profile:
        meta_data.extend([
            ["", ""],
            ["Empresa Contratante", f"@{company_profile.username}"],
            ["Nome Empresa", company_profile.full_name],
            ["Seguidores Empresa", company_profile.followers],
            ["Biografia Empresa", company_profile.biography],
        ])
    
    for row_idx, row_data in enumerate(meta_data, 1):
        for col_idx, value in enumerate(row_data, 1):
            cell = ws4.cell(row=row_idx, column=col_idx, value=value)
            if row_idx == 1 or (row_idx > 1 and col_idx == 1 and value):
                cell.font = Font(bold=True)
            cell.border = thin_border
    
    ws4.column_dimensions['A'].width = 30
    ws4.column_dimensions['B'].width = 80
    
    # Salvar
    wb.save(output_file)
    return output_file

def load_from_excel(file_path: Path) -> Dict[str, Any]:
    """Carrega dados do Excel gerado para uso no dashboard."""
    result = {
        "postagens": [],
        "hashtags": [],
        "conteudo": [],
        "metadados": {}
    }
    
    try:
        # Aba Postagens
        df_posts = pd.read_excel(file_path, sheet_name="Postagens")
        
        # Converter para formato PostData
        for _, row in df_posts.iterrows():
            # Parse hashtags
            hashtags_raw = row.get('hashtags', '')
            if pd.isna(hashtags_raw) or hashtags_raw == '':
                hashtags = []
            else:
                hashtags = [h.strip().lower() for h in str(hashtags_raw).split(',') if h.strip()]
            
            post = {
                "shortcode": str(row.get('id_postagem', '')),
                "post_id": int(row.get('id_postagem', 0)),
                "date_utc": datetime.strptime(str(row.get('data_postagem', '')), '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc) if row.get('data_postagem') else datetime.now(timezone.utc),
                "date_br": str(row.get('data_postagem', '')),
                "is_video": str(row.get('tipo_postagem', '')).lower() == 'video',
                "typename": str(row.get('tipo_postagem', '')).capitalize(),
                "post_type": str(row.get('tipo_postagem', 'image')),
                "caption": str(row.get('legenda_postagem', '')),
                "likes": int(row.get('numero_likes', 0)) if pd.notna(row.get('numero_likes')) else 0,
                "comments": int(row.get('numero_comentarios', 0)) if pd.notna(row.get('numero_comentarios')) else 0,
                "views": int(row.get('numero_views', 0)) if pd.notna(row.get('numero_views')) else 0,
                "shares": int(row.get('numero_republicado', 0)) if pd.notna(row.get('numero_republicado')) else 0,
                "saves": int(row.get('numero_compartilhamento', 0)) if pd.notna(row.get('numero_compartilhamento')) else 0,
                "hashtags": hashtags,
                "category": "",  # Will be filled from Conteudo sheet
                "url": f"https://www.instagram.com/p/{row.get('id_postagem', '')}/"
            }
            result["postagens"].append(post)
        
        # Aba Conteudo - para pegar as categorias
        try:
            df_content = pd.read_excel(file_path, sheet_name="Conteudo")
            content_map = {}
            for _, row in df_content.iterrows():
                post_id = int(row.get('id_postagem', 0))
                category = str(row.get('tematica_conteudo', 'outros'))
                content_map[post_id] = category
            
            # Atualizar categorias nos posts
            for post in result["postagens"]:
                post_id = post["post_id"]
                if post_id in content_map:
                    post["category"] = content_map[post_id]
        except:
            pass
        
        # Aba Hashtags (opcional, para referência)
        try:
            df_tags = pd.read_excel(file_path, sheet_name="Hashtags")
            result["hashtags"] = df_tags.to_dict('records')
        except:
            pass
        
        # Aba Metadados
        df_meta = pd.read_excel(file_path, sheet_name="Metadados")
        meta_dict = {}
        for _, row in df_meta.iterrows():
            if pd.notna(row.iloc[0]) and pd.notna(row.iloc[1]):
                meta_dict[str(row.iloc[0])] = row.iloc[1]
        
        # Map to ProfileData fields
        result["metadados"] = {
            "username": meta_dict.get("Perfil Analisado", "").replace("@", ""),
            "user_id": int(meta_dict.get("ID Perfil", 0)) if meta_dict.get("ID Perfil") else 0,
            "full_name": meta_dict.get("Nome Completo", ""),
            "biography": meta_dict.get("Biografia", ""),
            "followers": int(meta_dict.get("Seguidores", 0)) if meta_dict.get("Seguidores") else 0,
            "followees": int(meta_dict.get("Seguindo", 0)) if meta_dict.get("Seguindo") else 0,
            "mediacount": int(meta_dict.get("Total de Posts", 0)) if meta_dict.get("Total de Posts") else 0,
            "profile_pic_url": meta_dict.get("Foto do Perfil", ""),
            "is_verified": meta_dict.get("Verificado") == "Sim",
            "is_private": meta_dict.get("Privado") == "Sim",
        }
                
    except Exception as e:
        print(f"Erro ao carregar Excel: {e}")
        import traceback
        traceback.print_exc()
    
    return result