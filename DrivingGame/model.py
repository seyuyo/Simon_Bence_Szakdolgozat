import pandas as pd
import os
import csv
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.optimizers import Adam, SGD, RMSprop
# noinspection PyUnresolvedReferences
from tensorflow.keras.models import Model, load_model, Sequential
from tensorflow.keras.layers import Input, Dense, Dropout
from keras.callbacks import EarlyStopping, ReduceLROnPlateau
import numpy as np
import matplotlib.pyplot as plt



# Optimalizálók inicializálása
sgd_optimizer = SGD(learning_rate=0.001, momentum=0.9, nesterov=True)
rmsprop_optimizer = RMSprop(learning_rate=0.001)
adam_optimizer = Adam(learning_rate=0.001)
# Adatok betöltése


def load_data():
    # Adatok beolvasása
    df = pd.read_csv('automated_driving_data_full.csv')
    df = df.replace({'G': 1, 'Y': 2, 'R': 3, 'B': 4, 'O': 5})

    # Bemenetek (szenzor adatok)
    X = df[['sensor_1', 'sensor_2', 'sensor_3', 'sensor_4', 'sensor_5', 'sensor_6']].values

    # Normalizálás
    scaler = MinMaxScaler()
    X = scaler.fit_transform(X)

    # kimenetek (sebesség, forgási sebesség, gyorsulás)
    y_velocity = df['velocity'].values

    # Tömbök egyesítése listába
    y = [y_velocity]

    return X, y

# Modell létrehozása és optimalizáló beállítása
def create_model(input_dim, optimizer):
    input_layer = Input(shape=(input_dim,))
    x = Dense(512, activation='relu')(input_layer)
    x = Dropout(0.3)(x)
    x = Dense(256, activation='relu')(x)
    x = Dropout(0.3)(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.3)(x)
    x = Dense(64, activation='relu')(x)

    velocity_output = Dense(1, name='velocity_output')(x)
    direction_output = Dense(5, activation='softmax', name='direction_output')(x)

    model = Model(inputs=input_layer, outputs=[velocity_output, direction_output])
    model.compile(optimizer=optimizer,
                  loss={'velocity_output': 'mean_squared_error',
                        'direction_output': 'categorical_crossentropy'},
                  loss_weights={'velocity_output': 0.5, 'direction_output': 1.0},
                  metrics={'velocity_output': ['mse'],
                           'direction_output': ['categorical_accuracy']})
    return model


# Adatok betöltése és előkészítése
X, y = load_data()

# A kimenetek kezelése egyesítve, hogy megfeleljenek a train_test_split követelményeinek
X_train, X_test, y_train, y_test = train_test_split(X, np.transpose(y), test_size=0.2, random_state=42)

# A y_train és y_test tömböket vissza kell alakítani különálló tömbökké, mielőtt a modellt tanítanánk velük
y_train = [y_train[:, i] for i in range(y_train.shape[1])]
y_test = [y_test[:, i] for i in range(y_test.shape[1])]

# Optimalizálók definiálása
optimizers = {
    'adam': Adam(learning_rate=0.001),
    'sgd': SGD(learning_rate=0.001),
    'rmsprop': RMSprop(learning_rate=0.001)
}

# Modell tanítása és eredmények gyűjtése
def train_model(optimizer_name, optimizer):
    model = create_model(X_train.shape[1], optimizer)
    reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.2, patience=3, min_lr=1e-6)
    early_stopping = EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)
    history = model.fit(X_train, y_train, epochs=100, batch_size=32, validation_split=0.2, callbacks=[early_stopping, reduce_lr])
    return history

# Eredmények tárolása
# histories = {}
#
# for optimizer_name, optimizer in optimizers.items():
#     print(f"Training with {optimizer_name} optimizer...")
#     history = train_model(optimizer_name, optimizer)
#     histories[optimizer_name] = history
#
# # Eredmények plotolása és mentése
# for optimizer_name, history in histories.items():
#     plt.figure(figsize=(12, 6))
#
#     # Loss plot
#     plt.subplot(1, 2, 1)
#     plt.plot(history.history['loss'], label='Train Loss')
#     plt.plot(history.history['val_loss'], label='Validation Loss')
#     plt.title(f'Model Loss with {optimizer_name}')
#     plt.ylabel('Loss')
#     plt.xlabel('Epoch')
#     plt.legend(loc='upper right')
#
#     plt.tight_layout()
#
#     # Save plot
#     if not os.path.exists('results'):
#         os.makedirs('results')
#     plt.savefig(f'results/{optimizer_name}_results.png')
#     plt.close()

load_model = load_model('automated_trained_model_long_v1.16_rms_optimizer_5output_LR_0.001.h5')
