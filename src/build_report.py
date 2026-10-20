import json, pathlib
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether
ROOT = pathlib.Path(__file__).resolve().parents[1]
R = json.load(open(ROOT / "results/results.json"))
for _f in R["E1"].values():
    for _d in _f.values(): _d["gap_mean_pct"]=abs(_d["gap_mean_pct"]) if abs(_d["gap_mean_pct"])<1e-6 else _d["gap_mean_pct"]; F = ROOT / "results/fig/"
GITHUB = "https://github.com/USERNAME/tsp-surabaya-kuliner (isi setelah di-upload)"
ss = getSampleStyleSheet()
B = ParagraphStyle("B", parent=ss["BodyText"], fontName="Helvetica", fontSize=10.5, leading=15, alignment=4, spaceAfter=6)
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=16, spaceBefore=6, spaceAfter=10)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12.5, spaceBefore=8, spaceAfter=5)
CAP = ParagraphStyle("CAP", parent=B, fontSize=9, leading=12, alignment=1, textColor=colors.HexColor("#444444"))
BL = ParagraphStyle("BL", parent=B, leftIndent=14, bulletIndent=2, spaceAfter=2)
def P(t): return Paragraph(t, B)
def bl(items): return [Paragraph(i, BL, bulletText="•") for i in items]
def img(n, w=15.5):
    from PIL import Image as PI
    iw, ih = PI.open(F / n).size; return Image(str(F / n), width=w * cm, height=w * cm * ih / iw)
