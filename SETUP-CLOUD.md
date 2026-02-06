# Setup Cloud Database (Free Tier)

Panduan setup database cloud gratis untuk Ko-Desain Platform.

---

## 1. PostgreSQL - Supabase (Recommended)

### Langkah Setup:
1. Buka https://supabase.com dan Sign Up (bisa pakai GitHub)
2. Klik "New Project"
3. Isi:
   - Project name: `kodesain`
   - Database password: (simpan password ini!)
   - Region: Singapore (terdekat)
4. Tunggu project selesai dibuat (~2 menit)
5. Pergi ke **Settings > Database**
6. Scroll ke **Connection string > URI**
7. Copy connection string, formatnya:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```

### Masukkan ke .env:
```env
POSTGRES_HOST=db.xxxxx.supabase.co
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DB=postgres
```

Atau gunakan DATABASE_URL langsung:
```env
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres
```

---

## 2. MongoDB - MongoDB Atlas

### Langkah Setup:
1. Buka https://mongodb.com/atlas dan Sign Up
2. Create a Free Cluster:
   - Cloud Provider: AWS
   - Region: Singapore
   - Cluster Tier: M0 (Free)
3. Tunggu cluster selesai (~3 menit)
4. Klik "Connect"
5. Pilih "Connect your application"
6. Copy connection string:
   ```
   mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/
   ```
7. **Penting**: Tambahkan database name di akhir URL:
   ```
   mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/kodesain_artifacts
   ```

### Setup Network Access:
1. Pergi ke **Network Access**
2. Klik "Add IP Address"
3. Klik "Allow Access from Anywhere" (untuk development)

### Masukkan ke .env:
```env
MONGODB_URL=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/kodesain_artifacts
MONGODB_DB=kodesain_artifacts
```

---

## 3. Redis - Upstash

### Langkah Setup:
1. Buka https://upstash.com dan Sign Up
2. Klik "Create Database"
3. Pilih:
   - Name: `kodesain`
   - Region: Singapore
   - Type: Regional
4. Setelah dibuat, copy **UPSTASH_REDIS_REST_URL**
5. Format connection string:
   ```
   rediss://default:xxxxx@xxx-xxx.upstash.io:6379
   ```

### Masukkan ke .env:
```env
REDIS_URL=rediss://default:xxxxx@xxx-xxx.upstash.io:6379
```

---

## 4. Claude API Key - Anthropic

### Langkah Setup:
1. Buka https://console.anthropic.com
2. Sign Up atau Login
3. Pergi ke **API Keys**
4. Klik "Create Key"
5. Copy API key (dimulai dengan `sk-ant-...`)

### Masukkan ke .env:
```env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

---

## Contoh File .env Lengkap (Cloud)

```env
# Application
APP_NAME=Ko-Desain Platform
APP_VERSION=1.0.0
DEBUG=true

# Security
SECRET_KEY=generate-random-string-32-chars-here

# PostgreSQL (Supabase)
POSTGRES_HOST=db.xxxxx.supabase.co
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-supabase-password
POSTGRES_DB=postgres

# MongoDB (Atlas)
MONGODB_URL=mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net/kodesain_artifacts
MONGODB_DB=kodesain_artifacts

# Redis (Upstash)
REDIS_URL=rediss://default:xxxxx@xxx-xxx.upstash.io:6379

# Claude API
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# TTS/STT
TTS_VOICE_MALE=id-ID-ArdiNeural
TTS_VOICE_FEMALE=id-ID-GadisNeural
WHISPER_MODEL=base

# Storage
UPLOAD_DIR=./uploads
AUDIO_DIR=./uploads/audio

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## Menjalankan Setelah Setup

### 1. Install Python dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Jalankan backend
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Install dan jalankan frontend
```bash
cd frontend
npm install
npm run dev
```

### 4. Akses aplikasi
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs
