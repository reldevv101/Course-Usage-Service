# Course Usage Service — Project Plan

## Status dokumen

Rancangan ini telah disetujui untuk memulai implementasi lokal. Integrasi Supabase dan deployment ke Render tetap terpisah dan belum dimulai.

## 1. Ringkasan proyek dan masalah

Course Usage Service adalah REST API untuk simulasi layanan pembelajaran digital. API mencatat course, penggunaan oleh mahasiswa simulasi, dan tagihan berbasis pemakaian. Proyek menunjukkan bagaimana layanan cloud mengukur konsumsi sumber daya (measured service / usage metering) dan menghitung biaya berdasarkan tarif (utility computing / usage-based billing).

Sistem bukan LMS: tidak menangani materi, kelas virtual, autentikasi mahasiswa, pembayaran, atau tampilan frontend. Nilai utamanya adalah data penggunaan yang tervalidasi, perhitungan biaya yang dilakukan server, dan bukti historis tarif yang dipakai.

## 2. Fitur wajib dan batasan

### Fitur wajib

- CRUD course: membuat, membaca daftar/detail, memperbarui, menghapus.
- Mencatat penggunaan dengan `student_id` simulasi dan referensi course.
- Membaca riwayat penggunaan dengan filter sederhana (`student_id`, `course_id`).
- Mengukur jam belajar, akses materi premium, dan kuis selesai.
- Menghitung tagihan di backend dengan tarif awal Rp2.000/jam, Rp500/akses premium, Rp1.000/kuis.
- Menyimpan jumlah pemakaian, tarif snapshot, rincian, dan total tagihan sehingga perubahan konfigurasi tarif tidak mengubah tagihan lama.
- JSON request/response, HTTP GET/POST/PUT/PATCH/DELETE, validasi input, dan dokumentasi OpenAPI `/docs`.

### Batasan versi pertama

- Python + FastAPI; PostgreSQL sebagai target database. Pengembangan lokal harus dapat dijalankan tanpa akun cloud.
- Tidak ada UI khusus, login mahasiswa/admin, pembayaran, ML, microservices, Docker/Kubernetes, atau integrasi provider pada tahap awal.
- ID mahasiswa hanya data simulasi seperti `S001`.
- Tagihan tersimpan bersifat historis dan tidak dapat diedit melalui API.
- Tidak boleh mengandalkan tarif yang dikirim klien; tarif adalah konfigurasi server.

### Keputusan yang direkomendasikan

- Gunakan UUID yang dibuat server-side sebagai primary key untuk ketiga tabel. UUID aman dibawa di URL dan tidak membocorkan jumlah baris.
- Gunakan jam belajar dengan presisi dua angka desimal (`NUMERIC(8,2)`); akses dan kuis bilangan bulat. Validasi menolak angka negatif, nilai bukan angka/finite, ID di luar pola, dan course yang tidak ada.
- Simpan nominal Rupiah sebagai bilangan bulat (`BIGINT`) karena tarif dan hasil hitung dalam satuan Rupiah. Tarif dapat berupa integer positif atau nol.
- Tagihan dibuat eksplisit melalui endpoint billing setelah usage record dicatat. Satu usage record maksimal memiliki satu tagihan (unique constraint). Pengulangan permintaan untuk usage yang sama memberi `409 Conflict`, agar tidak terjadi tagihan ganda.
- Catatan penggunaan tidak dapat diubah setelah memiliki tagihan. Sebelum ditagihkan, boleh diperbarui atau dihapus. Ini menjaga snapshot billing tetap konsisten.
- Rekomendasi awal: gunakan SQLite lokal untuk memulai cepat bila PostgreSQL lokal belum tersedia, tetapi struktur SQL/ORM tetap kompatibel PostgreSQL. Sebelum integrasi Supabase, verifikasi perilaku migrasi, constraint, UUID, dan tipe numerik terhadap PostgreSQL. Alternatifnya gunakan PostgreSQL lokal bila memang tersedia; tidak perlu menganggapnya sudah terpasang.
- Saat dideploy, lindungi operasi mutasi dan data riwayat dengan API key sederhana pada header `X-API-Key` dari environment variable. Jangan menyimpan key di repository. Untuk demo lokal, proteksi dapat dimatikan lewat konfigurasi development yang eksplisit. API key bukan pengganti autentikasi produksi, tetapi lebih baik daripada membuka endpoint tulis tanpa perlindungan untuk demo UTS.

## 3. Usulan struktur folder

