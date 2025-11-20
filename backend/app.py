from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import hashlib
import os
from datetime import datetime
import math
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='../static')
CORS(app)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
ALLOWED_EXTENSIONS_IMAGES = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_EXTENSIONS_DOCS = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure upload directories exist
os.makedirs(os.path.join(UPLOAD_FOLDER, 'users'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'businesses'), exist_ok=True)

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.db')

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_client_ip():
    """Get client IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr

def log_user_activity(user_id, user_type, email, action, latitude=None, longitude=None):
    """Log user activity"""
    conn = get_db()
    cursor = conn.cursor()
    ip_address = get_client_ip()
    
    cursor.execute('''
        INSERT INTO user_activity (user_id, user_type, email, ip_address, latitude, longitude, action)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, user_type, email, ip_address, latitude, longitude, action))
    
    conn.commit()
    conn.close()

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    R = 6371  # Earth's radius in kilometers
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distance = R * c
    return round(distance, 2)

def allowed_file(filename, file_type='image'):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    if file_type == 'image':
        return ext in ALLOWED_EXTENSIONS_IMAGES
    elif file_type == 'document':
        return ext in ALLOWED_EXTENSIONS_DOCS
    return False

def check_nearby_users(business_lat, business_lon, business_id, business_name, radius_km=10):
    """Check for users within radius and create notifications"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get all users with location
    cursor.execute('SELECT id, name, email, latitude, longitude FROM users WHERE latitude IS NOT NULL')
    users = cursor.fetchall()
    
    notifications_created = 0
    
    for user in users:
        distance = calculate_distance(user['latitude'], user['longitude'], business_lat, business_lon)
        
        if distance <= radius_km:
            # Create notification
            title = f"New Business Near You! 🎉"
            message = f"{business_name} just registered {distance}km away from you!"
            
            cursor.execute('''
                INSERT INTO notifications (user_id, business_id, title, message)
                VALUES (?, ?, ?, ?)
            ''', (user['id'], business_id, title, message))
            
            notifications_created += 1
    
    conn.commit()
    conn.close()
    
    return notifications_created

