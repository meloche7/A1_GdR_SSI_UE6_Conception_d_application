from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from si_barrage.db import get_db

from . import services
from .models import MaintenanceTicket

router = APIRouter()


def _html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


@router.get("/interventions", response_class=HTMLResponse)
def page_interventions(db: Session = Depends(get_db)):
    """
    Page principale de la Feature 3.

    On lit maintenant les équipements depuis la table `maintenance`
    via le modèle `MaintenanceTicket`, conformément à la consigne du prof.
    """
    rows = (
        db.query(MaintenanceTicket.id_equipement)
        .filter(MaintenanceTicket.id_equipement.isnot(None))
        .distinct()
        .order_by(MaintenanceTicket.id_equipement)
        .all()
    )
    equipements = [r[0] for r in rows if r and r[0]]

    options = "\n".join(
        [
            f'<option value="{_html_escape(e)}">{_html_escape(e)}</option>'
            for e in equipements
        ]
    )

    html = f"""
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Maintenance • Historique des interventions</title>

  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.14/dist/full.min.css" rel="stylesheet" type="text/css" />
</head>

<body class="bg-base-200 min-h-screen">
  <div class="max-w-7xl mx-auto p-6">

    <div class="flex flex-col gap-2 mb-6">
      <div class="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 class="text-3xl font-bold">Maintenance</h1>
          <p class="text-base-content/70">Historique & analyse des interventions par équipement</p>
        </div>
      </div>
    </div>

    <div class="card bg-base-100 shadow-xl mb-6">
      <div class="card-body gap-5">

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <label class="form-control w-full">
            <div class="label"><span class="label-text font-semibold">Équipement</span></div>
            <select id="eq" class="select select-bordered w-full">
              <option value="" selected>-- choisir --</option>
              {options}
            </select>
          </label>

          <label class="form-control w-full">
            <div class="label"><span class="label-text font-semibold">Pagination</span></div>
            <div class="join w-full">
              <button class="btn join-item btn-outline" onclick="prevPage()">◀</button>
              <div class="join-item w-full">
                <input id="limit" type="number" class="input input-bordered w-full" min="1" max="200" value="20" />
              </div>
              <button class="btn join-item btn-outline" onclick="nextPage()">▶</button>
            </div>
            <div class="label"><span class="label-text-alt text-base-content/60">limit (par page) • offset auto</span></div>
          </label>

          <div class="flex items-end">
            <button class="btn btn-primary w-full" onclick="loadList(true)">
              Charger l'historique
            </button>
          </div>
        </div>

        <div class="divider my-0"></div>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <label class="form-control w-full">
            <div class="label"><span class="label-text font-semibold">Top N</span></div>
            <input id="topn" type="number" class="input input-bordered w-full" min="1" max="50" value="5"/>
          </label>

          <label class="form-control w-full">
            <div class="label"><span class="label-text font-semibold">start_date</span></div>
            <input id="start" type="text" class="input input-bordered w-full" placeholder="YYYY-MM-DD"/>
          </label>

          <label class="form-control w-full">
            <div class="label"><span class="label-text font-semibold">end_date</span></div>
            <input id="end" type="text" class="input input-bordered w-full" placeholder="YYYY-MM-DD"/>
          </label>

          <div class="flex items-end">
            <button class="btn btn-secondary w-full" onclick="loadAnalyse()">
              Analyser
            </button>
          </div>
        </div>

        <div id="toast" class="hidden alert mt-2"></div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

      <div class="card bg-base-100 shadow-xl lg:col-span-2">
        <div class="card-body">
          <div class="flex items-center justify-between flex-wrap gap-2">
            <h2 class="card-title">Historique</h2>
            <div class="text-sm text-base-content/60">
              offset: <span id="offsetLabel">0</span>
            </div>
          </div>

          <div id="list" class="mt-2">
            <div class="text-base-content/60">Choisis un équipement puis clique “Charger l’historique”.</div>
          </div>

          <div class="flex gap-2 justify-end mt-4">
            <button class="btn btn-outline btn-sm" onclick="prevPage()">Précédent</button>
            <button class="btn btn-outline btn-sm" onclick="nextPage()">Suivant</button>
          </div>
        </div>
      </div>

      <div class="flex flex-col gap-6">

        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <h2 class="card-title">Détail</h2>
            <div id="detail" class="text-base-content/60">
              Clique sur “Voir” dans le tableau.
            </div>
          </div>
        </div>

        <div class="card bg-base-100 shadow-xl">
          <div class="card-body">
            <h2 class="card-title">Analyse</h2>
            <div id="analyse" class="text-base-content/60">
              Lance une analyse (Top N + dates optionnelles).
            </div>
          </div>
        </div>

      </div>
    </div>

  </div>

<script>
let offset = 0;

function toast(kind, msg) {{
  const el = document.getElementById('toast');
  el.className = "alert mt-2";
  el.classList.remove("hidden");
  el.classList.remove("alert-success", "alert-info", "alert-warning", "alert-error");

  if (kind === "success") el.classList.add("alert-success");
  else if (kind === "warning") el.classList.add("alert-warning");
  else if (kind === "error") el.classList.add("alert-error");
  else el.classList.add("alert-info");

  el.innerHTML = `<span>${{msg}}</span>`;
  setTimeout(() => el.classList.add("hidden"), 4500);
}}

function getEq() {{
  const eq = document.getElementById('eq').value;
  return (eq || "").trim();
}}

function getLimit() {{
  const v = parseInt(document.getElementById('limit').value || "20", 10);
  if (isNaN(v) || v < 1) return 20;
  return Math.min(v, 200);
}}

async function loadList(resetOffset) {{
  const eq = getEq();
  if (!eq) {{
    toast("warning", "Choisis un équipement.");
    return;
  }}
  if (resetOffset) offset = 0;

  document.getElementById('offsetLabel').textContent = offset;
  document.getElementById('detail').innerHTML = `<span class="text-base-content/60">Clique sur “Voir” dans le tableau.</span>`;
  document.getElementById('analyse').innerHTML = `<span class="text-base-content/60">Lance une analyse (Top N + dates optionnelles).</span>`;

  const limit = getLimit();
  const url = `/maintenance/equipements/${{encodeURIComponent(eq)}}/interventions/list?limit=${{limit}}&offset=${{offset}}`;

  document.getElementById('list').innerHTML = `
    <div class="flex items-center gap-3">
      <span class="loading loading-spinner loading-md"></span>
      <span class="text-base-content/60">Chargement…</span>
    </div>
  `;

  const res = await fetch(url);
  const txt = await res.text();
  document.getElementById('list').innerHTML = txt;

  if (!res.ok) {{
    toast("error", "Erreur lors du chargement (voir message).");
  }}
}}

function nextPage() {{
  offset += getLimit();
  loadList(false);
}}

function prevPage() {{
  offset = Math.max(0, offset - getLimit());
  loadList(false);
}}

async function loadDetail(id) {{
  const res = await fetch(`/maintenance/interventions/${{id}}/detail`);
  document.getElementById('detail').innerHTML = await res.text();
}}

async function loadAnalyse() {{
  const eq = getEq();
  if (!eq) {{
    toast("warning", "Choisis un équipement avant l'analyse.");
    return;
  }}

  const topn = parseInt(document.getElementById('topn').value || "5", 10) || 5;
  const start = (document.getElementById('start').value || "").trim();
  const end = (document.getElementById('end').value || "").trim();

  const qs = new URLSearchParams();
  qs.set("top_n", String(Math.min(Math.max(topn, 1), 50)));
  if (start) qs.set("start_date", start);
  if (end) qs.set("end_date", end);

  document.getElementById('analyse').innerHTML = `
    <div class="flex items-center gap-3">
      <span class="loading loading-spinner loading-md"></span>
      <span class="text-base-content/60">Analyse…</span>
    </div>
  `;

  const res = await fetch(`/maintenance/equipements/${{encodeURIComponent(eq)}}/interventions/analyse?` + qs.toString());
  document.getElementById('analyse').innerHTML = await res.text();

  if (!res.ok) {{
    toast("error", "Erreur analyse (dates invalides ?).");
  }}
}}
</script>

</body>
</html>
"""
    return html


