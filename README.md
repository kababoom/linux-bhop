# linux-bhop

A tiny **hold-to-bunny-hop** (auto-jump) helper for Linux games, using `evdev`. Unlike AutoHotkey-style X11 tools (`xdotool`), it injects **real hardware-level** key events via `uinput`, so games actually see them — works in fullscreen, **native or Proton**.

## Behaviour
- **Tap** Space → one normal space (typing stays safe)
- **Hold** Space past a short threshold → auto-repeats Space (bhop), with an instant first jump

## Why evdev, not xdotool
Most games (especially Source/Proton) read input at the `evdev` level and ignore X11-faked keys. This **grabs the real keyboard** and re-emits through `uinput`, so the synthetic presses are indistinguishable from a real key — it works where `xdotool` silently does nothing.

## Install & run
```bash
sudo apt install python3-evdev      # or your distro's equivalent
sudo python3 bhop.py                # auto-detects your keyboard
sudo python3 bhop.py Asus           # or force a device by name substring
```
Needs root (reads `/dev/input`, writes `/dev/uinput`). Stop with **Ctrl+C**.

> ⚠️ It **grabs the keyboard system-wide** while running — so only run it while gaming, and stop it (Ctrl+C) when you're done.

## Tuning
Edit the two constants at the top of `bhop.py`:
- `THRESHOLD` (default `0.20`s) — how long you must hold before it starts repeating. Raise it if normal typing produces double-spaces.
- `INTERVAL` (default `0.035`s) — repeat speed; lower = faster.

## Running without sudo (optional)
Grant access to input devices instead of using root each time:
```bash
sudo usermod -aG input "$USER"
echo 'KERNEL=="uinput", GROUP="input", MODE="0660"' | sudo tee /etc/udev/rules.d/99-uinput.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
# log out and back in, then just:  python3 bhop.py
```

## License
[MIT](LICENSE)
