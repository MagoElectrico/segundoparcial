import cv2
import numpy as np
import tensorflow as tf

# ==============================================================================
# 1. CONFIGURACIÓN INICIAL Y CARGA DEL MODELO
# ==============================================================================
# El orden numérico estricto debe coincidir con tu entrenamiento con MobileNetV2
nombres_clases = ['Coca Cola', 'Fanta', 'Pepsi', 'Salvietti']

# CONFIANZA MÍNIMA: Si el modelo está menos de 75% seguro, dirá que no hay nada
UMBRAL_CONFIANZA = 0.75  

print("Cargando el modelo optimizado para tiempo real...")
model = tf.keras.models.load_model('detector_gaseosas_cnn.h5')

# Inicializar la cámara web (0 es el ID por defecto de la cámara integrada)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    raise IOError("No se pudo abrir la cámara web. Verifica los permisos de tu sistema.")

print("\n=== ¡CÁMARA INICIADA! ===")
print("Coloca una botella frente a la cámara.")
print("Presiona la tecla 'q' para cerrar la ventana.")
print("==========================\n")

# ==============================================================================
# 2. BUCLE PRINCIPAL DE CAPTURA EN VIVO
# ==============================================================================
while True:
    # Capturar fotograma por fotograma
    ret, frame = cap.read()
    if not ret or frame is None:
        continue

    # Duplicar el fotograma para procesarlo sin arruinar la imagen que se muestra
    img_analisis = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Redimensionar al tamaño que espera la red (160x160 para MobileNetV2)
    img_resizada = cv2.resize(img_analisis, (160, 160))
    
    # Normalizar los píxeles y expandir dimensiones para crear el batch (1, 160, 160, 3)
    img_input = np.array(img_resizada, dtype='float32') / 255.0
    img_input = np.expand_dims(img_input, axis=0)

    # ==============================================================================
    # 3. PREDICCIÓN (INFERENCIA) EN TIEMPO REAL
    # ==============================================================================
    predicciones = model.predict(img_input, verbose=0)[0]
    indice_ganador = np.argmax(predicciones)
    probabilidad_ganadora = predicciones[indice_ganador]
    clase_predicha = nombres_clases[indice_ganador]

    # ==============================================================================
    # 4. FILTRO DE UMBRAL Y DIBUJAR LOS RESULTADOS
    # ==============================================================================
    # Si la seguridad de la predicción supera nuestro umbral, muestra la marca
    if probabilidad_ganadora >= UMBRAL_CONFIANZA:
        texto_pantalla = f"{clase_predicha}: {probabilidad_ganadora * 100:.1f}%"
        color = (0, 255, 0) # Verde para acierto seguro
    else:
        # Si está por debajo del umbral, ignoramos las suposiciones locas del modelo
        texto_pantalla = "No hay nada"
        color = (200, 200, 200) # Gris claro para estado vacío

    # Pintar un rectángulo de fondo para que el texto sea legible
    cv2.rectangle(frame, (10, 20), (450, 70), (0, 0, 0), -1)
    
    # Escribir el resultado sobre el fotograma en vivo
    cv2.putText(
        frame, 
        texto_pantalla, 
        (20, 55), 
        cv2.FONT_HERSHEY_SIMPLEX, 
        1.1, 
        color, 
        3, 
        cv2.LINE_AA
    )

    # Mostrar la ventana con el video y el texto superpuesto
    cv2.imshow('Detector de Sodas en Vivo', frame)

    # Escuchar el teclado. Si presionas 'q', el bucle se rompe y se cierra la cámara
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# ==============================================================================
# 5. LIBERAR RECURSOS
# ==============================================================================
cap.release()
cv2.destroyAllWindows()
print("Cámara cerrada correctamente. ¡Prueba terminada!")
