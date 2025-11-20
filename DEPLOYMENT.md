# Book & Bloom - Deployment Guide (Updated)

## 🚀 Deploy to Render - CORRECT SETTINGS

### IMPORTANT: Use These EXACT Settings

When deploying to Render, use these settings:

**Build Command:**
```
pip install -r requirements.txt && cd backend && python database.py
```

**Start Command:**
```
gunicorn --chdir backend app:app --bind 0.0.0.0:$PORT
```

**Root Directory:** Leave BLANK (or use `.`)

---

## 📝 Step-by-Step Deployment

### Step 1: Upload to GitHub (Manual Method)
1. Go to https://github.com and create account
2. Click "+" → "New repository"
3. Name: `book-and-bloom`
4. Make it Public
5. Click "Create repository"
6. Click "uploading an existing file"
7. Upload ALL files from `c:/Users/joat0/AppData/bb10/`
8. Click "Commit changes"

### Step 2: Deploy to Render
1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Select your `book-and-bloom` repo
5. **IMPORTANT - Enter these EXACT values:**
   - **Name**: `book-and-bloom`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && cd backend && python database.py`
   - **Start Command**: `gunicorn --chdir backend app:app --bind 0.0.0.0:$PORT`
   - **Root Directory**: (leave blank)
6. Click "Create Web Service"
7. Wait 2-3 minutes

### Step 3: Your App is Live!
- URL: `https://book-and-bloom.onrender.com`
- GPS will work (HTTPS enabled)

---

## 🔧 If You Get Errors

### Error: "Could not open requirements file"
**Solution**: Make sure you uploaded ALL files including `requirements.txt`

### Error: "Module not found"
**Solution**: Check that `requirements.txt` contains:
```
Flask==3.1.2
Werkzeug==3.1.3
gunicorn==21.2.0
```

### Error: "Application failed to start"
**Solution**: Verify the Start Command is exactly:
```
gunicorn --chdir backend app:app --bind 0.0.0.0:$PORT
```

---

## 🎯 Alternative: Railway (Easier)

Railway auto-detects everything:

1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select `book-and-bloom`
5. Click "Deploy"
6. Done! No configuration needed

---

## ✅ Checklist Before Deploying

Make sure these files exist in your GitHub repo:
- [ ] `requirements.txt`
- [ ] `Procfile`
- [ ] `runtime.txt`
- [ ] `backend/app.py`
- [ ] `backend/database.py`
- [ ] `static/` folder with all files

---

## 🎉 Success!

Once deployed:
- Your app will be accessible worldwide
- GPS location will work automatically
- HTTPS is enabled by default
- You can share the URL with anyone!

**Need help?** Check the Render logs in the dashboard for detailed error messages.
