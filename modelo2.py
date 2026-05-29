import cv2
import numpy as np
import tensorflow as tf
import time
import matplotlib.pyplot as plt

nombres_clases = ['Coca Cola', 'Fanta', 'Pepsi', 'Salvietti']
UMBRAL_CONFIANZA = 0.75  

contador_botellas = {
    'Coca Cola': 0,
    'Fanta': 0,
    'Pepsi': 0,
    'Salvietti': 0
}

print("Cargando el modelo optimizado...")
model = tf.keras.models.load_model('/home/cookie/Segundo_parcial/detector_gaseosas_cnn.h5')

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise IOError("No se pudo abrir la cámara web.")

print("\n=========================================")
print(" ¡SISTEMA DE INSPECCIÓN ESTADÍSTICA OPTIMIZADO!")
print("El análisis durará exactamente 60 segundos.")
print("Las botellas se contabilizan máximo UNA VEZ cada 2 segundos.")
print("=========================================\n")

tiempo_inicio = time.time()
DURACION_INSPECCION = 60.0  

ultimo_tiempo_conteo = 0
INTERVALO_CONTEO = 2.0 


while True:
    tiempo_actual = time.time()
    tiempo_transcurrido = tiempo_actual - tiempo_inicio
    tiempo_restante = DURACION_INSPECCION - tiempo_transcurrido

    if tiempo_transcurrido >= DURACION_INSPECCION:
        print("\n ¡Tiempo cumplido! Finalizando captura de video...")
        break

    ret, frame = cap.read()
    if not ret or frame is None:
        continue

    img_analisis = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img_resizada = cv2.resize(img_analisis, (160, 160))
    img_input = np.array(img_resizada, dtype='float32') / 255.0
    img_input = np.expand_dims(img_input, axis=0)

    predicciones = model.predict(img_input, verbose=0)[0]
    indice_ganador = np.argmax(predicciones)
    probabilidad_ganadora = predicciones[indice_ganador]
    clase_predicha = nombres_clases[indice_ganador]

    if probabilidad_ganadora >= UMBRAL_CONFIANZA:
        if tiempo_actual - ultimo_tiempo_conteo >= INTERVALO_CONTEO:
            contador_botellas[clase_predicha] += 1
            ultimo_tiempo_conteo = tiempo_actual 
            print(f" Registrado con éxito: {clase_predicha}")
            
        texto_pantalla = f"{clase_predicha} ({probabilidad_ganadora * 100:.1f}%)"
        color = (0, 255, 0)
    else:
        texto_pantalla = "Buscando objeto..."
        color = (200, 200, 200)

    texto_reloj = f"Tiempo restante: {int(tiempo_restante)}s"
    cv2.rectangle(frame, (10, 10), (620, 80), (0, 0, 0), -1)
    cv2.putText(frame, texto_pantalla, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)
    cv2.putText(frame, texto_reloj, (400, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2, cv2.LINE_AA)
    
    cv2.imshow('Contador Estadistico por Tiempo', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\n Inspección cancelada por el usuario.")
        break

cap.release()
cv2.destroyAllWindows()

ruta_txt = "reporte_conteo.txt"
with open(ruta_txt, "w") as archivo:
    archivo.write("=========================================\n")
    archivo.write("   REPORTE DE INSPECCIÓN - MODELO IA     \n")
    archivo.write("=========================================\n")
    archivo.write(f"Fecha y Hora de Cierre: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    archivo.write(f"Duración establecida: {DURACION_INSPECCION} segundos\n\n")
    archivo.write("RESULTADOS DEL CONTEO (Unidades controladas):\n")
    for marca, conteo in contador_botellas.items():
        archivo.write(f"- {marca}: {conteo} unidades detectadas.\n")
    archivo.write("=========================================\n")

print(f"✓ Archivo '{ruta_txt}' generado con éxito.")


top_3_botellas = sorted(contador_botellas.items(), key=lambda item: item[1], reverse=True)[:3]

marcas_grafica = [item[0] for item in top_3_botellas]
conteos_grafica = [item[1] for item in top_3_botellas]

plt.figure(figsize=(8, 5))
colores_barras = ['#d63031', '#2ecc71', '#0984e3']

plt.bar(marcas_grafica, conteos_grafica, color=colores_barras, edgecolor='black', width=0.6)
plt.title('Top 3 Botellas Más Detectadas (Muestreo cada 2s)', fontsize=14, weight='bold', pad=15)
plt.xlabel('Marca de Gaseosa', fontsize=12, labelpad=10)
plt.ylabel('Cantidad de Unidades', fontsize=12, labelpad=10)
plt.grid(axis='y', linestyle='--', alpha=0.7)

plt.gca().yaxis.get_major_locator().set_params(integer=True)

for i, valor in enumerate(conteos_grafica):
    plt.text(i, valor + 0.05, str(valor), ha='center', va='bottom', fontsize=11, weight='bold')

plt.tight_layout()
print("\nMostrando gráfica final...")
plt.show()
