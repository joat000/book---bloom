// BOOK&BLOOM - Clean Working Version
// All transitions, signup, and login properly implemented

let currentUser = null;
let userLocation = { lat: null, lon: null };
let map = null;
let userMarker = null;
let businessMarkers = [];
let allBusinesses = [];
let currentFilter = 'All';
let userFavorites = [];

// ============ PAGE NAVIGATION - CLEAN IMPLEMENTATION ============
function goToLanding() {
    showPage('landing-page');
}

function goToUserAuth() {
    showPage('user-auth-page');
}

function goToBusinessAuth() {
    showPage('business-auth-page');
}

function goToProfile() {
    showPage('profile-page');
    setTimeout(() => {
        initMap();

        // Auto-request location if not already set
        if (userLocation.lat === null || userLocation.lon === null) {
            enableLocation(true); // true = autoRetry, won't show "Requesting..." toast
        } else {
            loadBusinesses();
        }

        loadNotifications();
        loadFavorites();
        checkUnreadNotifications();
    }, 100);
}

function showPage(pageId) {
    // Hide all pages
    const allPages = document.querySelectorAll('.app-page');
    allPages.forEach(page => {
        page.classList.remove('active');
    });

    // Show target page
    setTimeout(() => {
        document.getElementById(pageId).classList.add('active');
    }, 400);
}

// ============ TAB SWITCHING ============
function switchUserTab(tabName) {
    // Update tab buttons
    const tabs = document.querySelectorAll('#user-auth-page .tab-btn');
    tabs.forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');

    // Update tab content
    document.getElementById('user-login-tab').classList.remove('active');
    document.getElementById('user-register-tab').classList.remove('active');

    if (tabName === 'login') {
        document.getElementById('user-login-tab').classList.add('active');
    } else {
        document.getElementById('user-register-tab').classList.add('active');
    }
}

function switchBusinessTab(tabName) {
    // Update tab buttons
    const tabs = document.querySelectorAll('#business-auth-page .tab-btn');
    tabs.forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');

    // Update tab content
    document.getElementById('business-login-tab').classList.remove('active');
    document.getElementById('business-register-tab').classList.remove('active');

    if (tabName === 'login') {
        document.getElementById('business-login-tab').classList.add('active');
    } else {
        document.getElementById('business-register-tab').classList.add('active');
    }
}

function switchSection(sectionName) {
    // Update menu items
    document.querySelectorAll('.menu-item').forEach(item => item.classList.remove('active'));
    event.currentTarget.classList.add('active');

    // Update content sections
    document.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));
    document.getElementById(`${sectionName}-section`).classList.add('active');

    // Load data for specific sections
    if (sectionName === 'notifications') {
        loadNotifications();
    } else if (sectionName === 'favorites') {
        loadFavorites();
    }
}

// Toggle mobile settings menu
function toggleMobileMenu() {
    const panel = document.getElementById('mobile-settings-panel');
    const overlay = document.getElementById('mobile-settings-overlay');

    panel.classList.toggle('active');
    overlay.classList.toggle('active');

    // Update remove photo button visibility in mobile menu
    const mobileRemoveBtn = document.getElementById('mobile-remove-photo');
    if (currentUser && currentUser.profile_photo) {
        mobileRemoveBtn.style.display = 'flex';
    } else {
        mobileRemoveBtn.style.display = 'none';
    }
}


// ============ FILE PREVIEW ============
function previewUserPhoto(input) {
    const preview = document.getElementById('user-photo-preview');
    if (input.files && input.files[0]) {
        preview.innerHTML = `✓ ${input.files[0].name}`;
        preview.classList.add('active');
    }
}

function previewBizDoc(input) {
    const preview = document.getElementById('biz-doc-preview');
    if (input.files && input.files[0]) {
        preview.innerHTML = `✓ ${input.files[0].name}`;
        preview.classList.add('active');
    }
}

