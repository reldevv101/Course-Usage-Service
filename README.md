# Course Usage Service

Backend REST API sederhana untuk mengelola course, mencatat pemakaian belajar mahasiswa simulasi, dan menghitung tagihan. Panduan ini memisahkan penggunaan lokal dari konfigurasi cloud. **Untuk mulai sekarang, cukup jalankan bagian A; Supabase dan Render belum wajib dibuat.**

## Peta file konfigurasi

| File | Kegunaan | Perlu diubah sekarang? |
|---|---|---|
| `.env` | Konfigurasi lokal yang dibaca aplikasi, termasuk database dan API key | Biasanya biarkan nilai default untuk SQLite lokal. File ini sudah ada di folder proyek saat panduan ini ditulis. |
| `.env.example` | Contoh nama dan nilai awal konfigurasi, aman dibagikan | Tidak perlu diisi. Jangan menaruh password atau key sungguhan di sini. |
| `requirements.txt` | Daftar paket Python yang diperlukan | Tidak perlu diubah untuk menjalankan aplikasi. |
| `app/config.py` | Membaca isi `.env` dan nilai konfigurasi | Jangan ubah untuk setup normal. |
| `app/security.py` | Memeriksa `X-API-Key` pada route yang dilindungi | Jangan ubah untuk setup normal. |
| `migrations/` | Instruksi pembuatan skema database PostgreSQL | Dipakai saat menyiapkan database Supabase. |
| `.gitignore` | Mencegah `.env`, database lokal, dan virtual environment masuk Git | Pastikan file ini tetap ada. |

**Rahasia yang penting:** `.env` berisi konfigurasi pribadi dan diabaikan oleh Git. Jangan mengirim isinya lewat chat, jangan mengunggahnya ke GitHub, dan jangan memakai password asli pada file contoh.

## A. Jalankan di komputer sendiri (disarankan sekarang)

Saat ini `.env` proyek memakai SQLite lokal. Artinya belum perlu akun Supabase, Render, database password, atau API key untuk mencoba API.

1. Buka PowerShell di folder proyek:

   ```powershell
   cd "C:\Users\USER\Documents\Codex\Course-Usage-Service"
   ```

2. Pastikan file `.env` tersedia. File itu sudah ada di folder proyek saat panduan ini ditulis. Jika menyiapkan salinan proyek baru dan `.env` belum ada, buat salinan tanpa menimpa file yang mungkin sudah berisi konfigurasi:

   ```powershell
   if (-not (Test-Path .env)) { Copy-Item .env.example .env }
   ```

   Untuk pemakaian lokal, biarkan `DATABASE_URL` berisi nilai SQLite dan `ENVIRONMENT` bernilai `development`.

