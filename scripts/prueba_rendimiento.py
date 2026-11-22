"""Prueba de rendimiento de la consulta por radio (RNF: p95 < 500 ms con 10,000 reportes).
Uso: python3 scripts/prueba_rendimiento.py [URL_BASE] [N_PETICIONES] [RADIO_M]
Solo usa la biblioteca estándar de Python."""
import json
import random
import statistics
import sys
import time
import urllib.request

base = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
n = int(sys.argv[2]) if len(sys.argv) > 2 else 300
radio = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
random.seed(7)
tiempos = []
for _ in range(n):
    lat, lon = 22.08 + random.random() * 0.12, -101.05 + random.random() * 0.15
    url = f"{base}/api/v1/reportes?latitud={lat:.5f}&longitud={lon:.5f}&radio_m={radio}&tamano=50"
    t0 = time.perf_counter()
    with urllib.request.urlopen(url) as r:
        r.read()
    tiempos.append((time.perf_counter() - t0) * 1000)
tiempos.sort()
q = statistics.quantiles(tiempos, n=100)
resultado = {"peticiones": n, "radio_m": radio, "media_ms": round(statistics.mean(tiempos), 1),
             "p50_ms": round(q[49], 1), "p95_ms": round(q[94], 1), "p99_ms": round(q[98], 1), "max_ms": round(tiempos[-1], 1),
             "cumple_500ms_p95": q[94] < 500}
print(json.dumps(resultado, indent=2))
