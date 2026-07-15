from __future__ import annotations

import json
import os
import queue
import re
import sys
import threading
import subprocess
import urllib.request
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageChops, ImageOps

# AVIF-ondersteuning
# Installeren met:
# python3 -m pip install pillow-avif-plugin
try:
    import pillow_avif  # noqa: F401

    AVIF_AVAILABLE = True
except ImportError:
    AVIF_AVAILABLE = False


APP_VERSION = "1.0.0"
APP_EDITION = "Portret"
UPDATE_CHECK_ENABLED = False
GITHUB_RELEASE_API_URL = (
    "https://api.github.com/repos/"
    "Dvanno1/stigros-image-tool/releases/latest"
)
GITHUB_RELEASE_PAGE_URL = (
    "https://github.com/Dvanno1/"
    "stigros-image-tool/releases/latest"
)
UPDATE_TIMEOUT_SECONDS = 4

WHITE = (255, 255, 255)
TOLERANCE = 12
TARGET_FILL = 0.75
PNG_COMPRESSION = 6
JPG_QUALITY = 92

# Rustige kleuren met voldoende contrast voor een goed leesbare interface.
APP_BACKGROUND = "#EEF3F7"
CARD_BACKGROUND = "#FFFFFF"
HEADER_BACKGROUND = "#173B57"
HEADER_SUBTITLE = "#DCE9F2"
TEXT_COLOR = "#1F2933"
MUTED_TEXT = "#52606D"
PRIMARY_COLOR = "#26734D"
PRIMARY_HOVER = "#1E5D3E"
SECONDARY_COLOR = "#DCE7EF"
SECONDARY_HOVER = "#C9D9E5"
BORDER_COLOR = "#C7D5DF"
PROGRESS_COLOR = "#2F80A7"

# Formaten en marges
FORMATS = {
    "wine": {
        "label": "Wijn / gedistilleerd — 115 × 180",
        "width": 115,
        "height": 180,
        "size_suffix": "_115x180",
    },
    "beer": {
        "label": "Bier — 115 × 180",
        "width": 115,
        "height": 180,
        "size_suffix": "_115x180",
    },
}

OUTPUT_FORMATS = {
    "png": {
        "label": "PNG",
        "extension": ".png",
        "pillow_format": "PNG",
    },
    "jpg": {
        "label": "JPG",
        "extension": ".jpg",
        "pillow_format": "JPEG",
    },
}

SUPPORTED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".jfif",
    ".webp",
    ".gif",
    ".tif",
    ".tiff",
    ".bmp",
    ".psd",
    ".avif",
}

SEMANTIC_VERSION_PATTERN = re.compile(
    r"^[vV]?(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)

SemanticVersion = tuple[
    int,
    int,
    int,
    tuple[str, ...],
]


def parse_semantic_version(
    value: object,
) -> SemanticVersion | None:
    """
    Leest een SemVer-versie, met een optionele v voor Git-tags.
    Ongeldige of ontbrekende waarden leveren None op.
    """
    if not isinstance(value, str):
        return None

    match = SEMANTIC_VERSION_PATTERN.fullmatch(
        value.strip()
    )

    if match is None:
        return None

    prerelease_text = match.group(4)
    prerelease = (
        tuple(prerelease_text.split("."))
        if prerelease_text
        else ()
    )

    # Numerieke SemVer-identifiers mogen geen voorloopnul hebben.
    if any(
        identifier.isdigit()
        and len(identifier) > 1
        and identifier.startswith("0")
        for identifier in prerelease
    ):
        return None

    return (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
        prerelease,
    )


def compare_prerelease(
    left: tuple[str, ...],
    right: tuple[str, ...],
) -> int:
    """
    Vergelijkt twee geldige SemVer-prerelease-delen.
    """
    if left == right:
        return 0

    if not left:
        return 1

    if not right:
        return -1

    for left_part, right_part in zip(left, right):
        if left_part == right_part:
            continue

        left_is_number = left_part.isdigit()
        right_is_number = right_part.isdigit()

        if left_is_number and right_is_number:
            return (
                1
                if int(left_part) > int(right_part)
                else -1
            )

        if left_is_number:
            return -1

        if right_is_number:
            return 1

        return 1 if left_part > right_part else -1

    return 1 if len(left) > len(right) else -1


def is_newer_version(
    current_version: object,
    latest_version: object,
) -> bool:
    """
    Geeft alleen True terug als beide versies geldig zijn en de laatste
    versie volgens Semantic Versioning nieuwer is.
    """
    current = parse_semantic_version(current_version)
    latest = parse_semantic_version(latest_version)

    if current is None or latest is None:
        return False

    current_numbers = current[:3]
    latest_numbers = latest[:3]

    if current_numbers != latest_numbers:
        return latest_numbers > current_numbers

    return compare_prerelease(
        latest[3],
        current[3],
    ) > 0


def fetch_latest_release_version() -> str | None:
    """
    Haalt de nieuwste openbare GitHub Release-tag op.
    Netwerkfouten worden afgehandeld door de aanroepende achtergrondtaak.
    """
    request = urllib.request.Request(
        GITHUB_RELEASE_API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": (
                f"Stigros-Afbeeldingen/{APP_VERSION}"
            ),
        },
    )

    with urllib.request.urlopen(
        request,
        timeout=UPDATE_TIMEOUT_SECONDS,
    ) as response:
        data = json.load(response)

    if not isinstance(data, dict):
        return None

    tag_name = data.get("tag_name")

    return tag_name if isinstance(tag_name, str) else None


def bundled_resource_path(
    relative_path: str,
) -> Path:
    """
    Vindt een meegeleverd bestand in de bronmap of in een uitgepakte
    PyInstaller --onefile-bundel.
    """
    bundle_folder = Path(
        getattr(
            sys,
            "_MEIPASS",
            Path(__file__).resolve().parent,
        )
    )

    return bundle_folder / relative_path


def set_window_icon(root: tk.Tk) -> None:
    """
    Gebruikt het Stigros-logo als venstericoon als het beschikbaar is.
    """
    try:
        icon = tk.PhotoImage(
            file=str(
                bundled_resource_path(
                    "stigros_logo.png"
                )
            )
        )
        root.iconphoto(True, icon)

        # Bewaar een verwijzing zolang het venster bestaat.
        root.stigros_icon = icon  # type: ignore[attr-defined]
    except (OSError, tk.TclError):
        # Een ontbrekend icoon mag de hoofdfunctionaliteit nooit blokkeren.
        pass


def unique_destination(
    output_folder: Path,
    filename: str,
) -> Path:
    """
    Geeft een vrije bestandsnaam terug zonder bestaande uitvoer te
    overschrijven.
    """
    destination = output_folder / filename

    if not destination.exists():
        return destination

    stem = destination.stem
    suffix = destination.suffix
    duplicate_number = 2

    while True:
        candidate = output_folder / (
            f"{stem}_{duplicate_number}{suffix}"
        )

        if not candidate.exists():
            return candidate

        duplicate_number += 1


def output_suffix(
    product_format_key: str,
    output_format_key: str,
) -> str:
    """
    Maakt de uitvoersuffix uit het gekozen formaat en de afmetingen.
    """
    product_settings = FORMATS[product_format_key]
    output_settings = OUTPUT_FORMATS[output_format_key]

    return (
        str(product_settings["size_suffix"])
        + str(output_settings["extension"])
    )


def save_output_image(
    image: Image.Image,
    destination: Path,
    output_format_key: str,
) -> None:
    """
    Slaat een verwerkte afbeelding met de juiste formaatopties op.
    """
    if output_format_key == "png":
        image.save(
            destination,
            format="PNG",
            optimize=True,
            compress_level=PNG_COMPRESSION,
        )
        return

    if output_format_key == "jpg":
        image.convert("RGB").save(
            destination,
            format="JPEG",
            quality=JPG_QUALITY,
            optimize=True,
            progressive=True,
        )
        return

    raise ValueError(
        f"Onbekend uitvoerformaat: {output_format_key}"
    )