# ============ SERVE STATIC FILES ============
@app.route('/')
def serve_index():
    return send_from_directory('../static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../static', path)

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# ============ USER ENDPOINTS ============
@app.route('/api/user/register', methods=['POST'])
def user_register():
    """Register a new user"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not name or not email or not password:
            return jsonify({'error': 'All fields are required'}), 400
        
        password_hash = hash_password(password)
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (name, email, password_hash, latitude, longitude)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, email, password_hash, latitude, longitude))
            
            user_id = cursor.lastrowid
            conn.commit()
            
            # Log activity
            log_user_activity(user_id, 'user', email, 'register', latitude, longitude)
            
            # Get user data
            cursor.execute('SELECT id, name, email, profile_photo FROM users WHERE id = ?', (user_id,))
            user = dict(cursor.fetchone())
            
            conn.close()
            
            return jsonify({
                'message': 'Registration successful!',
                'user': user
            }), 201
            
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Email already exists'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/login', methods=['POST'])
def user_login():
    """User login"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        password_hash = hash_password(password)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Case-insensitive search for email, but password hash must match
        cursor.execute('''
            SELECT id, name, email, profile_photo 
            FROM users 
            WHERE LOWER(email) = ? AND password_hash = ?
        ''', (email, password_hash))
        
        user = cursor.fetchone()
        
        if user:
            user_dict = dict(user)
            
            # Update user location
            if latitude and longitude:
                cursor.execute('''
                    UPDATE users SET latitude = ?, longitude = ? WHERE id = ?
                ''', (latitude, longitude, user_dict['id']))
                conn.commit()
            
            # Log activity
            log_user_activity(user_dict['id'], 'user', email, 'login', latitude, longitude)
            
            conn.close()
            
            return jsonify({
                'message': 'Login successful!',
                'user': user_dict
            }), 200
        else:
            conn.close()
            return jsonify({'error': 'Invalid email or password'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/upload-photo', methods=['POST'])
def upload_user_photo():
    """Upload user profile photo"""
    try:
        if 'photo' not in request.files:
            return jsonify({'error': 'No photo provided'}), 400
        
        file = request.files['photo']
        user_id = request.form.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename, 'image'):
            return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP'}), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"user_{user_id}_{timestamp}_{filename}"
        
        filepath = os.path.join(UPLOAD_FOLDER, 'users', filename)
        file.save(filepath)
        
        # Update database
        photo_path = f"/uploads/users/{filename}"
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET profile_photo = ? WHERE id = ?', (photo_path, user_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Photo uploaded successfully!',
            'photo_url': photo_path
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/remove-photo', methods=['POST'])
def remove_user_photo():
    """Remove user profile photo"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        # Get current photo path
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT profile_photo FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user and user['profile_photo']:
            # Delete file from filesystem
            photo_path = user['profile_photo'].replace('/uploads/', '')
            full_path = os.path.join(UPLOAD_FOLDER, photo_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        
        # Update database
        cursor.execute('UPDATE users SET profile_photo = NULL WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Photo removed successfully!'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/delete', methods=['POST'])
def delete_user_account():
    """Delete user account and all related data"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
            
        conn = get_db()
        cursor = conn.cursor()
        
        # 1. Get user info to delete photo file
        cursor.execute('SELECT profile_photo FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        if user and user['profile_photo']:
            photo_path = user['profile_photo'].replace('/uploads/', '')
            full_path = os.path.join(UPLOAD_FOLDER, photo_path)
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                except:
                    pass # Ignore file deletion errors
        
        # 2. Delete related records (Manual Cascade)
        cursor.execute('DELETE FROM favorites WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM notifications WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM user_activity WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM bookings WHERE user_id = ?', (user_id,))
        
        # 3. Delete user
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Account deleted successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ BUSINESS ENDPOINTS ============
@app.route('/api/business/register', methods=['POST'])
def business_register():
    """Register a new business"""
    try:
        data = request.get_json()
        business_name = data.get('business_name', '').strip()
        owner_name = data.get('owner_name', '').strip()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone')
        business_type = data.get('business_type')
        address = data.get('address')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        website = data.get('website', '')
        password = data.get('password')
        services = data.get('services', [])
        
        if not all([business_name, owner_name, email, phone, business_type, address, latitude, longitude, password]):
            return jsonify({'error': 'All required fields must be filled'}), 400
        
        password_hash = hash_password(password)
        
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO businesses (business_name, owner_name, email, phone, business_type,
                                       address, latitude, longitude, website, password_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (business_name, owner_name, email, phone, business_type, address,
                  float(latitude), float(longitude), website, password_hash))
            
            business_id = cursor.lastrowid
            
            # Add services
            for service in services:
                cursor.execute('''
                    INSERT INTO services (business_id, service_name, price)
                    VALUES (?, ?, ?)
                ''', (business_id, service['name'], float(service['price'])))
            
            conn.commit()
            
            # Log activity
            log_user_activity(business_id, 'business', email, 'register', latitude, longitude)
            
            # Check for nearby users and create notifications
            notifications_count = check_nearby_users(float(latitude), float(longitude), business_id, business_name)
            
            conn.close()
            
            return jsonify({
                'message': f'Business registered successfully! {notifications_count} nearby users notified.',
                'business_id': business_id
            }), 201
            
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': 'Email already exists'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/business/login', methods=['POST'])
def business_login():
    """Business login"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '').strip()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        password_hash = hash_password(password)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Case-insensitive search for email, but password hash must match
        cursor.execute('''
            SELECT id, business_name, owner_name, email, phone, business_type, 
                   address, verified, verification_doc
            FROM businesses 
            WHERE LOWER(email) = ? AND password_hash = ?
        ''', (email, password_hash))
        
        business = cursor.fetchone()
        
        if business:
            business_dict = dict(business)
            
            # Log activity
            log_user_activity(business_dict['id'], 'business', email, 'login', latitude, longitude)
            
            conn.close()
            
            return jsonify({
                'message': 'Login successful!',
                'business': business_dict
            }), 200
        else:
            conn.close()
            return jsonify({'error': 'Invalid email or password'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/business/upload-document', methods=['POST'])
def upload_business_document():
    """Upload business verification document"""
    try:
        if 'document' not in request.files:
            return jsonify({'error': 'No document provided'}), 400
        
        file = request.files['document']
        business_id = request.form.get('business_id')
        
        if not business_id:
            return jsonify({'error': 'Business ID required'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename, 'document'):
            return jsonify({'error': 'Invalid file type. Allowed: PDF, DOC, DOCX, JPG, PNG'}), 400
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"business_{business_id}_{timestamp}_{filename}"
        
        filepath = os.path.join(UPLOAD_FOLDER, 'businesses', filename)
        file.save(filepath)
        
        # Update database
        doc_path = f"/uploads/businesses/{filename}"
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE businesses SET verification_doc = ? WHERE id = ?', (doc_path, business_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Document uploaded successfully!',
            'document_url': doc_path
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/business/remove-document', methods=['POST'])
def remove_business_document():
    """Remove business verification document"""
    try:
        data = request.get_json()
        business_id = data.get('business_id')
        
        if not business_id:
            return jsonify({'error': 'Business ID required'}), 400
        
        # Get current document path
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT verification_doc FROM businesses WHERE id = ?', (business_id,))
        business = cursor.fetchone()
        
        if business and business['verification_doc']:
            # Delete file from filesystem
            doc_path = business['verification_doc'].replace('/uploads/', '')
            full_path = os.path.join(UPLOAD_FOLDER, doc_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        
        # Update database
        cursor.execute('UPDATE businesses SET verification_doc = NULL WHERE id = ?', (business_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Document removed successfully!'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ SEARCH & DISCOVERY ============
@app.route('/api/businesses/nearby', methods=['POST'])
def get_nearby_businesses():
    """Get businesses near user location"""
    try:
        data = request.get_json()
        user_lat = data.get('latitude')
        user_lon = data.get('longitude')
        radius = data.get('radius', 50)  # Default 50km radius
        business_type = data.get('business_type')
        
        conn = get_db()
        cursor = conn.cursor()
        
        query = '''
            SELECT b.*, GROUP_CONCAT(s.service_name || ' ($' || s.price || ')') as services
            FROM businesses b
            LEFT JOIN services s ON b.id = s.business_id
            WHERE b.verified = 1
        '''
        
        params = []
        
        if business_type:
            query += ' AND b.business_type = ?'
            params.append(business_type)
        
        query += ' GROUP BY b.id'
        
        cursor.execute(query, params)
        businesses = cursor.fetchall()
        
        # Calculate distances
        result = []
        for biz in businesses:
            biz_dict = dict(biz)
            
            if user_lat and user_lon:
                distance = calculate_distance(user_lat, user_lon, biz_dict['latitude'], biz_dict['longitude'])
                
                if distance <= radius:
                    biz_dict['distance'] = distance
                    result.append(biz_dict)
            else:
                biz_dict['distance'] = None
                result.append(biz_dict)
        
        # Sort by distance if available
        if user_lat and user_lon:
            result.sort(key=lambda x: x['distance'] if x['distance'] is not None else float('inf'))
        
        conn.close()
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/businesses/search', methods=['GET'])
def search_businesses():
    """Search businesses by name"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify([]), 200
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT b.*, GROUP_CONCAT(s.service_name || ' ($' || s.price || ')') as services
            FROM businesses b
            LEFT JOIN services s ON b.id = s.business_id
            WHERE b.verified = 1 
            AND (b.business_name LIKE ? OR b.address LIKE ? OR b.business_type LIKE ?)
            GROUP BY b.id
            LIMIT 20
        ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
        
        businesses = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(businesses), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ NOTIFICATIONS ============
@app.route('/api/user/<int:user_id>/notifications', methods=['GET'])
def get_user_notifications(user_id):
    """Get user notifications"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT n.*, b.business_name, b.business_type, b.address
            FROM notifications n
            JOIN businesses b ON n.business_id = b.id
            WHERE n.user_id = ?
            ORDER BY n.created_at DESC
            LIMIT 50
        ''', (user_id,))
        
        notifications = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(notifications), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<int:user_id>/notifications/unread', methods=['GET'])
def get_unread_notifications(user_id):
    """Get unread notification count"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) as count FROM notifications 
            WHERE user_id = ? AND is_read = 0
        ''', (user_id,))
        
        count = cursor.fetchone()['count']
        conn.close()
        
        return jsonify({'count': count}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
def mark_notification_read(notification_id):
    """Mark notification as read"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE notifications SET is_read = 1 WHERE id = ?', (notification_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Notification marked as read'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ FAVORITES ============
@app.route('/api/user/<int:user_id>/favorites', methods=['GET'])
def get_user_favorites(user_id):
    """Get user's favorite businesses"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT b.*, GROUP_CONCAT(s.service_name || ' ($' || s.price || ')') as services
            FROM favorites f
            JOIN businesses b ON f.business_id = b.id
            LEFT JOIN services s ON b.id = s.business_id
            WHERE f.user_id = ?
            GROUP BY b.id
        ''', (user_id,))
        
        favorites = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify(favorites), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<int:user_id>/favorites/<int:business_id>', methods=['POST'])
