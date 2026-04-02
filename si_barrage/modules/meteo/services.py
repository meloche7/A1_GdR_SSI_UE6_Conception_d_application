# Logique métier pour la météo

from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_latest_releves(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """Récupère les derniers relevés météo (débit + pluviométrie)."""
    result = db.execute(
        text(
            """
            SELECT id, date, debit_riviere_m3s, pluviometrie_mm
            FROM meteo
            ORDER BY date DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).fetchall()

    releves: List[Dict[str, Any]] = []
    for row in result:
        releves.append(
            {
                "id": row[0],
                "date": row[1],
                "debit_riviere_m3s": row[2],
                "pluviometrie_mm": row[3],
            }
        )

    return releves


def get_latest_previsions(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """Récupère les dernières prévisions météo/hydrologiques."""
    result = db.execute(
        text(
            """
            SELECT id, date_prevision, date_creation, debit_riviere_m3s_prevu, pluviometrie_mm_prevue
            FROM meteo_previsions
            ORDER BY date_prevision ASC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).fetchall()

    previsions: List[Dict[str, Any]] = []
    for row in result:
        previsions.append(
            {
                "id": row[0],
                "date_prevision": row[1],
                "date_creation": row[2],
                "debit_riviere_m3s_prevu": row[3],
                "pluviometrie_mm_prevue": row[4],
            }
        )

    return previsions


def render_graph_with_axes(
    values_real, values_prev, width=800, height=400, y_label="Débit (m³/s)"
) -> str:
    """
    Retourne un graphique SVG professionnel avec axes X/Y comparant 2 séries de données.
    """
    if not values_real or not values_prev:
        return (
            "<div style='text-align:center;color:#666;'>Aucune donnée disponible</div>"
        )

    # Normaliser les deux séries ensemble
    all_values = values_real + values_prev
    min_v = min(all_values)
    max_v = max(all_values)
    span = max_v - min_v if max_v > min_v else 1

    # Dimensions
    margin_left = 70
    margin_right = 30
    margin_top = 40
    margin_bottom = 80
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom

    # Générer les points
    def get_points(values):
        points = []
        for i, v in enumerate(values):
            x = (
                margin_left + (i / (len(values) - 1)) * plot_width
                if len(values) > 1
                else margin_left + plot_width / 2
            )
            y = margin_top + plot_height - ((v - min_v) / span) * plot_height
            points.append((x, y, v))
        return points

    points_real = get_points(values_real)
    points_prev = get_points(values_prev)

    # Polylines
    def create_polyline(points, color):
        coords = " ".join([f"{x},{y}" for x, y, _ in points])
        return f'<polyline fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" points="{coords}" />'

    polyline_real = create_polyline(points_real, "#0099ff")
    polyline_prev = create_polyline(points_prev, "#f59e0b")

    # Axes
    x_axis = f'<line x1="{margin_left}" y1="{margin_top + plot_height}" x2="{width - margin_right}" y2="{margin_top + plot_height}" stroke="#333" stroke-width="2"/>'
    y_axis = f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_height}" stroke="#333" stroke-width="2"/>'

    # Graduations Y
    y_ticks = ""
    for i in range(5):
        y_val = min_v + (i / 4) * span
        y_pos = margin_top + plot_height - (i / 4) * plot_height
        y_ticks += f'<line x1="{margin_left - 8}" y1="{y_pos}" x2="{margin_left}" y2="{y_pos}" stroke="#333" stroke-width="1"/>'
        y_ticks += f'<text x="{margin_left - 12}" y="{y_pos + 4}" font-size="11" text-anchor="end" fill="#666">{y_val:.0f}</text>'

    # Graduations X
    x_ticks = ""
    num_ticks = min(len(values_real), 8)
    for i in range(num_ticks):
        x_idx = (
            int((i / (num_ticks - 1)) * (len(values_real) - 1)) if num_ticks > 1 else 0
        )
        x_pos = (
            margin_left + (x_idx / (len(values_real) - 1)) * plot_width
            if len(values_real) > 1
            else margin_left + plot_width / 2
        )
        x_ticks += f'<line x1="{x_pos}" y1="{margin_top + plot_height}" x2="{x_pos}" y2="{margin_top + plot_height + 8}" stroke="#333" stroke-width="1"/>'
        x_ticks += f'<text x="{x_pos}" y="{margin_top + plot_height + 25}" font-size="11" text-anchor="middle" fill="#666">{x_idx}</text>'

    # Labels axes
    y_label_text = f'<text x="20" y="{margin_top + plot_height / 2}" font-size="12" fill="#666" text-anchor="middle" transform="rotate(-90 20 {margin_top + plot_height / 2})">{y_label}</text>'
    x_label_text = f'<text x="{margin_left + plot_width / 2}" y="{margin_top + plot_height + 65}" font-size="12" text-anchor="middle" fill="#666">Temps (indices)</text>'

    svg = f"""
    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="{width}" height="{height}" fill="white" stroke="#eee" stroke-width="1"/>
        {y_ticks}
        {x_ticks}
        {x_axis}
        {y_axis}
        {polyline_real}
        {polyline_prev}
        {y_label_text}
        {x_label_text}
    </svg>
    """

    return svg


def get_mean_production(db: Session) -> float:
    """
    Calcule la production moyenne en MWh.
    """
    result = db.execute(
        text("SELECT AVG(production_mwh) as mean_prod FROM production")
    ).fetchone()

    if result and result[0]:
        return round(result[0], 2)
    return 0.0


def get_last_maintenance(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Récupère les dernières maintenances.
    """
    result = db.execute(
        text("""
            SELECT id, id_equipement, nom_equipement, statut, description, date_creation
            FROM maintenance
            ORDER BY date_creation DESC
            LIMIT :limit
        """),
        {"limit": limit},
    ).fetchall()

    maintenance_list = []
    for row in result:
        maintenance_list.append(
            {
                "id": row[0],
                "id_equipement": row[1],
                "nom_equipement": row[2],
                "statut": row[3],
                "description": row[4],
                "date_creation": row[5],
            }
        )

    return maintenance_list
