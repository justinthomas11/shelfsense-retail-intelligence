"""
Product Catalog for ShelfSense Data Simulator
-----------------------------------------------
Defines realistic Indian grocery products across all 20 categories.
Each product has a name, brand, unit size, category, and base MRP.
"""

# fmt: off
PRODUCT_CATALOG = [
    # ── Staples: Rice & Grains ──
    {"name": "India Gate Basmati Rice",        "brand": "India Gate",    "unit": "5 kg",   "category": "Rice & Grains",        "base_mrp": 599.00},
    {"name": "Daawat Rozana Basmati Rice",     "brand": "Daawat",       "unit": "5 kg",   "category": "Rice & Grains",        "base_mrp": 449.00},
    {"name": "Fortune Everyday Basmati Rice",  "brand": "Fortune",      "unit": "5 kg",   "category": "Rice & Grains",        "base_mrp": 475.00},
    {"name": "24 Mantra Organic Sonamasuri",   "brand": "24 Mantra",    "unit": "5 kg",   "category": "Rice & Grains",        "base_mrp": 525.00},
    {"name": "Kohinoor Super Value Basmati",   "brand": "Kohinoor",     "unit": "5 kg",   "category": "Rice & Grains",        "base_mrp": 545.00},

    # ── Staples: Pulses & Lentils ──
    {"name": "Tata Sampann Toor Dal",          "brand": "Tata Sampann", "unit": "1 kg",   "category": "Pulses & Lentils",     "base_mrp": 185.00},
    {"name": "Fortune Chana Dal",              "brand": "Fortune",      "unit": "1 kg",   "category": "Pulses & Lentils",     "base_mrp": 135.00},
    {"name": "24 Mantra Organic Moong Dal",    "brand": "24 Mantra",    "unit": "1 kg",   "category": "Pulses & Lentils",     "base_mrp": 215.00},
    {"name": "Tata Sampann Masoor Dal",        "brand": "Tata Sampann", "unit": "1 kg",   "category": "Pulses & Lentils",     "base_mrp": 145.00},
    {"name": "BB Royal Rajma",                 "brand": "BB Royal",     "unit": "1 kg",   "category": "Pulses & Lentils",     "base_mrp": 195.00},

    # ── Staples: Cooking Oil ──
    {"name": "Fortune Sunlite Refined Oil",    "brand": "Fortune",      "unit": "5 L",    "category": "Cooking Oil",          "base_mrp": 799.00},
    {"name": "Saffola Gold Edible Oil",        "brand": "Saffola",      "unit": "5 L",    "category": "Cooking Oil",          "base_mrp": 945.00},
    {"name": "Fortune Rice Bran Oil",          "brand": "Fortune",      "unit": "5 L",    "category": "Cooking Oil",          "base_mrp": 825.00},
    {"name": "Nature Fresh Mustard Oil",       "brand": "Nature Fresh", "unit": "5 L",    "category": "Cooking Oil",          "base_mrp": 780.00},
    {"name": "Figaro Olive Oil",               "brand": "Figaro",       "unit": "1 L",    "category": "Cooking Oil",          "base_mrp": 699.00},

    # ── Staples: Spices & Masala ──
    {"name": "MDH Garam Masala",               "brand": "MDH",          "unit": "100 g",  "category": "Spices & Masala",      "base_mrp": 92.00},
    {"name": "Everest Turmeric Powder",        "brand": "Everest",      "unit": "200 g",  "category": "Spices & Masala",      "base_mrp": 85.00},
    {"name": "Catch Red Chilli Powder",        "brand": "Catch",        "unit": "200 g",  "category": "Spices & Masala",      "base_mrp": 98.00},
    {"name": "MDH Chole Masala",               "brand": "MDH",          "unit": "100 g",  "category": "Spices & Masala",      "base_mrp": 72.00},
    {"name": "Tata Sampann Coriander Powder",  "brand": "Tata Sampann", "unit": "200 g",  "category": "Spices & Masala",      "base_mrp": 78.00},

    # ── Staples: Flour & Atta ──
    {"name": "Aashirvaad Superior MP Atta",    "brand": "Aashirvaad",   "unit": "10 kg",  "category": "Flour & Atta",         "base_mrp": 485.00},
    {"name": "Pillsbury Chakki Fresh Atta",    "brand": "Pillsbury",    "unit": "10 kg",  "category": "Flour & Atta",         "base_mrp": 455.00},
    {"name": "Fortune Chakki Atta",            "brand": "Fortune",      "unit": "10 kg",  "category": "Flour & Atta",         "base_mrp": 425.00},
    {"name": "Aashirvaad Multigrain Atta",     "brand": "Aashirvaad",   "unit": "5 kg",   "category": "Flour & Atta",         "base_mrp": 320.00},
    {"name": "Rajdhani Besan",                 "brand": "Rajdhani",     "unit": "1 kg",   "category": "Flour & Atta",         "base_mrp": 125.00},

    # ── Staples: Sugar & Jaggery ──
    {"name": "Madhur Pure Sugar",              "brand": "Madhur",       "unit": "5 kg",   "category": "Sugar & Jaggery",      "base_mrp": 249.00},
    {"name": "Trust Classic Sugar",            "brand": "Trust",        "unit": "5 kg",   "category": "Sugar & Jaggery",      "base_mrp": 239.00},
    {"name": "Organic Tattva Jaggery Powder",  "brand": "Organic Tattva","unit": "1 kg",  "category": "Sugar & Jaggery",      "base_mrp": 175.00},

    # ── Dairy: Milk ──
    {"name": "Amul Taaza Toned Milk",          "brand": "Amul",         "unit": "1 L",    "category": "Milk",                 "base_mrp": 60.00},
    {"name": "Mother Dairy Full Cream Milk",   "brand": "Mother Dairy", "unit": "1 L",    "category": "Milk",                 "base_mrp": 68.00},
    {"name": "Amul Gold Full Cream Milk",      "brand": "Amul",         "unit": "1 L",    "category": "Milk",                 "base_mrp": 72.00},

    # ── Dairy: Curd & Yogurt ──
    {"name": "Amul Masti Dahi",                "brand": "Amul",         "unit": "400 g",  "category": "Curd & Yogurt",        "base_mrp": 42.00},
    {"name": "Mother Dairy Classic Curd",      "brand": "Mother Dairy", "unit": "400 g",  "category": "Curd & Yogurt",        "base_mrp": 45.00},
    {"name": "Epigamia Greek Yogurt",          "brand": "Epigamia",     "unit": "90 g",   "category": "Curd & Yogurt",        "base_mrp": 55.00},

    # ── Dairy: Paneer & Cheese ──
    {"name": "Amul Fresh Paneer",              "brand": "Amul",         "unit": "200 g",  "category": "Paneer & Cheese",      "base_mrp": 95.00},
    {"name": "Amul Cheese Slices",             "brand": "Amul",         "unit": "200 g",  "category": "Paneer & Cheese",      "base_mrp": 120.00},
    {"name": "Britannia Cheese Block",         "brand": "Britannia",    "unit": "400 g",  "category": "Paneer & Cheese",      "base_mrp": 215.00},

    # ── Dairy: Butter & Ghee ──
    {"name": "Amul Butter",                    "brand": "Amul",         "unit": "500 g",  "category": "Butter & Ghee",        "base_mrp": 285.00},
    {"name": "Amul Cow Ghee",                  "brand": "Amul",         "unit": "1 L",    "category": "Butter & Ghee",        "base_mrp": 620.00},
    {"name": "Mother Dairy Cow Ghee",          "brand": "Mother Dairy", "unit": "1 L",    "category": "Butter & Ghee",        "base_mrp": 599.00},

    # ── Snacks: Biscuits & Cookies ──
    {"name": "Britannia Good Day Cashew",      "brand": "Britannia",    "unit": "600 g",  "category": "Biscuits & Cookies",   "base_mrp": 175.00},
    {"name": "Parle-G Gold Biscuits",          "brand": "Parle",        "unit": "1 kg",   "category": "Biscuits & Cookies",   "base_mrp": 120.00},
    {"name": "Sunfeast Dark Fantasy Choco",    "brand": "Sunfeast",     "unit": "300 g",  "category": "Biscuits & Cookies",   "base_mrp": 150.00},
    {"name": "Oreo Original Vanilla Creme",    "brand": "Cadbury",      "unit": "300 g",  "category": "Biscuits & Cookies",   "base_mrp": 110.00},

    # ── Snacks: Chips & Namkeen ──
    {"name": "Lays Classic Salted Chips",      "brand": "Lays",         "unit": "235 g",  "category": "Chips & Namkeen",      "base_mrp": 99.00},
    {"name": "Haldiram Aloo Bhujia",           "brand": "Haldiram",     "unit": "400 g",  "category": "Chips & Namkeen",      "base_mrp": 155.00},
    {"name": "Kurkure Masala Munch",           "brand": "Kurkure",      "unit": "235 g",  "category": "Chips & Namkeen",      "base_mrp": 85.00},
    {"name": "Bingo Mad Angles Achaari",       "brand": "Bingo",        "unit": "200 g",  "category": "Chips & Namkeen",      "base_mrp": 78.00},

    # ── Snacks: Chocolates ──
    {"name": "Cadbury Dairy Milk Silk",        "brand": "Cadbury",      "unit": "150 g",  "category": "Chocolates",           "base_mrp": 175.00},
    {"name": "KitKat 4 Finger",                "brand": "Nestle",       "unit": "37.3 g", "category": "Chocolates",           "base_mrp": 40.00},
    {"name": "5 Star 3D Chocolate Bar",        "brand": "Cadbury",      "unit": "42 g",   "category": "Chocolates",           "base_mrp": 30.00},
    {"name": "Ferrero Rocher Pack",            "brand": "Ferrero",      "unit": "16 pcs", "category": "Chocolates",           "base_mrp": 549.00},

    # ── Beverages: Tea & Coffee ──
    {"name": "Tata Tea Gold",                  "brand": "Tata Tea",     "unit": "500 g",  "category": "Tea & Coffee",         "base_mrp": 285.00},
    {"name": "Red Label Natural Care",         "brand": "Brooke Bond",  "unit": "500 g",  "category": "Tea & Coffee",         "base_mrp": 310.00},
    {"name": "Nescafe Classic Instant Coffee", "brand": "Nescafe",      "unit": "200 g",  "category": "Tea & Coffee",         "base_mrp": 525.00},
    {"name": "Bru Gold Instant Coffee",        "brand": "Bru",          "unit": "200 g",  "category": "Tea & Coffee",         "base_mrp": 490.00},

    # ── Beverages: Soft Drinks & Juices ──
    {"name": "Coca-Cola Pet Bottle",           "brand": "Coca-Cola",    "unit": "2.25 L", "category": "Soft Drinks & Juices",  "base_mrp": 96.00},
    {"name": "Tropicana Mixed Fruit Juice",    "brand": "Tropicana",    "unit": "1 L",    "category": "Soft Drinks & Juices",  "base_mrp": 120.00},
    {"name": "Real Masala Pomegranate Juice",  "brand": "Real",         "unit": "1 L",    "category": "Soft Drinks & Juices",  "base_mrp": 115.00},
    {"name": "Sprite Pet Bottle",              "brand": "Sprite",       "unit": "2.25 L", "category": "Soft Drinks & Juices",  "base_mrp": 96.00},

    # ── Personal Care: Soap & Bodywash ──
    {"name": "Dove Cream Beauty Bathing Bar",  "brand": "Dove",         "unit": "4x100 g","category": "Soap & Bodywash",      "base_mrp": 316.00},
    {"name": "Lux Soft Glow Body Wash",        "brand": "Lux",          "unit": "245 ml", "category": "Soap & Bodywash",      "base_mrp": 175.00},
    {"name": "Dettol Original Soap",           "brand": "Dettol",       "unit": "4x125 g","category": "Soap & Bodywash",      "base_mrp": 248.00},

    # ── Personal Care: Shampoo & Conditioner ──
    {"name": "Head & Shoulders Anti-Dandruff", "brand": "Head & Shoulders","unit": "650 ml","category": "Shampoo & Conditioner","base_mrp": 560.00},
    {"name": "Dove Hair Fall Rescue Shampoo",  "brand": "Dove",         "unit": "650 ml", "category": "Shampoo & Conditioner", "base_mrp": 494.00},
    {"name": "Pantene Advanced Hairfall Soln", "brand": "Pantene",      "unit": "650 ml", "category": "Shampoo & Conditioner", "base_mrp": 475.00},

    # ── Personal Care: Toothpaste ──
    {"name": "Colgate Strong Teeth Toothpaste","brand": "Colgate",      "unit": "300 g",  "category": "Toothpaste",           "base_mrp": 155.00},
    {"name": "Pepsodent Germicheck Toothpaste","brand": "Pepsodent",    "unit": "300 g",  "category": "Toothpaste",           "base_mrp": 132.00},
    {"name": "Sensodyne Sensitive Toothpaste", "brand": "Sensodyne",    "unit": "150 g",  "category": "Toothpaste",           "base_mrp": 225.00},

    # ── Household: Detergent ──
    {"name": "Surf Excel Easy Wash Detergent", "brand": "Surf Excel",   "unit": "4 kg",   "category": "Detergent",            "base_mrp": 560.00},
    {"name": "Ariel Matic Top Load Detergent", "brand": "Ariel",        "unit": "4 kg",   "category": "Detergent",            "base_mrp": 799.00},
    {"name": "Tide Plus Extra Power Detergent","brand": "Tide",         "unit": "4 kg",   "category": "Detergent",            "base_mrp": 475.00},

    # ── Household: Dishwash ──
    {"name": "Vim Dishwash Liquid Gel",        "brand": "Vim",          "unit": "750 ml", "category": "Dishwash",             "base_mrp": 139.00},
    {"name": "Pril Dishwash Liquid",           "brand": "Pril",         "unit": "750 ml", "category": "Dishwash",             "base_mrp": 155.00},
    {"name": "Exo Dishwash Bar",               "brand": "Exo",          "unit": "700 g",  "category": "Dishwash",             "base_mrp": 62.00},
]
# fmt: on
