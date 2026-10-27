# Course Usage Service

Backend REST API sederhana untuk mengelola course, mencatat pemakaian belajar mahasiswa simulasi, dan menghitung tagihan. Panduan ini memisahkan penggunaan lokal dari konfigurasi cloud. Untuk menjalankan lokal, gunakan bagian A. Untuk opsi hosting Vercel dengan database Supabase, ikuti bagian C.

## Peta file konfigurasi

| File | Kegunaan | Perlu diubah sekarang? |
|---|---|---|
| `.env` | Konfigurasi lokal yang dibaca aplikasi, termasuk database dan API key | Periksa nilainya sebelum menjalankan; file ini tidak diunggah ke GitHub. |
| `.env.example` | Contoh nama dan nilai awal konfigurasi, aman dibagikan | Tidak perlu diisi. Jangan menaruh password atau key sungguhan di sini. |
| `requirements.txt` | Daftar paket Python yang diperlukan | Tidak perlu diubah untuk menjalankan aplikasi. |
| `app/config.py` | Membaca isi `.env` dan nilai konfigurasi | Jangan ubah untuk setup normal. |
| `app/security.py` | Memeriksa `X-API-Key` pada route yang dilindungi | Jangan ubah untuk setup normal. |
| `migrations/` | Instruksi pembuatan skema database PostgreSQL | Dipakai saat menyiapkan database Supabase. |
| `.gitignore` | Mencegah `.env`, database lokal, dan virtual environment masuk Git | Pastikan file ini tetap ada. |

**Rahasia yang penting:** `.env` berisi konfigurasi pribadi dan diabaikan oleh Git. Jangan mengirim isinya lewat chat, jangan mengunggahnya ke GitHub, dan jangan memakai password asli pada file contoh.

## A. Jalankan di komputer sendiri (disarankan sekarang)

Untuk menjalankan API lokal, komputer tidak memerlukan akun hosting. Proyek mendukung SQLite lokal ataupun PostgreSQL Supabase. Jika `.env` Anda saat ini sudah menggunakan Supabase, jangan menimpa connection string tersebut sebelum membuat salinan aman.

1. Buka PowerShell di folder proyek:

   ```powershell
   cd "C:\Users\USER\Documents\Codex\Course-Usage-Service"
   ```