def add_favorite(user_id, business_id):
    """Add business to favorites"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO favorites (user_id, business_id)
                VALUES (?, ?)
            ''', (user_id, business_id))
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Added to favorites'}), 200
            
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'message': 'Already in favorites'}), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<int:user_id>/favorites/<int:business_id>', methods=['DELETE'])
def remove_favorite(user_id, business_id):
    """Remove business from favorites"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM favorites 
            WHERE user_id = ? AND business_id = ?
        ''', (user_id, business_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Removed from favorites'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ ACTIVITY TRACKING ============
@app.route('/api/user/activity', methods=['POST'])
def track_activity():
    """Track user activity"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        user_type = data.get('user_type')
        email = data.get('email')
        action = data.get('action')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        log_user_activity(user_id, user_type, email, action, latitude, longitude)
        
        return jsonify({'message': 'Activity tracked'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize database
    from database import init_db, add_sample_data
    init_db()
    add_sample_data()
    
    print("=" * 60)
    print(" BOOK&BLOOM Beta Server Starting... ")
    print("=" * 60)
    print("Server: http://localhost:5000")
    print("Upload folders ready:")
    print(f"  - Users: {os.path.join(UPLOAD_FOLDER, 'users')}")
    print(f"  - Businesses: {os.path.join(UPLOAD_FOLDER, 'businesses')}")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
