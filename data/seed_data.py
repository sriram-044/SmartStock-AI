import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from backend.database.db import get_db, transaction
from backend.auth.security import hash_password
from backend.services.inventory_service import record_transaction
from backend.ai.agent import InventoryAgent

def seed_database(force: bool = False):
    """Generates a complete, authentic Indian & Tamil Nadu retail dataset."""
    print("[Seed] Starting database population...")
    from backend.database.db import init_db
    if force:
        init_db()
    conn = get_db()
    try:
        # Check if already seeded
        if not force:
            cur = conn.execute("SELECT COUNT(*) as count FROM products")
            if cur.fetchone()["count"] > 20:
                print("[Seed] Database already contains products. Skipping initial seed.")
                return

        # 1. Users
        print("[Seed] Creating default user roles...")
        users = [
            ("admin", "admin123", "S. Ramanathan (Shop Owner)", "admin"),
            ("manager", "manager123", "K. Selvam (Store Manager)", "manager"),
            ("cashier", "cashier123", "M. Priya (Senior Cashier)", "cashier")
        ]
        for username, pwd, name, role in users:
            conn.execute(
                """
                INSERT OR IGNORE INTO users (username, password_hash, full_name, role)
                VALUES (?, ?, ?, ?)
                """,
                (username, hash_password(pwd), name, role)
            )

        # 2. Categories
        print("[Seed] Creating retail categories with Tamil localization...")
        categories = [
            ("Provisions & Grains", "மளிகை & தானியங்கள்", "Rice, wheat, pulses, spices, sugar, salt"),
            ("Edible Oils & Ghee", "சமையல் எண்ணெய் & நெய்", "Cooking oils, gingelly oil, ghee, coconut oil"),
            ("Beverages & Dairy", "பானங்கள் & பால் பொருட்கள்", "Milk, butter, paneer, tea, coffee, health drinks"),
            ("Packaged Foods & Snacks", "சிற்றுண்டி & உணவுப் பொருட்கள்", "Biscuits, noodles, namkeen, wafers"),
            ("Personal Care & Toiletries", "தனிநபர் பராமரிப்பு", "Soaps, shampoos, toothpaste, skincare"),
            ("Household & Cleaning", "வீட்டு உபயோகம் & தூய்மை", "Detergents, dishwash, surface cleaners"),
            ("Stationery & Electronics", "எழுதுபொருட்கள் & மின்சாதனம்", "Notebooks, pens, batteries, bulbs")
        ]
        cat_map = {}
        for name, t_name, desc in categories:
            cur = conn.execute(
                "INSERT INTO categories (name, tamil_name, description) VALUES (?, ?, ?)",
                (name, t_name, desc)
            )
            cat_map[name] = cur.lastrowid

        # 3. Suppliers across Tamil Nadu
        print("[Seed] Creating Tamil Nadu wholesale suppliers...")
        suppliers = [
            ("Chennai Koyambedu Agro Wholesalers", "R. Swaminathan", "98401 23456", "sales@koyambeduagro.in", "Tamil Nadu", "Chennai", "Koyambedu Wholesale Complex", 4.7, 96.5, 2, 0.8),
            ("Madurai Sri Meenakshi Traders", "M. Chidambaram", "94431 87654", "meenakshitraders@mdu.in", "Tamil Nadu", "Madurai", "Simmakkal Market", 4.5, 94.0, 3, 1.2),
            ("Erode Turmeric & Commodity Mandi", "P. Sengottaiyan", "98427 11223", "orders@erodemanditraders.com", "Tamil Nadu", "Erode", "Brough Road APMC", 4.8, 98.0, 3, 0.5),
            ("Salem Sago & FMCG Distributors", "V. Kulanthaivel", "97890 33445", "salemfmcg@salemnet.in", "Tamil Nadu", "Salem", "Shevapet Commercial Street", 4.3, 91.5, 4, 1.5),
            ("Coimbatore Western Provision Hub", "G. Palaniswamy", "98940 55667", "westprovisions@cbehub.com", "Tamil Nadu", "Coimbatore", "R.S. Puram Goods Terminal", 4.6, 95.0, 3, 0.9),
            ("Tiruchirappalli Kaveri Wholesale Agency", "T. Natarajan", "94432 99887", "kaveriagency@trichy.in", "Tamil Nadu", "Tiruchirappalli", "Gandhi Market Main Gate", 4.4, 93.0, 3, 1.4),
            ("Tirunelveli Nellai Oil & Provisions", "S. Arumugam", "94860 12378", "nellaioils@nellai.in", "Tamil Nadu", "Tirunelveli", "Town Hall Road", 4.6, 95.5, 4, 0.7),
            ("Vellore Fort City FMCG Supplies", "J. Venkatraman", "97871 44556", "vellorefmcg@fortcity.in", "Tamil Nadu", "Vellore", "Katpadi Industrial Estate", 4.2, 89.0, 5, 2.0),
            ("Thanjavur Delta Rice & Grain Mills", "A. Thangavel", "98433 77889", "deltamills@thanjavur.in", "Tamil Nadu", "Thanjavur", "Kumbakonam Main Road", 4.9, 97.5, 2, 0.6),
            ("Krishnagiri Agro & Commodity Hub", "C. Muniyappa", "99450 66778", "orders@hosuragro.in", "Tamil Nadu", "Hosur/Krishnagiri", "Sipcot Hub Hosur", 4.5, 92.5, 4, 1.1)
        ]
        sup_ids = []
        for name, cp, ph, em, st, dt, addr, rat, rel, lt, ret in suppliers:
            cur = conn.execute(
                """
                INSERT INTO suppliers (name, contact_person, phone, email, state, district, address, rating, reliability_score, avg_lead_time_days, return_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (name, cp, ph, em, st, dt, addr, rat, rel, lt, ret)
            )
            sup_ids.append(cur.lastrowid)

        # 4. Products List (55 Authentic Indian Retail Items)
        print("[Seed] Creating 55+ Indian retail products...")
        raw_products = [
            # Provisions & Grains
            ("890103000001", "Ponni Boiled Rice 25kg", "பொன்னி புழுங்கல் அரிசி 25கிலோ", "Provisions & Grains", "Rice", "Babu Brand", "Bag", "25kg", 1350.0, 1550.0, 1600.0, 0.0, 10, 80, 25, 12, 1, 0, 8.0), # CRITICAL STOCKOUT
            ("890103000002", "Ponni Boiled Rice 5kg", "பொன்னி புழுங்கல் அரிசி 5கிலோ", "Provisions & Grains", "Rice", "Babu Brand", "Bag", "5kg", 280.0, 330.0, 350.0, 0.0, 15, 100, 30, 15, 1, 0, 42.0),
            ("890103000003", "Idli Rice 5kg", "இட்லி அரிசி 5கிலோ", "Provisions & Grains", "Rice", "Anil Brand", "Bag", "5kg", 210.0, 260.0, 280.0, 0.0, 15, 120, 35, 15, 9, 0, 38.0),
            ("890103000004", "Aashirvaad Shudh Chakki Atta 5kg", "ஆசீர்வாத் கோதுமை மாவு 5கிலோ", "Provisions & Grains", "Atta", "Aashirvaad", "Pack", "5kg", 245.0, 290.0, 310.0, 0.0, 15, 90, 30, 15, 1, 1, 14.0), # REORDER NOW
            ("890103000005", "Aashirvaad Atta 1kg", "ஆசீர்வாத் கோதுமை மாவு 1கிலோ", "Provisions & Grains", "Atta", "Aashirvaad", "Pack", "1kg", 54.0, 65.0, 70.0, 0.0, 20, 150, 40, 20, 1, 1, 65.0),
            ("890103000006", "Toor Dal 1kg", "துவரம் பருப்பு 1கிலோ", "Provisions & Grains", "Pulses", "Tata Sampann", "Pack", "1kg", 145.0, 175.0, 185.0, 0.0, 25, 150, 50, 25, 3, 0, 28.0), # REORDER SOON
            ("890103000007", "Moong Dal 500g", "பாசிப் பருப்பு 500கி", "Provisions & Grains", "Pulses", "Tata Sampann", "Pack", "500g", 68.0, 85.0, 92.0, 0.0, 20, 100, 35, 15, 3, 0, 45.0),
            ("890103000008", "Urad Dal Gota 1kg", "உளுத்தம் பருப்பு 1கிலோ", "Provisions & Grains", "Pulses", "Udhaiyam", "Pack", "1kg", 132.0, 160.0, 170.0, 0.0, 20, 120, 40, 20, 3, 0, 50.0),
            ("890103000009", "Chana Dal 1kg", "கடலைப் பருப்பு 1கிலோ", "Provisions & Grains", "Pulses", "Udhaiyam", "Pack", "1kg", 88.0, 108.0, 115.0, 0.0, 15, 100, 30, 15, 3, 0, 36.0),
            ("890103000010", "Tata Salt 1kg", "டாடா உப்பு 1கிலோ", "Provisions & Grains", "Salt", "Tata", "Pack", "1kg", 22.0, 28.0, 30.0, 0.0, 30, 200, 60, 30, 1, 0, 85.0),
            ("890103000011", "Madhur Pure Crystal Sugar 1kg", "சர்க்கரை 1கிலோ", "Provisions & Grains", "Sugar", "Madhur", "Pack", "1kg", 42.0, 50.0, 55.0, 5.0, 30, 250, 70, 30, 1, 0, 110.0),
            ("890103000012", "Organic Nattu Sakkarai (Brown Sugar) 1kg", "நாட்டுச் சர்க்கரை 1கிலோ", "Provisions & Grains", "Sugar", "Nature Farm", "Pack", "1kg", 65.0, 90.0, 95.0, 5.0, 15, 80, 25, 10, 3, 0, 32.0),
            ("890103000013", "Aachi Turmeric Powder 100g", "ஆச்சி மஞ்சள் தூள் 100கி", "Provisions & Grains", "Spices", "Aachi", "Pack", "100g", 24.0, 32.0, 35.0, 5.0, 25, 150, 45, 20, 3, 1, 62.0),
            ("890103000014", "Everest Kashmiri Chilli Powder 100g", "காஷ்மீரி மிளகாய் தூள் 100கி", "Provisions & Grains", "Spices", "Everest", "Pack", "100g", 42.0, 56.0, 60.0, 5.0, 20, 120, 35, 15, 1, 1, 48.0),
            ("890103000015", "Premium Sago / Javvarisi 500g", "சேலம் ஜவ்வரிசி 500கி", "Provisions & Grains", "Staples", "Salem Pride", "Pack", "500g", 38.0, 55.0, 60.0, 5.0, 10, 60, 15, 10, 4, 0, 85.0), # OVERSTOCK

            # Edible Oils & Ghee
            ("890103000016", "Gold Winner Sunflower Oil 1L", "கோல்ட் வின்னர் சூரியகாந்தி எண்ணெய் 1லி", "Edible Oils & Ghee", "Refined Oil", "Gold Winner", "Pouch", "1L", 118.0, 138.0, 145.0, 5.0, 30, 250, 60, 30, 1, 1, 35.0), # REORDER SOON
            ("890103000017", "Idhayam Gingelly Oil 1L Bottle", "இதயம் நல்லெண்ணெய் 1லி பாட்டில்", "Edible Oils & Ghee", "Gingelly Oil", "Idhayam", "Bottle", "1L", 295.0, 350.0, 370.0, 5.0, 15, 120, 30, 15, 7, 1, 28.0),
            ("890103000018", "Parachute Pure Coconut Oil 500ml", "பாராசூட் தேங்காய் எண்ணெய் 500மி.லி", "Edible Oils & Ghee", "Coconut Oil", "Parachute", "Bottle", "500ml", 145.0, 180.0, 195.0, 5.0, 20, 150, 40, 20, 1, 1, 55.0),
            ("890103000019", "GRB Pure Cow Ghee 500ml Jar", "ஜிஆர்பி நெய் 500மி.லி", "Edible Oils & Ghee", "Ghee", "GRB", "Jar", "500ml", 360.0, 430.0, 450.0, 12.0, 12, 80, 25, 12, 2, 1, 19.0),
            ("890103000020", "Fortune Kachi Ghani Mustard Oil 1L", "பார்ச்சூன் கடுகு எண்ணெய் 1லி", "Edible Oils & Ghee", "Mustard Oil", "Fortune", "Bottle", "1L", 140.0, 175.0, 185.0, 5.0, 10, 50, 15, 10, 1, 1, 6.0), # SLOW / DEAD STOCK

            # Beverages & Dairy
            ("890103000021", "Aavin Toned Fresh Milk 500ml", "ஆவின் பால் 500மி.லி", "Beverages & Dairy", "Milk", "Aavin", "Pouch", "500ml", 21.0, 25.0, 25.0, 0.0, 40, 300, 80, 40, 1, 1, 15.0), # CRITICAL EXPIRY / NEAR EXPIRY
            ("890103000022", "Amul Pasteurized Butter 100g", "அமுல் வெண்ணெய் 100கி", "Beverages & Dairy", "Butter", "Amul", "Pack", "100g", 48.0, 58.0, 60.0, 12.0, 20, 100, 35, 15, 1, 1, 18.0), # EXPIRING SOON
            ("890103000023", "Milky Mist Paneer 200g", "மில்கி மிஸ்ட் பன்னீர் 200கி", "Beverages & Dairy", "Paneer", "Milky Mist", "Pack", "200g", 88.0, 115.0, 120.0, 5.0, 15, 80, 25, 12, 5, 1, 24.0),
            ("890103000024", "Bru Instant Coffee Jar 100g", "ப்ரூ இன்ஸ்டன்ட் காபி 100கி", "Beverages & Dairy", "Coffee", "Bru", "Jar", "100g", 165.0, 205.0, 215.0, 18.0, 15, 90, 30, 15, 1, 1, 42.0),
            ("890103000025", "Narasu's Pure Filter Coffee 500g", "நரசுஸ் பில்டர் காபி 500கி", "Beverages & Dairy", "Coffee", "Narasu's", "Pack", "500g", 195.0, 245.0, 260.0, 5.0, 15, 80, 30, 15, 4, 1, 31.0),
            ("890103000026", "3 Roses Dust Tea 250g", "3 ரோசஸ் தேயிலை 250கி", "Beverages & Dairy", "Tea", "Brooke Bond", "Pack", "250g", 125.0, 155.0, 165.0, 5.0, 20, 120, 40, 20, 1, 1, 48.0),
            ("890103000027", "Red Label Natural Care Tea 250g", "ரெட் லேபிள் டீ 250கி", "Beverages & Dairy", "Tea", "Brooke Bond", "Pack", "250g", 135.0, 168.0, 175.0, 5.0, 15, 90, 30, 15, 1, 1, 38.0),
            ("890103000028", "Boost Energy Drink Refill 500g", "பூஸ்ட் ஹெல்த் டிரிங்க் 500கி", "Beverages & Dairy", "Health Drinks", "Boost", "Pack", "500g", 235.0, 285.0, 300.0, 18.0, 15, 80, 25, 12, 1, 1, 22.0),
            ("890103000029", "Horlicks Classic Malt 500g", "ஹார்லிக்ஸ் 500கி", "Beverages & Dairy", "Health Drinks", "Horlicks", "Jar", "500g", 245.0, 295.0, 315.0, 18.0, 15, 80, 25, 12, 1, 1, 26.0),
            ("890103000030", "Exotic Green Tea Detox 100g", "கிரீன் டீ 100கி", "Beverages & Dairy", "Tea", "Himalayan", "Box", "100g", 210.0, 310.0, 330.0, 5.0, 10, 40, 15, 8, 5, 1, 34.0), # DEAD STOCK

            # Packaged Foods & Snacks
            ("890103000031", "Britannia Marie Gold 300g Family Pack", "பிரிட்டானியா மேரி கோல்ட் 300கி", "Packaged Foods & Snacks", "Biscuits", "Britannia", "Pack", "300g", 34.0, 42.0, 45.0, 18.0, 25, 180, 50, 25, 1, 1, 68.0),
            ("890103000032", "Parle-G Gold Biscuits 250g", "பார்லே-ஜி பிஸ்கட் 250கி", "Packaged Foods & Snacks", "Biscuits", "Parle", "Pack", "250g", 24.0, 30.0, 30.0, 18.0, 30, 200, 60, 30, 1, 1, 82.0),
            ("890103000033", "Sunfeast Dark Fantasy Choco Fills 300g", "டார்க் பேண்டஸி சாக்லேட் பிஸ்கட் 300கி", "Packaged Foods & Snacks", "Cookies", "Sunfeast", "Box", "300g", 115.0, 145.0, 150.0, 18.0, 15, 90, 30, 15, 1, 1, 35.0),
            ("890103000034", "Britannia Good Day Butter 200g", "குட் டே வெண்ணெய் பிஸ்கட் 200கி", "Packaged Foods & Snacks", "Cookies", "Britannia", "Pack", "200g", 38.0, 48.0, 50.0, 18.0, 20, 140, 40, 20, 1, 1, 52.0),
            ("890103000035", "Kurkure Masala Munch 90g", "குர்குரே மசாலா முஞ்ச் 90கி", "Packaged Foods & Snacks", "Namkeen", "Kurkure", "Pouch", "90g", 16.0, 20.0, 20.0, 12.0, 25, 150, 50, 25, 1, 1, 74.0),
            ("890103000036", "Haldiram's Aloo Bhujia 150g", "ஹல்திராம் ஆலூ புஜியா 150கி", "Packaged Foods & Snacks", "Namkeen", "Haldiram's", "Pouch", "150g", 42.0, 55.0, 60.0, 12.0, 20, 120, 40, 20, 1, 1, 48.0),
            ("890103000037", "Maggi 2-Minute Masala Noodles 4-Pack 280g", "மேகி நூடுல்ஸ் 280கி", "Packaged Foods & Snacks", "Noodles", "Maggi", "Pack", "280g", 52.0, 64.0, 68.0, 18.0, 25, 160, 50, 25, 1, 1, 62.0),
            ("890103000038", "Imported Sugar-Free Wafer Biscuits 150g", "சுகர்-ஃப்ரீ வேபர் பிஸ்கட் 150கி", "Packaged Foods & Snacks", "Cookies", "Gullon", "Box", "150g", 160.0, 250.0, 275.0, 18.0, 10, 40, 15, 8, 8, 1, 28.0), # DEAD STOCK

            # Personal Care & Toiletries
            ("890103000039", "Hamam Neem Soap 100g (Pack of 3)", "ஹமாம் வேப்பிலை சோப் 100கி (3 பேக்)", "Personal Care & Toiletries", "Soap", "Hamam", "Pack", "3x100g", 115.0, 142.0, 150.0, 18.0, 20, 120, 40, 20, 1, 0, 46.0),
            ("890103000040", "Medimix Ayurvedic Soap 125g", "மேடிமிக்ஸ் ஆயுர்வேத சோப் 125கி", "Personal Care & Toiletries", "Soap", "Medimix", "Piece", "125g", 44.0, 56.0, 60.0, 18.0, 20, 130, 40, 20, 2, 0, 54.0),
            ("890103000041", "Clinic Plus Strong & Long Shampoo 340ml", "கிளினிக் பிளஸ் ஷாம்பு 340மி.லி", "Personal Care & Toiletries", "Shampoo", "Clinic Plus", "Bottle", "340ml", 175.0, 220.0, 235.0, 18.0, 15, 80, 25, 12, 1, 1, 4.0), # CRITICAL STOCKOUT
            ("890103000042", "Head & Shoulders Anti-Dandruff 180ml", "ஹெட் & ஷோல்டர்ஸ் ஷாம்பு 180மி.லி", "Personal Care & Toiletries", "Shampoo", "P&G", "Bottle", "180ml", 145.0, 185.0, 199.0, 18.0, 15, 75, 25, 12, 1, 1, 28.0),
            ("890103000043", "Colgate Strong Teeth Toothpaste 150g", "கோல்கேட் பற்பசை 150கி", "Personal Care & Toiletries", "Toothpaste", "Colgate", "Box", "150g", 82.0, 105.0, 112.0, 18.0, 20, 140, 45, 20, 1, 1, 58.0),
            ("890103000044", "Dettol Antiseptic Disinfectant Liquid 250ml", "டெட்டால் கிருமிநாசினி 250மி.லி", "Personal Care & Toiletries", "Antiseptic", "Dettol", "Bottle", "250ml", 125.0, 158.0, 168.0, 12.0, 15, 80, 25, 12, 1, 1, 32.0),

            # Household & Cleaning
            ("890103000045", "Surf Excel Quick Wash Detergent Powder 1kg", "சர்ப் எக்செல் சலவைத்தூள் 1கிலோ", "Household & Cleaning", "Detergent", "Surf Excel", "Pack", "1kg", 155.0, 195.0, 210.0, 18.0, 20, 120, 40, 20, 1, 0, 7.0), # CRITICAL
            ("890103000046", "Rin Detergent Bar 250g (Pack of 4)", "ரின் சலவை சோப் 250கி (4 பேக்)", "Household & Cleaning", "Detergent Bar", "Rin", "Pack", "4x250g", 64.0, 80.0, 85.0, 18.0, 25, 150, 45, 25, 1, 0, 62.0),
            ("890103000047", "Vim Dishwash Gel Lemon 500ml", "விம் டிஷ்வாஷ் ஜெல் 500மி.லி", "Household & Cleaning", "Dishwash", "Vim", "Bottle", "500ml", 112.0, 140.0, 150.0, 18.0, 15, 90, 30, 15, 1, 0, 38.0),
            ("890103000048", "Harpic Power Plus Disinfectant Toilet Cleaner 500ml", "ஹார்பிக் டாய்லெட் கிளீனர் 500மி.லி", "Household & Cleaning", "Cleaners", "Harpic", "Bottle", "500ml", 82.0, 102.0, 110.0, 18.0, 20, 110, 35, 15, 1, 0, 45.0),
            ("890103000049", "Lizol Disinfectant Floor Cleaner Citrus 1L", "லைசால் தரை தூய்மையாக்கி 1லி", "Household & Cleaning", "Cleaners", "Lizol", "Bottle", "1L", 185.0, 230.0, 245.0, 18.0, 15, 80, 25, 12, 1, 0, 33.0),
            ("890103000050", "Industrial Brass Polish 500ml", "பித்தளை பாலிஷ் திரவம் 500மி.லி", "Household & Cleaning", "Cleaners", "ShineMax", "Bottle", "500ml", 140.0, 220.0, 240.0, 18.0, 8, 30, 10, 5, 8, 0, 22.0), # DEAD STOCK

            # Stationery & Electronics
            ("890103000051", "Classmate Long Notebook 192 Pages Unruled", "கிளாஸ்மேட் நோட்டுப் புத்தகம் 192 பக்கங்கள்", "Stationery & Electronics", "Notebooks", "Classmate", "Piece", "192p", 52.0, 68.0, 75.0, 12.0, 25, 200, 50, 25, 1, 0, 80.0),
            ("890103000052", "Reynolds 045 Fine Carbure Ball Pen (Pack of 5)", "ரெனால்ட்ஸ் பேனா 5 பேக்", "Stationery & Electronics", "Pens", "Reynolds", "Pack", "5 pcs", 38.0, 50.0, 50.0, 18.0, 20, 150, 40, 20, 1, 0, 140.0), # OVERSTOCK
            ("890103000053", "Eveready AA Alkaline Batteries (Pack of 4)", "எவரெடி ஏஏ பேட்டரி 4 பேக்", "Stationery & Electronics", "Batteries", "Eveready", "Pack", "4 pcs", 115.0, 150.0, 160.0, 18.0, 15, 80, 25, 12, 1, 0, 36.0),
            ("890103000054", "Syska 9W Cool Daylight LED Bulb B22", "சிஸ்கா 9W எல்இடி பல்பு", "Stationery & Electronics", "Lighting", "Syska", "Piece", "9W", 65.0, 95.0, 120.0, 18.0, 20, 120, 35, 15, 1, 0, 48.0),
            ("890103000055", "GoodKnight Gold Flash Mosquito Bat", "கொசு பேட் ரீசார்ஜபிள்", "Stationery & Electronics", "Pest Control", "GoodKnight", "Piece", "1 pc", 320.0, 450.0, 499.0, 18.0, 8, 50, 15, 8, 1, 0, 18.0)
        ]

        prod_id_map = {}
        for (barcode, name, t_name, cat_name, subcat, brand, unit, pack_sz, pur_price, sell_price, mrp, gst, min_s, max_s, reorder_lvl, safety_s, pref_sup_idx, exp_app, init_stock) in raw_products:
            cat_id = cat_map.get(cat_name)
            pref_sup_id = sup_ids[pref_sup_idx - 1] if pref_sup_idx <= len(sup_ids) else sup_ids[0]

            cur = conn.execute(
                """
                INSERT INTO products (
                    barcode, name, tamil_name, category_id, subcategory, brand, unit, pack_size,
                    purchase_price, selling_price, mrp, gst_rate, min_stock, max_stock,
                    reorder_level, safety_stock, preferred_supplier_id, expiry_applicable, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (barcode, name, t_name, cat_id, subcat, brand, unit, pack_sz, pur_price, sell_price, mrp, gst, min_s, max_s, reorder_lvl, safety_s, pref_sup_id, exp_app)
            )
            p_id = cur.lastrowid
            prod_id_map[barcode] = p_id

            # Initialize inventory & opening stock
            conn.execute("INSERT INTO inventory (product_id, current_stock) VALUES (?, ?)", (p_id, init_stock))
            conn.execute(
                """
                INSERT INTO inventory_transactions (product_id, change_qty, balance_after, transaction_type, reference_id, reason)
                VALUES (?, ?, ?, 'OPENING', 'INITIAL-SETUP', 'Initial shop opening balance')
                """,
                (p_id, init_stock, init_stock)
            )

            # Link product to 2-3 suppliers for comparison
            # Supplier A (Fast, slightly higher cost)
            conn.execute(
                """
                INSERT INTO supplier_products (supplier_id, product_id, supplier_price, moq, delivery_time_days)
                VALUES (?, ?, ?, ?, ?)
                """,
                (pref_sup_id, p_id, pur_price, 5, random.choice([2, 3]))
            )
            # Supplier B (Slower, 3-5% cheaper)
            alt_sup_id = sup_ids[(pref_sup_idx % len(sup_ids))]
            if alt_sup_id != pref_sup_id:
                conn.execute(
                    """
                    INSERT INTO supplier_products (supplier_id, product_id, supplier_price, moq, delivery_time_days)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (alt_sup_id, p_id, round(pur_price * 0.96, 2), 15, random.choice([4, 5, 6]))
                )

        # 5. Product Batches for Perishables (FEFO demonstration)
        print("[Seed] Creating perishable product batches...")
        today = datetime.now().date()
        batches = [
            # Aavin Milk: Batch expiring in 2 days
            ("890103000021", "BATCH-AV-889", str(today - timedelta(days=2)), str(today + timedelta(days=2)), 30.0, 15.0),
            # Amul Butter: Batch expiring in 12 days
            ("890103000022", "BATCH-AM-402", str(today - timedelta(days=50)), str(today + timedelta(days=12)), 25.0, 18.0),
            # Paneer: Batch expiring in 6 days
            ("890103000023", "BATCH-MM-109", str(today - timedelta(days=10)), str(today + timedelta(days=6)), 20.0, 14.0),
            # Aashirvaad Atta 5kg: Expiring in 45 days
            ("890103000004", "BATCH-ASH-77", str(today - timedelta(days=30)), str(today + timedelta(days=45)), 50.0, 14.0),
            # Gold Winner 1L: Expiring in 90 days
            ("890103000016", "BATCH-GW-55", str(today - timedelta(days=40)), str(today + timedelta(days=90)), 60.0, 35.0)
        ]
        for barcode, b_num, mfg, exp, qty, rem in batches:
            p_id = prod_id_map.get(barcode)
            if p_id:
                conn.execute(
                    """
                    INSERT INTO product_batches (product_id, batch_number, mfg_date, expiry_date, quantity, remaining_qty)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (p_id, b_num, mfg, exp, qty, rem)
                )

        # 6. Historical Sales (180 Days of realistic transactions)
        print("[Seed] Generating 180 days of historical sales transactions...")
        start_date = today - timedelta(days=180)
        all_p_ids = list(prod_id_map.values())

        # Pull product pricing into memory for fast batch simulation
        p_info = {}
        for r in conn.execute("SELECT id, name, unit, selling_price, purchase_price, mrp, gst_rate FROM products").fetchall():
            p_info[r["id"]] = dict(r)

        # Indian payment methods
        payment_methods = ["UPI", "UPI", "CASH", "CASH", "DEBIT_CARD", "CREDIT_CARD"]
        customer_names = [
            "Walk-in Customer", "Walk-in Customer", "R. Murugan", "S. Lakshmi",
            "M. Karthik", "K. Meenakshi", "P. Senthil", "A. Subramanian",
            "V. Anitha", "T. Rajesh", "S. Gomathi", "D. Vijay"
        ]

        sales_inserts = []
        sale_items_inserts = []
        inv_trans_inserts = []

        dead_stock_ids = [prod_id_map.get(b) for b in ["890103000020", "890103000030", "890103000038", "890103000050"]]
        dead_stock_ids = [x for x in dead_stock_ids if x is not None]

        for day_offset in range(180):
            current_day = start_date + timedelta(days=day_offset)
            current_day_str = current_day.strftime('%Y-%m-%d')
            dow = current_day.weekday()
            is_weekend = dow in [5, 6]

            # Seasonal Pongal spike in mid-January, Diwali spike in early November
            is_pongal = (current_day.month == 1 and 12 <= current_day.day <= 16)
            is_diwali = (current_day.month == 11 and 1 <= current_day.day <= 5)
            
            # Orders per day
            num_orders = random.randint(12, 22)
            if is_weekend:
                num_orders += random.randint(8, 14)
            if is_pongal or is_diwali:
                num_orders = int(num_orders * 2.2)

            # Available products for this day (exclude dead stock for the last 75 days)
            eligible_p_ids = all_p_ids
            if day_offset > 105:
                eligible_p_ids = [p for p in all_p_ids if p not in dead_stock_ids]

            for order_idx in range(num_orders):
                hour = random.randint(8, 21)
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                ts_str = f"{current_day_str} {hour:02d}:{minute:02d}:{second:02d}"
                inv_no = f"INV-{current_day.strftime('%Y%m%d')}-{day_offset:03d}{order_idx:02d}"

                # 2 to 6 items per order
                cart_prod_ids = random.sample(eligible_p_ids, k=random.randint(2, 6))
                
                subtotal = 0.0
                total_gst = 0.0
                total_amount = 0.0
                order_items = []

                for prod_id in cart_prod_ids:
                    info = p_info[prod_id]
                    # Higher quantity for rice/atta/oil during festivals
                    qty = random.choice([1.0, 1.0, 2.0, 3.0])
                    if (is_pongal or is_diwali) and prod_id in all_p_ids[:15]:
                        qty += random.choice([1.0, 2.0])

                    price = info["selling_price"]
                    gst_r = info["gst_rate"]
                    line_tot = round(qty * price, 2)
                    base_u = price / (1.0 + gst_r / 100.0)
                    line_gst = round((price - base_u) * qty, 2)

                    subtotal += round(base_u * qty, 2)
                    total_gst += line_gst
                    total_amount += line_tot

                    order_items.append((prod_id, qty, price, info["mrp"], gst_r, line_gst, 0.0, line_tot))

                cust = random.choice(customer_names)
                pay_method = random.choice(payment_methods)

                # Insert sale
                cur_sale = conn.execute(
                    """
                    INSERT INTO sales (invoice_number, user_id, customer_name, subtotal, discount_amount, gst_amount, total_amount, payment_method, created_at)
                    VALUES (?, 3, ?, ?, 0.0, ?, ?, ?, ?)
                    """,
                    (inv_no, cust, round(subtotal, 2), round(total_gst, 2), round(total_amount, 2), pay_method, ts_str)
                )
                sale_id = cur_sale.lastrowid

                for p_id, qty, pr, mrp, gst_r, gst_amt, disc, l_tot in order_items:
                    conn.execute(
                        """
                        INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, mrp, gst_rate, gst_amount, discount, total)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (sale_id, p_id, qty, pr, mrp, gst_r, gst_amt, disc, l_tot)
                    )

        # 7. Physical Stock Audit Session with discrepancies
        print("[Seed] Creating physical stock audit with realistic discrepancies...")
        cur_aud = conn.execute(
            """
            INSERT INTO stock_audits (audit_number, conducted_by, status, notes, created_at)
            VALUES (?, 2, 'IN_PROGRESS', 'Monthly Physical Verification - Section A & B', CURRENT_TIMESTAMP)
            """,
            (f"AUD-{today.strftime('%Y%m%d')}-01",)
        )
        aud_id = cur_aud.lastrowid

        discrepancies = [
            # Aashirvaad Atta 5kg: System 14, physical 11 -> variance -3 (transit damage / shrinkage)
            (prod_id_map["890103000004"], 14.0, 11.0, -3.0, "Physical count is lower by 3 units. Possible causes: Unrecorded customer handling damage or loose bag tear at back warehouse."),
            # Tata Salt: System 85, physical 82 -> variance -3 (cashier barcode miss)
            (prod_id_map["890103000010"], 85.0, 82.0, -3.0, "Physical count is lower by 3 units. Possible causes: Multi-pack checkout scan skip during peak evening hours."),
            # Gold Winner 1L: System 35, physical 37 -> variance +2 (supplier over-delivery)
            (prod_id_map["890103000016"], 35.0, 37.0, 2.0, "Physical count is higher by 2 units. Possible causes: Supplier box pack contained 12 units instead of invoiced 10 units.")
        ]
        for p_id, sys_s, phys_s, var_q, cause in discrepancies:
            conn.execute(
                """
                INSERT INTO stock_audit_items (audit_id, product_id, system_stock, physical_stock, variance_qty, ai_likely_cause)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (aud_id, p_id, sys_s, phys_s, var_q, cause)
            )

        # 8. Customer Returns
        print("[Seed] Creating customer return records...")
        conn.execute(
            """
            INSERT INTO returns (return_number, product_id, quantity, refund_amount, return_reason, customer_name, created_by, created_at)
            VALUES (?, ?, 1.0, 290.0, 'Pouch outer seal tear during transport', 'R. Murugan', 3, CURRENT_TIMESTAMP)
            """,
            (f"RET-{today.strftime('%Y%m%d')}-01", prod_id_map["890103000004"])
        )

        # 9. Festivals Table
        print("[Seed] Populating Tamil Nadu festival calendar...")
        fest_path = Path(__file__).resolve().parent / "festivals_tn.json"
        if fest_path.exists():
            with open(fest_path, "r", encoding="utf-8") as f:
                f_data = json.load(f)
                for fest in f_data:
                    conn.execute(
                        """
                        INSERT INTO festivals (name, tamil_name, month, day, duration_days, affected_categories, demand_multiplier, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            fest["name"],
                            fest["tamil_name"],
                            fest["month"],
                            fest["day"],
                            fest["duration_days"],
                            json.dumps(fest["affected_categories"]),
                            fest["demand_multiplier"],
                            fest["notes"]
                        )
                    )

        conn.commit()
        print("[Seed] Database seeded successfully!")

        # 10. Run initial AI Agent Cycle to generate real recommendations
        print("[Seed] Running initial Agentic AI cycle to generate recommendation cards...")
        agent = InventoryAgent()
        cycle_res = agent.run_cycle()
        print(f"[Seed] AI Agent cycle complete: {cycle_res['new_or_updated_recommendations']} recommendations generated.")

    finally:
        conn.close()

def check_and_seed():
    """Checks if database needs initial seeding."""
    conn = get_db()
    try:
        cur = conn.execute("SELECT COUNT(*) as count FROM products")
        cnt = cur.fetchone()["count"]
        if cnt < 10:
            seed_database()
        else:
            print(f"[Seed] Database ready with {cnt} products.")
    finally:
        conn.close()

if __name__ == "__main__":
    seed_database()