// ============ USER AUTHENTICATION ============
async function handleUserLogin(event) {
    event.preventDefault();

    const email = document.getElementById('user-login-email').value;
    const password = document.getElementById('user-login-password').value;
    const btn = document.getElementById('user-login-btn');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Signing in...';

    try {
        const response = await fetch('/api/user/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email,
                password,
                latitude: userLocation.lat,
                longitude: userLocation.lon
            })
        });

        const data = await response.json();

        if (response.ok) {
            currentUser = { ...data.user, type: 'user' };
            localStorage.setItem('currentUser', JSON.stringify(currentUser));

            showToast('Login successful! Welcome back! 🎉', 'success');

            // Update profile
            updateProfileDisplay();

            setTimeout(() => goToProfile(), 1000);
        } else {
            showToast(data.error || 'Login failed', 'error');
        }
    } catch (error) {
        showToast('Network error. Please try again.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Sign In ✨';
    }
}

async function handleUserRegister(event) {
    event.preventDefault();

    const name = document.getElementById('user-reg-name').value;
    const email = document.getElementById('user-reg-email').value;
    const password = document.getElementById('user-reg-password').value;
    const photoFile = document.getElementById('user-photo-input').files[0];
    const btn = document.getElementById('user-reg-btn');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Creating account...';

    try {
        // Register user
        const response = await fetch('/api/user/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                email,
                password,
                latitude: userLocation.lat,
                longitude: userLocation.lon
            })
        });

        const data = await response.json();

        if (response.ok) {
            currentUser = { ...data.user, type: 'user' };

            // Upload photo if provided
            if (photoFile) {
                const formData = new FormData();
                formData.append('photo', photoFile);
                formData.append('user_id', currentUser.id);

                const uploadResponse = await fetch('/api/user/upload-photo', {
                    method: 'POST',
                    body: formData
                });

                if (uploadResponse.ok) {
                    const uploadData = await uploadResponse.json();
                    currentUser.profile_photo = uploadData.photo_url;
                }
            }

            localStorage.setItem('currentUser', JSON.stringify(currentUser));

            showToast('Account created successfully! Welcome! 🎉', 'success');

            // Update profile
            updateProfileDisplay();

            setTimeout(() => goToProfile(), 1000);
        } else {
            showToast(data.error || 'Registration failed', 'error');
        }
    } catch (error) {
        showToast('Network error. Please try again.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Create Account ✨';
    }
}

// ============ BUSINESS AUTHENTICATION ============
async function handleBusinessLogin(event) {
    event.preventDefault();

    const email = document.getElementById('business-login-email').value;
    const password = document.getElementById('business-login-password').value;
    const btn = document.getElementById('business-login-btn');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Signing in...';

    try {
        const response = await fetch('/api/business/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (response.ok) {
            showToast('Business login successful! 💼', 'success');
            setTimeout(() => {
                showToast('Business dashboard coming soon!', 'success');
                setTimeout(goToLanding, 2000);
            }, 1500);
        } else {
            showToast(data.error || 'Login failed', 'error');
        }
    } catch (error) {
        showToast('Network error. Please try again.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Sign In 💼';
    }
}

async function handleBusinessRegister(event) {
    event.preventDefault();

    const business_name = document.getElementById('biz-name').value;
    const owner_name = document.getElementById('biz-owner').value;
    const email = document.getElementById('biz-email').value;
    const phone = document.getElementById('biz-phone').value;
    const business_type = document.getElementById('biz-type').value;
    const address = document.getElementById('biz-address').value;
    const latitude = document.getElementById('biz-lat').value;
    const longitude = document.getElementById('biz-lon').value;
    const website = document.getElementById('biz-website').value;
    const password = document.getElementById('biz-password').value;
    const docFile = document.getElementById('biz-doc-input').files[0];
    const btn = document.getElementById('business-reg-btn');

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Registering...';

    try {
        const response = await fetch('/api/business/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                business_name,
                owner_name,
                email,
                phone,
                business_type,
                address,
                latitude,
                longitude,
                website,
                password,
                services: []
            })
        });

        const data = await response.json();

        if (response.ok) {
            const businessId = data.business_id;

            // Upload document if provided
            if (docFile) {
                const formData = new FormData();
                formData.append('document', docFile);
                formData.append('business_id', businessId);
                await fetch('/api/business/upload-document', {
                    method: 'POST',
                    body: formData
                });
            }

            showToast(data.message || 'Business registered! 🎉', 'success');

            setTimeout(() => {
                event.target.reset();
                switchBusinessTab('login');
            }, 2000);
        } else {
            showToast(data.error || 'Registration failed', 'error');
        }
    } catch (error) {
        showToast('Network error. Please try again.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Register Business 🌸';
    }
}