```text
Course-Usage-Service/
├── PROJECT_PLAN.md          # Rancangan tahap awal
├── README.md                # Instalasi, konfigurasi, menjalankan API, contoh demo
├── requirements.txt         # Dependensi Python yang dipatok
├── .env.example             # Nama variabel tanpa secret sungguhan
├── .gitignore               # venv, cache, .env, database lokal, hasil sementara
├── app/
│   ├── __init__.py
│   ├── main.py              # Buat FastAPI app, middleware, router, health check
│   ├── config.py            # Baca environment, mode lokal/cloud, API key, tarif
│   ├── database.py          # Engine/session dan konfigurasi koneksi
│   ├── models.py            # Model ORM dan constraint tabel
│   ├── schemas.py           # Pydantic request/response dan validasi
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── courses.py       # Endpoint course
│   │   ├── usage.py         # Pencatatan dan riwayat penggunaan
│   │   └── billing.py       # Pembuatan dan pembacaan tagihan
│   └── services/
│       ├── __init__.py
│       └── billing.py       # Rumus, snapshot tarif, transaksi pembuatan invoice
├── migrations/              # Migrasi skema bila memakai Alembic
└── tests/
    ├── conftest.py          # Test client dan database terisolasi
    ├── test_courses.py
    ├── test_usage.py
    └── test_billing.py
```

Struktur ini usulan, bukan berkas yang sudah dibuat. Hindari lapisan repository tambahan sampai ada kebutuhan nyata. Gunakan migrasi skema saat integrasi PostgreSQL agar perubahan database tercatat dan dapat direproduksi.

## 4. Rancangan database PostgreSQL

### `courses`

| Kolom | Tipe | Aturan / fungsi |
|---|---|---|
| `id` | UUID | Primary key, dibuat server |
| `course_code` | VARCHAR(30) | NOT NULL, UNIQUE; kode seperti `CC101` |
| `name` | VARCHAR(150) | NOT NULL |
| `description` | TEXT | Nullable |
| `is_active` | BOOLEAN | NOT NULL, default TRUE |
| `created_at` | TIMESTAMPTZ | NOT NULL, default waktu UTC |
| `updated_at` | TIMESTAMPTZ | NOT NULL, diperbarui saat update |

### `usage_records`

| Kolom | Tipe | Aturan / fungsi |
|---|---|---|
| `id` | UUID | Primary key |
| `student_id` | VARCHAR(20) | NOT NULL; validasi format seperti `S001` |
| `course_id` | UUID | NOT NULL, FK ke `courses.id`, ON DELETE RESTRICT |
| `study_hours` | NUMERIC(8,2) | NOT NULL, CHECK >= 0 |
| `material_accesses` | INTEGER | NOT NULL, CHECK >= 0 |
| `quizzes_completed` | INTEGER | NOT NULL, CHECK >= 0 |
| `recorded_at` | TIMESTAMPTZ | NOT NULL, default waktu UTC |
| `created_at` | TIMESTAMPTZ | NOT NULL, default waktu UTC |
| `updated_at` | TIMESTAMPTZ | NOT NULL, diperbarui saat update |

Buat index untuk `student_id`, `course_id`, dan `recorded_at` (atau composite index untuk query riwayat yang benar-benar dipakai). Foreign key RESTRICT mencegah penghapusan course yang masih punya usage history. Course dapat dinonaktifkan agar tidak menerima penggunaan baru tanpa menghapus histori.

### `invoices`

| Kolom | Tipe | Aturan / fungsi |
|---|---|---|
| `id` | UUID | Primary key |
| `usage_record_id` | UUID | NOT NULL, UNIQUE, FK ke `usage_records.id`, ON DELETE RESTRICT |
| `student_id` | VARCHAR(20) | Snapshot identitas simulasi pada saat penagihan |
| `course_id` | UUID | Snapshot referensi course; FK RESTRICT |
| `study_hours` | NUMERIC(8,2) | Snapshot nilai penggunaan |
| `material_accesses` | INTEGER | Snapshot nilai penggunaan |
| `quizzes_completed` | INTEGER | Snapshot nilai penggunaan |
| `study_rate_per_hour` | BIGINT | Tarif snapshot: awalnya 2000 |
| `material_rate_per_access` | BIGINT | Tarif snapshot: awalnya 500 |
| `quiz_rate_per_completion` | BIGINT | Tarif snapshot: awalnya 1000 |
| `study_cost` | BIGINT | Hasil komponen jam belajar |
| `material_cost` | BIGINT | Hasil komponen akses premium |
| `quiz_cost` | BIGINT | Hasil komponen kuis |
| `total_cost` | BIGINT | NOT NULL, hasil penjumlahan komponen |
| `currency` | CHAR(3) | NOT NULL, default `IDR` |
| `created_at` | TIMESTAMPTZ | Waktu invoice dihitung; historis dan immutable |

