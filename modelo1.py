import cv2
import numpy as np
import tensorflow as tf
import serial
import time

try:
    uart = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
    print("✓ Puerto UART inicializado con éxito a 9600 baudios.")
except Exception as e:
    print(f"⚠️ Alerta UART: No se pudo abrir el puerto físico ({e}). Se ejecutará en modo simulación.")
    uart = None

nombres_clases = ['Coca Cola', 'Fanta', 'Pepsi', 'Salvietti']
UMBRAL_CONFIANZA = 0.75  

print("Cargando el modelo optimizado...")
model = tf.keras.models.load_model('/home/cookie/Segundo_parcial/detector_gaseosas_cnn.h5')

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise IOError("No se pudo abrir la cámara web.")

print("\n=== ¡SISTEMA INTEGRADO INICIADO! ===")
print("Presiona 'q' para salir.\n")

ultimo_estado_enviado = None
ultimo_tiempo_envio = time.time()


while True:
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
        if clase_predicha == 'Coca Cola':
            estado_actual = 'C' 
            texto_pantalla = f"Coca Cola: {probabilidad_ganadora * 100:.1f}% -> UART: C"
            color = (0, 0, 255) 
        elif clase_predicha == 'Salvietti':
            estado_actual = 'S' 
            texto_pantalla = f"Salvietti: {probabilidad_ganadora * 100:.1f}% -> UART: S"
            color = (0, 255, 0) 
        else:
            estado_actual = 'X' 
            texto_pantalla = f"{clase_predicha} -> Fuera de regla -> UART: X"
            color = (255, 0, 0)
    else:
        estado_actual = 'X'   
        texto_pantalla = "No hay nada -> UART: X"
        color = (200, 200, 200)

    if uart is not None:
        if (estado_actual != ultimo_estado_enviado) or (time.time() - ultimo_tiempo_envio > 1.5):
            uart.write(estado_actual.encode('utf-8'))
            ultimo_estado_enviado = estado_actual
            ultimo_tiempo_envio = time.time()
            print(f"Enviado por UART: {estado_actual}")

    cv2.rectangle(frame, (10, 20), (550, 70), (0, 0, 0), -1)
    cv2.putText(frame, texto_pantalla, (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2, cv2.LINE_AA)
    cv2.imshow('Raspberry Pi to TIVA - UART Out', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if uart is not None:
    uart.close()
