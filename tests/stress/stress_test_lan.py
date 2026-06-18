import urllib.request
import threading
import time

URL = 'http://127.0.0.1:8000/api/live_scan'
NUM_THREADS = 5
REQUESTS_PER_THREAD = 100

exitos = 0
fallos = 0
lock = threading.Lock()

def worker(thread_id):
    global exitos, fallos
    for i in range(REQUESTS_PER_THREAD):
        try:
            req = urllib.request.Request(URL)
            response = urllib.request.urlopen(req, timeout=0.5)
            data = response.read()
            with lock:
                exitos += 1
        except Exception as e:
            with lock:
                fallos += 1
        # Simular el polling super agresivo (100ms)
        time.sleep(0.05)

print(f'[STRESS TEST LAN] Iniciando bombardeo a {URL}')
print(f'Simulando {NUM_THREADS} Cartelerias consultando {REQUESTS_PER_THREAD} veces cada una...')

start_time = time.time()

threads = []
for i in range(NUM_THREADS):
    t = threading.Thread(target=worker, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

end_time = time.time()

print('[STRESS TEST LAN] Bombardeo finalizado.')
print(f'Tiempo total: {end_time - start_time:.2f} segundos')
print(f'Peticiones Exitosas: {exitos}')
print(f'Peticiones Fallidas: {fallos}')
