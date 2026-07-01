# -*- coding: utf-8 -*-
"""
Integrasi Google Sheets untuk UAS Ekonomi UMKM dua kelas (K3 dan K4).
Setiap kelas menyimpan ke spreadsheet berbeda (k3_spreadsheet_key / k4_spreadsheet_key).

Kredensial Service Account di st.secrets["gcp_service_account"].
Jika belum diatur, fungsi mengembalikan status offline agar aplikasi tetap jalan.
"""

from datetime import datetime

try:
    import gspread
    from google.oauth2.service_account import Credentials
    _GSPREAD_ADA = True
except Exception:
    _GSPREAD_ADA = False

import streamlit as st

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
_TAB = "Hasil_UAS"
_HEADER = ["Waktu", "Kelas", "Nama", "NPM", "Nilai", "Benar", "Total",
           "Pindah_Tab", "Durasi_Detik", "Catatan"]


def _client():
    if not _GSPREAD_ADA or "gcp_service_account" not in st.secrets:
        return None
    try:
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=_SCOPES
        )
        return gspread.authorize(creds)
    except Exception:
        return None


def _normalisasi_key(nilai):
    """Menerima kunci polos ATAU URL lengkap Google Sheet, mengembalikan kunci saja."""
    nilai = str(nilai).strip()
    if "/d/" in nilai:
        nilai = nilai.split("/d/", 1)[1].split("/", 1)[0]
    return nilai


def _key_kelas(kelas):
    k = str(kelas).strip().upper()
    kunci = "k3_spreadsheet_key" if k == "K3" else "k4_spreadsheet_key"
    return _normalisasi_key(st.secrets.get(kunci, ""))


def _buka_worksheet(kelas):
    gc = _client()
    key = _key_kelas(kelas)
    if gc is None or not key:
        return None
    try:
        sh = gc.open_by_key(key)
    except Exception:
        return None
    try:
        ws = sh.worksheet(_TAB)
    except Exception:
        ws = sh.add_worksheet(title=_TAB, rows=1000, cols=len(_HEADER))
        ws.append_row(_HEADER)
    try:
        if ws.row_count == 0 or not ws.acell("A1").value:
            ws.append_row(_HEADER)
    except Exception:
        pass
    return ws


def npm_sudah_mengerjakan(npm, kelas):
    """Cek apakah NPM sudah pernah mengerjakan di kelas ini (satu NPM satu kesempatan)."""
    ws = _buka_worksheet(kelas)
    if ws is None:
        return False
    try:
        kolom_npm = ws.col_values(4)  # kolom D = NPM
        return str(npm).strip() in [x.strip() for x in kolom_npm]
    except Exception:
        return False


def simpan_hasil(nama, npm, nilai, benar, total, kelas,
                 pindah_tab=0, durasi_detik=0, catatan=""):
    """Menyimpan satu baris hasil ke Google Sheet kelas yang sesuai."""
    ws = _buka_worksheet(kelas)
    baris = [
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        str(kelas).strip().upper(),
        str(nama).strip(), str(npm).strip(),
        nilai, benar, total, pindah_tab, durasi_detik, catatan,
    ]
    if ws is None:
        return False, "Google Sheet belum tersambung. Hasil belum tersimpan online."
    try:
        ws.append_row(baris, value_input_option="USER_ENTERED")
        return True, f"Hasil tersimpan ke Google Sheet kelas {str(kelas).upper()}."
    except Exception as e:
        return False, f"Gagal menyimpan: {e}"