2. Pastikan file `.env` tersedia. File itu sudah ada di folder proyek saat panduan ini ditulis. Jika menyiapkan salinan proyek baru dan `.env` belum ada, buat salinan tanpa menimpa file yang mungkin sudah berisi konfigurasi:

   ```powershell
   if (-not (Test-Path .env)) { Copy-Item .env.example .env }
   ```

   Untuk pemakaian SQLite lokal, gunakan `DATABASE_URL=sqlite:///./course_usage.db`, `ENVIRONMENT=development`, dan `DB_POOL_MODE=session`. Jika `.env` menunjuk ke Supabase, periksa agar `ENVIRONMENT=development` dan pilih mode `session` bila connection string memakai Session pooler.

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
DB_POOL_MODE=session
API_KEY=
STUDY_RATE_PER_HOUR=2000
MATERIAL_RATE_PER_ACCESS=500
QUIZ_RATE_PER_COMPLETION=1000
```

- `DATABASE_URL`: alamat database. Nilai SQLite di atas berarti data disimpan ke file `course_usage.db` di folder proyek.
- `DB_POOL_MODE`: gunakan `session` untuk SQLite dan Supabase Session pooler; `transaction` khusus untuk Supabase Transaction pooler pada serverless Vercel.
- `ENVIRONMENT=development`: mode lokal. Dalam mode ini route yang nanti dilindungi tidak meminta API key.
- `API_KEY`: boleh kosong saat lokal. Ini adalah kunci akses sederhana milik aplikasi, bukan kunci Supabase.
- Tiga `*_RATE_*`: tarif simulasi. Biarkan nilainya seperti contoh bila tidak ingin mengubah harga.

SQLite dan Supabase adalah dua pilihan database yang berbeda; SQLite tidak mengirim data ke internet. Untuk kerja lokal yang tetap memakai Supabase, gunakan Session pooler seperti setup migrasi Anda.

## B. Supabase: PostgreSQL

Supabase pada proyek ini hanya akan menjadi **host database PostgreSQL**. Backend mengakses PostgreSQL memakai SQLAlchemy dan `DATABASE_URL`; tidak memakai Supabase Data API atau Supabase Auth pada implementasi saat ini. Jadi untuk setup backend ini, yang dibutuhkan adalah connection string database, bukan `SUPABASE_URL` atau publishable/secret API key Supabase. [Panduan resmi koneksi database Supabase](https://supabase.com/docs/guides/database/connecting-to-postgres)

1. Buat akun dan project Supabase. Pilih region yang dekat dengan lokasi backend nanti. Simpan database password di password manager.
2. Di project Supabase, tekan **Connect** dan salin connection string PostgreSQL. Jangan menaruh password di screenshot, laporan, GitHub, atau chat. Bila password punya karakter khusus, ikuti petunjuk encoding Supabase.
3. Untuk migrasi dari komputer lokal, **Session pooler** seperti yang sudah Anda gunakan boleh dipakai. Untuk Vercel, pilih **Transaction pooler** (biasanya port `6543`) karena Vercel menjalankan backend sebagai function serverless. Saat `DB_POOL_MODE=transaction`, aplikasi menggunakan satu koneksi pool per instance, menonaktifkan prepared statements, dan meminta SSL. [Panduan koneksi Supabase](https://supabase.com/docs/guides/database/connecting-to-postgres)
4. Untuk membuat tabel di database Supabase yang masih kosong:
   - Buat salinan aman dari `.env` lokal sebelum mengubahnya, atau catat nilai SQLite agar bisa dipulihkan.
   - Buka `.env` dengan editor teks dan ubah **hanya** `DATABASE_URL` menjadi connection string PostgreSQL dari langkah sebelumnya. Biarkan `ENVIRONMENT=development` selama migrasi lokal.
   - Di PowerShell yang sudah mengaktifkan `.venv`, jalankan:

     ```powershell
     python -m alembic upgrade head
     ```

   - Perintah ini membuat tabel sesuai migrasi proyek. Jangan menjalankan migrasi awal pada database yang sudah berisi tabel aplikasi tanpa meninjau skema terlebih dahulu.
   - Sebelum menjalankan migrasi, Anda boleh memeriksa jenis database yang benar-benar terbaca. Perintah ini hanya menampilkan jenis URL, bukan password atau connection string:

     ```powershell
     python -c "from app.config import settings; print(settings.database_url.split('://', 1)[0])"
     ```

     Hasil untuk Supabase harus `postgresql+psycopg`. Jika hasilnya `sqlite`, perintah akan menuju database lokal. Pastikan PowerShell berada di folder proyek. Jika `.env` sudah berisi Supabase tetapi hasil masih `sqlite`, hapus hanya environment variable lama dari sesi PowerShell, lalu periksa ulang:

     ```powershell
     Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
     python -c "from app.config import settings; print(settings.database_url.split('://', 1)[0])"
     ```

     Environment variable PowerShell yang sudah disetel dapat mengalahkan nilai di `.env`. Jangan jalankan `alembic stamp` atau menghapus tabel SQLite sebagai cara memperbaiki target database yang salah.
5. Setelah migrasi, Anda boleh mengembalikan `DATABASE_URL` di `.env` ke SQLite untuk kerja lokal, atau mempertahankan Supabase untuk pengembangan lokal. Jangan menaruh connection string asli di `.env.example`. Untuk Vercel, connection string diisi terpisah pada pengaturan proyek, bukan pada file yang diunggah ke GitHub.

## C. Vercel: jalankan backend di internet

Vercel menjalankan FastAPI sebagai function dan Supabase menyimpan data PostgreSQL. Vercel dapat mendeteksi FastAPI dari `requirements.txt` dan entrypoint `app/main.py`; proyek ini tidak memerlukan `vercel.json`, build command, atau start command khusus. [Python Runtime Vercel](https://vercel.com/docs/functions/runtimes/python) · [Panduan FastAPI Vercel](https://vercel.com/kb/guide/ship-a-fastapi-app-on-vercel)

### Sebelum deploy

Pastikan repository proyek sudah ada di GitHub dan `.env`, `course_usage.db`, serta `.venv` tidak ikut ter-commit. `.gitignore` proyek mengecualikan file lokal tersebut. Jangan mengirim isi `.env` ke GitHub atau chat. Vercel Hobby ditawarkan gratis untuk proyek personal dengan batas penggunaan tertentu; periksa syarat dan kuota di halaman resmi karena layanan cloud dapat mengubahnya. [Vercel Hobby](https://vercel.com/docs/plans/hobby)

### Langkah deploy dari GitHub

1. Di dashboard Vercel pilih **Add New → Project**, hubungkan GitHub, lalu impor repository Course Usage Service. Deployment Git dapat otomatis berjalan saat ada perubahan pada branch terhubung. [Panduan Git Vercel](https://vercel.com/docs/git)
2. Biarkan framework dan build settings terdeteksi otomatis. Pastikan **Root Directory** adalah folder proyek yang memuat `requirements.txt`, `app/`, dan `migrations/`.
3. Pada **Project Settings → Environment Variables**, tambahkan variabel berikut. Pilih environment **Production**; pilih **Preview** juga bila ingin mencoba preview. Setiap variabel dibuat dengan **Add Another**:

   | Key | Value |
   |---|---|
   | `DATABASE_URL` | Connection string Supabase **Transaction pooler** dari tombol **Connect**. Ini rahasia; jangan memakai Session pooler untuk Vercel. |
   | `DB_POOL_MODE` | `transaction` |
   | `ENVIRONMENT` | `production` |
   | `API_KEY` | Key rahasia acak untuk header `X-API-Key`; jangan gunakan password database. |

   Buat API key acak di PowerShell:

   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

   Salin output ke value `API_KEY` Vercel dan simpan untuk Postman. Jangan tulis key atau connection string asli pada README, `.env.example`, atau GitHub. Tidak perlu menambahkan `SUPABASE_URL` atau `SUPABASE_KEY`; aplikasi memakai koneksi PostgreSQL langsung.

4. Klik **Deploy**. Setelah build selesai, buka URL deployment dan periksa `/health`, lalu `/docs`. Vercel mengelola runtime function sehingga tidak ada perintah `uvicorn` yang perlu diisi.
5. Untuk endpoint yang dilindungi, tambahkan header berikut pada Postman:

   ```text
   X-API-Key: <API_KEY yang Anda simpan>
   ```

   Route usage dan invoice serta operasi create/update/delete course memerlukan key saat `ENVIRONMENT=production`. `GET /health` dan pembacaan daftar/detail course tidak memerlukannya. Key ini satu kunci bersama untuk demo, bukan login admin dan mahasiswa.

6. Skema Supabase sudah dibuat dengan Alembic pada tahap setup sebelumnya. Jangan menjalankan migrasi awal lagi setiap kali deploy. Jika kelak ada migrasi baru, jalankan secara terencana dari komputer lokal terhadap database yang benar.

## D. Gambaran hubungan komponennya

```text
Postman / pengguna
        │ HTTPS
        ▼
