"""
Tools Transaksi & Layanan Toko Buku Digital — LibraBot
Fungsi-fungsi Python ini otomatis diubah oleh Agno menjadi Function Tools yang bisa dipanggil oleh AI Agent.
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

# Mock Database Catalog Buku (Di production diganti PostgreSQL / Elasticsearch)
DATABASE_CATALOG = {
    "programming": {
        "name": "Programming & Tech",
        "books": [
            {"sku": "PRG-001", "title": "Clean Code", "author": "Robert C. Martin", "price": 125000, "format": "PDF+EPUB", "promo": True},
            {"sku": "PRG-002", "title": "The Pragmatic Programmer", "author": "Hunt & Thomas", "price": 110000, "format": "PDF", "promo": False},
            {"sku": "PRG-003", "title": "Python Crash Course", "author": "Eric Matthes", "price": 95000, "format": "PDF+EPUB", "promo": True},
            {"sku": "PRG-004", "title": "Designing Data-Intensive Applications", "author": "Martin Kleppmann", "price": 145000, "format": "PDF", "promo": False},
            {"sku": "PRG-005", "title": "System Design Interview", "author": "Alex Xu", "price": 130000, "format": "PDF+EPUB", "promo": True},
        ]
    },
    "business": {
        "name": "Bisnis & Entrepreneurship",
        "books": [
            {"sku": "BIZ-001", "title": "Zero to One", "author": "Peter Thiel", "price": 89000, "format": "PDF+EPUB", "promo": True},
            {"sku": "BIZ-002", "title": "The Lean Startup", "author": "Eric Ries", "price": 85000, "format": "PDF", "promo": False},
            {"sku": "BIZ-003", "title": "Good to Great", "author": "Jim Collins", "price": 92000, "format": "EPUB", "promo": False},
            {"sku": "BIZ-004", "title": "Atomic Habits", "author": "James Clear", "price": 79000, "format": "PDF+EPUB", "promo": True},
            {"sku": "BIZ-005", "title": "The Psychology of Money", "author": "Morgan Housel", "price": 75000, "format": "PDF+EPUB", "promo": True},
        ]
    },
    "self_development": {
        "name": "Pengembangan Diri",
        "books": [
            {"sku": "DEV-001", "title": "Deep Work", "author": "Cal Newport", "price": 82000, "format": "PDF+EPUB", "promo": False},
            {"sku": "DEV-002", "title": "Ikigai", "author": "Héctor García", "price": 69000, "format": "PDF+EPUB", "promo": True},
            {"sku": "DEV-003", "title": "The 7 Habits of Highly Effective People", "author": "Stephen Covey", "price": 95000, "format": "PDF", "promo": False},
            {"sku": "DEV-004", "title": "Mindset", "author": "Carol S. Dweck", "price": 72000, "format": "EPUB", "promo": True},
        ]
    },
    "ai_ml": {
        "name": "AI & Machine Learning",
        "books": [
            {"sku": "AI-001", "title": "Hands-On Machine Learning", "author": "Aurélien Géron", "price": 155000, "format": "PDF", "promo": False},
            {"sku": "AI-002", "title": "Deep Learning", "author": "Goodfellow et al.", "price": 165000, "format": "PDF", "promo": False},
            {"sku": "AI-003", "title": "Building LLM Apps", "author": "Valentina Alto", "price": 135000, "format": "PDF+EPUB", "promo": True},
        ]
    }
}

# Mock Orders DB
ORDERS_DB: Dict[str, Dict[str, Any]] = {
    "INV-0001": {
        "invoice_id": "INV-0001",
        "buyer_name": "Andi Wijaya",
        "book_title": "The Psychology of Money",
        "sku": "BIZ-005",
        "amount": 75000,
        "payment_method": "QRIS",
        "status": "SUCCESS",
        "download_link": "https://libra-books.com/download/INV-0001",
        "created_at": "2026-09-28 10:30:00",
        "notes": "File PDF+EPUB siap diunduh."
    }
}


def get_book_catalog(category: Optional[str] = None, search: Optional[str] = None) -> Dict[str, Any]:
    """Mengambil katalog buku digital berdasarkan kategori atau kata kunci pencarian.

    Args:
        category: Kategori buku ('programming', 'business', 'self_development', 'ai_ml'). Kosong = semua.
        search: Kata kunci judul atau penulis untuk pencarian.
    """
    if search:
        results = []
        for cat_key, cat_data in DATABASE_CATALOG.items():
            for book in cat_data["books"]:
                if search.lower() in book["title"].lower() or search.lower() in book["author"].lower():
                    results.append({**book, "category": cat_data["name"]})
        if results:
            return {"status": "success", "query": search, "results": results}
        return {"status": "not_found", "message": f"Buku dengan kata kunci '{search}' tidak ditemukan."}

    if category:
        slug = category.lower().replace(" ", "_")
        if slug in DATABASE_CATALOG:
            return {"status": "success", "category": slug, "data": DATABASE_CATALOG[slug]}
        return {"status": "error", "message": f"Kategori '{category}' tidak ada. Tersedia: {list(DATABASE_CATALOG.keys())}"}

    return {"status": "success", "all_categories": DATABASE_CATALOG}


def get_book_recommendation(interest: str, budget: Optional[int] = None) -> Dict[str, Any]:
    """Memberikan rekomendasi buku berdasarkan minat dan budget pembaca.

    Args:
        interest: Topik minat (contoh: 'python', 'investasi', 'produktivitas', 'AI')
        budget: Budget maksimal dalam rupiah (opsional)
    """
    keyword_map = {
        "python": ["PRG-003"], "programming": ["PRG-001", "PRG-002"],
        "system design": ["PRG-004", "PRG-005"], "bisnis": ["BIZ-001", "BIZ-002", "BIZ-005"],
        "investasi": ["BIZ-005"], "produktivitas": ["DEV-001", "DEV-002"],
        "habit": ["BIZ-004"], "ai": ["AI-001", "AI-003"], "machine learning": ["AI-001", "AI-002"],
        "mindset": ["DEV-004"], "startup": ["BIZ-002", "BIZ-001"]
    }

    matched_skus = []
    for key, skus in keyword_map.items():
        if key in interest.lower():
            matched_skus.extend(skus)

    recommendations = []
    for cat_data in DATABASE_CATALOG.values():
        for book in cat_data["books"]:
            if book["sku"] in matched_skus:
                if budget is None or book["price"] <= budget:
                    recommendations.append(book)

    if not recommendations:
        # Fallback: promo books within budget
        for cat_data in DATABASE_CATALOG.values():
            for book in cat_data["books"]:
                if book["promo"] and (budget is None or book["price"] <= budget):
                    recommendations.append(book)

    return {
        "status": "success",
        "interest": interest,
        "budget": budget,
        "recommendations": recommendations[:4]
    }


def create_book_order(
    buyer_name: str,
    book_sku: str,
    payment_method: str = "QRIS"
) -> Dict[str, Any]:
    """Membuat pesanan pembelian buku digital dan menghasilkan invoice + link download.

    Args:
        buyer_name: Nama pembeli
        book_sku: Kode SKU buku (contoh: 'PRG-001', 'BIZ-005')
        payment_method: Metode pembayaran ('QRIS', 'Transfer Bank', 'GoPay', 'OVO')
    """
    selected_book = None
    for cat_data in DATABASE_CATALOG.values():
        for book in cat_data["books"]:
            if book["sku"] == book_sku.upper():
                selected_book = book
                break

    if not selected_book:
        return {"status": "error", "message": f"Buku dengan SKU '{book_sku}' tidak ditemukan."}

    invoice_id = f"INV-{uuid.uuid4().hex[:4].upper()}"
    order = {
        "invoice_id": invoice_id,
        "buyer_name": buyer_name,
        "book_title": selected_book["title"],
        "author": selected_book["author"],
        "sku": book_sku.upper(),
        "format": selected_book["format"],
        "amount": selected_book["price"],
        "payment_method": payment_method,
        "status": "PENDING",
        "download_link": f"https://libra-books.com/download/{invoice_id}",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "pay_link": f"https://libra-books.com/pay/{invoice_id}",
        "notes": f"Setelah pembayaran dikonfirmasi, file {selected_book['format']} siap diunduh."
    }
    ORDERS_DB[invoice_id] = order
    return {"status": "success", "message": "Pesanan berhasil dibuat!", "order": order}


def check_order_status(invoice_id: str) -> Dict[str, Any]:
    """Mengecek status pesanan dan link download buku berdasarkan Invoice ID.

    Args:
        invoice_id: Nomor invoice (contoh: 'INV-0001')
    """
    order = ORDERS_DB.get(invoice_id.upper())
    if not order:
        return {"status": "not_found", "message": f"Invoice '{invoice_id}' tidak ditemukan."}
    return {"status": "success", "order": order}


def get_promo_books() -> Dict[str, Any]:
    """Mengambil daftar buku digital yang sedang dalam promo atau diskon."""
    promo_list = []
    for cat_data in DATABASE_CATALOG.values():
        for book in cat_data["books"]:
            if book["promo"]:
                promo_list.append({**book, "category": cat_data["name"]})
    return {"status": "success", "total_promo": len(promo_list), "books": promo_list}
