import cv2
import numpy as np
import tensorflow as tf
import time
import matplotlib.pyplot as plt
import RPi.GPIO as GPIO  

# 1. CONFIGURACIÓN DE PINES GPIO
PIN_BOTON = 17 

GPIO.setmode(GPIO.BCM)

GPIO.setup(PIN_BOTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# 2. CONFIGURACIÓN DEL MODELO IA
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
print("¡SISTEMA ESTADÍSTICO CON PARADA DE EMERGENCIA!")
print("Conecta tu botón al GPIO 17 de la Raspberry Pi.")
print("=========================================\n")

# Control de tiempos y estados
tiempo_inicio = time.time()
DURACION_INSPECCION = 60.0  
ultimo_tiempo_conteo = 0  
INTERVALO_CONTEO = 2.0    

# Variables de estado para el Botón de Emergencia
sistema_pausado = False
ultimo_estado_boton = 1  

# 3. BUCLE PRINCIPAL DE CAPTURA
while True:
    lectura_boton = GPIO.input(PIN_BOTON)
    
    # Detectar el flanco de bajada (cuando pasa de NO presionado [1] a presionado [0])
    if lectura_boton == 0 and ultimo_estado_boton == 1:
        sistema_pausado = not sistema_pausado 
        
        if sistema_pausado:
            print("\n[EMERGENCIA] ¡Botón presionado! Sistema CONGELADO. Conteo resguardado.")
        else:
            print("\n[REANUDADO] ¡Botón presionado de nuevo! El sistema continúa trabajando.")
            
        time.sleep(0.2)  
        
    ultimo_estado_boton = lectura_boton

    #  CASO A: EL SISTEMA ESTÁ EN PAUSA DE EMERGENCIA 
    if sistema_pausado:
        ret, frame = cap.read()
        if not ret or frame is None:
            continue
            
      
        tiempo_inicio += (time.time() - (tiempo_inicio + (DURACION_INSPECCION - (DURACION_INSPECCION - (time.time() - tiempo_inicio)))))
        
        # Interfaz visual de Advertencia de Emergencia
        cv2.rectangle(frame, (10, 10), (620, 80), (0, 0, 255), -1)
        cv2.putText(frame, " PARADA DE EMERGENCIA ", (30, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 3, cv2.LINE_AA)
        cv2.putText(frame, "Conteo congelado y a salvo", (160, 73), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        
        cv2.imshow('Laboratorio UCB - Contador Estadistico por Tiempo', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue 

    #  CASO B: EL SISTEMA TRABAJA NORMALMENTE 
    tiempo_actual = time.time()
    tiempo_transcurrido = tiempo_actual - tiempo_inicio
    tiempo_restante = DURACION_INSPECCION - tiempo_transcurrido

    if tiempo_transcurrido >= DURACION_INSPECCION:
        print("\n¡Tiempo cumplido! Finalizando captura de video...")
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

    # Dibujar Interfaz Estándar
    texto_reloj = f"Tiempo restante: {int(tiempo_restante)}s"
    cv2.rectangle(frame, (10, 10), (620, 80), (0, 0, 0), -1)
    cv2.putText(frame, texto_pantalla, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)
    cv2.putText(frame, texto_reloj, (400, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2, cv2.LINE_AA)
    
    cv2.imshow('Contador Estadistico por Tiempo', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
GPIO.cleanup()  

# 4. GENERAR ARCHIVO DE TEXTO (.TXT) Y GRÁFICA
ruta_txt = "reporte_conteo.txt"
with open(ruta_txt, "w") as archivo:
    archivo.write("=========================================\n")
    archivo.write("   REPORTE DE INSPECCIÓN - CON E-STOP    \n")
    archivo.write("=========================================\n")
    archivo.write("RESULTADOS DEL CONTEO (Resguardado con exito):\n")
    for marca, conteo in contador_botellas.items():
        archivo.write(f"- {marca}: {conteo} unidades detectadas.\n")
    archivo.write("=========================================\n")

print(f"Archivo '{ruta_txt}' generado con éxito.")

# Graficar
top_3_botellas = sorted(contador_botellas.items(), key=lambda item: item[1], reverse=True)[:3]
marcas_grafica = [item[0] for item in top_3_botellas]
conteos_grafica = [item[1] for item in top_3_botellas]

plt.figure(figsize=(8, 5))
plt.bar(marcas_grafica, conteos_grafica, color=['#d63031', '#2ecc71', '#0984e3'], edgecolor='black', width=0.6)
plt.title('Top 3 Botellas (Protegido por Parada de Emergencia)', fontsize=13, weight='bold', pad=15)
plt.ylabel('Cantidad de Unidades')
plt.gca().yaxis.get_major_locator().set_params(integer=True)
for i, valor in enumerate(conteos_grafica):
    plt.text(i, valor + 0.05, str(valor), ha='center', va='bottom', weight='bold')

plt.tight_layout()
plt.show()
