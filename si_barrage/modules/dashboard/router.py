# Endpoints de l'API pour le dashboard
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard_page():
    """
    Page principale du dashboard météo avec HTMX.
    """
    return "Coucou, c'est le dashboard !"
