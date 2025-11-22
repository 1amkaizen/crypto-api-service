# 📍 routers/users/landing.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """
    Halaman landing page publik
    """
    return templates.TemplateResponse("landing.html", {"request": request})
