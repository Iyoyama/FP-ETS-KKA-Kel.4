"""Ambil matriks jarak/waktu jalan asli dari OSRM publik (jalankan di laptop dengan internet).
Hasil: data/dist_osrm.npy (km) dan data/time_osrm.npy (menit). Lalu jalankan: python src/run_experiments.py --osrm
"""
import csv, json, urllib.request, numpy as np, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
rows = list(csv.DictReader(open(root/'data/places.csv', encoding='utf-8')))
coords = ';'.join(f"{r['lon']},{r['lat']}" for r in rows)
url = f"https://router.project-osrm.org/table/v1/driving/{coords}?annotations=distance,duration"
data = json.load(urllib.request.urlopen(url, timeout=60))
np.save(root/'data/dist_osrm.npy', np.array(data['distances'])/1000.0)
np.save(root/'data/time_osrm.npy', np.array(data['durations'])/60.0)
print('OSRM matrix saved', np.array(data['distances']).shape)