3. Aktifkan virtual environment dan jalankan server. Virtual environment `.venv` sudah tersedia di folder ini.

   ```powershell
   .\.venv\Scripts\Activate.ps1
   python -m uvicorn app.main:app --reload
   ```

   Jika `.venv` belum tersedia pada komputer lain, buat dan pasang paket satu kali:

   ```powershell
   py -3 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

4. Buka dokumentasi interaktif di [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). Coba buat course, catat usage, lalu buat invoice. Health check ada di [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health).

5. Hentikan server dengan `Ctrl+C` di PowerShell.

### Arti isi `.env` untuk lokal

```dotenv
DATABASE_URL=sqlite:///./course_usage.db
ENVIRONMENT=development
API_KEY=
STUDY_RATE_PER_HOUR=2000
MATERIAL_RATE_PER_ACCESS=500
QUIZ_RATE_PER_COMPLETION=1000
```

- `DATABASE_URL`: alamat database. Nilai SQLite di atas berarti data disimpan ke file `course_usage.db` di folder proyek.
- `ENVIRONMENT=development`: mode lokal. Dalam mode ini route yang nanti dilindungi tidak meminta API key.
- `API_KEY`: boleh kosong saat lokal. Ini adalah kunci akses sederhana milik aplikasi, bukan kunci Supabase.
- Tiga `*_RATE_*`: tarif simulasi. Biarkan nilainya seperti contoh bila tidak ingin mengubah harga.

Jangan mengganti `DATABASE_URL` ke Supabase dulu jika hanya ingin menguji lokal. SQLite dan Supabase adalah dua pilihan database yang berbeda; SQLite tidak mengirim data ke internet.

## B. Supabase: siapkan PostgreSQL (nanti, setelah lokal siap)

Supabase pada proyek ini hanya akan menjadi **host database PostgreSQL**. Backend mengakses PostgreSQL memakai SQLAlchemy dan `DATABASE_URL`; tidak memakai Supabase Data API atau Supabase Auth pada implementasi saat ini. Jadi untuk setup backend ini, yang dibutuhkan adalah connection string database, bukan `SUPABASE_URL` atau publishable/secret API key Supabase. [Panduan resmi koneksi database Supabase](https://supabase.com/docs/guides/database/connecting-to-postgres)

1. Buat akun dan project Supabase. Pilih region yang dekat dengan lokasi service Render nanti. Simpan database password di password manager.
2. Di project Supabase, tekan **Connect** dan salin connection string PostgreSQL. Jangan menaruh password di screenshot, laporan, GitHub, atau chat. Bila password punya karakter khusus, ikuti petunjuk encoding Supabase.
3. Pilih jenis koneksi berdasarkan jaringan: direct connection sesuai untuk backend tetap dan migrasi, tetapi endpoint direct biasanya memerlukan IPv6; bila komputer/hosting hanya memiliki IPv4, gunakan **Session pooler** dari menu Connect. Hindari **Transaction pooler** untuk server backend ini kecuali pengaturan driver disesuaikan. [Pilihan koneksi Supabase](https://supabase.com/docs/guides/database/connecting-to-postgres#which-connection-method-do-you-use)
4. Untuk membuat tabel di database Supabase yang masih kosong:
   - Buat salinan aman dari `.env` lokal sebelum mengubahnya, atau catat nilai SQLite agar bisa dipulihkan.
   - Buka `.env` dengan editor teks dan ubah **hanya** `DATABASE_URL` menjadi connection string PostgreSQL dari langkah sebelumnya. Biarkan `ENVIRONMENT=development` selama migrasi lokal.
   - Di PowerShell yang sudah mengaktifkan `.venv`, jalankan:

     ```powershell
     python -m alembic upgrade head
     ```

   - Perintah ini membuat tabel sesuai migrasi proyek. Jangan menjalankan migrasi awal pada database yang sudah berisi tabel aplikasi tanpa meninjau skema terlebih dahulu.
5. Setelah selesai migrasi, kembalikan `DATABASE_URL` di `.env` ke SQLite jika Anda ingin pengembangan harian tetap lokal. Jangan mengubah `.env.example` untuk menyimpan connection string asli.

## C. Render: jalankan backend di internet (setelah Supabase dan GitHub siap)

Render akan menjalankan FastAPI; Supabase menyimpan datanya. Agar Render dapat mengambil kode, repository harus sudah ada di GitHub. File `.env`, `course_usage.db`, dan `.venv` jangan diunggah. Render menyediakan environment variables melalui halaman pengaturan service dan menggunakannya setelah deploy. [Environment variables dan secrets Render](https://render.com/docs/configure-environment-variables)

1. Pastikan kode sudah berada di repository GitHub dan `.env` tidak ikut ter-commit.
2. Di Render Dashboard pilih **New → Web Service**, hubungkan akun GitHub, lalu pilih repository proyek ini.
3. Isi pengaturan service:

   | Isian Render | Nilai |
   |---|---|
   | Language / Runtime | Python |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
   | Health Check Path | `/health` |

   Render perlu aplikasi mendengarkan pada `0.0.0.0` dan port dari `$PORT`. Lihat [panduan Web Services Render](https://render.com/docs/web-services).

4. Sebelum membuat service atau sebelum deploy pertama, buka **Environment** pada service dan tambahkan:

   | Key | Value yang diisi |
   |---|---|
   | `DATABASE_URL` | Connection string PostgreSQL Supabase yang sama; isinya rahasia. |
   | `ENVIRONMENT` | `production` |
   | `API_KEY` | Buat key acak baru, jangan gunakan password Supabase. |

   Untuk membuat API key acak di komputer sendiri, jalankan:

   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

   Salin hasilnya langsung ke value `API_KEY` di Render. Simpan juga di password manager jika akan dipakai untuk Postman. Jangan menaruh hasilnya di README, `.env.example`, atau GitHub.

5. Simpan environment variables dan deploy service. Buka URL service Render yang diberikan, lalu periksa `/health` dan `/docs`.
6. Untuk memanggil route yang dilindungi, tambahkan header berikut di Postman:

   ```text
   X-API-Key: <API_KEY yang Anda simpan>
   ```

   Route usage dan invoice serta operasi create/update/delete course memerlukan key saat `ENVIRONMENT=production`. `GET /health` dan pembacaan daftar/detail course tidak memerlukannya. Key ini masih satu key bersama untuk penggunaan demo; ini **bukan** login terpisah untuk admin dan mahasiswa.

## D. Gambaran hubungan komponennya

```text
Postman / pengguna
        │ HTTPS
        ▼
FastAPI di Render ───── DATABASE_URL ─────► PostgreSQL di Supabase
```

Saat lokal, FastAPI berjalan di komputer dan database default-nya berupa file SQLite.

## E. Bantuan jika ada masalah

- `ModuleNotFoundError`: aktifkan `.venv`, lalu jalankan `python -m pip install -r requirements.txt`.
- `Invalid or missing API key`: pastikan key yang sama dikirim sebagai header `X-API-Key`; jangan menambahkan tanda `< >` pada nilainya.
- `API key protection is not configured`: di Render, isi `API_KEY` lalu deploy ulang.
- Error login/koneksi PostgreSQL: periksa `DATABASE_URL` di Render, database password, mode koneksi, dan SSL. Jangan mengirim connection string ke chat untuk diperiksa.
- Error tabel tidak ditemukan: pastikan migrasi `python -m alembic upgrade head` sudah berhasil dijalankan pada database Supabase yang benar.
- Jika ingin kembali ke lokal, pastikan `.env` menggunakan `DATABASE_URL=sqlite:///./course_usage.db` dan `ENVIRONMENT=development`.

## Batasan dan pengembangan selanjutnya

Login admin/user belum dibuat. API key di atas hanya gate sederhana untuk deployment demo dan tidak memberi identitas atau hak berbeda per mahasiswa. Login berikutnya perlu akun, password hashing, token, role admin/user, dan pembatasan agar mahasiswa hanya dapat melihat data miliknya. Pembayaran dan frontend tidak termasuk versi pertama.
