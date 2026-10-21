# Optimasi Rute Wisata Kuliner Surabaya: HC vs SA vs GA vs Memetic GA

Proyek ini membandingkan empat algoritma metaheuristik untuk mencari rute kunjungan ke tempat-tempat kuliner di Surabaya. Semua rute berawal dan berakhir di depot (Stasiun Gubeng). Setiap algoritma diberi **anggaran evaluasi fungsi biaya yang sama** supaya perbandingannya adil.

## Daftar isi
- [Masalah yang diselesaikan](#masalah-yang-diselesaikan)
- [Struktur folder](#struktur-folder)
- [Instalasi](#instalasi)
- [Cara menjalankan](#cara-menjalankan)
- [Format data](#format-data)
- [Penjelasan kode](#penjelasan-kode)
- [Eksperimen](#eksperimen)
- [Output](#output)
- [Catatan penting](#catatan-penting)

---

## Masalah yang diselesaikan

Ada 1 depot (node 0) dan 20 tempat kuliner (node 1–20). Rute adalah permutasi 20 tempat itu, sedangkan depot otomatis menjadi titik awal dan akhir. Ada dua varian masalah:

| Varian | Tujuan | Fungsi |
|---|---|---|
| **TSP** | Minimalkan total jarak tempuh (km) | `cost_tsp` |
| **TSPTW** (soft time window) | Minimalkan durasi total tur (menit, termasuk waktu menunggu) ditambah penalti keterlambatan | `cost_tw` |

Pada TSPTW, setiap tempat punya jam buka dan tutup. Jika tiba **sebelum buka**, pengunjung menunggu. Jika tiba **setelah tutup**, ada penalti:

```
biaya_TW = (waktu_selesai - 08:00) + 5 × total_menit_terlambat
```

---

## Struktur folder

```
proyek/
├── data/
│   ├── places.csv          # daftar tempat (wajib)
│   ├── dist_osrm.npy       # opsional, dibuat oleh fetch_osrm.py (km)
│   └── time_osrm.npy       # opsional, dibuat oleh fetch_osrm.py (menit)
├── results/
│   └── results.json        # dibuat oleh run_experiments.py
└── src/
    ├── tsplib.py           # inti proyek: data, fungsi biaya, 4 algoritma, Held-Karp
    ├── run_experiments.py  # menjalankan semua eksperimen + uji statistik
    └── fetch_osrm.py       # mengambil matriks jarak/waktu jalan asli dari OSRM
```

Folder `results/` harus dibuat dulu (`mkdir results`) sebelum menjalankan eksperimen.

---

## Instalasi

Butuh Python 3.9 atau lebih baru.

```bash
pip install numpy scipy
```

---

## Cara menjalankan

Jalankan dari **folder utama proyek** (bukan dari dalam `src/`):

```bash
# 1. Mode default: jarak jalan = jarak garis lurus (haversine) × 1.3
python src/run_experiments.py

# 2. (Opsional) Pakai jarak jalan asli dari OSRM
python src/fetch_osrm.py                  # butuh internet
python src/run_experiments.py --osrm
```

Eksperimen penuh memakan waktu cukup lama (puluhan menit, tergantung laptop) karena ada 30 seed × 4 algoritma × banyak konfigurasi anggaran, ditambah uji skalabilitas sampai 60 titik.

---

## Format data

`data/places.csv` dengan header:

```csv
id,name,lat,lon,open,close,category
0,Stasiun Gubeng (Depot),-7.2654,112.7533,0,1440,depot
1,Soto Ambengan,-7.2565,112.7455,06:00,11:00,sarapan
...
```

- **Baris pertama (node 0) harus depot.**
- `open` dan `close` boleh `HH:MM` (misalnya `06:00`, `24:00`) atau langsung dalam menit sejak tengah malam (misalnya `0`, `1440`).
- Kolom `id` tidak dipakai kode, hanya kolom `name, lat, lon, open, close, category`.
- Spasi di depan angka lat/lon tidak masalah.

---

## Penjelasan kode

### `src/tsplib.py` (inti proyek)

**Konstanta**

| Nama | Nilai | Arti |
|---|---|---|
| `DETOUR` | 1.30 | Jarak jalan ≈ 1.3 × garis lurus (dipakai jika tanpa OSRM) |
| `SPEED_KMH` | 25 | Kecepatan rata-rata kota |
| `SERVICE_MIN` | 20 | Lama makan atau icip di tiap titik (menit) |
| `START_MIN` | 480 | Tur dimulai pukul 08:00 |
| `LATE_PEN` | 5.0 | Penalti per menit keterlambatan |

**Kelas `Instance`**: memuat data dan menyimpan matriks jarak `D` (km) dan waktu `T` (menit).
- `Instance()` memakai dataset kuliner Surabaya dari `places.csv`.
- `Instance(use_osrm=True)` memuat matriks OSRM dari file `.npy`.
- `Instance(n_random=N, seed=42)` membuat N titik antar-paket acak di area Surabaya (service 5 menit) untuk uji skalabilitas. Depot tetap diambil dari `places.csv`, dan mode ini selalu memakai haversine.
- Fungsi biaya:
  - `cost_tsp(perm)` menghitung total jarak tur tertutup.
  - `cost_tw(perm)` menghitung durasi tur + penalti keterlambatan (versi cepat, untuk optimasi).
  - `simulate(perm)` menghasilkan jadwal rinci tiap stop (tiba, mulai, selesai, telat) plus total waktu selesai, keterlambatan, dan menunggu.

**Operator tetangga `neighbor(p, rng)`**: dipakai semua algoritma. Pilihannya acak dengan peluang 50% 2-opt (balik segmen), 25% swap (tukar dua stop), dan 25% insert (pindahkan satu stop).

**Kelas `Budget`**: pembungkus fungsi biaya yang menghitung jumlah evaluasi, mencatat solusi terbaik (`best`, `best_perm`), dan menyimpan kurva konvergensi (`curve`, best-so-far tiap sekian evaluasi). Karena semua algoritma lewat `Budget`, jumlah evaluasi mereka sama persis.

**Empat algoritma**

| Kode | Algoritma | Cara kerja | Parameter utama |
|---|---|---|---|
| `HC` | Hill-Climbing | Random-restart, first-improvement. Mulai dari rute acak, terima tetangga yang lebih baik, restart jika macet. | `patience=1000` |
| `SA` | Simulated Annealing | Terima solusi lebih buruk dengan peluang `exp(-Δ/T)`. Suhu turun geometrik dan disesuaikan dengan sisa anggaran. | `t0_frac=0.03`, `t_ratio=0.01` |
| `GA` | Genetic Algorithm | Seleksi tournament, Order Crossover (OX), mutasi dengan `neighbor`, elitism. | `pop=60`, `pc=0.9`, `pm=0.9`, `k=5`, `elite=2` |
| `MA` | Memetic GA | GA dengan perbaikan lokal: tiap anak diperbaiki 5 langkah hill-climbing. | `pop=30`, `pm=0.5`, `memetic=5` |

Skala suhu awal SA dihitung dari 20 rute acak. Evaluasi untuk kalibrasi ini **tidak** dihitung ke anggaran.

**Baseline dan optimum**
- `nearest_neighbor(inst)`: heuristik tetangga terdekat (berdasarkan jarak).
- `held_karp(D)`: optimum **eksak** TSP dengan dynamic programming bitmask (tervektorisasi numpy). Dipakai sebagai acuan gap pada TSP. Untuk 20 titik ini memakai memori sekitar 200 MB.

### `src/run_experiments.py`

Skrip yang menjalankan semua eksperimen lalu menyimpan hasilnya ke `results/results.json`:

1. **Referensi**: optimum Held-Karp, Nearest Neighbor, rata-rata 2000 rute acak, dan evaluasi rute TSP-optimal di bawah model time window (untuk melihat dampak mengabaikan jam buka/tutup).
2. **E1, perbandingan utama**: 4 algoritma × 2 fungsi biaya × 30 seed, anggaran 5000 evaluasi.
3. **E2, sensitivitas anggaran**: anggaran 1000, 2000, 5000, 10000, dan 50000 evaluasi dengan 15 seed.
4. **E3, skalabilitas**: instance acak 30 dan 60 titik, anggaran 50000, 30 seed, termasuk waktu komputasi.
5. **Best-known TSPTW**: nilai terbaik dari seluruh run, dipakai sebagai acuan gap karena optimum eksak TSPTW tidak dihitung.
6. **Ringkasan statistik**: mean, std, best, worst, median, gap rata-rata terhadap acuan (%), `hit_pct` (persentase run yang mencapai ≤ 1.001 × acuan), dan waktu rata-rata.
7. **Uji signifikansi**: Mann-Whitney U untuk setiap pasangan algoritma pada E1.

### `src/fetch_osrm.py`

Mengambil matriks jarak dan durasi jalan asli dari server publik OSRM (`router.project-osrm.org`) untuk semua titik di `places.csv`, lalu menyimpannya sebagai `data/dist_osrm.npy` (km) dan `data/time_osrm.npy` (menit). Matriksnya asimetris, jadi jalan satu arah ikut diperhitungkan. Jalankan di komputer yang punya internet.

---

## Eksperimen

| ID | Tujuan | Konfigurasi |
|---|---|---|
| E1 | Membandingkan kualitas solusi | 20 titik, 5000 evaluasi, 30 seed, TSP dan TSPTW |
| E2 | Pengaruh besar anggaran | 1000–50000 evaluasi, 15 seed |
| E3 | Skalabilitas ke instance lebih besar | 30 dan 60 titik, 50000 evaluasi, 30 seed |

---

## Output

`results/results.json` berisi antara lain:
- `opt_tsp`, `opt_path`: optimum eksak TSP dan rutenya
- `nn_tsp`, `nn_tw`, `rand_tsp`, `rand_tw`: nilai baseline
- `opt_tsp_under_tw`: dampak mengabaikan time window
- `best_tw`, `best_tw_perm`, `best_tw_detail`: rute TSPTW terbaik beserta jadwal rincinya
- `E1`, `E2`, `E3`: ringkasan statistik tiap eksperimen (E1 juga memuat kurva konvergensi)
- `tests`: p-value uji Mann-Whitney
- `names`, `coords`, `open`, `close`, `cat`, `params`: data pendukung untuk membuat grafik atau laporan

---

## Catatan penting

- **Hasil bersifat stokastik.** Seed tetap (0–29), jadi hasil bisa direproduksi, tetapi kecepatan eksekusi berbeda di tiap komputer.
- **Matriks OSRM harus sesuai `places.csv`.** Jumlah dan urutan titik di matriks harus sama dengan di CSV. Gunakan `fetch_osrm.py` agar keduanya otomatis sinkron.
- **`dist_m.json` / `dur_s.json` tidak dipakai** oleh `tsplib.py` (yang membaca `.npy`). Jika kamu menyimpan file `core.py` dan `algos.py` dari versi awal proyek, keduanya adalah implementasi alternatif yang berdiri sendiri dan **tidak dipakai** `run_experiments.py`. Skema kolom CSV-nya juga berbeda (`service_min`, `tw_open_min`, `tw_close_min`), jadi sebaiknya tidak dimasukkan ke repo kecuali kamu memang memeliharanya.
- Berkas `.pyc` tidak perlu di-commit. Tambahkan `__pycache__/` dan `*.pyc` ke `.gitignore`.