FastAPI Function di Vercel ── DATABASE_URL ──► PostgreSQL di Supabase
```

Saat lokal, FastAPI berjalan di komputer dan database default-nya berupa file SQLite.

## E. Bantuan jika ada masalah

- `ModuleNotFoundError`: aktifkan `.venv`, lalu jalankan `python -m pip install -r requirements.txt`.
- `Invalid or missing API key`: pastikan key yang sama dikirim sebagai header `X-API-Key`; jangan menambahkan tanda `< >` pada nilainya.
- `API key protection is not configured`: di Vercel, isi `API_KEY` untuk environment yang dipakai lalu redeploy.
- Log Alembic bertuliskan `Context impl SQLiteImpl` atau `table courses already exists`: migrasi sedang menuju SQLite lokal, bukan Supabase. Jalankan pemeriksaan jenis URL di bagian B. Jangan menghapus tabel lokal.
- `could not resolve host` saat memakai URL PostgreSQL: periksa kembali connection string melalui tombol **Connect** di Supabase dan koneksi internet/DNS. Jika direct connection tidak dapat dijangkau dari jaringan IPv4, coba Session pooler.
- Error koneksi PostgreSQL di Vercel: pastikan `DATABASE_URL` memakai Transaction pooler dari tombol Connect Supabase (biasanya port `6543`), `DB_POOL_MODE=transaction`, password benar, dan variabel sudah diset untuk environment deployment. Jangan mengirim connection string ke chat untuk diperiksa.
- Error tabel tidak ditemukan: pastikan migrasi `python -m alembic upgrade head` sudah berhasil dijalankan pada database Supabase yang benar.
- Jika ingin kembali ke lokal, pastikan `.env` menggunakan `DATABASE_URL=sqlite:///./course_usage.db` dan `ENVIRONMENT=development`.

## Batasan dan pengembangan selanjutnya

Login admin/user belum dibuat. API key di atas hanya gate sederhana untuk deployment demo dan tidak memberi identitas atau hak berbeda per mahasiswa. Login berikutnya perlu akun, password hashing, token, role admin/user, dan pembatasan agar mahasiswa hanya dapat melihat data miliknya. Pembayaran dan frontend tidak termasuk versi pertama.