def tbl(data, cw=None, hdr=True):
    t = Table(data, colWidths=cw, repeatRows=1)
    st = [("FONTSIZE", (0, 0), (-1, -1), 8.5), ("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#aaaaaa")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f6fa")])]
    if hdr: st += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e79")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    t.setStyle(TableStyle(st)); return t
hm = lambda m: f"{int(m//60):02d}:{int(m%60):02d}"
E1, T = R["E1"], R["tests"]; AN = {"HC": "Hill-Climbing", "SA": "Simulated Annealing", "GA": "Genetic Algorithm", "MA": "Memetic GA"}
p = R["params"]; ut = R["opt_tsp_under_tw"]; bd = R["best_tw_detail"]

s = []
# ---- cover ----
s += [Spacer(1, 4 * cm), Paragraph("<b>MIDTERM PROJECT</b>", ParagraphStyle("c0", parent=B, alignment=1, fontSize=12)), Spacer(1, .5 * cm),
      Paragraph("<b>Optimasi Rute Wisata Kuliner Surabaya sebagai TSP dengan Time Window:<br/>Perbandingan Hill-Climbing, Simulated Annealing, dan Genetic Algorithm</b>", ParagraphStyle("c1", parent=B, alignment=1, fontSize=18, leading=24)),
      Spacer(1, 2 * cm), Paragraph("Mata Kuliah: [isi nama mata kuliah]<br/>Dosen: [isi]<br/><br/>Disusun oleh:<br/>[Nama] — [NRP]<br/><br/>[Institusi]<br/>Oktober 2026", ParagraphStyle("c2", parent=B, alignment=1, fontSize=12, leading=18)), PageBreak()]
# ---- Bab 1 ----
s += [Paragraph("Bab 1. Latar Belakang, Rumusan Masalah, dan Manfaat", H1), Paragraph("1.1 Latar Belakang", H2),
 P("Surabaya memiliki banyak kuliner khas (rawon, lontong balap, rujak cingur, sate klopo, pecel semanggi) yang tersebar di seluruh kota. Wisatawan atau pengelola paket wisata kuliner perlu menentukan urutan kunjungan agar waktu di jalan sesingkat mungkin. Ini adalah <i>Traveling Salesman Problem</i> (TSP), masalah NP-hard: untuk n titik terdapat (n-1)!/2 rute berbeda, sehingga pencarian menyeluruh tidak praktis untuk n besar."),
 P("Dalam praktik, kuliner punya <b>jam buka</b>. Pecel semanggi dan lontong kupang hanya tersedia pagi hari, sementara Kya-Kya Kembang Jepun baru ramai sore sampai malam. Rute terpendek menurut jarak belum tentu bisa dijalankan. Karena itu proyek ini memodelkan juga varian TSP dengan <i>time window</i> (TSPTW)."),
 Paragraph("1.2 Rumusan Masalah", H2)]
s += bl(["Berapa rute terpendek untuk mengunjungi 20 titik kuliner Surabaya dari satu depot (Stasiun Gubeng) dan kembali (TSP)?",
 "Bagaimana rute berubah jika setiap titik punya jam buka dan tur dimulai pukul 08.00 (TSPTW)?",
 "Di antara Hill-Climbing, Simulated Annealing, dan Genetic Algorithm, mana yang paling baik pada anggaran evaluasi yang sama, dan bagaimana performanya saat masalah membesar?"])
s += [Paragraph("1.3 Tujuan dan Batasan", H2),
 P("Tujuan: mengimplementasikan dan membandingkan tiga metode (ditambah satu varian modifikasi, Memetic GA) secara adil. Batasan: (a) jarak jalan memakai aproksimasi haversine &times; 1,3 karena API OSRM tidak dapat diakses saat eksperimen (skrip <font face='Courier'>fetch_osrm.py</font> disediakan untuk mengganti dengan jarak jalan asli); (b) koordinat adalah perkiraan sekitar titik-titik tersebut dan jam buka merupakan asumsi eksperimen, bukan data resmi tiap tempat."),
 Paragraph("1.4 Manfaat", H2)]
s += bl(["Praktis: contoh perencanaan rute kuliner/pengantaran yang menghormati jam operasional.", "Akademis: perbandingan empiris metode metaheuristik dengan anggaran evaluasi sama, uji statistik, dan optimum eksak sebagai pembanding.", "Reproduksibel: seluruh kode, data, dan seed tersedia di repositori."])
s += [PageBreak()]
# ---- Bab 2 ----
s += [Paragraph("Bab 2. Metode", H1), Paragraph("2.1 Dataset", H2),
 P(f"Dataset terdiri dari 1 depot dan 20 titik kuliner Surabaya (lihat Gambar 1). Setiap titik memiliki koordinat (lintang, bujur) dan jam buka/tutup. Matriks jarak: <b>{R['source']}</b>. Waktu tempuh = jarak / {p['speed']:.0f} km/jam; lama kunjungan {p['service']} menit per titik; tur dimulai pukul {hm(p['start'])}."),
 img("f1_dataset.png", 11), Paragraph("Gambar 1. Sebaran titik dataset berdasarkan kategori jam buka.", CAP),
 Paragraph("2.2 Formulasi Masalah", H2),
 P("Solusi adalah permutasi π dari 20 titik; rute: depot → π<sub>1</sub> → … → π<sub>20</sub> → depot."),
 P("<b>TSP:</b> minimalkan f(π) = Σ d(π<sub>i</sub>, π<sub>i+1</sub>) (km)."),
 P(f"<b>TSPTW (soft window):</b> waktu tiba t. Jika t &lt; buka, menunggu sampai buka. Keterlambatan L<sub>i</sub> = max(0, t − tutup<sub>i</sub>). Minimalkan f(π) = (durasi tur dalam menit, termasuk menunggu dan kunjungan) + {p['late_pen']:.0f} × ΣL<sub>i</sub>. Penalti besar membuat solusi tanpa keterlambatan selalu lebih disukai."),
 Paragraph("2.3 Algoritma", H2)]
s += bl(["<b>Hill-Climbing (random restart):</b> mulai dari permutasi acak; ambil tetangga acak (2-opt 50%, swap 25%, insert 25%) dan terima hanya bila lebih baik; jika 1000 percobaan beruntun gagal, restart.",
 "<b>Simulated Annealing:</b> tetangga yang sama; solusi lebih buruk diterima dengan peluang exp(−selisih biaya / T). Suhu turun geometrik dari T<sub>0</sub> = 3% skala biaya acak ke 1% dari T<sub>0</sub> tepat pada akhir anggaran (jadwal sadar-anggaran).",
 "<b>Genetic Algorithm:</b> populasi 60, seleksi turnamen k=5, Order Crossover (pc=0,9), mutasi tetangga (pm=0,9), elitisme 2.",
 "<b>Memetic GA (modifikasi):</b> GA populasi 30 dengan 5 langkah perbaikan lokal (hill-climbing) pada tiap anak; menggabungkan eksplorasi populasi dan eksploitasi lokal."])
s += [P("<b>Keadilan perbandingan:</b> semua algoritma diberi anggaran sama, yaitu jumlah evaluasi fungsi biaya (5.000 pada eksperimen utama), diulang dengan 30 seed. Parameter di atas dipilih lewat <i>grid search</i> kecil pada instance penyetelan terpisah (30 titik acak, seed 7), bukan pada data uji."),
 Paragraph("2.4 Pembanding dan Pengukuran", H2)]
s += bl(["Optimum eksak TSP dengan Held-Karp (DP bitmask) sehingga gap terhadap optimum dapat dihitung.", "Baseline: Nearest Neighbor dan rata-rata 2.000 rute acak.", "Metrik: rata-rata, simpangan baku, terbaik, gap (%) terhadap referensi, persentase run yang mencapai ≤0,1% dari referensi, dan waktu CPU. Uji signifikansi: Mann-Whitney U.",
 "Untuk TSPTW tidak ada optimum eksak; referensi adalah <i>best-known</i> (nilai terbaik dari seluruh run)."])
s += [PageBreak()]
# ---- Bab 3 ----
s += [Paragraph("Bab 3. Eksperimen dan Pembahasan", H1), P(f"Kode dan data: <font face='Courier'>{GITHUB}</font>"),
 Paragraph("3.1 Efek Time Window: mengapa TSP biasa tidak cukup", H2),
 P(f"Rute TSP optimum eksak sepanjang <b>{R['opt_tsp']:.2f} km</b>. Namun bila rute itu dijalankan dengan jam buka yang berlaku, <b>{ut['n_late']} dari 20 titik terlambat</b> (total keterlambatan {ut['late']:.0f} menit) dan tur baru selesai {hm(ut['finish'])} (hari berikutnya bila melewati 24.00). Rute TSPTW terbaik justru lebih panjang, <b>{bd['dist']:.1f} km</b>, tetapi tanpa keterlambatan, hampir tanpa menunggu ({bd['wait']:.1f} menit), dan selesai {hm(bd['finish'])}. Rute pendek kalah praktis dibanding rute yang menghormati jam buka: sarapan dikunjungi pagi, titik malam di akhir (Gambar 2 dan 3)."),
 img("f4_routes.png", 16), Paragraph("Gambar 2. Rute TSP optimum (kiri) dan rute TSPTW terbaik (kanan).", CAP), img("f5_timeline.png", 12.5), Paragraph("Gambar 3. Jadwal rute TSPTW terbaik terhadap jam buka tiap titik.", CAP),
 Paragraph("3.2 Perbandingan Utama (5.000 evaluasi, 30 seed)", H2)]
rows = [["Metode", "Mean", "Std", "Terbaik", "Gap rata-rata", "Capai ≤0,1%", "Waktu (s)"]]
for fn, un in (("tsp", "TSP (km)"), ("tw", "TSPTW (menit)")):
    rows.append([un, "", "", "", "", "", ""])
    for a in ("HC", "SA", "GA", "MA"):
        d = E1[fn][a]; rows.append([AN[a], f"{d['mean']:.2f}", f"{d['std']:.2f}", f"{d['best']:.2f}", f"{d['gap_mean_pct']:.2f}%", f"{d['hit_pct']:.0f}%", f"{d['time_s']:.2f}"])
rows.append(["Referensi", f"TSP optimum eksak = {R['opt_tsp']:.2f} km; TSPTW best-known = {R['best_tw']:.2f} menit", "", "", "", "", ""])
rows.append(["Baseline", f"Nearest Neighbor: {R['nn_tsp']:.1f} km (TSP), {R['nn_tw']:.0f} (TSPTW); acak: {R['rand_tsp']:.1f} km, {R['rand_tw']:.0f}", "", "", "", "", ""])
t = tbl(rows, [4.2*cm, 1.9*cm, 1.6*cm, 1.9*cm, 2.6*cm, 2.4*cm, 1.9*cm]); 
t.setStyle(TableStyle([("SPAN", (0, 1), (-1, 1)), ("SPAN", (0, 6), (-1, 6)), ("SPAN", (1, 11), (-1, 11)), ("SPAN", (1, 12), (-1, 12)), ("FONTNAME", (0, 1), (0, 1), "Helvetica-Bold"), ("FONTNAME", (0, 6), (0, 6), "Helvetica-Bold"), ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#dfe8f3")), ("BACKGROUND", (0, 6), (-1, 6), colors.HexColor("#dfe8f3"))]))
s += [t, Paragraph("Tabel 1. Hasil eksperimen utama.", CAP), img("f3_boxplot.png", 15.5), Paragraph("Gambar 4. Sebaran biaya terbaik 30 run.", CAP), img("f2_convergence.png", 15.5), Paragraph("Gambar 5. Kurva konvergensi.", CAP)]
tp = T["tsp"]; tw_ = T["tw"]
s += [P(f"<b>Temuan TSP.</b> Hill-Climbing (gap {E1['tsp']['HC']['gap_mean_pct']:.2f}%) dan SA ({E1['tsp']['SA']['gap_mean_pct']:.2f}%) tidak berbeda signifikan (p={tp['HC-SA']:.2f}), dan keduanya jauh lebih baik daripada GA ({E1['tsp']['GA']['gap_mean_pct']:.2f}%) dan Memetic GA ({E1['tsp']['MA']['gap_mean_pct']:.2f}%), dengan p&lt;0,001 untuk HC vs GA/MA. GA dan Memetic GA tidak berbeda signifikan (p={tp['GA-MA']:.2f})."),
 P(f"<b>Temuan TSPTW.</b> Hill-Climbing menemukan nilai terbaik pada <b>30 dari 30</b> run, SA paling lemah (gap {E1['tw']['SA']['gap_mean_pct']:.2f}%), sedangkan GA ({E1['tw']['GA']['gap_mean_pct']:.2f}%) dan Memetic GA ({E1['tw']['MA']['gap_mean_pct']:.2f}%) berada di tengah. Semua perbedaan terhadap HC dan SA signifikan (p&lt;0,01). Satu dugaan: penalti keterlambatan membuat permukaan biaya bergerigi sehingga penerimaan solusi buruk pada SA lebih banyak membuang anggaran; dugaan ini belum diuji dengan penyetelan SA khusus TSPTW."),
 Paragraph("3.3 Sensitivitas terhadap Anggaran Evaluasi", H2), img("f6_budget.png", 15.5), Paragraph("Gambar 6. Gap rata-rata terhadap anggaran (15 seed).", CAP),
 P("Pada anggaran sangat kecil (1.000 evaluasi) metode berbasis satu lintasan (HC, SA) jauh unggul; GA/Memetic GA membutuhkan populasi awal yang mahal. Pada 50.000 evaluasi semua metode mendekati optimum (gap &lt;1%), sehingga untuk 20 titik perbedaan metode hanya penting bila anggaran terbatas. GA masih sedikit tertinggal di TSP."),
 Paragraph("3.4 Skalabilitas (30 dan 60 titik antar-paket acak, 50.000 evaluasi)", H2)]
rows = [["Instance", "Masalah", "HC", "SA", "GA", "MA", "Nearest Neighbor"]]
for nr in ("30", "60"):
    for fn, nm in (("tsp", "TSP km"), ("tw", "TSPTW")):
        d = R["E3"][nr][fn]; rows.append([f"{nr} titik", nm] + [f"{d[a]['mean']:.1f} ± {d[a]['std']:.1f}" for a in ("HC", "SA", "GA", "MA")] + [f"{d['nn']:.1f}"])
s += [tbl(rows, [2.2*cm, 2.2*cm, 2.7*cm, 2.7*cm, 2.7*cm, 2.7*cm, 2.6*cm]), Paragraph("Tabel 2. Rata-rata ± simpangan baku biaya (30 seed).", CAP), img("f7_scale.png", 15), Paragraph("Gambar 7. Biaya relatif terhadap metode terbaik.", CAP),
 P("Pada 60 titik TSP, SA menjadi yang terbaik (110,6 km) mengungguli HC (112,9 km) dan GA (119,8 km), yang menunjukkan SA mulai unggul saat ruang pencarian membesar. Pada TSPTW 60 titik, keterlambatan tidak dapat dihindari (jadwal memuat 300 menit layanan ditambah perjalanan terhadap jam tutup yang ketat), sehingga biaya didominasi penalti; HC tetap terbaik, Memetic GA kedua, dan semua jauh lebih baik daripada Nearest Neighbor (49.054)."),
 Paragraph("3.5 Ancaman Validitas", H2)]
s += bl(["Jarak jalan adalah aproksimasi (haversine × 1,3); tanpa data jalan satu arah atau kemacetan. Rute akhir dapat bergeser jika memakai OSRM.", "Koordinat dan jam buka adalah asumsi eksperimen.", "Parameter diselaraskan pada TSP; SA mungkin lebih baik pada TSPTW bila disetel terpisah.", "Instance 20 titik terlalu kecil untuk membedakan metode pada anggaran besar."])
s += [PageBreak()]
# ---- Bab 4 ----
s += [Paragraph("Bab 4. Kesimpulan", H1)]
s += bl([f"Rute kuliner terpendek (TSP) adalah {R['opt_tsp']:.1f} km, tetapi tidak layak: {ut['n_late']} titik terlambat. Memodelkan jam buka (TSPTW) menghasilkan rute {bd['dist']:.0f} km yang sepenuhnya layak dan selesai {hm(bd['finish'])}.",
 "Pada anggaran sama, Hill-Climbing dengan restart adalah yang paling andal untuk 20 titik (TSP dan TSPTW), SA unggul tipis pada 60 titik TSP, dan GA/Memetic GA tertinggal pada anggaran kecil.",
 "Memetic GA memperbaiki GA biasa pada TSPTW dan skala besar, namun tidak mengalahkan HC/SA di eksperimen ini.",
 "Saran: ganti jarak dengan OSRM (jalan asli dan waktu tempuh), gunakan jam buka nyata dari Google Maps, tambah operator Or-opt/2-opt penuh atau metode lanjut (ACO, LKH), dan stel SA khusus TSPTW."])
s += [Paragraph("Referensi", H1)]
refs = ["Applegate, D. L., Bixby, R. E., Chvátal, V., Cook, W. J. (2006). <i>The Traveling Salesman Problem: A Computational Study</i>. Princeton University Press.",
 "Held, M., Karp, R. M. (1962). A dynamic programming approach to sequencing problems. <i>J. SIAM</i>, 10(1), 196–210.",
 "Kirkpatrick, S., Gelatt, C. D., Vecchi, M. P. (1983). Optimization by simulated annealing. <i>Science</i>, 220(4598), 671–680.",
 "Davis, L. (1985). Applying adaptive algorithms to epistatic domains. <i>Proc. IJCAI</i> (Order Crossover).",
 "Moscato, P. (1989). On evolution, search, optimization, genetic algorithms and martial arts: Towards memetic algorithms. Caltech Concurrent Computation Program Report 826.",
 "Russell, S., Norvig, P. (2021). <i>Artificial Intelligence: A Modern Approach</i> (4th ed.). Pearson.",
 "Luxen, D., Vetter, C. (2011). Real-time routing with OpenStreetMap data. <i>Proc. ACM SIGSPATIAL GIS</i> (OSRM).",
 "Solomon, M. M. (1987). Algorithms for the vehicle routing and scheduling problems with time window constraints. <i>Operations Research</i>, 35(2), 254–265."]
s += [Paragraph(f"[{i+1}] {r}", ParagraphStyle("r", parent=B, alignment=0, leftIndent=18, firstLineIndent=-18)) for i, r in enumerate(refs)]
def pn(c, d):
    c.setFont("Helvetica", 8); c.drawCentredString(A4[0] / 2, 1.2 * cm, str(d.page))
SimpleDocTemplate(str(ROOT / "Laporan_Midterm_TSP_Kuliner_Surabaya.pdf"), pagesize=A4, leftMargin=2.5*cm, rightMargin=2.5*cm, topMargin=2.3*cm, bottomMargin=2.2*cm, title="Optimasi Rute Kuliner Surabaya").build(s, onLaterPages=pn)
print("pdf ok")
