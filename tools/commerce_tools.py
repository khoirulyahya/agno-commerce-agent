"""
Tools Transaksi & Layanan Gaming AgnoCommerce ID
Fungsi-fungsi Python ini otomatis diubah oleh Agno menjadi Function Tools yang bisa dipanggil oleh AI Agent.
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

# Mock Database Sementara (Di production diganti PostgreSQL / MySQL / MongoDB)
DATABASE_CATALOG = {
    "mobile_legends": {
        "name": "Mobile Legends: Bang Bang",
        "packages": [
            {"sku": "ML-86", "name": "86 Diamonds", "price": 21000, "promo": True},
            {"sku": "ML-172", "name": "172 Diamonds", "price": 41500, "promo": False},
            {"sku": "ML-257", "name": "257 Diamonds", "price": 62000, "promo": True},
            {"sku": "ML-706", "name": "706 Diamonds", "price": 168000, "promo": False},
            {"sku": "ML-PASS-WP", "name": "Weekly Diamond Pass (WDP)", "price": 27500, "promo": True},
            {"sku": "ML-TWILIGHT", "name": "Twilight Pass", "price": 145000, "promo": False},
        ]
    },
    "free_fire": {
        "name": "Free Fire",
        "packages": [
            {"sku": "FF-70", "name": "70 Diamonds", "price": 9500, "promo": False},
            {"sku": "FF-140", "name": "140 Diamonds", "price": 19000, "promo": True},
            {"sku": "FF-355", "name": "355 Diamonds", "price": 47500, "promo": False},
            {"sku": "FF-720", "name": "720 Diamonds", "price": 95000, "promo": True},
            {"sku": "FF-MEMBERSHIP-W", "name": "Membership Mingguan", "price": 29000, "promo": True},
        ]
    },
    "roblox": {
        "name": "Roblox Robux",
        "packages": [
            {"sku": "RBX-80", "name": "80 Robux", "price": 15000, "promo": False},
            {"sku": "RBX-400", "name": "400 Robux", "price": 75000, "promo": True},
            {"sku": "RBX-800", "name": "800 Robux", "price": 149000, "promo": False},
            {"sku": "RBX-1700", "name": "1700 Robux", "price": 299000, "promo": True},
        ]
    },
    "honor_of_kings": {
        "name": "Honor of Kings (HOK)",
        "packages": [
            {"sku": "HOK-80", "name": "80 Tokens", "price": 14000, "promo": True},
            {"sku": "HOK-240", "name": "240 Tokens", "price": 42000, "promo": False},
            {"sku": "HOK-400", "name": "400 Tokens", "price": 69000, "promo": True},
        ]
    }
}

# Mock Database Orders
ORDERS_DB: Dict[str, Dict[str, Any]] = {
    "INV-9921": {
        "invoice_id": "INV-9921",
        "game": "Mobile Legends",
        "user_id": "12345678",
        "zone_id": "2026",
        "nickname": "ProPlayerSlayer",
        "package": "Weekly Diamond Pass (WDP)",
        "amount": 27500,
        "payment_method": "QRIS Instant",
        "status": "SUCCESS",
        "created_at": "2026-09-23 14:15:00",
        "notes": "Diamond sudah otomatis masuk ke akun game."
    }
}

# Mock Jual Beli Akun
ACCOUNTS_FOR_SALE = [
    {
        "account_id": "ACC-ML-01",
        "title": "Akun MLBB Sultan All Collector + 2 Legend (Gusion, Lesley)",
        "price": 850000,
        "rank": "Mythical Glory 75+",
        "total_heroes": 124,
        "total_skins": 340,
        "favorite_heroes": ["Gusion", "Fanny", "Chou"],
        "status": "AVAILABLE"
    },
    {
        "account_id": "ACC-ML-02",
        "title": "Akun MLBB Smurf Mantap Siap Ranked",
        "price": 175000,
        "rank": "Epic II",
        "total_heroes": 78,
        "total_skins": 85,
        "favorite_heroes": ["Hayabusa", "Lancelot", "Ling"],
        "status": "AVAILABLE"
    }
]


def get_game_catalog(game_name: Optional[str] = None) -> Dict[str, Any]:
    """Mengambil daftar katalog game dan harga paket top-up yang tersedia di AgnoCommerce.
    
    Args:
        game_name: Nama game opsional ('mobile_legends', 'free_fire', 'roblox', 'honor_of_kings'). Jika kosong, mengembalikan semua game.
    """
    if game_name:
        slug = game_name.lower().replace(" ", "_")
        if slug in DATABASE_CATALOG:
            return {"status": "success", "game": slug, "data": DATABASE_CATALOG[slug]}
        return {"status": "error", "message": f"Game '{game_name}' tidak ditemukan. Game yang didukung: {list(DATABASE_CATALOG.keys())}"}
    
    return {"status": "success", "all_games": DATABASE_CATALOG}


def validate_game_account(game: str, user_id: str, zone_id: Optional[str] = None) -> Dict[str, Any]:
    """Memvalidasi apakah User ID dan Zone ID akun game valid serta mengembalikan Nickname pemain.
    
    Args:
        game: Nama game (contoh: 'mobile_legends', 'free_fire', 'roblox')
        user_id: ID akun game user (contoh: '88392019')
        zone_id: Zone ID / Server ID (wajib untuk Mobile Legends, contoh: '2102')
    """
    game_clean = game.lower().strip()
    
    # Mocking Nickname lookup
    if "legend" in game_clean or "ml" in game_clean:
        if not zone_id:
            return {"status": "error", "message": "Untuk Mobile Legends, mohon sertakan Zone ID (4-5 digit di dalam kurung)."}
        mock_nick = f"JuraganML_{user_id[-4:]}"
    elif "fire" in game_clean or "ff" in game_clean:
        mock_nick = f"HeadshotMaster_{user_id[-3:]}"
    elif "roblox" in game_clean:
        mock_nick = f"RobloxBuilder_{user_id}"
    else:
        mock_nick = f"Player_{user_id[-4:]}"
        
    return {
        "status": "valid",
        "game": game,
        "user_id": user_id,
        "zone_id": zone_id or "Global",
        "nickname": mock_nick,
        "message": f"Akun valid! Nickname terdeteksi: **{mock_nick}**"
    }


def create_topup_order(
    game: str,
    user_id: str,
    zone_id: Optional[str],
    package_sku: str,
    payment_method: str = "QRIS"
) -> Dict[str, Any]:
    """Membuat invoice transaksi top up baru untuk customer dan menghasilkan instruksi pembayaran QRIS.
    
    Args:
        game: Nama game (contoh: 'mobile_legends')
        user_id: ID Akun game
        zone_id: Server / Zone ID (bisa kosong untuk FF/Roblox)
        package_sku: Kode SKU paket (contoh: 'ML-86', 'ML-PASS-WP', 'FF-140')
        payment_method: Metode pembayaran ('QRIS', 'BCA Virtual Account', 'GoPay', 'ShopeePay')
    """
    game_slug = game.lower().replace(" ", "_")
    
    # Cari paket
    selected_package = None
    if game_slug in DATABASE_CATALOG:
        for pkg in DATABASE_CATALOG[game_slug]["packages"]:
            if pkg["sku"].upper() == package_sku.upper() or package_sku.lower() in pkg["name"].lower():
                selected_package = pkg
                break
    
    if not selected_package:
        # Fallback default
        selected_package = {"sku": package_sku, "name": f"Paket {package_sku}", "price": 25000}
    
    invoice_id = f"INV-RP-{uuid.uuid4().hex[:6].upper()}"
    qris_mock_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=AgnoCommerce_{invoice_id}_{selected_package['price']}"
    
    order_data = {
        "invoice_id": invoice_id,
        "game": game,
        "user_id": user_id,
        "zone_id": zone_id or "-",
        "nickname": f"Juragan_{user_id[-4:]}",
        "package_name": selected_package["name"],
        "package_sku": selected_package["sku"],
        "total_amount": selected_package["price"],
        "payment_method": payment_method,
        "payment_qr_url": qris_mock_url,
        "status": "UNPAID",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "expired_in_minutes": 15,
        "pay_link": f"https://agno-commerce.com/pay/{invoice_id}"
    }
    
    ORDERS_DB[invoice_id] = order_data
    
    return {
        "status": "success",
        "message": f"Invoice {invoice_id} berhasil dibuat!",
        "order": order_data
    }


def check_order_status(invoice_id: str) -> Dict[str, Any]:
    """Memeriksa status pembayaran dan pengiriman paket top-up berdasarkan nomor Invoice.
    
    Args:
        invoice_id: Nomor invoice transaksi (contoh: 'INV-9921' atau 'INV-RP-XXXX')
    """
    inv_clean = invoice_id.strip().upper()
    if inv_clean in ORDERS_DB:
        return {
            "status": "found",
            "invoice": ORDERS_DB[inv_clean]
        }
    return {
        "status": "not_found",
        "message": f"Nomor invoice '{invoice_id}' tidak ditemukan di sistem database AgnoCommerce."
    }


def calculate_joki_price(current_rank: str, target_rank: str, current_stars: int = 0) -> Dict[str, Any]:
    """Menghitung estimasi biaya joki Mobile Legends dari rank saat ini ke rank tujuan.
    
    Args:
        current_rank: Rank sekarang (contoh: 'Grandmaster', 'Epic', 'Legend', 'Mythic')
        target_rank: Rank impian (contoh: 'Legend', 'Mythic', 'Mythical Glory')
        current_stars: Jumlah bintang saat ini di rank awal
    """
    rank_rate = {
        "master": 3000,
        "grandmaster": 4500,
        "epic": 6500,
        "legend": 9000,
        "mythic": 15000,
        "mythical honor": 20000,
        "mythical glory": 28000,
        "mythical immortal": 40000
    }
    
    c_clean = current_rank.lower().strip()
    t_clean = target_rank.lower().strip()
    
    price_estimasi = 85000
    if "epic" in c_clean and "mythic" in t_clean:
        price_estimasi = 135000
    elif "legend" in c_clean and "mythic" in t_clean:
        price_estimasi = 75000
    elif "grandmaster" in c_clean and "epic" in t_clean:
        price_estimasi = 50000
        
    return {
        "status": "success",
        "current_rank": current_rank,
        "target_rank": target_rank,
        "estimated_price": price_estimasi,
        "estimated_time": "1x24 Jam (Pro Player Verified)",
        "garansi": "100% Aman & Anti Banned Garansi Winrate Naik"
    }


def search_mlbb_accounts(max_price: Optional[int] = None, favorite_hero: Optional[str] = None) -> Dict[str, Any]:
    """Mencari daftar akun Mobile Legends bergaransi yang sedang dijual di marketplace AgnoCommerce.
    
    Args:
        max_price: Batas harga maksimum dalam Rupiah (opsional)
        favorite_hero: Nama hero kesukaan (contoh: 'Gusion', 'Fanny', 'Chou')
    """
    results = []
    for acc in ACCOUNTS_FOR_SALE:
        if max_price and acc["price"] > max_price:
            continue
        if favorite_hero:
            heroes_lower = [h.lower() for h in acc["favorite_heroes"]]
            if favorite_hero.lower() not in heroes_lower:
                continue
        results.append(acc)
        
    return {
        "status": "success",
        "count": len(results),
        "accounts": results if results else ACCOUNTS_FOR_SALE
    }
