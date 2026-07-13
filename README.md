# Stigros Afbeeldingen

Dit programma maakt productafbeeldingen automatisch passend voor de website. De originele foto's blijven ongewijzigd. De nieuwe afbeeldingen worden altijd als PNG-bestand opgeslagen, met de juiste beeldverhouding en een witte achtergrond.

Het programma ondersteunt JPG, JPEG, PNG, WebP en AVIF. Een beschadigd bestand wordt overgeslagen; de andere afbeeldingen worden gewoon verder verwerkt.

## Het programma gebruiken

1. Open `Stigros-Afbeeldingen.exe`.
2. Kies het soort product:
   - **Wijn / gedistilleerd — 500 × 500** voor een vierkante afbeelding.
   - **Bier — 332 × 424** voor een hogere, rechthoekige afbeelding.
3. Klik op **Map met originele foto's kiezen** en kies de map waar de bronfoto's staan.
4. Klik op **Map voor nieuwe foto's kiezen** en kies een andere map voor het resultaat.
5. Klik op **START — afbeeldingen verwerken**.
6. Wacht tot de voortgangsbalk vol is en de melding **KLAAR** verschijnt.
7. Klik op **Map met nieuwe afbeeldingen openen** om het resultaat te bekijken.

Het programma zoekt ook in onderliggende mappen. Als de gekozen uitvoermap binnen de invoermap staat, wordt die uitvoermap overgeslagen. Bestaande bestanden worden niet overschreven: bij een dubbele naam voegt het programma automatisch `_2`, `_3` enzovoort toe.

## Welk beeldformaat moet ik kiezen?

- **500 × 500 pixels** is bedoeld voor wijn en gedistilleerd. Dit formaat is vierkant.
- **332 × 424 pixels** is bedoeld voor bier. Dit formaat is hoger dan het breed is.

De productfoto wordt nooit uitgerekt. Het programma houdt de oorspronkelijke verhouding intact en vult de overgebleven ruimte met wit.

## De Windows-versie downloaden

De Windows-versie wordt automatisch gebouwd met GitHub Actions voor 64-bits Windows 10 en Windows 11.

1. Open deze repository op GitHub.
2. Klik bovenaan op **Actions**.
3. Open de meest recente geslaagde uitvoering van **Bouw Windows-programma**.
4. Ga onderaan naar **Artifacts**.
5. Download **Stigros-Afbeeldingen-Windows-64-bit**.
6. Pak het gedownloade zipbestand uit en open `Stigros-Afbeeldingen.exe`.

Windows SmartScreen kan waarschuwen dat het programma van een onbekende uitgever komt. Dat gebeurt omdat het `.exe`-bestand niet digitaal is ondertekend. Controleer dat het bestand uit de GitHub Actions-build van deze repository komt. Kies daarna zo nodig **Meer informatie** en **Toch uitvoeren**.

## Zelf bouwen

De build gebruikt Python 3.11, PyInstaller en de vastgelegde versies uit `requirements.txt`. Start op GitHub de workflow handmatig via **Actions**, **Bouw Windows-programma**, **Run workflow**. De workflow draait op `windows-2022` en neemt de AVIF-ondersteuning mee in één vensterprogramma zonder apart Python-venster.
