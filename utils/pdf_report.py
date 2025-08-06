from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, Frame
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io
import os
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI para servidores
import matplotlib.pyplot as plt
import numpy as np
from math import pi

def get_metricas_generales_data(local, visitante, stats_local, stats_visitante):
    metricas = [
        ("xG", "xG"),
        ("Posesión", "Possession"),
        ("Field Tilt", "Field Tilt"),
        ("Pass in Opp. Half", "Passes in Opposition Half"),
        ("PPDA", "PPDA"),
        ("High Recovery", "High Recoveries"),
        ("Crosses", "Crosses"),
        ("Corners", "Corners"),
        ("Fouls", "Fouls"),
    ]
    data = [["Métrica", local, visitante]]
    for nombre, col in metricas:
        val_local = stats_local[col]
        val_visitante = stats_visitante[col]
        if "Possession" in col or "Field Tilt" in col:
            val_local = f"{val_local}%"
            val_visitante = f"{val_visitante}%"
        data.append([nombre, val_local, val_visitante])
    return data

def get_ranking_data(local, visitante, stats, fecha):
    metricas = [
        ("Goles", "Goals"),
        ("xG", "xG"),
        ("xA", "xA") if "xA" in stats.columns else None,
        ("Asistencias", "Assists") if "Assists" in stats.columns else None,
        ("Recuperaciones", "High Recoveries"),
        ("Faltas", "Fouls"),
        ("Corners", "Corners"),
    ]
    metricas = [m for m in metricas if m is not None]
    data = [["Métrica", local, visitante]]
    for nombre, col in metricas:
        partidos = stats[stats['Date'] == fecha]
        ranking = partidos.sort_values(by=col, ascending=False).reset_index(drop=True)
        pos_local = ranking[ranking['Team'] == local].index[0] + 1
        pos_visitante = ranking[ranking['Team'] == visitante].index[0] + 1
        data.append([nombre, f"{pos_local}º", f"{pos_visitante}º"])
    return data

def crear_radar_png(local, visitante, stats_local, stats_visitante, partido, path):
    
    # Configurar el estilo oscuro
    plt.style.use('dark_background')
    
    # Métricas y valores
    categorias = ["xG", "Shots", "PPDA", "Field Tilt", "High\nRecoveries", "Corners", "Crosses"]
    N = len(categorias)
    
    # Valores de cada equipo
    local_vals = [float(stats_local[m.replace("\n", " ")]) if "\n" not in m else float(stats_local["High Recoveries"]) for m in categorias]
    visitante_vals = [float(stats_visitante[m.replace("\n", " ")]) if "\n" not in m else float(stats_visitante["High Recoveries"]) for m in categorias]
    
    # Normalizar valores (0-1)
    maximos = [max(l, v) * 1.2 if max(l, v) > 0 else 1 for l, v in zip(local_vals, visitante_vals)]
    local_norm = [v/m for v, m in zip(local_vals, maximos)]
    visitante_norm = [v/m for v, m in zip(visitante_vals, maximos)]
    
    # Ángulos para cada categoría
    angulos = [n / N * 2 * pi for n in range(N)]
    local_norm += local_norm[:1]
    visitante_norm += visitante_norm[:1]
    angulos += angulos[:1]
    
    # Crear figura con márgenes ajustados
    fig, ax = plt.subplots(figsize=(12, 12), subplot_kw=dict(projection='polar'))
    fig.patch.set_facecolor('#24282a')
    ax.set_facecolor('#24282a')
    
    # Dibujar los datos
    ax.plot(angulos, local_norm, 'o-', linewidth=3, label=local, color='#2ecc71', markersize=10)
    ax.fill(angulos, local_norm, alpha=0.25, color='#2ecc71')
    
    ax.plot(angulos, visitante_norm, 'o-', linewidth=3, label=visitante, color='#3498db', markersize=10)
    ax.fill(angulos, visitante_norm, alpha=0.25, color='#3498db')
    
    # Configurar las etiquetas FUERA del círculo
    ax.set_xticks(angulos[:-1])
    ax.set_xticklabels(categorias, size=18, weight='bold', color='white')
    
    # IMPORTANTE: Mover las etiquetas más afuera
    ax.tick_params(axis='x', which='major', pad=20)  # Padding para sacar las etiquetas
    
    # Configurar la cuadrícula
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], size=14, color='#888')
    ax.grid(True, linewidth=1, color='#444', linestyle='-')
    
    # Líneas radiales más visibles
    ax.xaxis.grid(True, linewidth=2, color='#555')
    ax.yaxis.grid(True, linewidth=1, color='#555')
    
    # Leyenda en la esquina superior derecha
    legend = ax.legend(loc='upper right', bbox_to_anchor=(1.15, 1.15), fontsize=20, 
                      frameon=True, fancybox=True, shadow=True)
    legend.get_frame().set_facecolor('#24282a')
    legend.get_frame().set_edgecolor('#2ecc71')
    legend.get_frame().set_linewidth(2)
    
    # Ajustar márgenes para que quepa todo
    plt.tight_layout()
    
    # Guardar con alta calidad
    plt.savefig(path, dpi=150, facecolor='#24282a', edgecolor='none', bbox_inches='tight', pad_inches=0.2)
    plt.close()