// ============ PROFILE MANAGEMENT ============
function updateProfileDisplay() {
    document.getElementById('profile-name').textContent = currentUser.name;
    document.getElementById('profile-email').textContent = currentUser.email;

    const photoEl = document.getElementById('profile-photo');
    const removeBtn = document.getElementById('profile-photo-remove');

    if (currentUser.profile_photo) {
        photoEl.innerHTML = `<img src="${currentUser.profile_photo}" alt="Profile">`;
        removeBtn.classList.add('active');
    } else {
        photoEl.innerHTML = '👤';
        removeBtn.classList.remove('active');
    }
}

async function uploadPhoto() {
    const input = document.getElementById('profile-photo-input');
    const file = input.files[0];

    if (!file || !currentUser) return;

    showToast('Uploading photo...', 'success');

    const formData = new FormData();
    formData.append('photo', file);
    formData.append('user_id', currentUser.id);

    try {
        const response = await fetch('/api/user/upload-photo', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            currentUser.profile_photo = data.photo_url;
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            updateProfileDisplay();
            showToast('Photo updated! ✓', 'success');
        } else {
            showToast(data.error || 'Upload failed', 'error');
        }
    } catch (error) {
        showToast('Upload failed', 'error');
    }
}

async function removePhoto() {
    if (!currentUser || !currentUser.profile_photo) return;

    if (!confirm('Remove your profile photo?')) return;

    try {
        const response = await fetch('/api/user/remove-photo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.id })
        });

        if (response.ok) {
            currentUser.profile_photo = null;
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            updateProfileDisplay();
            showToast('Photo removed! ✓', 'success');
        }
    } catch (error) {
        showToast('Failed to remove photo', 'error');
    }
}

function viewPhoto() {
    if (!currentUser || !currentUser.profile_photo) return;

    const modal = document.getElementById('photo-modal');
    const img = document.getElementById('photo-modal-img');
    modal.classList.add('active');
    img.src = currentUser.profile_photo;
}

function closePhotoModal() {
    document.getElementById('photo-modal').classList.remove('active');
}

