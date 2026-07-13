from __future__ import annotations

import os
import sys
import threading
import subprocess
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


WHITE = (255, 255, 255)
TOLERANCE = 12
PNG_COMPRESSION = 6

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
        "label": "Wijn / gedistilleerd — 500 × 500",
        "width": 500,
        "height": 500,
        "margin": 55,
        "suffix": "_500x500.png",
    },
    "beer": {
        "label": "Bier — 332 × 424",
        "width": 332,
        "height": 424,
        "margin": 35,
        "suffix": "_332x424.png",
    },
}

SUPPORTED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".tif",
    ".tiff",
    ".bmp",
    ".psd",
    ".avif",
}


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
    margin: int,
) -> Image.Image:
    """
    Plaatst de afbeelding gecentreerd op een witte achtergrond.

    De beeldverhouding blijft behouden, zodat het product
    niet wordt uitgerekt.
    """
    prepared = prepare_image(image)

    width, height = prepared.size

    if width <= 0 or height <= 0:
        raise ValueError(
            "De afbeelding is leeg na het uitsnijden."
        )

    available_width = canvas_width - (2 * margin)
    available_height = canvas_height - (2 * margin)

    if available_width <= 0 or available_height <= 0:
        raise ValueError(
            "De ingestelde marge is te groot."
        )

    scale = min(
        available_width / width,
        available_height / height,
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
            "Stigros afbeeldingen"
        )

        self.root.geometry(
            "780x650"
        )

        self.root.minsize(
            720,
            620,
        )

        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()

        self.selected_format = tk.StringVar(
            value="wine"
        )

        self.status_text = tk.StringVar(
            value="Kies eerst de twee mappen en druk daarna op START."
        )

        self.progress_value = tk.DoubleVar(
            value=0
        )

        self.is_processing = False

        self.build_interface()

    def build_interface(self) -> None:
        """
        Bouwt de gebruikersinterface.
        """
        outer = ttk.Frame(
            self.root,
            padding=24,
            style="App.TFrame",
        )

        outer.pack(
            fill="both",
            expand=True,
        )

        header = ttk.Frame(
            outer,
            padding=(22, 18),
            style="Header.TFrame",
        )

        header.pack(
            fill="x",
            pady=(0, 18),
        )

        title = ttk.Label(
            header,
            text="Stigros productafbeeldingen",
            style="HeaderTitle.TLabel",
        )

        title.pack(
            anchor="w"
        )

        subtitle = ttk.Label(
            header,
            text=(
                "Maak productfoto’s automatisch "
                "geschikt voor de website."
            ),
            style="HeaderSubtitle.TLabel",
        )

        subtitle.pack(
            anchor="w",
            pady=(5, 0),
        )

        format_frame = ttk.LabelFrame(
            outer,
            text="1. Kies het type product",
            padding=14,
            style="Card.TLabelframe",
        )

        format_frame.pack(
            fill="x"
        )

        for key, settings in FORMATS.items():
            ttk.Radiobutton(
                format_frame,
                text=settings["label"],
                variable=self.selected_format,
                value=key,
                style="Card.TRadiobutton",
            ).pack(
                anchor="w",
                pady=6,
            )

        folders_frame = ttk.LabelFrame(
            outer,
            text="2. Kies de mappen",
            padding=14,
            style="Card.TLabelframe",
        )

        folders_frame.pack(
            fill="x",
            pady=14,
        )

        folders_frame.columnconfigure(
            0,
            weight=1,
        )

        self.input_entry = ttk.Entry(
            folders_frame,
            textvariable=self.input_folder,
            state="readonly",
            style="Folder.TEntry",
        )

        self.input_entry.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 10),
            pady=7,
        )

        ttk.Button(
            folders_frame,
            text="Map met originele foto's kiezen",
            command=self.choose_input_folder,
            style="Secondary.TButton",
        ).grid(
            row=0,
            column=1,
            sticky="ew",
            pady=7,
        )

        self.output_entry = ttk.Entry(
            folders_frame,
            textvariable=self.output_folder,
            state="readonly",
            style="Folder.TEntry",
        )

        self.output_entry.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=(0, 10),
            pady=7,
        )

        ttk.Button(
            folders_frame,
            text="Map voor nieuwe foto's kiezen",
            command=self.choose_output_folder,
            style="Secondary.TButton",
        ).grid(
            row=1,
            column=1,
            sticky="ew",
            pady=7,
        )

        self.start_button = ttk.Button(
            outer,
            text="3. START — afbeeldingen verwerken",
            command=self.start_processing,
            style="Primary.TButton",
        )

        self.start_button.pack(
            fill="x",
            ipady=8,
        )

        self.progress_bar = ttk.Progressbar(
            outer,
            variable=self.progress_value,
            maximum=100,
            mode="determinate",
            style="Blue.Horizontal.TProgressbar",
        )

        self.progress_bar.pack(
            fill="x",
            pady=(20, 8),
        )

        self.status_label = ttk.Label(
            outer,
            textvariable=self.status_text,
            wraplength=680,
            style="Status.TLabel",
        )

        self.status_label.pack(
            anchor="w"
        )

        self.open_output_button = ttk.Button(
            outer,
            text="Map met nieuwe afbeeldingen openen",
            command=self.open_output_folder,
            state="disabled",
            style="Secondary.TButton",
        )

        self.open_output_button.pack(
            anchor="e",
            pady=(16, 0),
        )

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
            ),
            daemon=True,
        )

        thread.start()

    def process_images(
        self,
        input_path: Path,
        output_path: Path,
        format_key: str,
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
                            margin=int(
                                settings["margin"]
                            ),
                        )

                    filename = output_filename(
                        path,
                        str(settings["suffix"]),
                    )

                    destination = unique_destination(
                        output_path,
                        filename,
                    )

                    output_image.save(
                        destination,
                        format="PNG",
                        optimize=True,
                        compress_level=PNG_COMPRESSION,
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
        "App.TFrame",
        background=APP_BACKGROUND,
    )
    style.configure(
        "Header.TFrame",
        background=HEADER_BACKGROUND,
    )
    style.configure(
        "HeaderTitle.TLabel",
        background=HEADER_BACKGROUND,
        foreground="white",
        font=("Segoe UI", 21, "bold"),
    )
    style.configure(
        "HeaderSubtitle.TLabel",
        background=HEADER_BACKGROUND,
        foreground=HEADER_SUBTITLE,
        font=("Segoe UI", 11),
    )
    style.configure(
        "Card.TLabelframe",
        background=CARD_BACKGROUND,
        bordercolor=BORDER_COLOR,
        lightcolor=BORDER_COLOR,
        darkcolor=BORDER_COLOR,
        relief="solid",
    )
    style.configure(
        "Card.TLabelframe.Label",
        background=APP_BACKGROUND,
        foreground=HEADER_BACKGROUND,
        font=("Segoe UI", 12, "bold"),
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

    ImageToolApp(root)

    root.mainloop()


if __name__ == "__main__":
    main()
