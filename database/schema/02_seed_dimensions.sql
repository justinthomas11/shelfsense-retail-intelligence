INSERT INTO dim_retailer (retailer_name, retailer_type, website_url) VALUES
('BigBasket',  'grocery',          'https://www.bigbasket.com'),
('Blinkit',    'quick_commerce',   'https://blinkit.com'),
('Zepto',      'quick_commerce',   'https://www.zeptonow.com'),
('JioMart',    'marketplace',      'https://www.jiomart.com')
ON CONFLICT (retailer_name) DO NOTHING;

INSERT INTO dim_category (category_name, parent_category) VALUES
('Rice & Grains',       'Staples'),
('Pulses & Lentils',    'Staples'),
('Cooking Oil',         'Staples'),
('Spices & Masala',     'Staples'),
('Flour & Atta',        'Staples'),
('Milk',                'Dairy'),
('Curd & Yogurt',       'Dairy'),
('Paneer & Cheese',     'Dairy'),
('Butter & Ghee',       'Dairy'),
('Biscuits & Cookies',  'Snacks'),
('Chips & Namkeen',     'Snacks'),
('Chocolates',          'Snacks'),
('Tea & Coffee',        'Beverages'),
('Soft Drinks & Juices','Beverages'),
('Soap & Bodywash',     'Personal Care'),
('Shampoo & Conditioner','Personal Care'),
('Toothpaste',          'Personal Care'),
('Detergent',           'Household'),
('Dishwash',            'Household'),
('Sugar & Jaggery',     'Staples')
ON CONFLICT (category_name) DO NOTHING;