// ============ LOCATION ============
function enableLocation(autoRetry = false) {
    console.log('🌍 [LOCATION] enableLocation() called, autoRetry:', autoRetry);

    if (!navigator.geolocation) {
        console.error('❌ [LOCATION] Geolocation API not supported');
        showToast('Geolocation not supported by your browser', 'error');
        getLocationFromIP(); // Try IP-based fallback
        return;
    }

    if (!autoRetry) {
        showToast('Requesting location access...', 'success');
    }

    console.log('📍 [LOCATION] Requesting browser geolocation...');

    navigator.geolocation.getCurrentPosition(
        (position) => {
            console.log('✅ [LOCATION] Browser geolocation SUCCESS:', {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude,
                accuracy: position.coords.accuracy
            });

            userLocation.lat = position.coords.latitude;
            userLocation.lon = position.coords.longitude;

            showToast(`Location found! ✓ (${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)})`, 'success');
            document.getElementById('location-status').classList.add('active');

            if (map) {
                map.setView([userLocation.lat, userLocation.lon], 13);

                if (userMarker) map.removeLayer(userMarker);

                userMarker = L.marker([userLocation.lat, userLocation.lon], {
                    icon: L.icon({
                        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                        iconSize: [25, 41],
                        iconAnchor: [12, 41],
                        popupAnchor: [1, -34],
                        shadowSize: [41, 41]
                    })
                }).addTo(map).bindPopup('📍 You are here!').openPopup();

                loadBusinesses();
            }
        },
        (error) => {
            console.error('❌ [LOCATION] Browser geolocation FAILED:', {
                code: error.code,
                message: error.message,
                PERMISSION_DENIED: error.PERMISSION_DENIED,
                POSITION_UNAVAILABLE: error.POSITION_UNAVAILABLE,
                TIMEOUT: error.TIMEOUT
            });

            let errorMessage = '';
            let detailedHelp = '';

            // Provide specific error messages
            switch (error.code) {
                case error.PERMISSION_DENIED:
                    errorMessage = '🚫 Location access denied';
                    detailedHelp = 'Please enable location permissions in your browser settings. On mobile, check your device location settings too.';
                    break;
                case error.POSITION_UNAVAILABLE:
                    errorMessage = '📡 Location unavailable';
                    detailedHelp = 'Your device cannot determine your location. Make sure GPS/location services are enabled.';
                    break;
                case error.TIMEOUT:
                    errorMessage = '⏱️ Location request timed out';
                    detailedHelp = 'Location detection is taking too long. Check your internet connection and try again.';
                    break;
                default:
                    errorMessage = '❌ Location error';
                    detailedHelp = 'An unknown error occurred while detecting your location.';
            }

            console.log(`📋 [LOCATION] Error details: ${errorMessage} - ${detailedHelp}`);
            showToast(`${errorMessage}. Trying IP-based location...`, 'warning');

            // Try IP-based geolocation as fallback
            getLocationFromIP();
        },
        {
            enableHighAccuracy: true,
            timeout: 30000, // 30 seconds for slower connections
            maximumAge: 300000 // Cache location for 5 minutes
        }
    );
}

// Get location from IP address (fallback method)
async function getLocationFromIP() {
    console.log('🌐 [IP-LOCATION] Attempting IP-based geolocation...');

    try {
        const response = await fetch('https://ipapi.co/json/');
        const data = await response.json();

        console.log('✅ [IP-LOCATION] IP geolocation SUCCESS:', data);

        if (data.latitude && data.longitude) {
            userLocation.lat = data.latitude;
            userLocation.lon = data.longitude;

            const locationName = data.city || data.region || data.country_name || 'Unknown';

            showToast(`📍 Location detected: ${locationName}, ${data.country_name}`, 'success');

            if (map) {
                map.setView([userLocation.lat, userLocation.lon], 12);

                if (userMarker) map.removeLayer(userMarker);

                userMarker = L.marker([userLocation.lat, userLocation.lon], {
                    icon: L.icon({
                        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
                        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                        iconSize: [25, 41],
                        iconAnchor: [12, 41],
                        popupAnchor: [1, -34],
                        shadowSize: [41, 41]
                    })
                }).addTo(map).bindPopup(`📍 ${locationName} (IP-based)`).openPopup();

                loadBusinesses();
            }

            const statusEl = document.getElementById('location-status');
            if (statusEl) {
                statusEl.textContent = `📍 ${locationName} (IP-based)`;
                statusEl.style.display = 'block';
            }
        } else {
            throw new Error('No coordinates in IP response');
        }
    } catch (error) {
        console.error('❌ [IP-LOCATION] IP geolocation FAILED:', error);
        showToast('Could not detect location. Using default (Toronto).', 'warning');
        setDefaultLocation();
    }
}

// Set default location (Toronto) when geolocation fails
function setDefaultLocation() {
    userLocation.lat = 43.6532;
    userLocation.lon = -79.3832;

    if (map) {
        map.setView([userLocation.lat, userLocation.lon], 12);
        loadBusinesses();
    }

    document.getElementById('location-status')?.classList.remove('active');
}

// ============ MAP ============
function initMap() {
    if (map) return;

    // Default to Toronto
    map = L.map('map').setView([43.6532, -79.3832], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    enableLocation();
}

// ============ BUSINESSES ============
async function loadBusinesses() {
    try {
        const response = await fetch('/api/businesses/nearby', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                latitude: userLocation.lat,
                longitude: userLocation.lon,
                radius: 10000, // 10,000km radius to show all Canadian businesses
                business_type: currentFilter === 'All' ? null : currentFilter
            })
        });

        allBusinesses = await response.json();
        displayBusinesses(allBusinesses);
        displayBusinessMarkers(allBusinesses);
    } catch (error) {
        console.error('Error loading businesses:', error);
    }
}

