# Simon Bence Szakdolgozata | Szegedi Tudományegyetem Természettudományi és Informatikai Kar | Programtervező informatikus

Önvezető jármű vezérlésének megvalósítása virtuális kétdimenziós környezetben, mesterséges intelligencia alkalmazásával


A szakdolgozatom célja egy olyan szimulált mesterséges intelligencia (MI) modell által vezérelt
jármű kifejlesztése, amely képes irányítani azt egy virtuális környezetben. A modell a “sofőr”
szemszögéből szenzorok alapján kapott információkat használja fel, hogy meghatározza a
megfelelő irányítási parancsokat.

A dolgozathoz a Python programozási nyelvet fogom használni, ami nagyon fontos
szerepet játszik a mesterséges intelligencia fejlesztésben. Könnyen tanulható, hatékony,
magasszintű adatstruktúrát, objektum-orientáltságot, dinamikus típusosságot kínál a
fejlesztőknek, kutatóknak a természettudományok területén is. Nem beszélve a
megszámlálhatatlan modulról, ami a fejlesztők rendelkezésére áll.
A pálya megvalósításához a PyGame nevű Python modult fogom használni, amely
alkalmas egy kétdimenziós tér elkészítéséhez. A felülnézetes pálya útból, pálya szélből és
különböző akadályokból állhat, például sár és egyéb nehezítések. A felhasználó képes
befolyásolni az autó sebességét, kanyarodási képességét, valamint a gyorsulást és a fékezést.
Az önvezetés egy mesterséges neurális hálóval lesz megvalósítva. A mesterséges
neurális hálózat olyan számítógépes rendszereket takar, amely a biológiai idegrendszert
hivatottak utánozni. Az emberi agy neuronoknak nevezett idegsejtekből áll, a mesterséges
neurális hálók is hasonlóan működnek. Céljuk a gépi tanulás, ami a tanuló rendszerek gyakorlati
alkalmazása.

A mesterséges neurális hálózatok az emberi agy működését szimuláló számítási
modellek, amelyek a mesterséges intelligencia és gépi tanulás területén jelentős áttörést hoztak.
Strukturálisan rétegekből állnak, ahol minden rétegben több neurális egység található, amelyek
a biológiai neuronokhoz hasonlóan továbbítják az információt a következő rétegekbe.
A neurális hálózatok képesek összetett mintázatok és összefüggések felismerésére nagy
mennyiségű adatban, legyen az képfeldolgozás, beszédfelismerés vagy természetes
nyelvfeldolgozás. A hálózatok megtanulják ezeket a mintákat egy olyan folyamaton keresztül,
amelyet tanításnak nevezünk, és amely során egy hibafüggvény segítségével optimalizálják a
belső paramétereiket, az úgynevezett súlyokat. Ez a képességük teszi a mesterséges neurális
hálózatokat nélkülözhetetlenné olyan feladatoknál, amelyek az emberi intuíciót és megértést
igénylik.

A szakdolgozat bemutatja a modell architektúráját, a tanulási módszertant, az
alkalmazott technológiákat, valamint az eredményeket és az értékelést. További célja, hogy
bemutassa, hogy az MI modell hogyan képes adaptálni és javítani a vezetési teljesítményét
különböző körülmények között. 

## Futtatás

```bash
pip install -r requirements.txt
python DrivingGame/main.py model      # neurális háló vezet (alapértelmezett)
python DrivingGame/main.py rule       # szabályalapú vezérlő (automated_car.py)
python DrivingGame/main.py manual     # kézi vezetés: W/A/S/D vagy nyilak
python DrivingGame/main.py qlearning  # Q-tanulás, kilépéskor menti a q_table.json-t
```

A modell újratanítása (az `automated_driving_data_full.csv` alapján):

```bash
cd DrivingGame && python model.py     # -> automated_trained_model_v2.keras
```

A tanítóadat csak a sebességet tartalmazza, ezért az irány címkéket a `model.py`
a szabályalapú vezérlő (`automated_car.py`) döntéséből állítja elő.

![A háló által vezetett autó útvonala több körön át](docs/model_trajectory.png)
