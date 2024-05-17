import numpy as np


# Szenzorok értékelése egyszerű szótárral
sensor_weights = {'G': 0, 'Y': 1, 'R': 2, 'B': 3, 'O': 4}

def apply_advanced_model_control(car, model, sensor_data):
    # Súlyozott szenzoradatok elkészítése
    weighted_sensor_data = [sensor_weights.get(data, -1) for data in sensor_data]
    if -1 in weighted_sensor_data:
        print("Hiba: Ismeretlen szenzoradat.")
        return

    try:
        # Modell predikciók végrehajtása
        predicted_outputs = model.predict(np.array([weighted_sensor_data]))

        predicted_velocity = float(predicted_outputs[0])
        predicted_direction = np.argmax(predicted_outputs[1])

        # Sebesség és irány beállítása
        car.set_velocity(predicted_velocity)

        # Utasítások hozzárendelése
        direction_instructions = {
            0: ("előre", car.move_forward),
            1: ("balra", lambda: setattr(car, "angle", car.angle + 5)),
            2: ("jobbra", lambda: setattr(car, "angle", car.angle - 5)),
            3: ("előre + balra", lambda: (car.move_forward(), car.rotate(right=True))),
            4: ("előre + jobbra", lambda: (car.move_forward(), car.rotate(left=True))),
        }

        # A megfelelő utasítás végrehajtása
        direction_name, action = direction_instructions.get(predicted_direction, ("Unknown", None))
        if action:
            action()
            print(direction_name)
        else:
            print("Hiba: Ismeretlen irányítás.")

    except Exception as e:
        print(f"Error: {e}")
        car.slowing()
        car.rotate(right=True)