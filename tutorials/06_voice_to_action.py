"""
MODULE 06: Voice-to-Action Agent (Voice Note Tukang ➡️ Otomatis Buat Surat Jalan & Cek Stok)
Jalankan: python tutorials/06_voice_to_action.py

Studi Kasus Toko Bangunan:
Tukang / Mandor di proyek kirim Voice Note WhatsApp (bahasa santai/lisan):
"Halo bos, tolong kirim semen gresik 25 sak sama pasir pasang 2 pick-up ya ke proyek pak Joko jalan Merpati nomor 12."

AI Agent:
1. Mengekstrak item, kuantiti, nama pembeli, dan alamat kirim dari ucapan lisan.
2. Memanggil tool cek_ketersediaan_stok(barang, qty).
3. Memanggil tool buat_surat_jalan_pengiriman(nama_penerima, alamat, daftar_barang, armada).
"""
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from src.agent_factory import GeminiKeyPool

# Database Dummy Toko Bangunan
STOK_BAHAN_BANGUNAN = {
    "Semen Gresik 50kg": 80,
    "Semen Tiga Roda 50kg": 40,
    "Pasir Pasang (Pick-up)": 15,
    "Bata Ringan Hebel (Kubik)": 30,
    "Besi Beton 10mm": 200
}

SURAT_JALAN_LIST = []

def cek_ketersediaan_stok(nama_barang: str, qty_dibutuhkan: int) -> str:
    """Mengecek apakah stok bahan bangunan di gudang mencukupi untuk dikirim.
    
    Args:
        nama_barang: Nama bahan bangunan
        qty_dibutuhkan: Jumlah yang diminta pelanggan
    """
    for item, stok in STOK_BAHAN_BANGUNAN.items():
        if nama_barang.lower() in item.lower():
            if stok >= qty_dibutuhkan:
                return f"[STOK AMAN] '{item}' tersedia {stok} unit (Permintaan: {qty_dibutuhkan} unit terpenuhi)."
            else:
                return f"[STOK KURANG] '{item}' hanya tersisa {stok} unit (Permintaan: {qty_dibutuhkan} unit). Butuh konfirmasi bos."
    return f"[BARANG TIDAK ADA] '{nama_barang}' tidak terdaftar di katalog gudang."

def buat_surat_jalan_pengiriman(penerima: str, alamat: str, ringkasan_barang: str, tipe_armada: str) -> str:
    """Membuat dokumen Surat Jalan dan jadwal armada pengiriman barang ke lokasi proyek.
    
    Args:
        penerima: Nama pemesan / mandor proyek
        alamat: Alamat pengiriman
        ringkasan_barang: Daftar barang dan jumlahnya
        tipe_armada: Kendaraan yang disiapkan ('Pick-up', 'Truk Engkel', 'Motor Roda Tiga')
    """
    nomor_sj = f"SJ-TB-{len(SURAT_JALAN_LIST) + 101}"
    sj_data = {
        "nomor_surat_jalan": nomor_sj,
        "penerima": penerima,
        "alamat": alamat,
        "barang": ringkasan_barang,
        "armada": tipe_armada,
        "status": "SIAP_BERANGKAT"
    }
    SURAT_JALAN_LIST.append(sj_data)
    return f"[SURAT JALAN TERBIT] #{nomor_sj} berhasil dibuat untuk {penerima} ({alamat}). Armada: {tipe_armada}."

def run_voice_agent():
    keys = GeminiKeyPool.get_keys()
    
    for key in keys:
        try:
            model = OpenAIChat(
                id="models/gemini-flash-latest",
                api_key=key,
                base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
            )
            agent = Agent(
                model=model,
                instructions=[
                    "Kamu adalah AI Admin Pengiriman & Logistik Toko Bangunan.",
                    "Tugasmu: Mendengarkan / membaca pesan suara dari mandor/pelanggan.",
                    "Cek ketersediaan stok setiap barang yang diminta menggunakan 'cek_ketersediaan_stok'.",
                    "Jika stok aman, buat surat jalan menggunakan 'buat_surat_jalan_pengiriman'.",
                    "Pilih tipe armada yang masuk akal (contoh: semen/pasir banyak pakai Pick-up/Truk).",
                    "Balas ke mandor dengan bahasa WhatsApp yang ramah, jelas, dan profesional."
                ],
                tools=[cek_ketersediaan_stok, buat_surat_jalan_pengiriman],
                markdown=True
            )
            
            # Simulasi hasil audio transkrip dari Voice Note WA mandor
            simulasi_voice_note = """
[TRANSKRIP PESAN SUARA WA DARI MANDOR JOKO]
"Halo assalamualaikum bos, tolong kirim semen gresik 25 sak sama pasir pasang 2 pick-up ya bos ke proyek pak Joko di jalan Merpati nomor 12 dekat pos ronda. Tolong kirim pakai pick-up sebelum jam 2 siang ya bos, makasih."
"""
            print("--- 🎙️ SIMULASI TERIMA VOICE NOTE DARI MANDOR ---")
            print("Isi rekaman suara:", simulasi_voice_note.strip())
            print("\n🤖 AGENT MEMPROSES VOICE ORDER...")
            res = agent.run(simulasi_voice_note)
            print("\n" + res.content)
            
            print("\n--- 📋 SURAT JALAN YANG OTOMATIS TERCETAK DI GUDANG ---")
            print(json.dumps(SURAT_JALAN_LIST, indent=2))
            return
        except Exception as e:
            if any(term in str(e).lower() for term in ["429", "503", "quota", "rate", "demand"]):
                continue
            raise e

if __name__ == "__main__":
    run_voice_agent()
