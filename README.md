# Optimasi Rute Kuliner Surabaya (TSP + Time Window)
Perbandingan Hill-Climbing, Simulated Annealing, Genetic Algorithm, dan Memetic GA.

```
pip install numpy scipy matplotlib reportlab python-pptx pillow
python src/fetch_osrm.py          # opsional: jarak jalan asli (butuh internet)
python src/run_experiments.py [--osrm]   # ~4 menit
python src/make_figures.py
python src/build_report.py && python src/build_ppt.py
```
- `data/places.csv`: koordinat & jam buka (aproksimasi, silakan ganti dengan data Google Maps)
- `src/tsplib.py`: model biaya + 4 algoritma + Held-Karp
