# Stigros Afbeeldingen

Dit programma maakt productafbeeldingen automatisch passend voor de website. De originele foto's blijven ongewijzigd. De nieuwe afbeeldingen worden als PNG- of JPG-bestand opgeslagen, met de juiste beeldverhouding en een witte achtergrond.

Het programma ondersteunt JPG, JPEG, JFIF, PNG, WebP en AVIF. Een beschadigd bestand wordt overgeslagen; de andere afbeeldingen worden gewoon verder verwerkt.

## Het programma gebruiken

1. Open `Stigros-Afbeeldingen.exe`.
2. Kies het soort product:
   - **Wijn / gedistilleerd — 500 × 500** voor een vierkante afbeelding.
   - **Bier — 332 × 424** voor een hogere, rechthoekige afbeelding.
3. Kies bij **Uitvoerformaat** voor **PNG** of **JPG**. PNG is de standaardkeuze.
4. Klik op **Map met originele foto's kiezen** en kies de map waar de bronfoto's staan.
5. Klik op **Map voor nieuwe foto's kiezen** en kies een andere map voor het resultaat.
6. Klik op **START — afbeeldingen verwerken**.
7. Wacht tot de voortgangsbalk vol is en de melding **KLAAR** verschijnt.
8. Klik op **Map met nieuwe afbeeldingen openen** om het resultaat te bekijken.

Het programma zoekt ook in onderliggende mappen. Als de gekozen uitvoermap binnen de invoermap staat, wordt die uitvoermap overgeslagen. Bestaande bestanden worden niet overschreven: bij een dubbele naam voegt het programma automatisch `_2`, `_3` enzovoort toe.

## Welk beeldformaat moet ik kiezen?

- **500 × 500 pixels** is bedoeld voor wijn en gedistilleerd. Dit formaat is vierkant.
- **332 × 424 pixels** is bedoeld voor bier. Dit formaat is hoger dan het breed is.

De productfoto wordt nooit uitgerekt. Het programma houdt de oorspronkelijke verhouding intact en vult de overgebleven ruimte met wit.

## Welk uitvoerformaat moet ik kiezen?

- **PNG** geeft de maximale beeldkwaliteit en ondersteunt transparantie. Het programma gebruikt voor productafbeeldingen altijd een witte achtergrond. PNG-bestanden zijn meestal groter.
- **JPG** geeft kleinere bestanden en is daardoor handig voor websites. JPG ondersteunt geen transparantie en gebruikt hier een hoge kwaliteit van 92%.

De bestandsnaam bevat altijd de gekozen afmetingen en extensie, bijvoorbeeld `product_500x500.png` of `product_500x500.jpg`.

## De Windows-versie downloaden

De Windows-versie wordt automatisch gebouwd met GitHub Actions voor 64-bits Windows 10 en Windows 11. Na iedere geslaagde build op `main` wordt de nieuwste openbare GitHub Release aangemaakt of bijgewerkt.

1. Open de pagina met de [nieuwste GitHub Release](https://github.com/Dvanno1/stigros-image-tool/releases/latest).
2. Klik onder **Assets** rechtstreeks op `Stigros-Afbeeldingen.exe`.
3. Open het gedownloade programma. Hiervoor is geen GitHub-account nodig.

Windows SmartScreen kan waarschuwen dat het programma van een onbekende uitgever komt. Dat gebeurt omdat het `.exe`-bestand niet digitaal is ondertekend. Controleer dat het bestand uit de GitHub Actions-build van deze repository komt. Kies daarna zo nodig **Meer informatie** en **Toch uitvoeren**.

## Controleren op updates

Bij het starten controleert het programma op de achtergrond of er een nieuwere openbare GitHub Release beschikbaar is. De bediening blijft tijdens deze korte controle gewoon werken. Zonder internetverbinding werkt het programma volledig door en verschijnt er geen foutmelding.

Als er een nieuwere versie is, vraagt het programma of de downloadpagina geopend mag worden. Na **Ja** wordt de pagina met de [nieuwste GitHub Release](https://github.com/Dvanno1/stigros-image-tool/releases/latest) in de standaardbrowser geopend. Het programma downloadt of installeert een update nooit automatisch en vervangt het actieve `.exe`-bestand niet.

## Zelf bouwen

De build gebruikt Python 3.11, PyInstaller en de vastgelegde versies uit `requirements.txt`. Start op GitHub de workflow handmatig via **Actions**, **Bouw Windows-programma**, **Run workflow**. De workflow draait op `windows-2022` en neemt de AVIF-ondersteuning en het Stigros-logo mee in één vensterprogramma zonder apart Python-venster.

Verhoog voor iedere nieuwe publicatie eerst `APP_VERSION` bovenaan in `Automatische_bottles.py`. Gebruik daarna bij de handmatige workflow dezelfde versie met een `v` ervoor als Release-tag. Bij `APP_VERSION = "1.2.1"` hoort bijvoorbeeld Release-tag `v1.2.1`.
