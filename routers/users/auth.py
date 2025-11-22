# 📍 routers/Users/auth.py
import logging
import asyncio
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.hash import bcrypt
from lib.supabase_client import supabase

router = APIRouter()
templates = Jinja2Templates(directory="templates")

logger = logging.getLogger("auth")
logger.setLevel(logging.INFO)


# ---------- REGISTER PAGE ----------
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html", {"request": request, "error": ""}
    )


@router.post("/register", response_class=HTMLResponse)
async def register_user(
    request: Request, email: str = Form(...), password: str = Form(...)
):
    logger.info(f"[REGISTER] Cek email: {email}")

    try:
        # Cek email di Supabase
        res = await asyncio.to_thread(
            lambda: supabase.table("Users").select("*").eq("email", email).execute()
        )
        logger.info(f"[REGISTER] Query cek email selesai. Found: {len(res.data)}")
    except Exception as e:
        logger.error(f"[REGISTER] ❌ Gagal akses Supabase saat cek email: {e}")
        return templates.TemplateResponse(
            "register.html", {"request": request, "error": "Gagal mengakses database"}
        )

    if res.data:
        logger.warning(f"[REGISTER] Email sudah terdaftar: {email}")
        return templates.TemplateResponse(
            "register.html", {"request": request, "error": "Email sudah terdaftar"}
        )

    # Hash password
    hashed = bcrypt.hash(password)
    logger.info(f"[REGISTER] Membuat user baru: {email}")

    try:
        await asyncio.to_thread(
            lambda: supabase.table("Users")
            .insert({"email": email, "password_hash": hashed, "is_active": True})
            .execute()
        )
        logger.info(f"[REGISTER] User berhasil dibuat: {email}")
    except Exception as e:
        logger.error(f"[REGISTER] ❌ Gagal menyimpan user: {e}")
        return templates.TemplateResponse(
            "register.html", {"request": request, "error": "Gagal menyimpan data"}
        )

    return RedirectResponse(url="/login", status_code=303)


# ---------- LOGIN PAGE ----------
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": ""})


@router.post("/login", response_class=HTMLResponse)
async def login_user(
    request: Request, email: str = Form(...), password: str = Form(...)
):
    logger.info(f"[LOGIN] User mencoba login: {email}")

    try:
        # Cek user di Supabase
        res = await asyncio.to_thread(
            lambda: supabase.table("Users").select("*").eq("email", email).execute()
        )
        logger.info(f"[LOGIN] Query login selesai. Found: {len(res.data)}")
    except Exception as e:
        logger.error(f"[LOGIN] ❌ Gagal akses Supabase saat login: {e}")
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Gagal mengakses database"}
        )

    if not res.data:
        logger.warning(f"[LOGIN] Email tidak ditemukan: {email}")
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Email atau password salah"}
        )

    # Verifikasi password
    if not bcrypt.verify(password, res.data[0]["password_hash"]):
        logger.warning(f"[LOGIN] Password salah untuk email: {email}")
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": "Email atau password salah"}
        )

    # Login OK
    logger.info(f"[LOGIN] User berhasil login: {email}")
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="user_id", value=str(res.data[0]["id"]))

    return response


# ---------- LOGOUT ----------
@router.get("/logout")
async def logout():
    logger.info("[LOGOUT] Menghapus cookie user_id")

    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("user_id")

    return response