def crear_barras_png(local, visitante, stats_local, stats_visitante, path):
    
    plt.style.use('dark_background')
    
    metricas = ["Corners", "Crosses", "Fouls", "On-Ball\nPressure", "Off-Ball\nPressure"]
    local_vals = [float(stats_local[m.replace("\n", " ")]) for m in metricas]
    visitante_vals = [float(stats_visitante[m.replace("\n", " ")]) for m in metricas]
    
    x = np.arange(len(metricas))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor('#24282a')
    ax.set_facecolor('#24282a')
    
    # Barras
    bars1 = ax.barh(x - width/2, local_vals, width, label=local, color='#2ecc71', edgecolor='white', linewidth=2)
    bars2 = ax.barh(x + width/2, visitante_vals, width, label=visitante, color='#3498db', edgecolor='white', linewidth=2)
    
    # Valores en las barras
    for bar, val in zip(bars1, local_vals):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                f'{val:.0f}', va='center', color='white', fontsize=16, weight='bold')
    
    for bar, val in zip(bars2, visitante_vals):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                f'{val:.0f}', va='center', color='white', fontsize=16, weight='bold')
    
    # Configuración
    ax.set_yticks(x)
    ax.set_yticklabels(metricas, fontsize=18, weight='bold')
    ax.set_xlabel('Valor', fontsize=16, weight='bold')
    
    # LEYENDA ABAJO CON FONDO TRANSPARENTE
    legend = ax.legend(
        fontsize=20, 
        loc='upper center',  # Centrada
        bbox_to_anchor=(0.5, -0.1),  # Debajo del gráfico
        ncol=2,  # En una fila horizontal
        frameon=True,
        fancybox=False,
        framealpha=0,  # Fondo transparente
        edgecolor='none'  # Sin borde
    )
    
    # Color del texto de la leyenda
    for text in legend.get_texts():
        text.set_color('white')
    
    ax.grid(True, alpha=0.3, axis='x')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig(path, dpi=150, facecolor='#24282a', bbox_inches='tight')
    plt.close()

def get_stats_partido(stats, partido, local, visitante):
    stats_partido = stats[stats['Match'] == partido]
    stats_local = stats_partido[stats_partido['Team'] == local].iloc[0]
    stats_visitante = stats_partido[stats_partido['Team'] == visitante].iloc[0]
    return stats_local, stats_visitante

def limpiar_tmp(*paths):
    for path in paths:
        try:
            os.remove(path)
        except Exception:
            pass

def get_radar_path(partido):
    return f"assets/tmp/radar_{partido}.png"

def get_barras_path(partido):
    return f"assets/tmp/barras_{partido}.png"

def normaliza_nombre(nombre):
    return nombre.lower().replace(" ", "_").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