Relasi: satu course memiliki banyak usage records; satu usage record memiliki nol atau satu invoice. Snapshot kolom usage di invoice mempertahankan apa yang ditagihkan meskipun sistem nanti mengizinkan perubahan catatan yang belum ditagihkan. Kursus yang memiliki histori tidak dapat dihapus karena FK RESTRICT.

Constraint tambahan: penggunaan non-negatif, tarif dan komponen biaya non-negatif, serta `total_cost = study_cost + material_cost + quiz_cost` (dapat ditegakkan di service dan bila sesuai dengan CHECK database). Migrasi harus menguji kompatibilitas tipe NUMERIC dan constraint pada PostgreSQL.

## 5. Rancangan endpoint REST API

Semua payload memakai JSON. Base path `/api/v1`. Bentuk error konsisten, misalnya `{"detail":"Course not found"}`; validasi FastAPI dapat menyertakan daftar detail field. `201` untuk resource baru, `200` untuk pembacaan/perubahan, `204` untuk hapus, `400` untuk aturan domain, `401` untuk API key cloud yang hilang/salah, `404` untuk ID tak ada, `409` untuk duplikasi/konflik constraint, `422` untuk input tidak valid, `500` untuk kegagalan tak terduga.

### Health

- `GET /health` — memeriksa proses API hidup; `200` `{"status":"ok"}`. Jangan mengembalikan rahasia atau string koneksi.

### Courses

| Method & path | Fungsi | Status utama |
|---|---|---|
| `POST /api/v1/courses` | Membuat course | `201`, `409`, `422` |
| `GET /api/v1/courses` | Daftar course; dukung `?active=true` dan pagination sederhana `limit`, `offset` | `200`, `422` |
| `GET /api/v1/courses/{course_id}` | Detail course | `200`, `404`, `422` |
| `PUT /api/v1/courses/{course_id}` | Mengganti seluruh field yang dapat diedit | `200`, `404`, `409`, `422` |
| `PATCH /api/v1/courses/{course_id}` | Mengubah sebagian field | `200`, `404`, `409`, `422` |
| `DELETE /api/v1/courses/{course_id}` | Menghapus jika belum dirujuk usage; selain itu konflik FK | `204`, `404`, `409` |

Contoh create:

```http
POST /api/v1/courses
Content-Type: application/json
```

```json
{"course_code":"CC101","name":"Cloud Computing Dasar","description":"Materi pengantar cloud","is_active":true}
```

Respons `201`:

```json
{"id":"7ad9c634-0182-4c53-92cf-66f93066bca4","course_code":"CC101","name":"Cloud Computing Dasar","description":"Materi pengantar cloud","is_active":true,"created_at":"2026-10-26T10:00:00Z","updated_at":"2026-10-26T10:00:00Z"}
```

### Usage

| Method & path | Fungsi | Status utama |
|---|---|---|
| `POST /api/v1/usage-records` | Mencatat pemakaian untuk course aktif | `201`, `404`, `422` |
| `GET /api/v1/usage-records` | Riwayat; filter opsional `student_id`, `course_id`, `limit`, `offset` | `200`, `422` |
| `GET /api/v1/usage-records/{usage_id}` | Detail pemakaian | `200`, `404`, `422` |
| `PATCH /api/v1/usage-records/{usage_id}` | Koreksi parsial hanya sebelum ditagihkan | `200`, `404`, `409`, `422` |
| `DELETE /api/v1/usage-records/{usage_id}` | Hapus hanya sebelum ditagihkan | `204`, `404`, `409` |

Contoh pencatatan:

```json
{"student_id":"S001","course_id":"7ad9c634-0182-4c53-92cf-66f93066bca4","study_hours":1.5,"material_accesses":3,"quizzes_completed":2}
```

Respons `201` berisi semua nilai yang tervalidasi, `id`, dan `recorded_at`. Tolak field tarif atau `total_cost` yang dikirim klien agar tidak dianggap sumber kebenaran. Nilai jam dibatasi dua angka desimal dan maksimum representable; akses/kuis harus integer >= 0; course harus ada dan aktif.

### Billing