def trim_transparent(image: Image.Image) -> Image.Image:
    """
    Snijdt transparante randen van een afbeelding af.
    """
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    bbox = alpha.getbbox()

    return rgba.crop(bbox) if bbox else rgba


def trim_near_white(
    image: Image.Image,
    tolerance: int = TOLERANCE,
) -> Image.Image:
    """
    Snijdt witte of bijna witte randen van een afbeelding af.
    """
    rgb = image.convert("RGB")

    white_background = Image.new(
        "RGB",
        rgb.size,
        WHITE,
    )

    difference = ImageChops.difference(
        rgb,
        white_background,
    ).convert("L")

    mask = difference.point(
        lambda value: 255 if value > tolerance else 0
    )

    bbox = mask.getbbox()

    return rgb.crop(bbox) if bbox else rgb


def prepare_image(image: Image.Image) -> Image.Image:
    """
    Corrigeert de oriëntatie, verwijdert lege randen en zet
    transparante achtergronden om naar wit.
    """
    image = ImageOps.exif_transpose(image)

    has_alpha = (
        image.mode in ("RGBA", "LA")
        or "transparency" in image.info
    )

    if has_alpha:
        trimmed = trim_transparent(image)

        white_background = Image.new(
            "RGBA",
            trimmed.size,
            WHITE + (255,),
        )

        return Image.alpha_composite(
            white_background,
            trimmed,
        ).convert("RGB")

    return trim_near_white(image)


def fit_on_white_canvas(
    image: Image.Image,
    canvas_width: int,
    canvas_height: int,
    target_fill: float = TARGET_FILL,
) -> Image.Image:
    """
    Plaatst de afbeelding gecentreerd op een witte achtergrond.

    De langste begrenzende zijde van het product gebruikt het
    ingestelde deel van de bijbehorende canvaszijde. De
    beeldverhouding blijft behouden, zodat het product niet wordt
    uitgerekt.
    """
    prepared = prepare_image(image)

    width, height = prepared.size

    if width <= 0 or height <= 0:
        raise ValueError(
            "De afbeelding is leeg na het uitsnijden."
        )

    if not 0 < target_fill <= 1:
        raise ValueError(
            "De doelvulling moet groter dan 0 en maximaal 1 zijn."
        )

    usable_width = max(
        1,
        round(canvas_width * target_fill),
    )
    usable_height = max(
        1,
        round(canvas_height * target_fill),
    )

    scale = min(
        usable_width / width,
        usable_height / height,
    )

    new_width = max(
        1,
        round(width * scale),
    )

    new_height = max(
        1,
        round(height * scale),
    )

    resized = prepared.resize(
        (new_width, new_height),
        Image.Resampling.LANCZOS,
    )

    canvas = Image.new(
        "RGB",
        (canvas_width, canvas_height),
        WHITE,
    )

    x = (canvas_width - new_width) // 2
    y = (canvas_height - new_height) // 2

    canvas.paste(
        resized,
        (x, y),
    )

    return canvas


def output_filename(
    path: Path,
    suffix: str,
) -> str:
    """
    Maakt een nette naam voor het uitvoerbestand.
    """
    name = path.name
    lower_name = name.lower()

    compound_extensions = (
        ".png.webp",
        ".jpg.webp",
        ".jpeg.webp",
        ".png.avif",
        ".jpg.avif",
        ".jpeg.avif",
    )

    for extension in compound_extensions:
        if lower_name.endswith(extension):
            base_name = name[:-len(extension)]
            return base_name + suffix

    return path.stem + suffix


def is_supported_image(path: Path) -> bool:
    """
    Controleert of het bestand een ondersteund afbeeldingstype is.
    """
    return (
        path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def open_folder(path: Path) -> None:
    """
    Opent een map in Windows Verkenner, macOS Finder of Linux.
    """
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)

        elif sys.platform == "darwin":
            subprocess.run(
                ["open", str(path)],
                check=True,
            )

        else:
            subprocess.run(
                ["xdg-open", str(path)],
                check=True,
            )

    except Exception as error:
        messagebox.showerror(
            "Map openen mislukt",
            f"De map kon niet worden geopend:\n{error}",
        )


class ImageToolApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root

        self.root.title(
            "Stigros afbeeldingen — Portret"
        )

        self.root.geometry(
            "960x700"
        )

        self.root.minsize(
            900,
            680,
        )

        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()

        self.selected_format = tk.StringVar(
            value="wine"
        )

        self.selected_output_format = tk.StringVar(
            value="png"
        )

        self.status_text = tk.StringVar(
            value="Kies eerst de twee mappen en druk daarna op START."
        )

        self.progress_value = tk.DoubleVar(
            value=0
        )

        self.is_processing = False

        self.build_interface()

        if UPDATE_CHECK_ENABLED:
            self.start_update_check()

    def build_interface(self) -> None:
        """
        Bouwt de gebruikersinterface.
        """
        outer = tk.Frame(
            self.root,
            background=APP_BACKGROUND,
        )

        outer.pack(
            fill="both",
            expand=True,
        )

        # De vaste werkbreedte voorkomt dat velden en knoppen onnatuurlijk
        # uitrekken wanneer het venster wordt gemaximaliseerd.
        content = tk.Frame(
            outer,
            width=880,
            height=640,
            background=APP_BACKGROUND,
        )

        content.pack(
            anchor="n",
            pady=20,
        )
        content.pack_propagate(False)

        header = tk.Frame(
            content,
            background=HEADER_BACKGROUND,
            padx=24,
            pady=18,
        )
        header.pack(fill="x")
        header.columnconfigure(0, weight=1)

        title = tk.Label(
            header,
            text="Stigros productafbeeldingen — Portret",
            background=HEADER_BACKGROUND,
            foreground="white",
            font=("Segoe UI", 20, "bold"),
        )
        title.grid(
            row=0,
            column=0,
            sticky="w",
        )

        subtitle = tk.Label(
            header,
            text=(
                "Maak productfoto’s in drie eenvoudige stappen "
                "geschikt voor de website."
            ),
            background=HEADER_BACKGROUND,
            foreground=HEADER_SUBTITLE,
            font=("Segoe UI", 11),
        )
        subtitle.grid(
            row=1,
            column=0,
            sticky="w",
            pady=(5, 0),
        )

        logo = getattr(
            self.root,
            "stigros_icon",
            None,
        )

        if logo is not None:
            tk.Label(
                header,
                image=logo,
                background=HEADER_BACKGROUND,
                borderwidth=0,
            ).grid(
                row=0,
                column=1,
                rowspan=2,
                padx=(20, 0),
            )

        def create_step_card(
            number: str,
            title_text: str,
        ) -> tk.Frame:
            card = tk.Frame(
                content,
                background=CARD_BACKGROUND,
                highlightbackground=BORDER_COLOR,
                highlightthickness=1,
                padx=18,
                pady=14,
            )
            card.pack(
                fill="x",
                pady=(14, 0),
            )

            heading = tk.Frame(
                card,
                background=CARD_BACKGROUND,
            )
            heading.pack(fill="x")

            tk.Label(
                heading,
                text=number,
                width=2,
                height=1,
                background=HEADER_BACKGROUND,
                foreground="white",
                font=("Segoe UI", 11, "bold"),
            ).pack(side="left")

            tk.Label(
                heading,
                text=title_text,
                background=CARD_BACKGROUND,
                foreground=HEADER_BACKGROUND,
                font=("Segoe UI", 12, "bold"),
            ).pack(
                side="left",
                padx=(10, 0),
            )

            body = tk.Frame(
                card,
                background=CARD_BACKGROUND,
            )
            body.pack(
                fill="x",
                pady=(10, 0),
            )

            return body

        format_frame = create_step_card(
            "1",
            "Kies product en uitvoerformaat",
        )

        product_choices = tk.Frame(
            format_frame,
            background=CARD_BACKGROUND,
        )
        product_choices.pack(fill="x")

        for key, settings in FORMATS.items():
            ttk.Radiobutton(
                product_choices,
                text=settings["label"],
                variable=self.selected_format,
                value=key,
                style="Card.TRadiobutton",
            ).pack(
                side="left",
                padx=(0, 34),
            )

        ttk.Separator(
            format_frame,
            orient="horizontal",
        ).pack(
            fill="x",
            pady=10,
        )

        output_format_frame = tk.Frame(
            format_frame,
            background=CARD_BACKGROUND,
        )
        output_format_frame.pack(fill="x")

        tk.Label(
            output_format_frame,
            text="Uitvoerformaat:",
            background=CARD_BACKGROUND,
            foreground=MUTED_TEXT,
            font=("Segoe UI", 10, "bold"),
        ).pack(
            side="left",
            padx=(0, 16),
        )

        for key, settings in OUTPUT_FORMATS.items():
            ttk.Radiobutton(
                output_format_frame,
                text=settings["label"],
                variable=self.selected_output_format,
                value=key,
                style="Card.TRadiobutton",
            ).pack(
                side="left",
                padx=(0, 18),
            )

        folders_frame = create_step_card(
            "2",
            "Kies de mappen",
        )

        folders_frame.columnconfigure(0, weight=1)

        tk.Label(
            folders_frame,
            text="Originele productfoto’s",
            background=CARD_BACKGROUND,
            foreground=MUTED_TEXT,
            font=("Segoe UI", 10, "bold"),
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
        )

        self.input_entry = ttk.Entry(
            folders_frame,
            textvariable=self.input_folder,
            state="readonly",
            style="Folder.TEntry",
        )

        self.input_entry.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(0, 12),
            pady=(5, 10),
        )

        ttk.Button(
            folders_frame,
            text="Bladeren…",
            command=self.choose_input_folder,
            style="Secondary.TButton",
        ).grid(
            row=1,
            column=1,
            sticky="ew",
            pady=(5, 10),
        )

        tk.Label(
            folders_frame,
            text="Map voor de nieuwe afbeeldingen",
            background=CARD_BACKGROUND,
            foreground=MUTED_TEXT,
            font=("Segoe UI", 10, "bold"),
        ).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="w",
        )

        self.output_entry = ttk.Entry(
            folders_frame,
            textvariable=self.output_folder,
            state="readonly",
            style="Folder.TEntry",
        )

        self.output_entry.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=(0, 12),
            pady=(5, 0),
        )

        ttk.Button(
            folders_frame,
            text="Bladeren…",
            command=self.choose_output_folder,
            style="Secondary.TButton",
        ).grid(
            row=3,
            column=1,
            sticky="ew",
            pady=(5, 0),
        )

        self.start_button = ttk.Button(
            content,
            text="3   AFBEELDINGEN VERWERKEN",
            command=self.start_processing,
            style="Primary.TButton",
        )

        self.start_button.pack(
            fill="x",
            pady=(14, 0),
        )

        self.progress_bar = ttk.Progressbar(
            content,
            variable=self.progress_value,
            maximum=100,
            mode="determinate",
            style="Blue.Horizontal.TProgressbar",
        )

        self.progress_bar.pack(
            fill="x",
            pady=(16, 8),
        )

        status_row = tk.Frame(
            content,
            background=APP_BACKGROUND,
        )
        status_row.pack(fill="x")

        self.status_label = ttk.Label(
            status_row,
            textvariable=self.status_text,
            wraplength=570,
            style="Status.TLabel",
        )

        self.status_label.pack(
            side="left",
            anchor="w",
            fill="x",
            expand=True,
        )

        self.open_output_button = ttk.Button(
            status_row,
            text="Resultaten openen",
            command=self.open_output_folder,
            state="disabled",
            style="Secondary.TButton",
        )

        self.open_output_button.pack(
            side="right",
            anchor="e",
        )

        ttk.Label(
            content,
            text=(
                f"Stigros Afbeeldingen {APP_EDITION}"
                f"  •  versie {APP_VERSION}"
            ),
            style="Version.TLabel",
        ).pack(
            anchor="e",
            pady=(9, 0),
        )

    def start_update_check(self) -> None:
        """
        Start de updatecontrole zonder de interface te blokkeren.
        """
        self.update_result: queue.Queue[str | None] = (
            queue.Queue(maxsize=1)
        )

        thread = threading.Thread(
            target=self.check_for_update_in_background,
            name="stigros-update-check",
            daemon=True,
        )
        thread.start()

        self.root.after(
            200,
            self.poll_update_result,
        )

    def check_for_update_in_background(self) -> None:
        """
        Haalt de Release-tag op. Iedere fout betekent stil doorgaan.
        """
        latest_version = None

        try:
            latest_version = fetch_latest_release_version()
        except Exception:
            # Offline werken blijft altijd mogelijk. Netwerk-, timeout- en
            # API-fouten zijn daarom bewust niet zichtbaar voor de gebruiker.
            pass

        self.update_result.put(latest_version)

    def poll_update_result(self) -> None:
        """
        Leest het resultaat veilig vanuit de Tkinter-hoofdthread.
        """
        try:
            latest_version = self.update_result.get_nowait()
        except queue.Empty:
            self.root.after(
                200,
                self.poll_update_result,
            )
            return

        if is_newer_version(
            APP_VERSION,
            latest_version,
        ):
            self.show_update_dialog(
                str(latest_version)
            )

    def show_update_dialog(
        self,
        latest_version: str,
    ) -> None:
        """
        Vraagt of de gebruiker de openbare downloadpagina wil openen.
        """
        display_version = latest_version.removeprefix(
            "v"
        ).removeprefix("V")

        open_download_page = messagebox.askyesno(
            "Nieuwe versie beschikbaar",
            (
                "Er is een nieuwe versie van Stigros Afbeeldingen "
                "beschikbaar.\n\n"
                f"Huidige versie: {APP_VERSION}\n"
                f"Nieuwe versie: {display_version}\n\n"
                "Wilt u de downloadpagina openen?"
            ),
            parent=self.root,
        )

        if open_download_page:
            try:
                webbrowser.open(
                    GITHUB_RELEASE_PAGE_URL
                )
            except Exception:
                pass

    def choose_input_folder(self) -> None:
        """
        Laat de gebruiker de map met originele afbeeldingen kiezen.
        """
        folder = filedialog.askdirectory(
            title="Kies de map met originele afbeeldingen"
        )

        if folder:
            self.input_folder.set(folder)

    def choose_output_folder(self) -> None:
        """
        Laat de gebruiker de opslagmap kiezen.
        """
        folder = filedialog.askdirectory(
            title="Kies de map voor de bewerkte afbeeldingen"
        )

        if folder:
            self.output_folder.set(folder)

    def open_output_folder(self) -> None:
        """
        Opent de gekozen outputmap.
        """
        folder = Path(
            self.output_folder.get()
        )

        if folder.exists():
            open_folder(folder)

    def start_processing(self) -> None:
        """
        Controleert de keuzes en start de verwerking.
        """
        if self.is_processing:
            return

        input_text = self.input_folder.get().strip()
        output_text = self.output_folder.get().strip()

        if not input_text or not output_text:
            messagebox.showwarning(
                "Mappen ontbreken",
                (
                    "Kies eerst de map met de originele foto's "
                    "en daarna de map voor de nieuwe foto's."
                ),
            )
            return

        input_path = Path(input_text)
        output_path = Path(output_text)

        if not input_path.exists() or not input_path.is_dir():
            messagebox.showerror(
                "Map niet gevonden",
                "De gekozen map met originele foto's bestaat niet.",
            )
            return

        if input_path.resolve() == output_path.resolve():
            messagebox.showwarning(
                "Dezelfde map gekozen",
                (
                    "Kies een andere outputmap, zodat originele "
                    "foto's niet worden overschreven."
                ),
            )
            return

        self.is_processing = True

        self.start_button.configure(
            state="disabled"
        )

        self.open_output_button.configure(
            state="disabled"
        )

        self.progress_value.set(0)

        self.status_text.set(
            "Afbeeldingen zoeken…"
        )

        thread = threading.Thread(
            target=self.process_images,
            args=(
                input_path,
                output_path,
                self.selected_format.get(),
                self.selected_output_format.get(),
            ),
            daemon=True,
        )

        thread.start()

    def process_images(
        self,
        input_path: Path,
        output_path: Path,
        format_key: str,
        output_format_key: str,
    ) -> None:
        """
        Verwerkt alle afbeeldingen in de inputmap.
        """
        try:
            settings = FORMATS[format_key]

            output_path.mkdir(
                parents=True,
                exist_ok=True,
            )

            output_resolved = output_path.resolve()

            files = []

            for path in input_path.rglob("*"):
                try:
                    if output_resolved in path.resolve().parents:
                        continue
                except OSError:
                    pass

                if is_supported_image(path):
                    files.append(path)

            files.sort(
                key=lambda item: str(item).lower()
            )

            if not files:
                self.root.after(
                    0,
                    lambda: self.finish_with_error(
                        "Geen ondersteunde afbeeldingen "
                        "gevonden in de inputmap."
                    ),
                )
                return

            contains_avif = any(
                path.suffix.lower() == ".avif"
                for path in files
            )

            if contains_avif and not AVIF_AVAILABLE:
                self.root.after(
                    0,
                    lambda: self.finish_with_error(
                        "Er zijn AVIF-bestanden gevonden, maar "
                        "AVIF-ondersteuning ontbreekt.\n\n"
                        "Installeer eerst:\n"
                        "python3 -m pip install pillow-avif-plugin"
                    ),
                )
                return

            ok_count = 0
            failed_files = []
            total = len(files)

            for index, path in enumerate(
                files,
                start=1,
            ):
                try:
                    with Image.open(path) as image:
                        output_image = fit_on_white_canvas(
                            image=image,
                            canvas_width=int(
                                settings["width"]
                            ),
                            canvas_height=int(
                                settings["height"]
                            ),
                        )

                    filename = output_filename(
                        path,
                        output_suffix(
                            format_key,
                            output_format_key,
                        ),
                    )

                    destination = unique_destination(
                        output_path,
                        filename,
                    )

                    save_output_image(
                        output_image,
                        destination,
                        output_format_key,
                    )

                    ok_count += 1

                except Exception as error:
                    failed_files.append(
                        f"{path.name}: {error}"
                    )

                percentage = (
                    index / total
                ) * 100

                status = (
                    f"{index} van {total} verwerkt…"
                )

                self.root.after(
                    0,
                    lambda p=percentage, s=status:
                    self.update_progress(p, s),
                )

            self.root.after(
                0,
                lambda: self.finish_successfully(
                    ok_count,
                    len(failed_files),
                    failed_files,
                ),
            )

        except Exception as error:
            self.root.after(
                0,
                lambda: self.finish_with_error(
                    f"Onverwachte fout:\n{error}"
                ),
            )

    def update_progress(
        self,
        percentage: float,
        status: str,
    ) -> None:
        """
        Werkt de voortgangsbalk en tekst bij.
        """
        self.progress_value.set(
            percentage
        )

        self.status_text.set(
            status
        )

    def finish_successfully(
        self,
        ok_count: int,
        fail_count: int,
        failed_files: list[str],
    ) -> None:
        """
        Toont het resultaat na de verwerking.
        """
        self.is_processing = False

        self.start_button.configure(
            state="normal"
        )

        self.open_output_button.configure(
            state="normal"
        )

        self.progress_value.set(100)

        if fail_count == 0:
            text = (
                f"KLAAR — {ok_count} afbeeldingen verwerkt. "
                "U kunt nu de map met nieuwe afbeeldingen openen."
            )

            self.status_text.set(text)

            messagebox.showinfo(
                "Klaar",
                text,
            )

        else:
            text = (
                f"Klaar — {ok_count} gelukt, "
                f"{fail_count} mislukt."
            )

            self.status_text.set(text)

            details = "\n".join(
                failed_files[:10]
            )

            if len(failed_files) > 10:
                details += (
                    f"\n…en nog "
                    f"{len(failed_files) - 10} fouten."
                )

            messagebox.showwarning(
                "Verwerking afgerond",
                (
                    f"{text}\n\n"
                    f"Mislukte bestanden:\n{details}"
                ),
            )

    def finish_with_error(
        self,
        message: str,
    ) -> None:
        """
        Herstelt de interface en toont een foutmelding.
        """
        self.is_processing = False

        self.start_button.configure(
            state="normal"
        )

        self.open_output_button.configure(
            state="disabled"
        )

        self.progress_value.set(0)

        self.status_text.set(
            message
        )

        messagebox.showerror(
            "Fout",
            message,
        )


