#!/usr/bin/env python3
"""
bhop.py - hold-to-bunny-hop, portable replacement for the old BHop.ahk

Behaviour:
  * a quick TAP of Space  -> one normal space (safe for typing)
  * HOLDING Space past THRESHOLD -> auto-repeats Space every INTERVAL (bhop)

Works at the evdev/uinput level, so games (incl. Steam/Proton) see real
hardware key events. Run it on any Linux PC with:

    sudo apt install -y python3-evdev
    sudo python3 bhop.py                # auto-detect keyboard
    sudo python3 bhop.py Asus           # or force a device by name substring

Stop with Ctrl+C.
"""
import sys, time, select
from evdev import InputDevice, UInput, ecodes, list_devices

THRESHOLD = 0.20   # seconds you must hold before bhop kicks in (the "pause")
INTERVAL  = 0.035  # seconds between auto-jumps while held (lower = faster)
SPACE     = ecodes.KEY_SPACE


def find_keyboard(name_filter=None):
    """Pick a real keyboard (has Space + A + Shift). Prefer one matching name,
    else the device exposing the most keys (skips mouse 'keyboard' interfaces)."""
    cands = []
    for path in list_devices():
        d = InputDevice(path)
        keys = d.capabilities().get(ecodes.EV_KEY, [])
        full_kbd = all(k in keys for k in (SPACE, ecodes.KEY_A, ecodes.KEY_LEFTSHIFT))
        if full_kbd and (name_filter is None or name_filter.lower() in d.name.lower()):
            cands.append((len(keys), d))
        else:
            d.close()
    if not cands:
        sys.exit("No keyboard found" + (f" matching '{name_filter}'" if name_filter else ""))
    cands.sort(key=lambda c: c[0], reverse=True)
    chosen = cands[0][1]
    for _, d in cands[1:]:
        d.close()
    return chosen


def main():
    name_filter = sys.argv[1] if len(sys.argv) > 1 else None
    dev = find_keyboard(name_filter)
    print(f"Using: {dev.name}  ({dev.path})   Ctrl+C to quit")
    ui = UInput.from_device(dev, name="bhop-virtual-kbd")
    dev.grab()  # take exclusive control so the physical Space is suppressed

    def jump():
        ui.write(ecodes.EV_KEY, SPACE, 1); ui.syn()
        ui.write(ecodes.EV_KEY, SPACE, 0); ui.syn()

    state = "idle"      # idle -> held (one tap already sent) -> spamming (held past threshold)
    press_t = 0.0
    next_t  = 0.0
    try:
        while True:
            now = time.monotonic()
            if state == "held":
                timeout = max(0.0, press_t + THRESHOLD - now)
            elif state == "spamming":
                timeout = max(0.0, next_t - now)
            else:
                timeout = None
            r, _, _ = select.select([dev.fd], [], [], timeout)
            now = time.monotonic()

            if r:
                for ev in dev.read():
                    if ev.type == ecodes.EV_KEY and ev.code == SPACE:
                        if ev.value == 1:            # pressed -> emit ONE space NOW (natural typing + instant first jump)
                            jump()
                            state, press_t = "held", now
                        elif ev.value == 0:          # released -> stop
                            state = "idle"
                        # value 2 (kernel autorepeat) for space: ignore
                    else:
                        ui.write(ev.type, ev.code, ev.value)   # pass everything else through
            else:
                if state == "held" and now >= press_t + THRESHOLD:   # still down after the pause -> start bhop
                    state, next_t = "spamming", now + INTERVAL
                if state == "spamming" and now >= next_t:
                    jump()
                    next_t = now + INTERVAL
    except KeyboardInterrupt:
        pass
    finally:
        dev.ungrab(); ui.close(); dev.close()
        print("\nstopped.")


if __name__ == "__main__":
    main()
