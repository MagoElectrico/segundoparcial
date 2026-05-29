import os
import cv2
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers, models
import matplotlib.pyplot as plt

# ==============================================================================
# 1. CARGAR EL DATASET (SOLO IMÁGENES Y CLASES)
# ==============================================================================
csv_maestro = pd.read_csv('dataset_completo.csv')

class_map = {
    'fanta2': 0, 'salvietti': 1,
    'pepsi': 2, 
    'cocacola': 3
}

X_images = []
Y_classes = []
RUTA_IMAGENES = "todas_las_imagenes/"

print("Cargando imágenes para Clasificación...")
for index, row in csv_maestro.iterrows():
    img_path = os.path.join(RUTA_IMAGENES, row['filename'])
    img = cv2.imread(img_path)
    
    if img is not None:
        img_resizada = cv2.resize(img, (150, 150)) # 150x150 es ideal para clasificación estándar
        X_images.append(img_resizada)
        
        clase_str = str(row['class']).lower().strip().replace(" ", "").replace("_", "").replace("-", "")
        Y_classes.append(class_map.get(clase_str, 3)) # Si no la encuentra, por defecto Coca-Cola

X_images = np.array(X_images, dtype='float32') / 255.0  # Normalizamos los píxeles directamente aquí
Y_classes = tf.keras.utils.to_categorical(np.array(Y_classes), num_classes=4)

print(f"Dataset cargado: {X_images.shape[0]} imágenes listas.")

# ==============================================================================
# 2. MODELO CNN DE CLASIFICACIÓN (La respuesta a: Which is the model architecture?)
# ==============================================================================
model = models.Sequential([
    # Entrada de la Red
    layers.Input(shape=(150, 150, 3)),
    
    # Bloque 1
    layers.Conv2D(32, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    
    # Bloque 2
    layers.Conv2D(64, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    
    # Bloque 3
    layers.Conv2D(128, (3, 3), activation='relu'),
    layers.MaxPooling2D((2, 2)),
    
    # Capas Densas de Clasificación
    layers.Flatten(),
    layers.Dense(128, activation='relu'),
    layers.Dropout(0.5), # Regularización para evitar sobreajuste
    layers.Dense(4, activation='softmax') # 4 salidas (Coca, Fanta, Pepsi, Salvieti)
])

model.compile(
    optimizer='adam',
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# ==============================================================================
# 3. ENTRENAMIENTO (Generates train and test results)
# ==============================================================================
print("\nEntrenando la CNN para superar el 88%...")
history = model.fit(
    X_images, Y_classes,
    epochs=25,
    batch_size=32,
    validation_split=0.2 # Divide automáticamente en datos de entrenamiento y test/validación
)

# ==============================================================================
# 4. RENDIMIENTO Y GRÁFICAS DEL ACCURACY
# ==============================================================================
plt.figure(figsize=(8, 5))
plt.plot(history.history['accuracy'], label='Train Accuracy', color='blue')
plt.plot(history.history['val_accuracy'], label='Test/Val Accuracy', color='orange')
plt.axhline(y=0.88, color='r', linestyle='--', label='Meta Requerida (88%)')
plt.title('Precisión del Modelo (Accuracy)')
plt.xlabel('Épocas')
plt.ylabel('Accuracy')
plt.legend()
plt.grid(True)
plt.show()

final_acc = history.history['val_accuracy'][-1] * 100
print(f"\n¡Listo! Accuracy final logrado en pruebas: {final_acc:.2f}%")