def main() -> None:
    root = tk.Tk()
    set_window_icon(root)
    root.configure(
        background=APP_BACKGROUND
    )

    try:
        style = ttk.Style(root)

        # Het clam-thema laat dezelfde rustige kleuren zien op Windows en
        # macOS en houdt de bediening herkenbaar als standaardknoppen.
        if "clam" in style.theme_names():
            style.theme_use("clam")

    except tk.TclError:
        pass

    # Iets grotere tekst en ruimere knoppen maken de bestaande interface
    # prettiger leesbaar en bedienbaar, ook op een Windows-laptop.
    root.option_add("*Font", ("Segoe UI", 11))
    style.configure(
        ".",
        font=("Segoe UI", 11),
        foreground=TEXT_COLOR,
    )
    style.configure(
        "Card.TRadiobutton",
        background=CARD_BACKGROUND,
        foreground=TEXT_COLOR,
        padding=(4, 4),
    )
    style.map(
        "Card.TRadiobutton",
        background=[("active", CARD_BACKGROUND)],
    )
    style.configure("TButton", padding=(10, 8))
    style.configure(
        "Primary.TButton",
        background=PRIMARY_COLOR,
        foreground="white",
        bordercolor=PRIMARY_COLOR,
        font=("Segoe UI", 12, "bold"),
        padding=(12, 11),
    )
    style.map(
        "Primary.TButton",
        background=[
            ("disabled", "#A8B8AE"),
            ("pressed", PRIMARY_HOVER),
            ("active", PRIMARY_HOVER),
        ],
        foreground=[("disabled", "#F4F6F5")],
    )
    style.configure(
        "Secondary.TButton",
        background=SECONDARY_COLOR,
        foreground=HEADER_BACKGROUND,
        bordercolor=BORDER_COLOR,
        font=("Segoe UI", 10, "bold"),
    )
    style.map(
        "Secondary.TButton",
        background=[
            ("disabled", "#E5EAED"),
            ("pressed", SECONDARY_HOVER),
            ("active", SECONDARY_HOVER),
        ],
        foreground=[("disabled", "#89959E")],
    )
    style.configure(
        "Folder.TEntry",
        fieldbackground=CARD_BACKGROUND,
        foreground=MUTED_TEXT,
        bordercolor=BORDER_COLOR,
        padding=8,
    )
    style.configure(
        "Blue.Horizontal.TProgressbar",
        background=PROGRESS_COLOR,
        troughcolor="#D7E1E8",
        bordercolor="#D7E1E8",
        lightcolor=PROGRESS_COLOR,
        darkcolor=PROGRESS_COLOR,
        thickness=18,
    )
    style.configure(
        "Status.TLabel",
        background=APP_BACKGROUND,
        foreground=MUTED_TEXT,
        font=("Segoe UI", 11, "bold"),
    )
    style.configure(
        "Version.TLabel",
        background=APP_BACKGROUND,
        foreground="#75838E",
        font=("Segoe UI", 9),
    )

    ImageToolApp(root)

    root.mainloop()


if __name__ == "__main__":
    main()
