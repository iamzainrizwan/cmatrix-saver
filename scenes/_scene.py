# Shared by the Python scenes (not a scene itself: the saver skips names
# starting with _). A scene subclasses Scene and fills in new_game() and
# step(); this takes care of the rest:
#
#   - a screen buffer: put() into it, and each frame only the cells that
#     changed are written out
#   - keys from the saver: 1-9 speed (DELAYS, 9 fastest), c colour scheme
#   - resizes (the notices strip coming and going on the primary monitor)
#   - the end of a game: step() returning False, or MAX_GAME seconds of
#     play, holds the last frame, dissolves it and starts a new one
#   - a score in the top right corner (self.hud), and a best per scene
#     kept across runs in $XDG_STATE_HOME/cmatrix-saver/best.json
#
# Colours are either a role (an int into the scheme below, so `c` recolours
# everything already on screen) or a "#rrggbb" string.
import json, os, random, select, signal, sys, termios, time, tty

# brightest to darkest, then an accent that stands out against them
SCHEMES = [
    ["#ff4444", "#cc2222", "#882222", "#551515", "#331010", "#e0e0e0"],
    ["#e0e0e0", "#999999", "#666666", "#444444", "#2a2a2a", "#cc2222"],
    ["#55ff55", "#22bb22", "#1a7a1a", "#124d12", "#0c300c", "#e0e0e0"],
]
HI, MID, LOW, DIM, FAINT, ACCENT = range(6)
BLANK = (" ", None, None)
HUD_GREY = "#666666"

out = sys.stdout


def hex_rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def mix(a, b, t):
    """a to b as t goes 0 to 1, both "#rrggbb"."""
    a, b = hex_rgb(a), hex_rgb(b)
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


class Best:
    """Best scores, kept across runs. Every monitor's scene writes here, so
    each save merges with what's on disk rather than overwriting it."""

    def __init__(self):
        state = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
        self.path = os.path.join(state, "cmatrix-saver", "best.json")

    def load(self):
        try:
            with open(self.path) as f:
                return json.load(f)
        except (OSError, ValueError):
            return {}

    def get(self, key):
        return self.load().get(key, 0)

    def offer(self, key, score):
        """Record score if it beats the best; returns the best."""
        best = self.load()
        if score <= best.get(key, 0):
            return best.get(key, 0)
        best[key] = score
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp = "%s.%d" % (self.path, os.getpid())
            with open(tmp, "w") as f:
                json.dump(best, f)
            os.replace(tmp, self.path)
        except OSError:
            pass
        return score


