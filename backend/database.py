import sqlite3
import os
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.db')

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table (with profile photo)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            profile_photo TEXT,
            latitude REAL,
            longitude REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Businesses table (with documents)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            owner_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            business_type TEXT NOT NULL,
            address TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            website TEXT,
            verified INTEGER DEFAULT 0,
            password_hash TEXT NOT NULL,
            verification_doc TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Services table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            service_name TEXT NOT NULL,
            price REAL NOT NULL,
            duration TEXT,
            description TEXT,
            FOREIGN KEY (business_id) REFERENCES businesses(id)
        )
    ''')
    
    # Business photos table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS business_photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            photo_path TEXT NOT NULL,
            FOREIGN KEY (business_id) REFERENCES businesses(id)
        )
    ''')
    
    # Bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            business_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            booking_date TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (business_id) REFERENCES businesses(id),
            FOREIGN KEY (service_id) REFERENCES services(id)
        )
    ''')
    
    # Favorites table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            business_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (business_id) REFERENCES businesses(id),
            UNIQUE(user_id, business_id)
        )
    ''')
    
    # User activity tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_type TEXT NOT NULL,
            email TEXT NOT NULL,
            ip_address TEXT,
            latitude REAL,
            longitude REAL,
            action TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Notifications table (NEW!)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            business_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (business_id) REFERENCES businesses(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def add_sample_data():
    """Add sample businesses for testing"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) FROM businesses")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print("Sample data already exists!")
        conn.close()
        return
    
    # Sample businesses across all Canadian provinces
    businesses = [
        # Ontario - Toronto
        {'business_name': 'Toronto Glow Spa', 'owner_name': 'Sarah Johnson', 'email': 'sarah@toglow.com', 'phone': '(416) 555-0101', 'business_type': 'Spa', 'address': '123 Yonge St, Toronto, ON M5C 1W4', 'latitude': 43.6532, 'longitude': -79.3832, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Full Body Massage', 120.00), ('Facial', 90.00)]},
        {'business_name': 'Queen Street Salon', 'owner_name': 'David Chen', 'email': 'david@queensalon.com', 'phone': '(416) 555-0202', 'business_type': 'Salon', 'address': '456 Queen St W, Toronto, ON M5V 2A8', 'latitude': 43.6487, 'longitude': -79.3962, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Haircut', 60.00), ('Coloring', 150.00)]},
        {'business_name': 'Yorkville Beauty', 'owner_name': 'Emma Wilson', 'email': 'emma@yorkvillebeauty.com', 'phone': '(416) 555-0303', 'business_type': 'Makeup', 'address': '789 Bloor St, Toronto, ON M4W 1A9', 'latitude': 43.6708, 'longitude': -79.3899, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Bridal Makeup', 200.00), ('Lash Extensions', 85.00)]},
        
        # Ontario - Ottawa
        {'business_name': 'Capital Skin Clinic', 'owner_name': 'Dr. Robert Brown', 'email': 'robert@capitalskin.com', 'phone': '(613) 555-0707', 'business_type': 'Skin Care', 'address': '50 Rideau St, Ottawa, ON K1N 9J7', 'latitude': 45.4215, 'longitude': -75.6972, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Dermatology Consult', 150.00), ('Laser Treatment', 200.00)]},
        {'business_name': 'ByWard Nails', 'owner_name': 'Sophie Martin', 'email': 'sophie@bywardnails.com', 'phone': '(613) 555-0808', 'business_type': 'Nails', 'address': '100 ByWard Market, Ottawa, ON K1N 7A1', 'latitude': 45.4267, 'longitude': -75.6927, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Gel Manicure', 55.00), ('Pedicure', 65.00)]},
        
        # British Columbia - Vancouver
        {'business_name': 'Pacific Wellness', 'owner_name': 'Emily Wong', 'email': 'emily@pacificwellness.com', 'phone': '(604) 555-0303', 'business_type': 'Spa', 'address': '789 Granville St, Vancouver, BC V6Z 1K9', 'latitude': 49.2827, 'longitude': -123.1207, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Hot Stone Massage', 140.00), ('Aromatherapy', 95.00)]},
        {'business_name': 'Gastown Barbers', 'owner_name': 'Mike Smith', 'email': 'mike@gastownbarbers.com', 'phone': '(604) 555-0404', 'business_type': 'Salon', 'address': '321 Water St, Vancouver, BC V6B 1B8', 'latitude': 49.2849, 'longitude': -123.1116, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Men\'s Cut', 40.00), ('Beard Trim', 25.00)]},
        {'business_name': 'Kitsilano Spa', 'owner_name': 'Rachel Green', 'email': 'rachel@kitsilanospa.com', 'phone': '(604) 555-0505', 'business_type': 'Spa', 'address': '2000 W 4th Ave, Vancouver, BC V6J 1M9', 'latitude': 49.2688, 'longitude': -123.1540, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Swedish Massage', 110.00), ('Body Scrub', 85.00)]},
        
        # Quebec - Montreal
        {'business_name': 'Beauté Montréal', 'owner_name': 'Isabelle Tremblay', 'email': 'isabelle@beaute.com', 'phone': '(514) 555-0505', 'business_type': 'Makeup', 'address': '100 Rue Sainte-Catherine O, Montréal, QC H2X 3V4', 'latitude': 45.5017, 'longitude': -73.5673, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Bridal Makeup', 180.00), ('Evening Look', 95.00)]},
        {'business_name': 'Plateau Salon', 'owner_name': 'Jean-Pierre Dubois', 'email': 'jp@plateausalon.com', 'phone': '(514) 555-0606', 'business_type': 'Salon', 'address': '4500 Rue Saint-Denis, Montréal, QC H2J 2L3', 'latitude': 45.5234, 'longitude': -73.5800, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Haircut', 70.00), ('Balayage', 190.00)]},
        
        # Alberta - Calgary
        {'business_name': 'Stampede Nails', 'owner_name': 'Jessica Lee', 'email': 'jessica@stampedenails.com', 'phone': '(403) 555-0606', 'business_type': 'Nails', 'address': '200 8 Ave SW, Calgary, AB T2P 1B5', 'latitude': 51.0447, 'longitude': -114.0719, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Gel Nails', 65.00), ('Pedicure', 55.00)]},
        {'business_name': 'Kensington Beauty Bar', 'owner_name': 'Amanda Taylor', 'email': 'amanda@kensingtonbeauty.com', 'phone': '(403) 555-0707', 'business_type': 'Salon', 'address': '1100 Kensington Rd NW, Calgary, AB T2N 3P1', 'latitude': 51.0523, 'longitude': -114.0859, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Haircut', 65.00), ('Highlights', 160.00)]},
        
        # Alberta - Edmonton
        {'business_name': 'Whyte Avenue Spa', 'owner_name': 'Laura Mitchell', 'email': 'laura@whytespa.com', 'phone': '(780) 555-0808', 'business_type': 'Spa', 'address': '8208 104 St NW, Edmonton, AB T6E 4E6', 'latitude': 53.5190, 'longitude': -113.5110, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Deep Tissue Massage', 125.00), ('Reflexology', 80.00)]},
        
        # Manitoba - Winnipeg
        {'business_name': 'Exchange District Salon', 'owner_name': 'Michelle Anderson', 'email': 'michelle@exchangesalon.com', 'phone': '(204) 555-0909', 'business_type': 'Salon', 'address': '100 Arthur St, Winnipeg, MB R3B 1H3', 'latitude': 49.8951, 'longitude': -97.1384, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Haircut', 55.00), ('Keratin Treatment', 180.00)]},
        
        # Saskatchewan - Saskatoon
        {'business_name': 'Broadway Beauty', 'owner_name': 'Karen White', 'email': 'karen@broadwaybeauty.com', 'phone': '(306) 555-1010', 'business_type': 'Spa', 'address': '700 Broadway Ave, Saskatoon, SK S7N 1B4', 'latitude': 52.1332, 'longitude': -106.6700, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Facial', 85.00), ('Body Wrap', 95.00)]},
        
        # Nova Scotia - Halifax
        {'business_name': 'Halifax Harbour Spa', 'owner_name': 'Jennifer MacLeod', 'email': 'jennifer@halifaxspa.com', 'phone': '(902) 555-1111', 'business_type': 'Spa', 'address': '1869 Upper Water St, Halifax, NS B3J 1S9', 'latitude': 44.6488, 'longitude': -63.5752, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Seaweed Wrap', 110.00), ('Massage', 100.00)]},
        {'business_name': 'Spring Garden Nails', 'owner_name': 'Lisa Park', 'email': 'lisa@springgardennails.com', 'phone': '(902) 555-1212', 'business_type': 'Nails', 'address': '5640 Spring Garden Rd, Halifax, NS B3J 1H6', 'latitude': 44.6445, 'longitude': -63.5784, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Acrylic Nails', 70.00), ('Nail Art', 45.00)]},
        
        # New Brunswick - Moncton
        {'business_name': 'Moncton Makeup Studio', 'owner_name': 'Claire Leblanc', 'email': 'claire@monctonmakeup.com', 'phone': '(506) 555-1313', 'business_type': 'Makeup', 'address': '655 Main St, Moncton, NB E1C 1E8', 'latitude': 46.0878, 'longitude': -64.7782, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Wedding Makeup', 175.00), ('Makeup Lesson', 90.00)]},
        
        # Prince Edward Island - Charlottetown
        {'business_name': 'Island Beauty Boutique', 'owner_name': 'Anne Gallant', 'email': 'anne@islandbeauty.com', 'phone': '(902) 555-1414', 'business_type': 'Salon', 'address': '142 Great George St, Charlottetown, PE C1A 4K7', 'latitude': 46.2382, 'longitude': -63.1311, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Haircut', 50.00), ('Color', 140.00)]},
        
        # Newfoundland - St. John's
        {'business_name': 'Water Street Wellness', 'owner_name': 'Mary O\'Brien', 'email': 'mary@waterstreetwellness.com', 'phone': '(709) 555-1515', 'business_type': 'Spa', 'address': '200 Water St, St. John\'s, NL A1C 1A9', 'latitude': 47.5615, 'longitude': -52.7126, 'password_hash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', 'services': [('Massage Therapy', 105.00), ('Hydrotherapy', 95.00)]},
    ]
    
    for biz in businesses:
        # Insert business
        cursor.execute('''
            INSERT INTO businesses (business_name, owner_name, email, phone, business_type, 
                                   address, latitude, longitude, password_hash, verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (biz['business_name'], biz['owner_name'], biz['email'], biz['phone'],
              biz['business_type'], biz['address'], biz['latitude'], biz['longitude'],
              biz['password_hash']))
        
        business_id = cursor.lastrowid
        
        # Insert services
        for service_name, price in biz['services']:
            cursor.execute('''
                INSERT INTO services (business_id, service_name, price)
                VALUES (?, ?, ?)
            ''', (business_id, service_name, price))
    
    conn.commit()
    conn.close()
    print(f"Added {len(businesses)} sample businesses!")

if __name__ == '__main__':
    init_db()
    add_sample_data()