function displayBusinesses(businesses) {
    const grid = document.getElementById('businesses-grid');

    if (businesses.length === 0) {
        grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #b8a9d6;"><p>🔍</p><p>No businesses found</p></div>';
        return;
    }

    grid.innerHTML = businesses.map(biz => `
        <div class="business-card">
            <button class="favorite-btn ${isFavorite(biz.id) ? 'active' : ''}" onclick="event.stopPropagation(); toggleFavorite(${biz.id})">
                ${isFavorite(biz.id) ? '❤️' : '🤍'}
            </button>
            <div class="business-type-badge">${biz.business_type}</div>
            <div class="business-name">${biz.business_name}</div>
            <div class="business-address">📍 ${biz.address}</div>
            ${biz.distance ? `<div class="business-distance">📏 ${formatDistance(biz.distance)}</div>` : ''}
        </div>
    `).join('');
}

function displayBusinessMarkers(businesses) {
    businessMarkers.forEach(marker => map.removeLayer(marker));
    businessMarkers = [];

    businesses.forEach(biz => {
        const marker = L.marker([biz.latitude, biz.longitude], {
            icon: L.icon({
                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                iconSize: [25, 41],
                iconAnchor: [12, 41],
                popupAnchor: [1, -34],
                shadowSize: [41, 41]
            })
        }).addTo(map).bindPopup(`<strong>${biz.business_name}</strong><br>${biz.business_type}<br>${biz.address}`);

        businessMarkers.push(marker);
    });
}

function filterBusinesses(type) {
    currentFilter = type;
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    loadBusinesses();
}

function formatDistance(km) {
    return km < 1 ? `${Math.round(km * 1000)}m` : `${km}km`;
}

