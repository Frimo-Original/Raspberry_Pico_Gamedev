import glob
import sys
import time
import tkinter as tk


BAUDRATE = 115200
SEND_INTERVAL_MS = 30
HOTBAR_KEYS = {"slash", "question", "period", "less", "Tab"}
HOTBAR_CHARS = {"/", "?", ".", ",", "ю", "Ю", "б", "Б"}
DIG_KEYS = {"greater"}
DIG_CHARS = {">"}


def find_default_port():
    ports = sorted(glob.glob("/dev/tty.usbmodem*") + glob.glob("/dev/tty.usbserial*"))
    if ports:
        return ports[0]
    return None


class KeyboardBridge:
    def __init__(self, root, serial_port):
        self.root = root
        self.serial_port = serial_port
        self.left = False
        self.right = False
        self.jump = False
        self.dig = False
        self.hotbar_toggle = False
        self.pressed = set()

        root.title("Pico Keyboard Bridge")
        root.geometry("360x170")
        root.resizable(False, False)
        self.label = tk.Label(
            root,
            text="Click here, then use arrows / Space\n\nLeft/Right: move\nUp/Space: jump\n?/Slash: choose slot\n>: dig/use\nQ: quit",
            font=("Arial", 16),
            justify=tk.CENTER,
        )
        self.label.pack(expand=True, fill=tk.BOTH)
        self.status = tk.Label(root, text="Ready", font=("Arial", 11))
        self.status.pack(fill=tk.X)

        root.bind("<KeyPress>", self._key_down)
        root.bind("<KeyRelease>", self._key_up)
        root.protocol("WM_DELETE_WINDOW", self._close)
        root.focus_force()
        self._send_state()

    def _key_down(self, event):
        key = event.keysym
        first_press = key not in self.pressed
        self.pressed.add(key)
        if key in ("Left", "a", "A"):
            self.left = True
        elif key in ("Right", "d", "D"):
            self.right = True
        elif key in ("Up", "space", "w", "W"):
            self.jump = True
        elif self._is_dig_key(event):
            self.dig = True
        elif self._is_hotbar_key(event) and first_press:
            self.hotbar_toggle = True
            self.status.config(text=f"Choose slot command sent: {key!r} {event.char!r}")
        elif key in ("q", "Q", "Escape"):
            self._close()

    def _is_hotbar_key(self, event):
        return event.keysym in HOTBAR_KEYS or event.char in HOTBAR_CHARS

    def _is_dig_key(self, event):
        return event.keysym in DIG_KEYS or event.char in DIG_CHARS

    def _key_up(self, event):
        key = event.keysym
        if key in self.pressed:
            self.pressed.remove(key)
        if key in ("Left", "a", "A"):
            self.left = False
        elif key in ("Right", "d", "D"):
            self.right = False
        elif key in ("Up", "space", "w", "W"):
            self.jump = False
        elif self._is_dig_key(event):
            self.dig = False

    def _send_state(self):
        data = bytearray()
        if self.left:
            data.append(ord("L"))
        if self.right:
            data.append(ord("R"))
        if self.jump:
            data.append(ord("J"))
        if self.dig:
            data.append(ord("D"))
        if self.hotbar_toggle:
            data.append(ord("H"))
            self.hotbar_toggle = False
        if data:
            self.serial_port.write(data)
        self.root.after(SEND_INTERVAL_MS, self._send_state)

    def _close(self):
        self.root.destroy()


def main():
    try:
        import serial
    except ImportError:
        print("pyserial is not installed.")
        print("Install it once:")
        print(f"  {sys.executable} -m pip install pyserial")
        raise SystemExit(1)

    port = sys.argv[1] if len(sys.argv) > 1 else find_default_port()
    if not port:
        print("Could not find Pico serial port.")
        print("Pass it explicitly, for example:")
        print("  python3 tools/keyboard_to_pico.py /dev/tty.usbmodemXXXX")
        raise SystemExit(1)

    print(f"Opening {port}")
    print("Temporary keyboard bridge window is opening.")
    print("Close the window or press Q/Escape to quit.")

    with serial.Serial(port, BAUDRATE, timeout=0, write_timeout=0) as serial_port:
        time.sleep(0.5)
        root = tk.Tk()
        KeyboardBridge(root, serial_port)
        root.mainloop()


if __name__ == "__main__":
    main()
