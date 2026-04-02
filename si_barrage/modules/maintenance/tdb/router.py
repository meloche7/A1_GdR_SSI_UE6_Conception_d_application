from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ....db import get_db
from . import services

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def maintenance_dashboard_page():
    """
    Page principale du tableau de bord maintenance.

    Cette page charge dynamiquement :
    - les KPI
    - les filtres
    - le tableau des équipements

    Le style est volontairement harmonisé avec la page Historique
    pour donner une interface cohérente, premium et professionnelle.
    """
    html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>Maintenance — Vue globale</title>
      <script src="https://unpkg.com/htmx.org@1.9.10"></script>

      <style>
        body {
            font-family: system-ui;
            padding: 20px;
            max-width: 1100px;
            margin: 0 auto;
            background: #f6f7fb;
            color: #1f2937;
        }

        .section-title {
            font-size: 2.2rem;
            font-weight: bold;
            margin-bottom: 6px;
        }

        .subtitle {
            color: #667085;
            margin-bottom: 24px;
            font-size: 1rem;
        }

        .card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
            padding: 22px;
            margin-bottom: 24px;
        }

        .panel-title {
            font-size: 1.25rem;
            font-weight: 800;
            margin: 0 0 14px 0;
        }

        .muted {
            color: #667085;
        }

        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
        }

        .kpi-card {
            background: white;
            border-radius: 16px;
            padding: 26px 20px;
            text-align: center;
            border: 1px solid #e5e7eb;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
        }

        .kpi-number {
            font-size: 3rem;
            font-weight: bold;
            line-height: 1;
            margin-bottom: 10px;
        }

        .kpi-label {
            color: #667085;
            font-size: 1rem;
        }

        .kpi-termine {
            border: 2px solid #16a34a;
        }

        .kpi-encours {
            border: 2px solid #f59e0b;
        }

        .kpi-attente {
            border: 2px solid #f87171;
        }

        .filter-bar {
            display: flex;
            gap: 18px;
            align-items: end;
            flex-wrap: wrap;
        }

        .field {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .field label {
            font-weight: 700;
            font-size: 0.98rem;
        }

        select {
            padding: 12px 14px;
            border: 1px solid #d0d5dd;
            border-radius: 10px;
            font-size: 16px;
            background: white;
            min-width: 180px;
        }

        select:focus {
            outline: none;
            border-color: #7c3aed;
            box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.15);
        }

        .info-note {
            color: #667085;
            margin: 4px 0 18px 0;
            font-size: 14px;
        }

        .loading-box,
        .info-box {
            border-radius: 12px;
            padding: 14px 16px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            color: #475467;
        }

        .table-wrap {
            overflow-x: auto;
        }

        table {
            width: 100%;
            border-collapse: collapse;
        }

        th, td {
            padding: 12px 14px;
            border-bottom: 1px solid #edf2f7;
            text-align: left;
            vertical-align: top;
        }

        th {
            color: #475467;
            font-size: 14px;
            font-weight: 800;
        }

        tbody tr:hover {
            filter: brightness(0.99);
        }

        .status-termine td {
            background-color: #dff3e3;
        }

        .status-encours td {
            background-color: #fbe0b5;
        }

        .status-attente td {
            background-color: #f8d7da;
        }

        .btn-delete,
        .btn-primary,
        .btn-secondary {
            border: none;
            border-radius: 12px;
            padding: 12px 20px;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            transition: 0.2s ease;
        }

        .btn-delete {
            background: #dc3545;
            color: white;
            padding: 10px 16px;
        }

        .btn-delete:hover {
            background: #bb2d3b;
            transform: translateY(-1px);
        }

        .btn-primary {
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white;
        }

        .btn-primary:hover {
            opacity: 0.96;
            transform: translateY(-1px);
        }

        .btn-secondary {
            background: linear-gradient(135deg, #7c3aed, #6d28d9);
            color: white;
        }

        .btn-secondary:hover {
            opacity: 0.96;
            transform: translateY(-1px);
        }

        .actions {
            margin: 20px 0;
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }

        .flash-message {
            display: none;
            margin-bottom: 18px;
            padding: 12px 16px;
            border-radius: 10px;
            background: #dcfce7;
            color: #166534;
            border: 1px solid #bbf7d0;
            font-weight: 600;
        }

        .mono {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }

        @media (max-width: 900px) {
            .kpi-grid {
                grid-template-columns: 1fr;
            }
        }
      </style>
    </head>
    <body>
      <div class="section-title">🛠️ Maintenance : Vue globale du parc</div>
      <div class="subtitle">Vue synthétique du dernier état connu de chaque équipement</div>

      <div id="flash-message" class="flash-message"></div>

      <div class="card">
        <div class="panel-title">Répartition des équipements par statut</div>
        <div id="kpis"
            hx-get="/maintenance/tdb/api/kpis"
            hx-trigger="load, every 10s"
            hx-swap="innerHTML">
        </div>
      </div>

      <div class="card">
        <div class="panel-title">Tableau récapitulatif des maintenances</div>
        <div class="info-note">
          Le tableau affiche au maximum les 5 dernières entrées visibles, après application des filtres.
        </div>

        <div id="filter"
             hx-get="/maintenance/tdb/api/id-prefix-filter"
             hx-trigger="load"
             hx-swap="innerHTML">
        </div>

        <div id="equipment-table"
             hx-get="/maintenance/tdb/api/equipment-table"
             hx-trigger="load, every 10s"
             hx-include="#prefix-select, #status-select"
             hx-swap="innerHTML">
          <div class="loading-box">Chargement…</div>
        </div>
      </div>

      <div class="actions">
        <a href="/maintenance/nouveau-ticket" class="btn-primary">
          ➕ Créer un nouveau ticket
        </a>

        <a href="/maintenance/interventions" class="btn-secondary">
          🛠️ Voir l'historique des interventions
        </a>
      </div>

      <script>
        document.body.addEventListener("htmx:afterRequest", function(event) {
          const elt = event.detail.elt;

          if (elt && elt.matches(".btn-delete") && event.detail.successful) {
            const equipmentName = elt.getAttribute("data-equipment-name") || "cet équipement";

            const flash = document.getElementById("flash-message");
            flash.textContent = "Suppression effectuée avec succès pour " + equipmentName + ".";
            flash.style.display = "block";

            htmx.ajax("GET", "/maintenance/tdb/api/equipment-table", {
              target: "#equipment-table",
              swap: "innerHTML",
              values: {
                prefix: document.getElementById("prefix-select")?.value || "",
                status: document.getElementById("status-select")?.value || ""
              }
            });

            htmx.ajax("GET", "/maintenance/tdb/api/kpis", {
              target: "#kpis",
              swap: "innerHTML"
            });

            setTimeout(() => {
              flash.style.display = "none";
            }, 3000);
          }
        });
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.get("/api/equipment-table", response_class=HTMLResponse)
async def equipment_table(
    prefix: str = "",
    status: str = "",
    db: Session = Depends(get_db),
):
    """
    Construit le tableau du TDB.

    Important :
    - le TDB n'affiche qu'une seule ligne par équipement : la plus récente
    - le service limite déjà le résultat aux 5 dernières entrées visibles
    - la suppression utilise le vrai `id` de la ligne dans la table maintenance
    """
    rows = services.get_equipment_events(db, prefix, status)

    trs = ""
    for r in rows:
        row_class = ""

        if r["statut"] == "Terminé":
            row_class = "status-termine"
        elif r["statut"] == "En cours":
            row_class = "status-encours"
        elif r["statut"] == "En attente":
            row_class = "status-attente"

        equipment_name = r["nom_equipement"] or r["id_equipement"]

        delete_btn = f"""
        <button
          class="btn-delete"
          data-equipment-name="{equipment_name}"
          hx-delete="/maintenance/tickets/{r['id']}"
          hx-confirm="Voulez-vous vraiment supprimer l’équipement {equipment_name} ?"
        >
          Supprimer
        </button>
        """

        trs += f"""
        <tr class="{row_class}">
          <td class="mono">{r["id_equipement"]}</td>
          <td>{r["nom_equipement"] or ""}</td>
          <td>{r["statut"] or ""}</td>
          <td>{r["date_creation"] or ""}</td>
          <td>{r["ticket_id"] if r["ticket_id"] is not None else ""}</td>
          <td>{r["description"] or ""}</td>
          <td>{delete_btn}</td>
        </tr>
        """

    html = f"""
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Nom</th>
            <th>Dernier statut</th>
            <th>Dernière MAJ</th>
            <th>Num_ticket</th>
            <th>Description</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {trs if trs else '<tr><td colspan="7">Aucune donnée maintenance.</td></tr>'}
        </tbody>
      </table>
    </div>
    """
    return HTMLResponse(content=html)


@router.get("/api/kpis", response_class=HTMLResponse)
async def kpis(db: Session = Depends(get_db)):
    """
    Retourne les KPI du tableau de bord :
    - terminés
    - en cours
    - en attente
    """
    data = services.get_kpis(db)

    html = f"""
    <div class="kpi-grid">
        <div class="kpi-card kpi-termine">
            <div class="kpi-number">{data["termines"]}</div>
            <div class="kpi-label">Terminés</div>
        </div>

        <div class="kpi-card kpi-encours">
            <div class="kpi-number">{data["encours"]}</div>
            <div class="kpi-label">En cours</div>
        </div>

        <div class="kpi-card kpi-attente">
            <div class="kpi-number">{data["attente"]}</div>
            <div class="kpi-label">En attente</div>
        </div>
    </div>
    """
    return HTMLResponse(content=html)


@router.get("/api/id-prefix-filter", response_class=HTMLResponse)
async def id_prefix_filter(db: Session = Depends(get_db)):
    """
    Construit les filtres du TDB :
    - filtre par préfixe d'équipement
    - filtre par statut
    """
    prefixes = services.get_id_prefixes(db)

    options = '<option value="">Tous</option>'
    for p in prefixes:
        options += f'<option value="{p}">{p}</option>'

    html = f"""
    <div class="filter-bar">
        <div class="field">
            <label for="prefix-select">Filtre ID</label>
            <select id="prefix-select"
                    name="prefix"
                    hx-preserve="true"
                    hx-get="/maintenance/tdb/api/equipment-table"
                    hx-trigger="change"
                    hx-target="#equipment-table"
                    hx-include="#prefix-select, #status-select">
                {options}
            </select>
        </div>

        <div class="field">
            <label for="status-select">Filtre statut</label>
            <select id="status-select"
                    name="status"
                    hx-preserve="true"
                    hx-get="/maintenance/tdb/api/equipment-table"
                    hx-trigger="change"
                    hx-target="#equipment-table"
                    hx-include="#prefix-select, #status-select">
                <option value="">Tous</option>
                <option value="Terminé">Vert - Terminé</option>
                <option value="En cours">Orange - En cours</option>
                <option value="En attente">Rouge - En attente</option>
            </select>
        </div>
    </div>
    """

    return HTMLResponse(content=html)