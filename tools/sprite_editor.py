import json
import re
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, simpledialog


ROOT = Path(__file__).resolve().parents[1]
SPRITE_DIR = ROOT / "assets" / "sprites"
TRANSPARENT = 0xF81F

SPRITE_TYPES = {
    "tile": {"size": "8x8", "folder": "tiles", "default": "grass"},
    "item": {"size": "8x8", "folder": "items", "default": "coin"},
    "player_layer": {"size": "8x16", "folder": "player", "default": "hair_spiky"},
    "player_hires": {"size": "16x32", "folder": "player_hires", "default": "player_default"},
    "enemy": {"size": "8x16", "folder": "enemies", "default": "slime"},
    "free": {"size": "16x16", "folder": "", "default": "sprite"},
}

SPRITE_TYPE_LABELS = {
    "tile": "Блок 8x8",
    "item": "Предмет 8x8",
    "player_layer": "Слой игрока 8x16",
    "player_hires": "Игрок 16x32",
    "enemy": "Враг 8x16",
    "free": "Свободный",
}
SPRITE_TYPE_BY_LABEL = {label: key for key, label in SPRITE_TYPE_LABELS.items()}

PLAYER_LAYERS = ("skin", "hair", "eyes", "shirt", "pants", "boots", "custom")
PLAYER_LAYER_ORDER = ("skin", "hair", "eyes", "shirt", "pants", "boots")
PLAYER_LAYER_LABELS = {
    "skin": "Кожа",
    "hair": "Прическа",
    "eyes": "Глаза",
    "shirt": "Одежда",
    "pants": "Штаны",
    "boots": "Ботинки",
    "custom": "Другое",
}
PLAYER_LAYER_BY_LABEL = {label: key for key, label in PLAYER_LAYER_LABELS.items()}

PALETTE = [
    ("black", 0x0000),
    ("white", 0xFFFF),
    ("red", 0xF800),
    ("green", 0x07E0),
    ("blue", 0x001F),
    ("yellow", 0xFFE0),
    ("cyan", 0x07FF),
    ("magenta", 0xF81F),
    ("skin", 0xFDB8),
    ("hair", 0x4208),
    ("shirt", 0x3D9F),
    ("pants", 0x18E3),
    ("grass", 0x45E6),
    ("dirt", 0x8A22),
    ("stone", 0x7BEF),
]


def rgb565_to_hex(color):
    r = ((color >> 11) & 0x1F) * 255 // 31
    g = ((color >> 5) & 0x3F) * 255 // 63
    b = (color & 0x1F) * 255 // 31
    return "#%02x%02x%02x" % (r, g, b)


def rgb888_to_rgb565(r, g, b):
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


def sanitize_name(name):
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9_]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "sprite"


def color_distance(a, b):
    ar = ((a >> 11) & 0x1F) * 255 // 31
    ag = ((a >> 5) & 0x3F) * 255 // 63
    ab = (a & 0x1F) * 255 // 31
    br = ((b >> 11) & 0x1F) * 255 // 31
    bg = ((b >> 5) & 0x3F) * 255 // 63
    bb = (b & 0x1F) * 255 // 31
    return abs(ar - br) + abs(ag - bg) + abs(ab - bb)


class SpriteEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Редактор спрайтов")
        self.width = 16
        self.height = 16
        self.cell = 28
        self.max_canvas_height = min(620, max(320, self.root.winfo_screenheight() - 260))
        self.name_var = tk.StringVar(value="player_idle")
        self.size_var = tk.StringVar(value="16x16")
        self.type_var = tk.StringVar(value=SPRITE_TYPE_LABELS["free"])
        self.layer_var = tk.StringVar(value=PLAYER_LAYER_LABELS["custom"])
        self.color = PALETTE[1][1]
        self.custom_colors = []
        self.image_colors = []
        self.pixels = [[TRANSPARENT for _ in range(self.width)] for _ in range(self.height)]
        self.dragging = False
        self.eraser = False

        self._build_ui()
        self._draw_grid()
        self._draw_preview()
        self._refresh_sprite_list()

    def _build_ui(self):
        top = tk.Frame(self.root)
        top.pack(fill=tk.X, padx=12, pady=(10, 8))

        fields = tk.Frame(top)
        fields.pack(side=tk.LEFT, fill=tk.X, expand=True)
        actions = tk.Frame(top)
        actions.pack(side=tk.RIGHT)

        tk.Label(fields, text="Имя").grid(row=0, column=0, sticky=tk.W)
        tk.Entry(fields, textvariable=self.name_var, width=20).grid(row=0, column=1, sticky=tk.W, padx=(6, 18))

        tk.Label(fields, text="Тип").grid(row=0, column=2, sticky=tk.W)
        tk.OptionMenu(fields, self.type_var, *SPRITE_TYPE_LABELS.values(), command=self._change_type).grid(row=0, column=3, sticky=tk.W, padx=(6, 18))

        tk.Label(fields, text="Слой").grid(row=0, column=4, sticky=tk.W)
        self.layer_menu = tk.OptionMenu(fields, self.layer_var, *PLAYER_LAYER_LABELS.values())
        self.layer_menu.grid(row=0, column=5, sticky=tk.W, padx=(6, 18))

        tk.Label(fields, text="Размер").grid(row=0, column=6, sticky=tk.W)
        tk.OptionMenu(fields, self.size_var, "8x8", "8x12", "12x16", "16x16", "16x24", "16x32", command=self._change_size).grid(row=0, column=7, sticky=tk.W, padx=(6, 0))

        tk.Button(actions, text="Новый", command=self._new_sprite, width=10).grid(row=0, column=0, padx=3)
        tk.Button(actions, text="Сохранить", command=self._save_sprite, width=12).grid(row=0, column=1, padx=3)
        tk.Button(actions, text="Открыть", command=self._load_selected, width=10).grid(row=0, column=2, padx=3)
        tk.Button(actions, text="Очистить", command=self._clear_sprite, width=10).grid(row=0, column=3, padx=3)

        body = tk.Frame(self.root)
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 12))
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=0)
        body.columnconfigure(2, weight=1)
        body.rowconfigure(0, weight=1)

        left = tk.LabelFrame(body, text="Холст", padx=8, pady=8)
        left.grid(row=0, column=0, sticky=tk.NW)

        canvas_box = tk.Frame(left)
        canvas_box.pack()
        self.canvas = tk.Canvas(
            canvas_box,
            bg="#eeeeee",
            highlightthickness=1,
            highlightbackground="#999999",
        )
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW)
        self.canvas_scroll = tk.Scrollbar(canvas_box, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas_scroll.grid(row=0, column=1, sticky=tk.NS)
        self.canvas.config(yscrollcommand=self.canvas_scroll.set)
        self._resize_canvas_view()
        self.canvas.bind("<ButtonPress-1>", self._paint_start)
        self.canvas.bind("<B1-Motion>", self._paint_drag)
        self.canvas.bind("<ButtonRelease-1>", self._paint_end)
        self.canvas.bind("<ButtonPress-3>", self._erase_start)
        self.canvas.bind("<B3-Motion>", self._erase_drag)
        self.canvas.bind("<ButtonRelease-3>", self._paint_end)
        self.canvas.bind("<MouseWheel>", self._scroll_canvas)
        self.canvas.bind("<Button-4>", self._scroll_canvas)
        self.canvas.bind("<Button-5>", self._scroll_canvas)

        tools = tk.Frame(body)
        tools.grid(row=0, column=1, sticky=tk.NW, padx=(14, 14))

        palette_box = tk.LabelFrame(tools, text="Палитры", padx=8, pady=8)
        palette_box.pack(fill=tk.X, anchor=tk.N)

        tk.Label(palette_box, text="Базовая").pack(anchor=tk.W)
        self.selected_label = tk.StringVar(value="Выбран: black 0x0000")
        self.palette_frame = tk.Frame(palette_box)
        self.palette_frame.pack(anchor=tk.W, pady=(4, 4))
        self.image_palette_container = tk.Frame(palette_box)
        self.image_palette_container.pack(anchor=tk.W, pady=(8, 4))
        self.image_palette_label = tk.Label(self.image_palette_container, text="Палитра из картинки: не загружена")
        self.image_palette_label.pack(anchor=tk.W)
        self.image_palette_frame = tk.Frame(self.image_palette_container)
        self.image_palette_frame.pack(anchor=tk.W, pady=(4, 0))
        self._draw_palette()

        palette_actions = tk.Frame(palette_box)
        palette_actions.pack(fill=tk.X, pady=(8, 0))
        tk.Button(palette_actions, text="Прозрачность", command=lambda: self._select_color(TRANSPARENT, "transparent"), width=14).grid(row=0, column=0, padx=(0, 4), pady=2, sticky=tk.W)
        tk.Button(palette_actions, text="Выбрать цвет...", command=self._choose_custom_color, width=14).grid(row=0, column=1, padx=(0, 4), pady=2, sticky=tk.W)
        tk.Button(palette_actions, text="Палитра из PNG...", command=self._import_palette_from_image, width=18).grid(row=1, column=0, columnspan=2, pady=2, sticky=tk.W)
        self.selected_swatch = tk.Label(palette_box, textvariable=self.selected_label, anchor=tk.W)
        self.selected_swatch.pack(fill=tk.X, pady=(8, 0))

        help_box = tk.LabelFrame(tools, text="Подсказка", padx=8, pady=8)
        help_box.pack(fill=tk.X, pady=(12, 0))
        help_text = "Редактируется один спрайт.\nЛевая кнопка: рисовать\nПравая кнопка: стирать\nЦвета хранятся как RGB565"
        tk.Label(help_box, text=help_text, justify=tk.LEFT).pack(anchor=tk.W)

        right = tk.Frame(body)
        right.grid(row=0, column=2, sticky=tk.NSEW)
        right.columnconfigure(0, weight=0)
        right.columnconfigure(1, weight=1)
        right.rowconfigure(1, weight=1)

        preview_box = tk.LabelFrame(right, text="Предпросмотр", padx=8, pady=8)
        preview_box.grid(row=0, column=0, sticky=tk.NW)
        self.preview = tk.Canvas(preview_box, width=128, height=128, bg="#dddddd", highlightthickness=1, highlightbackground="#999999")
        self.preview.pack(anchor=tk.W)

        player_box = tk.LabelFrame(right, text="Игрок", padx=8, pady=8)
        player_box.grid(row=0, column=1, sticky=tk.NW, padx=(12, 0))
        self.player_preview = tk.Canvas(player_box, width=64, height=128, bg="#dddddd", highlightthickness=1, highlightbackground="#999999")
        self.player_preview.pack(anchor=tk.W)
        tk.Button(player_box, text="Обновить", command=self._draw_player_preview).pack(anchor=tk.W, pady=(8, 0))

        list_box = tk.LabelFrame(right, text="Сохраненные спрайты", padx=8, pady=8)
        list_box.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW, pady=(12, 0))
        list_box.columnconfigure(0, weight=1)
        list_box.rowconfigure(0, weight=1)
        self.listbox = tk.Listbox(list_box, height=12, width=44)
        self.listbox.grid(row=0, column=0, sticky=tk.NSEW)
        scrollbar = tk.Scrollbar(list_box, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=tk.NS)
        self.listbox.config(yscrollcommand=scrollbar.set)
        self.listbox.bind("<Double-Button-1>", lambda _event: self._load_selected())

    def _draw_palette(self):
        for child in self.palette_frame.winfo_children():
            child.destroy()
        for child in self.image_palette_frame.winfo_children():
            child.destroy()

        self._draw_palette_group(self.palette_frame, PALETTE + self.custom_colors)

        if self.image_colors:
            self.image_palette_label.config(text="Палитра из картинки")
            self._draw_palette_group(self.image_palette_frame, self.image_colors)
        else:
            self.image_palette_label.config(text="Палитра из картинки: не загружена")

    def _draw_palette_group(self, parent, colors):
        for idx, (label, color) in enumerate(colors):
            swatch = tk.Canvas(
                parent,
                width=24,
                height=24,
                bg=rgb565_to_hex(color),
                highlightthickness=1,
                highlightbackground="#444444",
            )
            swatch.create_rectangle(0, 0, 24, 24, fill=rgb565_to_hex(color), outline="")
            swatch.grid(row=idx // 4, column=idx % 4, padx=3, pady=3)
            swatch.bind("<Button-1>", lambda _event, c=color, label=label: self._select_color(c, label))
            swatch.bind("<Enter>", lambda _event, c=color, label=label: self._show_color(label, c))

    def _resize_canvas_view(self):
        content_width = self.width * self.cell
        content_height = self.height * self.cell
        view_height = min(content_height, self.max_canvas_height)
        self.canvas.config(
            width=content_width,
            height=view_height,
            scrollregion=(0, 0, content_width + 1, content_height + 1),
        )

    def _scroll_canvas(self, event):
        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            delta = -1 if event.delta > 0 else 1
        self.canvas.yview_scroll(delta, "units")

    def _show_color(self, label, color):
        self.selected_label.set(f"Выбран: {label} 0x{color:04X}")

    def _select_color(self, color, label="custom"):
        self.color = color
        self._show_color(label, color)

    def _choose_custom_color(self):
        chosen = colorchooser.askcolor(title="Выбор цвета спрайта")
        if not chosen or not chosen[0]:
            return
        r, g, b = [int(v) for v in chosen[0]]
        color = rgb888_to_rgb565(r, g, b)
        label = f"custom_{len(self.custom_colors) + 1}"
        self.custom_colors.append((label, color))
        self._select_color(color, label)
        self._draw_palette()

    def _import_palette_from_image(self):
        path = filedialog.askopenfilename(
            title="Выбери PNG для палитры",
            filetypes=(("PNG images", "*.png"), ("All files", "*.*")),
        )
        if not path:
            return

        try:
            colors = self._extract_palette(Path(path), max_colors=24)
        except tk.TclError as exc:
            messagebox.showerror("Ошибка", f"Не удалось открыть картинку:\n{exc}")
            return

        if not colors:
            messagebox.showinfo("Палитра", "Не удалось найти цвета в картинке.")
            return

        self.image_colors = []
        existing = set()
        added = 0
        for color in colors:
            if color in existing or color == TRANSPARENT:
                continue
            label = f"img_{len(self.image_colors) + 1}"
            self.image_colors.append((label, color))
            existing.add(color)
            added += 1

        if added:
            self._draw_palette()
            self._select_color(self.image_colors[0][1], "из картинки")
        messagebox.showinfo("Палитра", f"Добавлено цветов: {added}")

    def _extract_palette(self, path, max_colors):
        image = tk.PhotoImage(file=str(path))
        width = image.width()
        height = image.height()
        step = max(1, max(width, height) // 160)
        counts = {}
        transparent_rgb = image.get(0, 0)

        for y in range(0, height, step):
            for x in range(0, width, step):
                try:
                    if image.transparency_get(x, y):
                        continue
                except tk.TclError:
                    pass
                rgb = image.get(x, y)
                if rgb == transparent_rgb:
                    continue
                color = rgb888_to_rgb565(*rgb)
                if color == TRANSPARENT:
                    continue
                counts[color] = counts.get(color, 0) + 1

        sorted_colors = sorted(counts, key=counts.get, reverse=True)
        result = []
        for color in sorted_colors:
            if all(color_distance(color, existing) > 18 for existing in result):
                result.append(color)
            if len(result) >= max_colors:
                break
        return result

    def _new_sprite(self):
        self.name_var.set(SPRITE_TYPES[self._selected_type()]["default"])
        self._clear_sprite()

    def _change_type(self, sprite_type_label):
        sprite_type = SPRITE_TYPE_BY_LABEL.get(sprite_type_label, sprite_type_label)
        spec = SPRITE_TYPES[sprite_type]
        self.size_var.set(spec["size"])
        self.name_var.set(spec["default"])
        if sprite_type != "player_layer":
            self.layer_var.set(PLAYER_LAYER_LABELS["custom"])
        elif self._selected_layer() == "custom":
            self.layer_var.set(PLAYER_LAYER_LABELS["hair"])
        self._change_size()
        self._refresh_sprite_list()

    def _clear_sprite(self):
        self.pixels = [[TRANSPARENT for _ in range(self.width)] for _ in range(self.height)]
        self._draw_grid()
        self._draw_preview()
        self._draw_player_preview()

    def _change_size(self, _value=None):
        old = self.pixels
        old_w = self.width
        old_h = self.height
        w, h = self.size_var.get().split("x")
        self.width = int(w)
        self.height = int(h)
        self.pixels = [[TRANSPARENT for _ in range(self.width)] for _ in range(self.height)]
        for y in range(min(old_h, self.height)):
            for x in range(min(old_w, self.width)):
                self.pixels[y][x] = old[y][x]
        self._resize_canvas_view()
        self._draw_grid()
        self._draw_preview()

    def _paint_start(self, event):
        self.dragging = True
        self.eraser = False
        self._paint_at(event.x, event.y)

    def _erase_start(self, event):
        self.dragging = True
        self.eraser = True
        self._paint_at(event.x, event.y)

    def _paint_drag(self, event):
        if self.dragging:
            self.eraser = False
            self._paint_at(event.x, event.y)

    def _erase_drag(self, event):
        if self.dragging:
            self.eraser = True
            self._paint_at(event.x, event.y)

    def _paint_end(self, _event):
        self.dragging = False

    def _paint_at(self, px, py):
        x = int(self.canvas.canvasx(px)) // self.cell
        y = int(self.canvas.canvasy(py)) // self.cell
        if 0 <= x < self.width and 0 <= y < self.height:
            self.pixels[y][x] = TRANSPARENT if self.eraser else self.color
            self._draw_cell(x, y)
            self._draw_preview()
            self._draw_player_preview()

    def _draw_grid(self):
        self.canvas.delete("all")
        for y in range(self.height):
            for x in range(self.width):
                self._draw_cell(x, y)

    def _draw_cell(self, x, y):
        color = self.pixels[y][x]
        x0 = x * self.cell
        y0 = y * self.cell
        x1 = x0 + self.cell
        y1 = y0 + self.cell
        if color == TRANSPARENT:
            fill = "#f4f4f4" if (x + y) % 2 == 0 else "#d6d6d6"
        else:
            fill = rgb565_to_hex(color)
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="#777777")

    def _draw_preview(self):
        self.preview.delete("all")
        scale = max(1, min(96 // self.width, 96 // self.height))
        ox = (96 - self.width * scale) // 2
        oy = (96 - self.height * scale) // 2
        for y in range(self.height):
            for x in range(self.width):
                color = self.pixels[y][x]
                if color == TRANSPARENT:
                    continue
                self.preview.create_rectangle(
                    ox + x * scale,
                    oy + y * scale,
                    ox + (x + 1) * scale,
                    oy + (y + 1) * scale,
                    fill=rgb565_to_hex(color),
                    outline="",
                )

    def _save_sprite(self):
        folder = self._current_folder()
        folder.mkdir(parents=True, exist_ok=True)
        name = sanitize_name(self.name_var.get())
        self.name_var.set(name)
        json_path = folder / f"{name}.json"
        bin_path = folder / f"{name}.bin"

        data = {
            "name": name,
            "type": self._selected_type(),
            "layer": self._selected_layer() if self._selected_type() == "player_layer" else "",
            "width": self.width,
            "height": self.height,
            "transparent": TRANSPARENT,
            "format": "RGB565_BE",
            "pixels": self.pixels,
        }
        json_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        raw = bytearray()
        for row in self.pixels:
            for color in row:
                raw.append((color >> 8) & 0xFF)
                raw.append(color & 0xFF)
        bin_path.write_bytes(raw)
        self._write_manifest()
        self._refresh_sprite_list()
        self._draw_player_preview()
        rel_json = json_path.relative_to(SPRITE_DIR)
        rel_bin = bin_path.relative_to(SPRITE_DIR)
        messagebox.showinfo("Сохранено", f"Сохранены {rel_json} и {rel_bin}")

    def _load_selected(self):
        selection = self.listbox.curselection()
        if not selection:
            name = simpledialog.askstring("Открыть спрайт", "Имя спрайта:")
            if not name:
                return
            path = self._current_folder() / f"{sanitize_name(name)}.json"
        else:
            path = SPRITE_DIR / self.listbox.get(selection[0])

        if not path.exists():
            messagebox.showerror("Не найдено", f"Не удалось найти {path.name}")
            return

        data = json.loads(path.read_text(encoding="utf-8"))
        self.name_var.set(sanitize_name(data["name"]))
        self.type_var.set(SPRITE_TYPE_LABELS.get(data.get("type", "free"), data.get("type", "free")))
        layer = data.get("layer", "custom") or "custom"
        self.layer_var.set(PLAYER_LAYER_LABELS.get(layer, layer))
        self.width = int(data["width"])
        self.height = int(data["height"])
        self.size_var.set(f"{self.width}x{self.height}")
        self.pixels = data["pixels"]
        self._resize_canvas_view()
        self._draw_grid()
        self._draw_preview()
        self._draw_player_preview()

    def _refresh_sprite_list(self):
        SPRITE_DIR.mkdir(parents=True, exist_ok=True)
        self.listbox.delete(0, tk.END)
        for path in self._sprite_json_files():
            self.listbox.insert(tk.END, str(path.relative_to(SPRITE_DIR)))

    def _write_manifest(self):
        sprites = []
        for path in self._sprite_json_files():
            data = json.loads(path.read_text(encoding="utf-8"))
            bin_path = path.with_suffix(".bin")
            sprites.append({
                "name": data["name"],
                "type": data.get("type", "free"),
                "layer": data.get("layer", ""),
                "width": data["width"],
                "height": data["height"],
                "file": str(bin_path.relative_to(SPRITE_DIR)),
                "transparent": data.get("transparent", TRANSPARENT),
                "format": data.get("format", "RGB565_BE"),
            })
        (SPRITE_DIR / "manifest.json").write_text(json.dumps({"sprites": sprites}, indent=2), encoding="utf-8")

    def _draw_player_preview(self):
        self.player_preview.delete("all")
        pixels = [[TRANSPARENT for _ in range(8)] for _ in range(16)]

        for layer in PLAYER_LAYER_ORDER:
            for path in sorted((SPRITE_DIR / "player").glob("*.json")):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except ValueError:
                    continue
                if data.get("type") != "player_layer" or data.get("layer") != layer:
                    continue
                if int(data.get("width", 0)) != 8 or int(data.get("height", 0)) != 16:
                    continue
                for y, row in enumerate(data["pixels"]):
                    for x, color in enumerate(row):
                        if color != TRANSPARENT:
                            pixels[y][x] = color
                break

        scale = 8
        for y in range(16):
            for x in range(8):
                color = pixels[y][x]
                if color == TRANSPARENT:
                    continue
                self.player_preview.create_rectangle(
                    x * scale,
                    y * scale,
                    (x + 1) * scale,
                    (y + 1) * scale,
                    fill=rgb565_to_hex(color),
                    outline="",
                )

    def _sprite_json_files(self):
        result = []
        for path in sorted(SPRITE_DIR.rglob("*.json")):
            if path.name == "manifest.json":
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except ValueError:
                continue
            if "pixels" in data and "width" in data and "height" in data:
                result.append(path)
        return result

    def _current_folder(self):
        folder = SPRITE_TYPES[self._selected_type()]["folder"]
        if folder:
            return SPRITE_DIR / folder
        return SPRITE_DIR

    def _selected_type(self):
        return SPRITE_TYPE_BY_LABEL.get(self.type_var.get(), self.type_var.get())

    def _selected_layer(self):
        return PLAYER_LAYER_BY_LABEL.get(self.layer_var.get(), self.layer_var.get())


def main():
    root = tk.Tk()
    SpriteEditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