// ============ SEARCH ============
async function performSearch() {
    const input = document.getElementById('search-input');
    if (!input || !input.value.trim()) return;

    const query = input.value.trim();
    showToast('Searching...', 'success');

    try {
        // 1. Try to geocode as a city/location first
        const geocodeResponse = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}`);
        const geocodeData = await geocodeResponse.json();

        if (geocodeData && geocodeData.length > 0) {
            const location = geocodeData[0];
            const lat = parseFloat(location.lat);
            const lon = parseFloat(location.lon);

            // Update user location context
            userLocation.lat = lat;
            userLocation.lon = lon;

            // Move map
            if (map) {
                map.setView([lat, lon], 13);
                L.popup()
                    .setLatLng([lat, lon])
                    .setContent(`📍 ${location.display_name.split(',')[0]}`)
                    .openOn(map);
            }

            showToast(`Found ${location.display_name.split(',')[0]}! Searching nearby...`, 'success');
            loadBusinesses();
            return;
        }

        // 2. Fallback to name search
        const response = await fetch(`/api/businesses/search?q=${encodeURIComponent(query)}`);
        const businesses = await response.json();
        allBusinesses = businesses;
        displayBusinesses(businesses);
        displayBusinessMarkers(businesses);

        if (businesses.length > 0) {
            showToast(`Found ${businesses.length} businesses`, 'success');
        } else {
            showToast('No businesses or locations found', 'error');
        }

    } catch (error) {
        console.error('Search error:', error);
        showToast('Search failed. Please try again.', 'error');
    }
}

document.getElementById('search-input')?.addEventListener('keyup', (e) => {
    if (e.key === 'Enter') performSearch();
});

// ============ ACCOUNT DELETION ============
async function deleteAccount() {
    if (!currentUser) return;

    if (!confirm('⚠️ ARE YOU SURE?\n\nThis will permanently delete your account and all your data.\nThis action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch('/api/user/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.id })
        });

        if (response.ok) {
            showToast('Account deleted successfully. Goodbye! 👋', 'success');
            localStorage.removeItem('currentUser');
            currentUser = null;
            setTimeout(goToLanding, 2000);
        } else {
            const data = await response.json();
            showToast(data.error || 'Failed to delete account', 'error');
        }
    } catch (error) {
        showToast('Network error. Please try again.', 'error');
    }
}

// ============ NOTIFICATIONS ============
async function loadNotifications() {
    if (!currentUser) return;

    try {
        const response = await fetch(`/api/user/${currentUser.id}/notifications`);
        const notifications = await response.json();

        const list = document.getElementById('notifications-list');

        if (notifications.length === 0) {
            list.innerHTML = '<p style="color: #b8a9d6; text-align: center; padding: 40px;">No notifications yet</p>';
            return;
        }

        list.innerHTML = notifications.map(notif => `
            <div class="notification-item ${notif.is_read ? '' : 'unread'}" onclick="markNotificationRead(${notif.id})">
                <div class="notification-title">${notif.title}</div>
                <div class="notification-message">${notif.message}</div>
                <div class="notification-time">${new Date(notif.created_at).toLocaleString()}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

async function checkUnreadNotifications() {
    if (!currentUser) return;

    try {
        const response = await fetch(`/api/user/${currentUser.id}/notifications/unread`);
        const data = await response.json();

        const badge = document.getElementById('notification-count');

        if (data.count > 0) {
            badge.textContent = data.count;
            badge.classList.add('active');
        } else {
            badge.classList.remove('active');
        }
    } catch (error) {
        console.error('Error checking notifications:', error);
    }
}

async function markNotificationRead(notificationId) {
    try {
        await fetch(`/api/notifications/${notificationId}/read`, { method: 'POST' });
        loadNotifications();
        checkUnreadNotifications();
    } catch (error) {
        console.error('Error marking notification read:', error);
    }
}

// ============ FAVORITES ============
async function loadFavorites() {
    if (!currentUser) return;

    try {
        const response = await fetch(`/api/user/${currentUser.id}/favorites`);
        userFavorites = await response.json();

        const grid = document.getElementById('favorites-grid');

        if (userFavorites.length === 0) {
            grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #b8a9d6;"><p style="font-size: 3rem;">❤️</p><p>No favorites yet</p></div>';
            return;
        }

        grid.innerHTML = userFavorites.map(biz => `
            <div class="business-card">
                <button class="favorite-btn active" onclick="event.stopPropagation(); toggleFavorite(${biz.id})">❤️</button>
                <div class="business-type-badge">${biz.business_type}</div>
                <div class="business-name">${biz.business_name}</div>
                <div class="business-address">📍 ${biz.address}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading favorites:', error);
    }
}

function isFavorite(businessId) {
    return userFavorites.some(fav => fav.id === businessId);
}

async function toggleFavorite(businessId) {
    if (!currentUser) {
        showToast('Please login to add favorites', 'error');
        return;
    }

    const isFav = isFavorite(businessId);

    try {
        if (isFav) {
            await fetch(`/api/user/${currentUser.id}/favorites/${businessId}`, { method: 'DELETE' });
            userFavorites = userFavorites.filter(fav => fav.id !== businessId);
            showToast('Removed from favorites', 'success');
        } else {
            await fetch(`/api/user/${currentUser.id}/favorites/${businessId}`, { method: 'POST' });
            showToast('Added to favorites ❤️', 'success');
            loadFavorites();
        }

        loadBusinesses();
    } catch (error) {
        console.error('Error toggling favorite:', error);
    }
}

// ============ LOGOUT ============
function logout() {
    localStorage.removeItem('currentUser');
    currentUser = null;
    userLocation = { lat: null, lon: null };
    showToast('Logged out successfully', 'success');
    setTimeout(goToLanding, 1000);
}

// ============ TOAST ============
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => toast.classList.remove('show'), 3000);
}

// ============ INITIALIZATION ============
document.addEventListener('DOMContentLoaded', () => {
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        updateProfileDisplay();
        goToProfile();
    }
});
