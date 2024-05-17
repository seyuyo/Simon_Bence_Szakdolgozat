def should_rotate_left(sensor_data):
    # Ellenőrzi, hogy van-e legalább egy sárga az elején, amit csak piros követ
    has_yellow = False
    for i, color in enumerate(sensor_data):
        if color == 'Y':
            has_yellow = True
        elif color == 'R' and has_yellow:
            continue
        else:
            # Ha talál egy nem pirosat a sárga után, vagy bármilyen más mintát, akkor False-t ad vissza
            return False
    # Csak akkor ad True-t vissza, ha legalább egy sárgát talált, amit csak piros követ
    return has_yellow

def apply_control(car, sensor_data):
    # Számolja az egyes színek észlelését
    green_count = sensor_data.count('G')
    yellow_count = sensor_data.count('Y')
    red_count = sensor_data.count('R')
    black_count = sensor_data.count('B')
    orange_count = sensor_data.count('O')

    # ha az autó 3 másodpercig nem mozog, akkor előre megy
    if car.get_velocity() == 0:
        car.move_forward()

        # Kezeli a gyalogost (fekete) azáltal, hogy a másik oldalra fordul
    if black_count > 0:
        # Bal oldali érzékelők
        if sensor_data[0] == 'B' or sensor_data[1] == 'B' or sensor_data[2] == 'B':
            car.slowing()
            car.rotate(left=True)
            print("Gyalogos érzékelve bal oldalon, jobbra fordulás.")
        # Jobb oldali érzékelők
        elif sensor_data[5] == 'B' or sensor_data[4] == 'B' or sensor_data[3] == 'B':
            car.slowing()
            car.rotate(right=True)
            print("Gyalogos érzékelve jobb oldalon, balra fordulás.")
        elif sensor_data[2] == 'B' and sensor_data[3] == 'B':
            car.slowing()
            car.rotate(left=True)
        elif sensor_data[3] == 'B' and sensor_data[4] == 'B':
            car.slowing()
            car.rotate(right=True)
        car.slowing()

        # Kezeli a sár érzékelését (O) lassítással
    elif orange_count > 0:
        # Bal oldali érzékelők
        if sensor_data[0] == 'O' or sensor_data[1] == 'O' or sensor_data[2] == 'O':
            car.slowing()
            car.rotate(left=True)
            print("Gyalogos érzékelve bal oldalon, jobbra fordulás.")
        # Jobb oldali érzékelők
        elif sensor_data[5] == 'O' or sensor_data[4] == 'O' or sensor_data[3] == 'O':
            car.slowing()
            car.rotate(right=True)
            print("Gyalogos érzékelve jobb oldalon, balra fordulás.")
        elif sensor_data[2] == 'O' and sensor_data[3] == 'O':
            car.slowing()
            car.rotate(left=True)
        elif sensor_data[3] == 'O' and sensor_data[4] == 'O':
            car.slowing()
            car.rotate(right=True)
        car.slowing()

    # Elsőbbséget élvez a piros érzékelése, hogy elkerülje a tiltott területeket
    if red_count > 0:
        # Értékeli, hol található a legtöbb piros észlelés
        left_red_count = sum(1 for i in sensor_data[:len(sensor_data) // 2] if i == 'R')
        right_red_count = sum(1 for i in sensor_data[len(sensor_data) // 2:] if i == 'R')

        if red_count > 0 and green_count > 0 and yellow_count > 0:
            car.move_forward()

        if red_count >= 4:
            car.move_forward()
            car.rotate(right=True)
            print("Túl sok piros; előre halad.")


        if left_red_count > right_red_count:
            if should_rotate_left(sensor_data):
                car.rotate(right=True)
            car.move_forward()
            car.rotate(left=True)
        elif right_red_count > left_red_count and green_count == 0:
            # print("Több piros jobb oldalon; hátrafelé halad és balra fordul.")
            if sensor_data[0] == 'Y' and sensor_data[-1] == 'R' or sensor_data[-1] == 'Y' and sensor_data[0] == 'R':
                car.rotate(right=True)
                car.move_forward()
            car.move_forward()
        elif left_red_count == right_red_count:
            # Ha a piros egyenletesen oszlik el vagy központosított
            # print("A piros központosított vagy egyenletesen elosztott; akció kiválasztása.")
            if sensor_data[0] == 'Y' and sensor_data[1] == 'R' and sensor_data[5] == 'R' and sensor_data[4] == 'R' and sensor_data[2] == 'R':
                car.rotate(right=True)
                print("Jobbra fordul")
            elif sensor_data[4] == 'Y' and sensor_data[3] == 'R' and sensor_data[0] == 'R' and sensor_data[1] == 'R' and sensor_data[2] == 'R':
                car.rotate(left=True)
                print("balra fordul")
            else:
                car.move_forward()

    # Kezeli a sárga érzékelését óvatos megközelítés vagy fordulás érdekében
    elif yellow_count > 0:
        if yellow_count >= 5:
            car.move_backward()

        if sensor_data[0] == 'Y' and sensor_data[5] == 'Y' and green_count > 0:
            car.move_forward()

        if sensor_data[0] == 'Y' or sensor_data[1] == 'Y':  # Assuming these are left-side sensors
            if sensor_data[0] == 'Y' and sensor_data[5] == 'R' or sensor_data[5] == 'Y' and sensor_data[0] == 'R':
                car.rotate(left=True)
            elif sensor_data[0] == 'Y' and sensor_data[5] == 'B' or sensor_data[5] == 'Y' and sensor_data[0] == 'B':
                car.rotate(left=True)
            car.rotate(left=True)

        elif sensor_data[5] == 'Y' or sensor_data[4] == 'Y':  # Right-side sensors
            if sensor_data[0] == 'Y' and sensor_data[5] == 'R' or sensor_data[5] == 'Y' and sensor_data[0] == 'R':
                car.rotate(left=True)
            car.rotate(right=True)

        elif sensor_data[2] == 'Y' or sensor_data[3] == 'Y':
            car.move_forward()

    elif orange_count > 0:
        if orange_count == len(sensor_data):
            car.move_forward()
        if sensor_data[0] == 'O' and sensor_data[5] == 'O' and green_count > 0:
            car.move_forward()
        if sensor_data[0] == 'O' or sensor_data[1] == 'O':
            if sensor_data[0] == 'O' and sensor_data[5] == 'R' or sensor_data[5] == 'O' and sensor_data[0] == 'R':
                car.rotate(right=True)
            car.rotate(left=True)
        elif sensor_data[5] == 'O' or sensor_data[4] == 'O':
            if sensor_data[0] == 'O' and sensor_data[5] == 'R' or sensor_data[5] == 'O' and sensor_data[0] == 'R':
                car.rotate(left=True)
            car.rotate(right=True)
    # előre megy, ha csak zöldet érzékel
    elif green_count == len(sensor_data):
        car.move_forward()

    else:
        # Lassít, ha egyik feltétel sem teljesül
        car.slowing()
