# Crypto API Service

API service untuk manajemen dan pengiriman token crypto (ETH, USDT, BNB, SOL, dan lainnya) dengan FastAPI.

## 📦 Fitur

- **Ping API** – Mengecek status service.
- **Send Token** – Mengirim token crypto ke address lain.
- **Balance** – Mengecek saldo wallet.
- **Price** – Mendapatkan harga token terkini.
- **History** – Melihat riwayat transaksi.
- **Estimate Gas** – Perkiraan biaya gas untuk transaksi.
- **Tokens** – Daftar token yang tersedia.
- **Swap** – Melakukan swap token.
- **Token Info** – Detail informasi token.
- **Transaction Status** – Mengecek status transaksi.
- **Wallet Monitor** – Endpoint `/subscribe` dan `/unsubscribe` untuk mengaktifkan listener transaksi wallet. Mendukung Solana, Ethereum, dan bisa ditambah chain lain.


## ⚡ Teknologi

- Python 3.12+
- [FastAPI](https://fastapi.tiangolo.com/)
- Asynchronous API (async/await)
- Modular routers untuk setiap fitur crypto

## 🚀 Instalasi

1. Clone repo:

```bash
git clone https://github.com/1amkaizen/crypto-api-service.git
cd crypto-api-service
````

2. Buat virtual environment & install dependencies:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Jalankan server FastAPI:

```bash
uvicorn main:app --reload
```

atau

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

Server akan berjalan di `http://127.0.0.1:8000`.

## 📌 Endpoint

Semua endpoint berada di prefix `/api/v1/crypto`. Contoh:name

| Endpoint                         | Method | Deskripsi                        |
|----------------------------------|--------|----------------------------------|
| `/api/v1/crypto/ping`            | GET    | Cek status service               |
| `/api/v1/crypto/send`            | POST   | Kirim token ke address tertentu  |
| `/api/v1/crypto/balance`         | GET    | Cek saldo wallet                 |
| `/api/v1/crypto/price`           | GET    | Mendapatkan harga token terkini  |
| `/api/v1/crypto/history`         | GET    | Riwayat transaksi                |
| `/api/v1/crypto/estimate_gas`    | GET    | Perkiraan biaya gas transaksi    |
| `/api/v1/crypto/tokens`          | GET    | Daftar token tersedia            |
| `/api/v1/crypto/swap`            | POST   | Swap token                       |
| `/api/v1/crypto/token_info`      | GET    | Detail informasi token           |
| `/api/v1/crypto/tx_status`       | GET    | Status transaksi                 |
| `/api/v1/crypto/subscribe`       | POST   | Aktifkan listener transaksi wallet (Solana/Ethereum) |
| `/api/v1/crypto/unsubscribe`     | POST   | Hentikan listener transaksi wallet                   |

> Dokumentasi interaktif tersedia di `http://127.0.0.1:8000/docs` (Swagger UI) dan `http://127.0.0.1:8000/redoc` (ReDoc).  

Kalau mau, gue bisa sekalian bikin **contoh request/response JSON** untuk tiap endpoint biar README lebih lengkap dan langsung bisa dicoba. Mau gue tambahin juga?


## 📂 Struktur Folder

```
.
├─ main.pyname
├─ routers/
│  └─ crypto/
│     ├─ ping.py
│     ├─ send.py
│     ├─ balance.py
│     ├─ price.py
│     ├─ history.py
│     ├─ estimate_gas.py
│     ├─ tokens.py
│     ├─ swap.py
│     ├─ token_info.py
│     ├─ tx_status.py
│     └─ wallet_monitor.py
└─ requirements.txt
```

## 📝 Catatan

* Semua handler API bersifat asynchronous.
* Project ini cocok untuk wallet management dan automasi transaksi crypto.
* Pastikan environment variables (API keys, wallet private key, dll) sudah diatur sebelum menjalankan.

## 👨‍💻 Kontribusi

1. Fork repo ini.
2. Buat branch baru: `git checkout -b feature/your-feature`
3. Commit perubahan: `git commit -m "Add some feature"`
4. Push ke branch: `git push origin feature/your-feature`
5. Buat Pull Request.

## 📄 Lisensi

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/1amkaizen/crypto-api-service/blob/main/LICENSE)


