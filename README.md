# Stigros Afbeeldingen

> **Portreteditie:** deze branch is bedoeld voor de bestaande Stigros-webshop die oude productafbeeldingen als 115 × 180-portret toont. De normale 500 × 500-versie blijft ongewijzigd beschikbaar op de branch `main`.

Dit programma maakt productafbeeldingen automatisch passend voor de website. De originele foto's blijven ongewijzigd. De nieuwe afbeeldingen worden als PNG- of JPG-bestand opgeslagen, met de juiste beeldverhouding en een witte achtergrond.

Het programma ondersteunt JPG, JPEG, JFIF, PNG, WebP en AVIF. Een beschadigd bestand wordt overgeslagen; de andere afbeeldingen worden gewoon verder verwerkt.

## Het programma gebruiken

1. Open `Stigros-Afbeeldingen.exe`.
2. Kies het soort product:
   - **Wijn / gedistilleerd — 115 × 180** voor dezelfde portretverhouding als de bestaande Stigros-productafbeeldingen.
   - **Bier — 115 × 180** voor dezelfde portretverhouding als de bestaande Stigros-bierafbeeldingen.
3. Kies bij **Uitvoerformaat** voor **PNG** of **JPG**. PNG is de standaardkeuze.
4. Klik op **Map met originele foto's kiezen** en kies de map waar de bronfoto's staan.
5. Klik op **Map voor nieuwe foto's kiezen** en kies een andere map voor het resultaat.
6. Klik op **START — afbeeldingen verwerken**.
7. Wacht tot de voortgangsbalk vol is en de melding **KLAAR** verschijnt.
8. Klik op **Map met nieuwe afbeeldingen openen** om het resultaat te bekijken.

Het programma zoekt ook in onderliggende mappen. Als de gekozen uitvoermap binnen de invoermap staat, wordt die uitvoermap overgeslagen. Bestaande bestanden worden niet overschreven: bij een dubbele naam voegt het programma automatisch `_2`, `_3` enzovoort toe.

## Welk beeldformaat moet ik kiezen?

- **115 × 180 pixels** is bedoeld voor wijn en gedistilleerd. Dit formaat sluit aan op de bestaande portretafbeeldingen van de Stigros-webshop.
- **115 × 180 pixels** wordt in deze portreteditie ook voor bier gebruikt. Een controle van de actuele webshop liet zien dat vrijwel alle bestaande bierafbeeldingen dit formaat gebruiken.

De productfoto wordt nooit uitgerekt. Het programma houdt de oorspronkelijke verhouding intact en vult de overgebleven ruimte met wit. Na het wegsnijden van lege randen gebruikt de langste begrenzende zijde van het product in deze portreteditie ongeveer 75% van de beschikbare canvaszijde. Dit komt overeen met de gemeten vulling van de bestaande Stigros-portretafbeeldingen.

## Welk uitvoerformaat moet ik kiezen?

- **PNG** geeft de maximale beeldkwaliteit en ondersteunt transparantie. Het programma gebruikt voor productafbeeldingen altijd een witte achtergrond. PNG-bestanden zijn meestal groter.
- **JPG** geeft kleinere bestanden en is daardoor handig voor websites. JPG ondersteunt geen transparantie en gebruikt hier een hoge kwaliteit van 92%.

De bestandsnaam bevat altijd de gekozen afmetingen en extensie, bijvoorbeeld `product_115x180.png` of `product_115x180.jpg`.

## De Windows-portretversie downloaden

Deze branch bouwt automatisch `Stigros-Afbeeldingen-Portret.exe` met GitHub Actions voor 64-bits Windows 10 en Windows 11. De portretbuild wordt bewust niet als de nieuwste openbare Release gemarkeerd, omdat die plek bij de normale 500 × 500-editie op `main` hoort.

1. Open op GitHub **Actions** en kies **Bouw Windows-programma (portret)**.
2. Open de nieuwste geslaagde run van de branch `codex/portrait-product-images`.
3. Download onder **Artifacts** `Stigros-Afbeeldingen-Portret-Windows-64-bit`.
4. Pak het artifact uit en open `Stigros-Afbeeldingen-Portret.exe`. Voor het downloaden van een Actions-artifact is een GitHub-account nodig.

Windows SmartScreen kan waarschuwen dat het programma van een onbekende uitgever komt. Dat gebeurt omdat het `.exe`-bestand niet digitaal is ondertekend. Controleer dat het bestand uit de GitHub Actions-build van deze repository komt. Kies daarna zo nodig **Meer informatie** en **Toch uitvoeren**.

## Updates van de portreteditie

De automatische updatecontrole staat in deze aparte portreteditie uit. Zo kan de app gebruikers nooit per ongeluk naar de normale 500 × 500-editie sturen. Nieuwe portretbuilds zijn terug te vinden bij de GitHub Actions-runs van deze branch.

## Zelf bouwen

De build gebruikt Python 3.11, PyInstaller en de vastgelegde versies uit `requirements.txt`. Start op GitHub de workflow handmatig via **Actions**, **Bouw Windows-programma (portret)**, **Run workflow**. De workflow draait op `windows-2022` en neemt de AVIF-ondersteuning en het Stigros-logo mee in één vensterprogramma zonder apart Python-venster.

Verhoog bij een nieuwe portretbuild zo nodig `APP_VERSION` bovenaan in `Automatische_bottles.py`. De portreteditie begint apart bij versie `1.0.0`.

De schaalgrootte is centraal instelbaar met `TARGET_FILL` bovenaan in `Automatische_bottles.py`. De waarde `0.75` betekent dat het product maximaal 75% van de bruikbare breedte of hoogte inneemt.
