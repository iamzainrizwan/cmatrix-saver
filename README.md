# cmatrix-saver

A `cmatrix` screensaver for GNOME on Wayland, which has no screensaver hooks of
its own.

![cmatrix-saver: a red title decrypts, then green cmatrix rain with a status bar](assets/demo.gif)

After 5 minutes without input, or straight away from a keyboard shortcut, a
fullscreen [kitty](https://sw.kovidgoyal.net/kitty/) window opens on every
monitor. The desktop fades to black, a title decrypts out of scrambled glyphs,
and then `cmatrix` runs in your terminal's colours. Any key press or mouse
movement closes it.

- **Primary monitor:** decrypts `<hostname> \\ idle`, then shows a status bar
  with the hostname, what's playing, idle time, battery, date and a clock.
- **Other monitors:** decrypt the current time and date, then plain `cmatrix`.
- **Now playing:** the track from whichever media player is playing (Spotify,
  a browser, mpv: anything that speaks MPRIS).
- **Low battery:** on battery at 20% or less, it shows plain black instead of
  animating, to save power.
- It doesn't trigger while something is inhibiting idle (a playing video, a
  presentation) or while the screen is locked.

## Requirements

- GNOME on Wayland. It reads idle time and the monitor layout from Mutter over
  D-Bus. Tested on GNOME 46.
- A recent kitty with `--position` support. Tested with 0.47; Ubuntu's 0.32
  package is too old. Distro packages often lag, so use the
  [official installer](https://sw.kovidgoyal.net/kitty/binary/), which puts
  kitty in `~/.local/bin`. That copy is preferred automatically.
- `cmatrix`, `tmux` (tested with 3.4), `python3-gi`, and `gdbus` (ships with
  GLib).

```sh
sudo apt install cmatrix tmux python3-gi
```

## Install

```sh
git clone https://github.com/iamzainrizwan/cmatrix-saver
cd cmatrix-saver
install -Dm755 cmatrix-saver cmatrix-saver-scene -t ~/.local/bin/
install -Dm644 cmatrix-saver.service -t ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now cmatrix-saver
```

Both scripts have to sit in the same directory, because `cmatrix-saver` looks
for `cmatrix-saver-scene` next to itself. If you install them somewhere other
than `~/.local/bin`, change `ExecStart` in the service file to match.

Set GNOME's own screen blank (**Settings → Power → Screen Blank**) to longer
than the saver's idle time. Otherwise the screen turns off before `cmatrix`
appears.

## Usage

```sh
cmatrix-saver now                             # show it straight away
cmatrix-saver test                            # counts down from 5, then shows it once
systemctl --user restart cmatrix-saver        # pick up edits
journalctl --user -u cmatrix-saver -n 20      # it didn't show? check here
```

### Start it from a shortcut

In **Settings → Keyboard → View and Customize Shortcuts → Custom Shortcuts**,
add a shortcut with this command, using your own home directory (GNOME doesn't
expand `~` here):

```
/home/you/.local/bin/cmatrix-saver now
```

It waits half a second for you to let go of the keys, then opens. If the saver
is already showing, it does nothing.

## Configuration

Settings are environment variables. For the service, set them with
`systemctl --user edit cmatrix-saver`:

```ini
[Service]
Environment=CMATRIX_SAVER_IDLE=600
```

| variable | default | effect |
|---|---|---|
| `CMATRIX_SAVER_IDLE` | `300` | seconds of no input before it starts |
| `CMATRIX_SAVER_TITLE` | `<hostname> \\ idle` | title decrypted on the primary monitor |
| `CMATRIX_SAVER_GREY` | `0` | `1` turns the green rain grey (dark grey trail, off-white heads), whatever your kitty colours are |
| `CMATRIX_SAVER_NOWPLAYING` | `1` | `0` hides the now-playing track |
| `CMATRIX_SAVER_LOW_BATTERY` | `20` | at or below this battery %, while discharging, show plain black instead |
| `CMATRIX_SAVER_SINGLE` | `0` | `1` opens one native Wayland window instead of one per monitor |

## How it works

- **`cmatrix-saver`** checks Mutter's idle time every 2 seconds. Once the idle
  time passes the threshold, it opens one kitty window per monitor. When you
  touch the keyboard or mouse, the idle time resets and it closes them.
- **`cmatrix-saver-scene`** runs inside each window. It fades the window in
  through kitty's remote control, plays the decrypt title, then starts
  `cmatrix` under a throwaway tmux server with no config, which draws the
  status bar.
- **Multiple monitors:** Mutter ignores the position a native Wayland window
  asks for. So each window runs under XWayland with `--position` set inside its
  monitor, then goes fullscreen there. The trade-off is that XWayland renders
  at 1×, so text is slightly soft on monitors with fractional scaling.
  `CMATRIX_SAVER_SINGLE=1` swaps this for a single, sharp native window.
- **Why not `cmatrix -s`:** kitty answers terminal queries when it starts,
  `cmatrix -s` counts those answers as a key press, and quits immediately.

## License

[MIT](LICENSE)
