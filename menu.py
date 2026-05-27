"""
Bərəkətli Menu & Farmer Data
=============================
Edit this file to update prices, add products, or change farmer info.
You don't need to touch any other file to update the menu.

Each product has:
  - id: short unique code (used internally)
  - name_az: how customer sees it (Azerbaijani)
  - emoji: visual icon
  - unit: per egg / per kg / per L / per jar
  - price: in AZN (customer-facing price)
  - farmer_id: which farmer it comes from (links to FARMERS dict below)
  - quantity_options: preset quantity buttons to show customer
  - active: True = show in menu, False = hide temporarily
"""

# ============================================================
# FARMERS — the people behind the products
# ============================================================
# photo_ids will be filled in AFTER we upload photos to Telegram once
# For now, leave them as None — bot will skip showing photos until set

FARMERS = {
    "sekine": {
        "name": "Səkinə xala",
        "village": "Liman, Lənkəran",
        "story": "30 ildir kənd toyuqları saxlayır. Toyuqları azad gəzir, taxıl və göy ilə qidalanır.",
        "main_photo_id": "AgACAgIAAxkBAANXaf3Ut1mMDpZc3RmD5hF0dRRCpbcAAvkUaxtqm_FLaUz3ETeZNeEBAAMCAANtAAM7BA",  
        "farm_photo_ids": ["AgACAgIAAxkBAANwaf3W4MhpLS_j29ezfMH2fKyFh50AAgoVaxtqm_FLmMOTWgzAQi8BAAMCAAN4AAM7BA",
				"AgACAgIAAxkBAANaaf3VoNX0DSiI8TZSB3mtJa7fqXUAAgEVaxtqm_FLX6Cbxr5yIhUBAAMCAANtAAM7BA",
					"AgACAgIAAxkBAANZaf3Vn56gtTcNdOlrWpaov3PWVjsAAxVrG2qb8UshL-XQJRcBUgEAAwIAA20AAzsE",],   
    },
    "rovshan": {
        "name": "Rövşən dayı",
        "village": "Boladi, Lənkəran",
        "story": "Ailə təsərrüfatı — inək və camış südü. Hər səhər təzə sağılır.",
        "main_photo_id": None,
        "farm_photo_ids": [],
    },
    "gulnara": {
        "name": "Gülnarə xala",
        "village": "Hirkan, Lənkəran",
        "story": "Ev şəraitində nehrə yağı və şor hazırlayır. Heç bir əlavə qatqı yoxdur.",
        "main_photo_id": None,
        "farm_photo_ids": [],
    },
    "mahire": {
        "name": "Mahirə xala",
        "village": "Lənkəran şəhəri",
        "story": "Hər il payızda evdə tutmalar və alça turşusu hazırlayır. Anasından öyrənib.",
        "main_photo_id": None,
        "farm_photo_ids": [],
    },
}

# ============================================================
# PRODUCTS — the menu
# ============================================================

PRODUCTS = {
    "yumurta": {
        "name_az": "Kənd yumurtası",
        "emoji": "🥚",
        "unit": "ədəd",
        "unit_label_az": "ədəd",
        "price": 0.40,
        "farmer_id": "sekine",
        "quantity_options": [10, 20, 30, 50, 100],
        "active": True,
    },
    "sud_inek": {
        "name_az": "İnək südü",
        "emoji": "🥛",
        "unit": "litr",
        "unit_label_az": "L",
        "price": 2.50,
        "farmer_id": "rovshan",
        "quantity_options": [1, 2, 3, 5],
        "active": True,
    },
    "sud_camis": {
        "name_az": "Camış südü",
        "emoji": "🥛",
        "unit": "litr",
        "unit_label_az": "L",
        "price": 4.00,
        "farmer_id": "rovshan",
        "quantity_options": [1, 2, 3],
        "active": True,
    },
    "shor": {
        "name_az": "Şor",
        "emoji": "🧀",
        "unit": "kq",
        "unit_label_az": "kq",
        "price": 3.50,
        "farmer_id": "gulnara",
        "quantity_options": [0.5, 1, 2, 3],
        "active": True,
    },
    "yag": {
        "name_az": "Nehrə yağı",
        "emoji": "🧈",
        "unit": "kq",
        "unit_label_az": "kq",
        "price": 22.00,
        "farmer_id": "gulnara",
        "quantity_options": [0.25, 0.5, 1, 2],
        "active": True,
    },
    "tolpa": {
        "name_az": "Toyuq çolpa",
        "emoji": "🍗",
        "unit": "kq",
        "unit_label_az": "kq",
        "price": 11.00,
        "farmer_id": "sekine",
        "quantity_options": [1, 1.5, 2, 3],
        "active": True,
    },
    "alca": {
        "name_az": "Alça turşusu",
        "emoji": "🍒",
        "unit": "kq",
        "unit_label_az": "kq",
        "price": 10.00,
        "farmer_id": "mahire",
        "quantity_options": [0.5, 1, 2],
        "active": True,
    },
    "biber_tutmasi": {
        "name_az": "Bibər tutması",
        "emoji": "🌶️",
        "unit": "bankə",
        "unit_label_az": "bankə (1L)",
        "price": 6.00,
        "farmer_id": "mahire",
        "quantity_options": [1, 2, 3],
        "active": True,
    },
    "lobya_tutmasi": {
        "name_az": "Lobya tutması",
        "emoji": "🫘",
        "unit": "bankə",
        "unit_label_az": "bankə (1L)",
        "price": 6.00,
        "farmer_id": "mahire",
        "quantity_options": [1, 2, 3],
        "active": True,
    },
}

# ============================================================
# BUSINESS RULES
# ============================================================

MINIMUM_ORDER_AZN = 20.00
ORDER_DEADLINE_DAY = 2  # 0=Mon, 1=Tue, 2=Wed, 3=Thu...
ORDER_DEADLINE_HOUR = 18  # 6 PM
DELIVERY_DAY_AZ = "Şənbə"
DELIVERY_TIME_AZ = "16:00 - 18:00"

# Bank info for transfer payments
BANK_INFO_AZ = """
🏦 Bank köçürməsi məlumatları:
Kart: 4169 7400 0000 0000
Sahibi: [Adınız]
Bank: [Bank adı]

Köçürmə açıqlamasına sifariş nömrənizi yazın.
"""


def get_active_products():
    """Return only products marked as active (in stock this week)."""
    return {pid: p for pid, p in PRODUCTS.items() if p["active"]}


def format_price(amount):
    """Format AZN price nicely: 12.5 -> '12.50 AZN'."""
    return f"{amount:.2f} AZN"
