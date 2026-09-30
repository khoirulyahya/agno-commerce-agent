"""
MODULE 05: Vision-to-Action Agent (Foto Nota Kulakan ➡️ Otomatis Update Stok & Kas)
Jalankan: python tutorials/05_vision_to_action.py
"""
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from src.agent_factory import GeminiKeyPool

# ==========================================
# 1. DATABASE DUMMY TOKO
# ==========================================
STOK_DATABASE = {
    "Plastik PP Bening": 100,
    "Plastik Mika Tebal": 25,
    "Kresek Hitam Jumbo": 50
}

KAS_PENGELUARAN = []

# ==========================================
# 2. TOOLS TRANSAKSI & INVENTORI
# ==========================================
def tambah_stok_barang(nama_barang: str, qty: int, harga_satuan: int) -> str:
    """Menambah stok barang ke sistem inventori toko.
    
    Args:
        nama_barang: Nama produk plastik (contoh: 'Plastik Mika Tebal')
        qty: Jumlah kuantiti yang dibeli
        harga_satuan: Harga beli modal per satuan
    """
    stok_lama = STOK_DATABASE.get(nama_barang, 0)
    STOK_DATABASE[nama_barang] = stok_lama + qty
    return f"[INVENTORI UPDATE] Stok '{nama_barang}' bertambah +{qty}. Stok sekarang: {STOK_DATABASE[nama_barang]} unit. (Harga Beli: Rp {harga_satuan:,})"

def catat_pengeluaran_kas(nominal: int, nama_supplier: str, no_nota: str) -> str:
    """Mencatat pengeluaran uang kas toko untuk pembayaran kulakan ke supplier.
    
    Args:
        nominal: Total rupiah yang dibayarkan
        nama_supplier: Nama toko/pabrik supplier
        no_nota: Nomor faktur/nota supplier
    """
    record = {
        "no_nota": no_nota,
        "supplier": nama_supplier,
        "nominal": nominal,
        "status": "LUNAS"
    }
    KAS_PENGELUARAN.append(record)
    return f"[KAS UPDATE] Pengeluaran kas Rp {nominal:,} ke supplier '{nama_supplier}' (Nota #{no_nota}) berhasil dicatat!"

# ==========================================
# 3. SETUP AGENT DENGAN AUTO KEY ROTATION
# ==========================================
def run_vision_agent():
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
                    "Kamu adalah AI Asisten Gudang & Kasir Toko.",
                    "Tugasmu: Menganalisis nota/faktur kulakan dan mengeksekusi penambahan stok serta pencatatan kas keluar.",
                    "Panggil tool 'tambah_stok_barang' untuk setiap item barang yang dibeli.",
                    "Panggil tool 'catat_pengeluaran_kas' untuk total biaya yang tertera di nota.",
                    "Berikan laporan ringkas dan jelas kepada Bos Toko."
                ],
                tools=[tambah_stok_barang, catat_pengeluaran_kas],
                markdown=True
            )
            
            simulasi_nota = """
[FOTO NOTA SUPPLIER DARI BOS]
TOKO SUMBER BERKAH PLASTIK - SUKABUMI
No Nota: SB-2026-889
Tanggal: 28 September 2026

1. Plastik Mika Tebal    | 50 Roll  @ Rp 25.000 = Rp 1.250.000
2. Kresek Hitam Jumbo    | 20 Pack  @ Rp 15.000 = Rp   300.000
-----------------------------------------
TOTAL BAYAR: Rp 1.550.000 (LUNAS)
Tolong proses nota ini ke pembukuan dan stok toko!
"""
            print("--- 📸 SIMULASI BOS UPLOAD FOTO NOTA KULAKAN ---")
            print("Data awal stok:", STOK_DATABASE)
            print("\n🤖 AGENT PROSES NOTA...")
            res = agent.run(simulasi_nota)
            print("\n" + res.content)
            
            print("\n--- 📊 HASIL SETELAH AGENTIC ACTION BERJALAN ---")
            print("Stok Gudang Terkini:", json.dumps(STOK_DATABASE, indent=2))
            print("Log Kas Pengeluaran:", json.dumps(KAS_PENGELUARAN, indent=2))
            return
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower() or "503" in str(e):
                continue
            raise e

if __name__ == "__main__":
    run_vision_agent()