class Scene:
    DELAYS = [0.2, 0.15, 0.11, 0.08, 0.06, 0.045, 0.033, 0.022, 0.012]
    MAX_GAME = 300  # seconds of play before a game is ended anyway
    HOLD = 1.0  # how long the last frame stays up before it dissolves

    def __init__(self):
        self.speed = 6
        self.scheme = 0
        self.hud = ""
        self.best = Best()
        self.resized = False
        self.played = 0.0
        self.sgr_cache = {}
        self.measure()

    # -- the screen buffer ------------------------------------------------

    def measure(self):
        cols, rows = os.get_terminal_size()
        self.w, self.h = max(cols, 8), max(rows, 4)
        self.cells = [[BLANK] * self.w for _ in range(self.h)]
        self.shown = [[BLANK] * self.w for _ in range(self.h)]
        out.write("\033[0m\033[2J")

    def put(self, x, y, ch, fg=None, bg=None):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.cells[y][x] = (ch, fg, bg)

    def text(self, x, y, s, fg=None, bg=None):
        for i, ch in enumerate(s):
            self.put(x + i, y, ch, fg, bg)

    def clear(self):
        for row in self.cells:
            row[:] = [BLANK] * self.w

    def repaint(self):
        """Everything goes out again on the next flush."""
        self.shown = [[None] * self.w for _ in range(self.h)]

    def colour(self, c):
        return SCHEMES[self.scheme][c] if isinstance(c, int) else c

    def ramp(self, t):
        """0 black through the scheme's darkest to its brightest at 1."""
        stops = ["#000000"] + SCHEMES[self.scheme][FAINT::-1]
        t = min(max(t, 0.0), 1.0) * (len(stops) - 1)
        i = min(int(t), len(stops) - 2)
        return mix(stops[i], stops[i + 1], t - i)

    def sgr(self, fg, bg):
        key = (self.scheme, fg, bg)
        s = self.sgr_cache.get(key)
        if s is None:
            s = "\033[0"
            if fg is not None:
                s += ";38;2;%d;%d;%d" % hex_rgb(self.colour(fg))
            if bg is not None:
                s += ";48;2;%d;%d;%d" % hex_rgb(self.colour(bg))
            s += "m"
            self.sgr_cache[key] = s
        return s

    def hud_row(self):
        """Row 0 with the score drawn over its right-hand end."""
        row = self.cells[0]
        if not self.hud:
            return row
        text = " %s " % self.hud
        if len(text) > self.w:
            return row
        row = row[:]
        x0 = self.w - len(text) - 1
        for i, ch in enumerate(text):
            row[x0 + i] = (ch, HUD_GREY, "#000000")
        return row

    def flush(self):
        parts, style, at = [], None, None
        for y in range(self.h):
            row = self.hud_row() if y == 0 else self.cells[y]
            seen = self.shown[y]
            if row == seen:
                continue
            for x in range(self.w):
                c = row[x]
                if c == seen[x]:
                    continue
                if at != (x, y):
                    parts.append("\033[%d;%dH" % (y + 1, x + 1))
                st = (c[1], c[2])
                if st != style:
                    parts.append(self.sgr(*st))
                    style = st
                parts.append(c[0])
                seen[x] = c
                at = (x + 1, y)
        if parts:
            out.write("".join(parts) + "\033[0m")
        out.flush()

    def scroll_up(self):
        """Move everything up a row, the terminal's own scroll included, and
        leave the bottom row blank."""
        out.write("\033[0m\033[%d;1H\n" % self.h)
        self.cells.append(self.cells.pop(0))
        self.cells[-1][:] = [BLANK] * self.w
        self.shown.append(self.shown.pop(0))
        self.shown[-1][:] = [BLANK] * self.w
        out.flush()

    # -- what a scene fills in --------------------------------------------

    def new_game(self):
        """Set up a fresh game on a clear screen."""

    def step(self):
        """One tick. Return False when the game is over."""
        return True

    def on_resize(self):
        """The buffer is already the new size and blank. By default the game
        starts over; override to carry it across."""
        self.new_game()

    def on_colour(self):
        """After `c`: roles recolour themselves; override for anything
        drawn with "#rrggbb" strings."""

    def game_over(self):
        """After a game ends, before the hold and dissolve: a last frame."""

    # -- the loop ---------------------------------------------------------

    @property
    def delay(self):
        return self.DELAYS[self.speed - 1]

    def key(self, ch):
        if ch in "123456789":
            self.speed = int(ch)
        elif ch == "c":
            self.scheme = (self.scheme + 1) % len(SCHEMES)
            self.on_colour()
            self.repaint()
            self.flush()

    def wait(self, secs):
        """Sleep, taking keys and noticing resizes as they come."""
        end = time.monotonic() + max(secs, 0)
        while True:
            left = end - time.monotonic()
            r, _, _ = select.select([sys.stdin], [], [], max(left, 0))
            if r:
                for ch in os.read(sys.stdin.fileno(), 64).decode(errors="ignore"):
                    self.key(ch)
            if left <= 0 or not r:
                return

    def dissolve(self):
        lit = [(x, y) for y in range(self.h) for x in range(self.w)
               if self.cells[y][x] != BLANK]
        for x, y in lit:
            ch, fg, bg = self.cells[y][x]
            self.cells[y][x] = (ch, DIM if fg is not None else None,
                                FAINT if bg is not None else None)
        self.hud = ""
        self.flush()
        self.wait(0.5)
        random.shuffle(lit)
        n = max(1, len(lit) // 40)
        for i in range(0, len(lit), n):
            for x, y in lit[i:i + n]:
                self.cells[y][x] = BLANK
            self.flush()
            self.wait(0.025)
        self.wait(0.6)

    def start(self):
        self.clear()
        self.hud = ""
        self.played = 0.0
        self.new_game()
        self.flush()

    def run(self):
        self.start()
        while True:
            if self.resized:
                self.resized = False
                self.measure()
                self.on_resize()
            t0 = time.monotonic()
            alive = self.step()
            self.flush()
            if alive is False or self.played > self.MAX_GAME:
                self.game_over()
                self.flush()
                self.wait(self.HOLD)
                self.dissolve()
                self.start()
                continue
            self.wait(self.delay - (time.monotonic() - t0))
            # a long gap is a pause (SIGSTOP), not play
            self.played += min(time.monotonic() - t0, 1.0)


def main(scene_class):
    fd = sys.stdin.fileno()
    saved = termios.tcgetattr(fd)
    out.write("\033[?25l\033[0m")
    scene = scene_class()

    def on_winch(*_):
        scene.resized = True

    def bye(*_):
        raise SystemExit

    signal.signal(signal.SIGWINCH, on_winch)
    signal.signal(signal.SIGTERM, bye)
    signal.signal(signal.SIGHUP, bye)
    try:
        tty.setcbreak(fd)
        scene.run()
    except (SystemExit, KeyboardInterrupt):
        pass
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)
        out.write("\033[0m\033[2J\033[?25h")
        out.flush()
