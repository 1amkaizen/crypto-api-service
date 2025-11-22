# 📍 File: lib/supabase_client.py

import os
import logging
import socket
from dotenv import load_dotenv
from supabase import create_client, Client

# =========================
# Load environment dari .env
# =========================
load_dotenv()

# =========================
# Setup Logging
# =========================
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

logger.info("🔧 [Supabase] Inisialisasi client...")

# =========================
# Ambil ENV
# =========================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# =========================
# Validasi ENV
# =========================
if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("❌ ENV Supabase belum lengkap (SUPABASE_URL / SUPABASE_KEY kosong)")
    raise RuntimeError(
        "❌ ENV Supabase belum lengkap (SUPABASE_URL / SUPABASE_KEY kosong)"
    )

if not SUPABASE_URL.startswith("https://"):
    logger.warning(f"⚠️ SUPABASE_URL tidak valid: {SUPABASE_URL}")

logger.info(f"🔍 SUPABASE_URL terbaca: {SUPABASE_URL}")
logger.info("🔍 Mengecek resolusi DNS Supabase...")

# =========================
# Cek apakah domain Supabase bisa di-resolve (debug DNS error)
# =========================
try:
    hostname = SUPABASE_URL.replace("https://", "").replace("/", "")
    ip = socket.gethostbyname(hostname)
    logger.info(f"🌐 DNS OK → {hostname} terhubung ke IP {ip}")
except Exception as dns_err:
    logger.error(f"❌ Gagal resolve DNS untuk {SUPABASE_URL}: {dns_err}")
    raise RuntimeError(f"❌ DNS error saat mengakses Supabase: {dns_err}")

# =========================
# Buat client Supabase
# =========================
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("✅ Berhasil menghubungkan ke Supabase")
except Exception as e:
    logger.exception(f"❌ Gagal membuat client Supabase: {e}")
    raise RuntimeError(f"❌ Gagal membuat client Supabase: {e}")


def generate_public_url(bucket_name: str, file_path: str) -> str:
    """
    Generate URL publik untuk file di bucket Supabase.
    """
    return f"{SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{file_path}"