| Method & path | Fungsi | Status utama |
|---|---|---|
| `POST /api/v1/invoices` | Menghitung dan menyimpan invoice untuk usage record | `201`, `404`, `409`, `422` |
| `GET /api/v1/invoices` | Daftar invoice; filter `student_id`, `course_id`, pagination | `200`, `422` |
| `GET /api/v1/invoices/{invoice_id}` | Detail invoice dan rincian | `200`, `404`, `422` |
| `GET /api/v1/usage-records/{usage_id}/invoice` | Invoice milik satu catatan penggunaan | `200`, `404` bila usage/invoice tak ditemukan |

Contoh permintaan hitung:

```json
{"usage_record_id":"04eab737-9fa2-4310-b504-17457a601851"}
```

Respons `201`:

```json
{"id":"d8a927c9-f0e9-451d-99fc-b5b7ca03e2db","usage_record_id":"04eab737-9fa2-4310-b504-17457a601851","student_id":"S001","course_id":"7ad9c634-0182-4c53-92cf-66f93066bca4","usage":{"study_hours":1.5,"material_accesses":3,"quizzes_completed":2},"rates":{"study_per_hour":2000,"material_per_access":500,"quiz_per_completion":1000},"breakdown":{"study_cost":3000,"material_cost":1500,"quiz_cost":2000},"total_cost":6500,"currency":"IDR","created_at":"2026-10-26T10:05:00Z"}
```

`POST /invoices` mengembalikan `409` bila usage sudah ditagihkan. Pembacaan invoice tetap tersedia untuk audit. Untuk MVP, invoice tidak punya status pembayaran karena tidak ada integrasi pembayaran.

## 6. Alur metering dan billing

1. Klien mengirim usage record; server memvalidasi student ID, course aktif, jam (finite, >=0, paling banyak dua desimal), akses dan kuis (integer >=0), lalu menyimpan catatan.
2. Klien meminta invoice dengan `usage_record_id`. Server membaca record dan tarif aktif dari konfigurasi backend, lalu hitung:
   - `study_cost = study_hours × 2000`
   - `material_cost = material_accesses × 500`
   - `quiz_cost = quizzes_completed × 1000`
   - `total_cost = study_cost + material_cost + quiz_cost`
3. Karena jam dibatasi dua desimal dan tarif per jam kelipatan Rp2.000, hasil tetap bilangan bulat Rupiah. Gunakan Decimal, bukan float biner, di model/perhitungan. Simpan input usage, seluruh tarif, rincian komponen, total, mata uang dan waktu dalam satu transaksi database.
4. Unique constraint pada `invoices.usage_record_id` menangani dua request bersamaan; hanya satu yang berhasil. Tangani pelanggaran unique sebagai `409`.
5. Setelah invoice dibuat, usage record terkunci untuk update/delete melalui aturan service dan FK. Invoice tidak diubah bila konfigurasi tarif berubah. Penyesuaian tarif berikutnya menggunakan environment/config versi baru dan hanya berlaku pada invoice mendatang.

## 7. Arsitektur lokal dan integrasi cloud

### Lokal

Klien Postman atau browser `/docs` → FastAPI → service/domain logic → database lokal. Tarif berasal dari konfigurasi server; file `.env` lokal tidak dikomit. `/health` dan log ringkas membantu demo. Jalankan server lokal dengan dokumentasi OpenAPI untuk demonstrasi CRUD, metering, dan billing.

Database lokal direkomendasikan SQLite untuk hambatan awal rendah. Karena target PostgreSQL, hindari fitur SQL yang eksklusif SQLite dan lakukan pemeriksaan/migrasi di PostgreSQL sebelum tahap cloud. Jika PostgreSQL lokal sudah tersedia, boleh dipakai langsung. Tidak ada kebutuhan Docker pada versi pertama.

### Cloud di tahap selanjutnya

- Supabase menyediakan PostgreSQL; backend Render menyimpan `DATABASE_URL` sebagai environment secret. Jangan menaruh service-role key atau password database di kode, screenshot publik, atau GitHub.
- Render menjalankan FastAPI dari repository GitHub; start command dan versi Python akan didokumentasikan setelah implementasi lokal.
- Aktifkan HTTPS dan API key untuk operasi mutasi serta akses riwayat. Simpan key di environment Render dan jangan expose di `/docs` atau respons. Batasi CORS ke origin yang diperlukan; untuk MVP tanpa frontend, tidak perlu membuka CORS lebar.
- Gunakan migration untuk membuat/memperbarui tabel. Jangan mengandalkan data lokal sebagai database cloud; siapkan seed/demo data terpisah dan dapat diulang.
- Paket gratis, kuota, perilaku sleep, dan syarat provider dapat berubah; verifikasi pada saat integrasi. Rp0 adalah target, bukan jaminan. Pantau batas dan hindari memasukkan data pribadi nyata.
- Sebelum deployment publik, verifikasi API key benar-benar wajib untuk route sensitif, HTTPS aktif, secret tidak ikut repository, error tidak membocorkan kredensial, dan endpoint write tidak terbuka tanpa kontrol.

