-- ShopStream Initial Seed Data for Reference Tables

INSERT INTO categories (category_id, name, description) VALUES
(1, 'Electronics', 'Gadgets, devices, and electronic accessories'),
(2, 'Clothing', 'Apparel, footwear, and fashion items'),
(3, 'Home & Kitchen', 'Home decor, furniture, and kitchen appliances'),
(4, 'Books', 'Physical and electronic books'),
(5, 'Sports & Outdoors', 'Sporting goods, outdoor gear, and fitness equipment')
ON CONFLICT (category_id) DO NOTHING;

INSERT INTO categories (category_id, name, description, parent_id) VALUES
(6, 'Smartphones', 'Mobile phones and accessories', 1),
(7, 'Laptops', 'Notebooks and personal computers', 1),
(8, 'Men Fashion', 'Clothing for men', 2),
(9, 'Women Fashion', 'Clothing for women', 2)
ON CONFLICT (category_id) DO NOTHING;

INSERT INTO suppliers (supplier_id, company_name, contact_name, email, phone) VALUES
(1, 'TechSupply Global', 'Alice Smith', 'contact@techsupply.com', '+1-555-0192'),
(2, 'Apparel World Inc.', 'Bob Jones', 'support@apparelworld.com', '+1-555-0144'),
(3, 'HomeGoods Direct', 'Charlie Brown', 'info@homegoodsdirect.com', '+1-555-0188')
ON CONFLICT (supplier_id) DO NOTHING;

-- Reset sequence counters so auto-increment works smoothly after manual ID inserts
SELECT setval('categories_category_id_seq', (SELECT MAX(category_id) FROM categories));
SELECT setval('suppliers_supplier_id_seq', (SELECT MAX(supplier_id) FROM suppliers));