def generar_pdf_postpartido(partido_row, stats):
    local = partido_row['Home']
    visitante = partido_row['Away']
    fecha = partido_row['Date']
    resultado = partido_row['Match']
    jornada = partido_row.get('Round', "")

    escudo_local = f"assets/Escudos/{normaliza_nombre(local)}.png"
    escudo_visitante = f"assets/Escudos/{normaliza_nombre(visitante)}.png"

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Fondo
    c.setFillColor(colors.HexColor("#24282a"))
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Tamaños y posiciones
    escudo_size = 80
    margen_lateral = 60
    y_cabecera = height - 120

    # Escudo local (izquierda)
    if os.path.exists(escudo_local):
        c.drawImage(escudo_local, margen_lateral, y_cabecera, width=escudo_size, height=escudo_size, mask='auto')
    else:
        c.setFillColor(colors.HexColor("#2ecc71"))
        c.rect(margen_lateral, y_cabecera, escudo_size, escudo_size, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica", 10)
        c.drawCentredString(margen_lateral + escudo_size/2, y_cabecera + escudo_size/2, "NO IMG")

    # Escudo visitante (derecha)
    if os.path.exists(escudo_visitante):
        c.drawImage(escudo_visitante, width - margen_lateral - escudo_size, y_cabecera, width=escudo_size, height=escudo_size, mask='auto')
    else:
        c.setFillColor(colors.HexColor("#3498db"))
        c.rect(width - margen_lateral - escudo_size, y_cabecera, escudo_size, escudo_size, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica", 10)
        c.drawCentredString(width - margen_lateral - escudo_size/2, y_cabecera + escudo_size/2, "NO IMG")

    # Jornada y fecha centrada, alineada con los escudos
    c.setFont("Helvetica", 20)
    c.setFillColor(colors.HexColor("#2ecc71"))
    texto_jornada = f"Jornada {jornada} - {fecha}" if jornada else fecha
    c.drawCentredString(width/2, y_cabecera + escudo_size/2, texto_jornada)

    # Marcador grande y centrado, justo debajo
    marcador = resultado
    c.setFont("Helvetica-Bold", 38)
    c.setFillColor(colors.HexColor("#2ecc71"))
    c.drawCentredString(width/2, y_cabecera - 40, marcador)

    # 1. Datos del partido
    stats_local, stats_visitante = get_stats_partido(stats, resultado, local, visitante)
    
    # 2. Tabla de métricas generales
    metricas_data = get_metricas_generales_data(local, visitante, stats_local, stats_visitante)
    
    # 3. Datos del ranking
    ranking_data = get_ranking_data(local, visitante, stats, fecha)
    
    # 4. PRIMER BLOQUE - TABLA + RANKING (intercambiado)
    y_primer_bloque = 350
    altura_primer_bloque = 300
    margen_horizontal = 20
    espacio_entre = 15
    ancho_total = width - 2 * margen_horizontal
    ancho_tabla = (ancho_total - espacio_entre) * 0.55
    ancho_ranking = (ancho_total - espacio_entre) * 0.45
    
    # TABLA DE ESTADÍSTICAS (izquierda)
    table = Table(metricas_data, colWidths=[ancho_tabla*0.4, ancho_tabla*0.3, ancho_tabla*0.3])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2ecc71")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#24282a")),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#2ecc71")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#24282a"), colors.HexColor("#1a1e20")]),
    ]))
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='TituloSeccion', fontSize=18, alignment=1, textColor=colors.HexColor("#2ecc71"), spaceAfter=10, spaceBefore=10, fontName="Helvetica-Bold"))
    story_tabla = [Paragraph("Estadísticas Generales", styles['TituloSeccion']), table]
    
    frame_tabla = Frame(margen_horizontal, y_primer_bloque, ancho_tabla, altura_primer_bloque, showBoundary=0)
    frame_tabla.addFromList(story_tabla, c)
    
    # TABLA DE RANKING (derecha) - COLOR VERDE
    ranking_table = Table(ranking_data, colWidths=[ancho_ranking*0.4, ancho_ranking*0.3, ancho_ranking*0.3])
    ranking_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2ecc71")),  # VERDE como la otra tabla
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#24282a")),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#2ecc71")),  # Bordes verdes
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#24282a"), colors.HexColor("#1a1e20")]),
    ]))
    
    styles.add(ParagraphStyle(
        name='TituloRanking', 
        fontSize=18, 
        alignment=1, 
        textColor=colors.HexColor("#2ecc71"),  # Verde
        spaceAfter=25,
        spaceBefore=10, 
        fontName="Helvetica-Bold"
    ))
    
    story_ranking = [
        Paragraph("Ranking en la Jornada", styles['TituloRanking']), 
        ranking_table
    ]
    
    frame_ranking = Frame(
        margen_horizontal + ancho_tabla + espacio_entre,
        y_primer_bloque, 
        ancho_ranking, 
        altura_primer_bloque,
        showBoundary=0
    )
    frame_ranking.addFromList(story_ranking, c)
    
    # 5. SEGUNDO BLOQUE - BARRAS + RADAR
    y_segundo_bloque = 30
    altura_segundo_bloque = 280

    # Generar gráfico de barras
    barras_path = get_barras_path(resultado)
    crear_barras_png(local, visitante, stats_local, stats_visitante, barras_path)

    # Generar radar chart
    radar_path = get_radar_path(resultado)
    crear_radar_png(local, visitante, stats_local, stats_visitante, resultado, radar_path)

    # TÍTULO CENTRADO PARA AMBOS GRÁFICOS
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.HexColor("#2ecc71"))
    c.drawCentredString(width/2, y_segundo_bloque + altura_segundo_bloque + 20, "Comparación de Métricas")

    # GRÁFICO DE BARRAS (izquierda) - SIN TÍTULO INDIVIDUAL
    if os.path.exists(barras_path):
        barras_x = margen_horizontal
        barras_y = y_segundo_bloque
        barras_width = ancho_tabla * 1.1
        barras_height = altura_segundo_bloque
        
        # Ya no ponemos título aquí, está centrado arriba
        c.drawImage(barras_path, barras_x, barras_y, width=barras_width, height=barras_height, mask='auto', preserveAspectRatio=True)

    # RADAR CHART (derecha)
    if os.path.exists(radar_path):
        radar_x = margen_horizontal + ancho_tabla + espacio_entre
        radar_y = y_segundo_bloque + 30
        radar_size = min(ancho_ranking, altura_segundo_bloque - 30)
        c.drawImage(radar_path, radar_x, radar_y, width=radar_size, height=radar_size, mask='auto', preserveAspectRatio=True)
    
    # Guardar y retornar
    c.save()
    buffer.seek(0)
    return buffer