## 8. Strategi pengujian

Pengujian dilakukan setelah implementasi dan menjadi cakupan Tahap 4. Gunakan test client FastAPI serta database terisolasi per test; jangan bergantung pada akun cloud.

- Course normal: create, list, get, PUT/PATCH; hapus course tanpa usage berhasil; duplikasi `course_code` ditolak.
- Course tidak ditemukan: GET/PATCH/PUT/DELETE ID acak memberi `404`.
- Course terpakai: hapus course dengan usage ditolak `409`.
- Usage normal: record dengan course aktif tersimpan dan terlihat di daftar/detail.
- Input tidak valid: jam negatif, jam >2 desimal, nilai NaN/infinite, akses/kuis negatif atau pecahan, student ID salah, course UUID malformed, field biaya/tarif dari klien, dan course tidak aktif; respons sesuai `422`/`404`.
- Usage tidak ditemukan: detail/update/delete memberi `404`; update/delete setelah invoice memberi `409`.
- Billing contoh: 1.5 jam, 3 akses, 2 kuis menghasilkan Rp6.500 dengan rincian Rp3.000 + Rp1.500 + Rp2.000.
- Billing batas: semua nol menghasilkan nol; jam desimal kecil sesuai presisi; nilai maksimum tervalidasi tidak overflow.
- Invoice ganda: tagihan kedua untuk usage yang sama memberi `409`; invoice lama masih menunjukkan snapshot tarif dan usage yang sama setelah konfigurasi tarif berubah.
- API protection: cloud mode menolak request tanpa/salah API key (`401`), key benar dapat melanjutkan; mode lokal hanya terbuka sesuai konfigurasi development.
- Jalankan migrasi pada PostgreSQL dan cek integritas/constraint, khususnya presisi decimal, unique invoice, dan foreign keys.

## 9. Risiko teknis dan mitigasi

| Risiko | Mitigasi |
|---|---|
| Perbedaan SQLite dan PostgreSQL | Pakai subset SQL umum, migrasi, dan verifikasi pada PostgreSQL sebelum Supabase; jangan menganggap test SQLite cukup untuk constraint cloud. |
| Float menghasilkan pembulatan biaya | Validasi jam dua desimal; gunakan `Decimal` dan Rupiah integer; sertakan kasus desimal di test. |
| Tagihan ganda akibat retry/concurrency | Unique constraint pada usage ID dan transaksi; `409` untuk duplikasi. |
| Tarif berubah mengubah histori | Simpan tarif dan komponen biaya sebagai snapshot immutable per invoice. |
| Penghapusan course merusak riwayat | FK RESTRICT, nonaktifkan course sebagai gantinya. |
| Endpoint tulis publik disalahgunakan | API key dari secret environment, HTTPS, CORS minimal, validasi payload dan batas ukuran/pagination; jangan deploy write tanpa kontrol. |
| Kebocoran kredensial | `.env` di `.gitignore`, `.env.example` tanpa nilai secret, environment variable provider, audit sebelum push. |
| Free tier berubah/terbatas | Cek kuota/masa aktif saat integrasi dan pantau; siapkan demo lokal tanpa ketergantungan cloud. |
| Ruang lingkup melebar | Tunda login penuh, pembayaran, frontend, role, dan fitur analitik sampai rubrik UTS terpenuhi. |
| Keterbatasan waktu kelompok | Bagi pekerjaan per domain, tetapkan pemilik integrasi, dan lakukan demo vertikal sederhana lebih awal. |

## Catatan lanjutan: login admin dan user

Login bukan bagian dari versi pertama, tetapi direncanakan sebagai pengembangan berikutnya. Admin dapat mengelola course dan melihat data layanan; user/mahasiswa hanya dapat membuat dan melihat usage serta invoice miliknya sendiri. Implementasi perlu menambahkan penyimpanan akun, password hashing, token sesi/JWT, serta pemeriksaan kepemilikan resource. Jangan mengaktifkan route publik untuk data mahasiswa sebelum kontrol akses ini diterapkan.