@router.get(
    "/equipements/{id_equipement}/interventions/list",
    response_class=HTMLResponse,
)
def page_interventions_list(
    id_equipement: str,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    if not services.equipment_exists(db, id_equipement):
        return f"""
<div class="alert alert-error">
  <span><b>Équipement inconnu:</b> <code>{_html_escape(id_equipement)}</code></span>
</div>
"""

    rows = services.get_interventions(db, id_equipement, limit=limit, offset=offset)

    # On masque les lignes supprimées côté affichage si jamais elles remontent
    rows = [it for it in rows if it.statut != "Supprimé"]

    if not rows:
        return f"""
<div class="alert alert-info">
  <span>Aucune intervention pour <code>{_html_escape(id_equipement)}</code>.</span>
</div>
"""

    trs = []
    for it in rows:
        problem = it.description or ""
        date_value = it.date_intervention or it.date_creation or ""
        intervenant_value = it.intervenant or ""

        trs.append(f"""
<tr class="hover">
  <td class="font-mono">{it.id}</td>
  <td>{_html_escape(str(date_value))}</td>
  <td>{_html_escape(intervenant_value)}</td>
  <td>{_html_escape(problem)}</td>
  <td class="text-right">
    <button class="btn btn-xs btn-outline" onclick="loadDetail({it.id})">Voir</button>
  </td>
</tr>
""")

    return f"""
<div class="overflow-x-auto">
  <table class="table table-zebra">
    <thead>
      <tr>
        <th>ID</th>
        <th>Date</th>
        <th>Intervenant</th>
        <th>Problème</th>
        <th class="text-right">Action</th>
      </tr>
    </thead>
    <tbody>
      {"".join(trs)}
    </tbody>
  </table>
</div>
<div class="mt-3 text-sm text-base-content/60">
  Équipement: <code>{_html_escape(id_equipement)}</code> • limit={limit} • offset={offset}
</div>
"""


@router.get("/interventions/{intervention_id}/detail", response_class=HTMLResponse)
def page_intervention_detail(intervention_id: int, db: Session = Depends(get_db)):
    it = services.get_intervention_by_id(db, intervention_id)
    if not it:
        return f"""
<div class="alert alert-error">
  <span><b>Intervention introuvable:</b> {intervention_id}</span>
</div>
"""

    def v(x):
        return "" if x is None else _html_escape(str(x))

    problem = it.description
    date_value = it.date_intervention or it.date_creation

    return f"""
<div class="grid grid-cols-1 gap-2 text-sm">
  <div class="flex justify-between"><span class="text-base-content/60">ID</span><span class="font-mono">{v(it.id)}</span></div>
  <div class="flex justify-between"><span class="text-base-content/60">Équipement</span><span class="font-mono">{v(it.id_equipement)}</span></div>
  <div class="flex justify-between"><span class="text-base-content/60">Date</span><span>{v(date_value)}</span></div>
  <div class="flex justify-between"><span class="text-base-content/60">Intervenant</span><span>{v(it.intervenant)}</span></div>

  <div class="divider my-1"></div>

  <div><span class="text-base-content/60">Problème</span><div class="font-semibold">{v(problem)}</div></div>
  <div><span class="text-base-content/60">Solution</span><div>{v(it.solution)}</div></div>

  <div class="divider my-1"></div>

  <div class="grid grid-cols-2 gap-2">
    <div class="flex justify-between"><span class="text-base-content/60">Ticket</span><span>{v(it.ticket_id)}</span></div>
    <div class="flex justify-between"><span class="text-base-content/60">Statut</span><span>{v(it.statut)}</span></div>
    <div class="flex justify-between"><span class="text-base-content/60">Durée</span><span>{v(it.duree_minutes)}</span></div>
    <div class="flex justify-between"><span class="text-base-content/60">Coût</span><span>{v(it.cout)}</span></div>
  </div>

  <div><span class="text-base-content/60">Pièces changées</span><div>{v(it.pieces_changees)}</div></div>
</div>
"""


@router.get(
    "/equipements/{id_equipement}/interventions/analyse",
    response_class=HTMLResponse,
)
def page_interventions_analyse(
    id_equipement: str,
    top_n: int = Query(5, ge=1, le=50),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    if not services.equipment_exists(db, id_equipement):
        return f"""
<div class="alert alert-error">
  <span><b>Équipement inconnu:</b> <code>{_html_escape(id_equipement)}</code></span>
</div>
"""

    for label, value in [("start_date", start_date), ("end_date", end_date)]:
        if value is not None:
            try:
                date.fromisoformat(value)
            except Exception:
                return f"""
<div class="alert alert-error">
  <span><b>Erreur:</b> {label} doit être au format ISO YYYY-MM-DD</span>
</div>
"""

    total, top, periode = services.analyse_recurrent_breakdowns(
        db,
        id_equipement,
        top_n=top_n,
        start_date=start_date,
        end_date=end_date,
    )

    if not top:
        return f"""
<div class="alert alert-info">
  <span>Aucune donnée d'analyse pour <code>{_html_escape(id_equipement)}</code>.</span>
</div>
"""

    items = "\n".join(
        [
            f"""
<li class="py-2">
  <div class="font-semibold">{_html_escape(t["probleme"])}</div>
  <div class="text-sm text-base-content/70">
    {t["occurrences"]} occurrence(s) • {t["premiere_date"]} → {t["derniere_date"]}
  </div>
</li>
"""
            for t in top
        ]
    )

    if periode:
        periode_txt = _html_escape(str(periode))
    else:
        periode_txt = "toutes dates"

    return f"""
<div class="flex flex-wrap gap-2 mb-3">
  <div class="badge badge-neutral">Équipement: <span class="ml-1 font-mono">{_html_escape(id_equipement)}</span></div>
  <div class="badge badge-outline">Total: {total}</div>
  <div class="badge badge-outline">Période: {periode_txt}</div>
  <div class="badge badge-outline">Top N: {top_n}</div>
</div>

<ul class="divide-y">
  {items}
</ul>
"""