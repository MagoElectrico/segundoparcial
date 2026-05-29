import cv2
import numpy as np
import tensorflow as tf
import serial
import time

try:
    uart = serial.Serial('/dev/serial0', baudrate=9600, timeout=1)
    print("Puerto UART inicializado con éxito a 9600 baudios.")
except Exception as e:
    print(f"Alerta UART: No se pudo abrir el puerto físico ({e}). Se ejecutará en modo simulación.")
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

# --- NUEVAS VARIABLES PARA EL CONTROL DEL MOTOR ---
tiempo_inicio_vacio = None  # Almacena el momento exacto en que la pantalla se quedó vacía
motor_activo = False        # Bandera para saber si el motor ya debería estar encendido

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

    # Evaluación principal de botellas
    if probabilidad_ganadora >= UMBRAL_CONFIANZA and clase_predicha in ['Coca Cola', 'Salvietti']:
        # Si hay una botella válida en pantalla, reiniciamos el cronómetro del motor
        tiempo_inicio_vacio = None
        motor_activo = False
        
        if clase_predicha == 'Coca Cola':
            estado_actual = 'C' 
            texto_pantalla = f"Coca Cola: {probabilidad_ganadora * 100:.1f}% -> UART: C"
            color = (0, 0, 255) 
        elif clase_predicha == 'Salvietti':
            estado_actual = 'S' 
            texto_pantalla = f"Salvietti: {probabilidad_ganadora * 100:.1f}% -> UART: S"
            color = (0, 255, 0) 
    else:
        # Si NO hay gaseosa válida (es Fanta, Pepsi, o la pantalla está completamente vacía)
        if tiempo_inicio_vacio is None:
            tiempo_inicio_vacio = time.time()  # Empezar a contar los 3 segundos desde este instante
        
        tiempo_transcurrido_vacio = time.time() - tiempo_inicio_vacio
        
        # Comprobar si ya superó el umbral de los 3 segundos para activar el motor
        if tiempo_transcurrido_vacio >= 3.0:
            motor_activo = True
            estado_actual = 'M'  # 'M' le ordena a la TIVA encender el motor al 50% PWM
            texto_pantalla = f"SIN SODA, MOTOR 50% -> UART: M"
            color = (0, 165, 255)  # Naranja de advertencia
        else:
            # Sigue en el periodo de gracia antes de los 3 segundos (Lógica normal 'X')
            estado_actual = 'X'   
            texto_pantalla = f"No hay nada ({3.0 - tiempo_transcurrido_vacio:.1f}s para Motor) -> UART: X"
            color = (200, 200, 200)

    # Envío de datos por UART optimizado
    if uart is not None:
        if (estado_actual != ultimo_estado_enviado) or (time.time() - ultimo_tiempo_envio > 1.2):
            uart.write(estado_actual.encode('utf-8'))
            ultimo_estado_enviado = estado_actual
            ultimo_tiempo_envio = time.time()
            print(f"Enviado por UART: {estado_actual}")

    # Dibujar la interfaz en pantalla
    cv2.rectangle(frame, (10, 20), (580, 70), (0, 0, 0), -1)
    cv2.putText(frame, texto_pantalla, (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)
    cv2.imshow('Raspberry Pi to TIVA', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if uart is not None:
    uart.close()
