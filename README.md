# cmatrix-saver

A `cmatrix` screensaver for GNOME on Wayland, which has no screensaver hooks of
its own.

![cmatrix-saver: a red title decrypts, then green cmatrix rain with a status bar](assets/demo.gif)

After 5 minutes without input, or straight away from a keyboard shortcut, a
fullscreen [kitty](https://sw.kovidgoyal.net/kitty/) window opens on every
monitor. The desktop fades to black, a title decrypts out of scrambled glyphs,
and then a scene runs: `cmatrix` in your terminal's colours,
[pipes.sh](https://github.com/pipeseroni/pipes.sh) if it's installed, or one
of ten of its own, from a snake that steers itself to Tetris that plays
itself (see [Scenes](#scenes)). A handful of keys control it while it runs;
anything else, or moving the mouse, closes it.

- **Primary monitor:** decrypts `<hostname> \\ idle`, then shows a status bar
  with the hostname and the scene that's running, what's playing, idle time,
  battery (green while plugged in), date and a clock.
- **Other monitors:** decrypt the current time and date, then the same scene
  with no status bar.
- **Now playing:** the track from whichever media player is playing (Spotify,
  a browser, mpv: anything that speaks MPRIS).
- **Low battery:** if it starts on battery at 20% or less, it shows plain black
  instead of animating, to save power. Then there are no keys, notices or
  status bar, and any key closes it.
- **Notices:** a strip along the top lists
  [Claude Code](https://claude.com/claude-code) sessions that finished or need
  your input while the saver was up, and your next calendar event today. It
  takes no space when there's nothing to show, and `m` folds it away (the
  status bar then says how many are waiting). Notices come from small source
  scripts, so you can add your own.
- It doesn't trigger while something is inhibiting idle (a playing video, a
  presentation) or while the screen is locked.

## Requirements

- GNOME on Wayland. It reads idle time and the monitor layout from Mutter over
  D-Bus. Tested on GNOME 46.
- A recent kitty with `--position` support. Tested with 0.47; Ubuntu's 0.32
  package is too old. Distro packages often lag, so use the
  [official installer](https://sw.kovidgoyal.net/kitty/binary/), which puts
  kitty in `~/.local/bin`. That copy is preferred automatically.
- `cmatrix`, `tmux` (tested with 3.4), `python3-gi`, `gdbus` (ships with
  GLib), and `xwininfo`/`xprop` (`x11-utils`) for multiple monitors.
- Optional: `python3-dateutil` for repeating events in the
  [calendar](#calendar) notices.
- Optional: `pipes.sh`. Each run picks a scene at random from cmatrix, pipes
  (when it's installed) and the ones in [Scenes](#scenes), which need only
  Python 3.

```sh
sudo apt install cmatrix tmux python3-gi x11-utils
sudo apt install pipes-sh    # optional
```

## Install

```sh
git clone https://github.com/iamzainrizwan/cmatrix-saver
cd cmatrix-saver
./install.sh
```

This copies the scripts to `~/.local/bin`, the scenes and notice sources to
`~/.config/cmatrix-saver/` (`$XDG_CONFIG_HOME` if you set it), and starts the
`cmatrix-saver` user service. After a `git pull`, run it again to update and
restart the service.

```sh
./install.sh --link         # symlink this clone instead, to hack on it
./install.sh --uninstall    # stop the service and remove it all
BIN=~/bin ./install.sh      # scripts somewhere else (the service follows)
```

Uninstalling keeps any scene or source in `~/.config/cmatrix-saver/` that
you've changed. Both scripts have to sit in the same directory, because
`cmatrix-saver` looks for `cmatrix-saver-scene` next to itself. A linked clone
finds its scenes and sources in its own `scenes/` and `sources/`.

Set GNOME's own screen blank (**Settings → Power → Screen Blank**) to longer
than the saver's idle time. Otherwise the screen turns off before `cmatrix`
appears.

## Keys

While it's showing:

| key | does |
|---|---|
| `space` | pause / resume |
| `1`–`9` | speed, `9` fastest (pipes: 20–100 fps) |
| `c` | colour: cycles cmatrix's colours, toggles pipes' colour, cycles the other scenes between red, grey and green (snake: red and grey) |
| `s` | next scene: cmatrix → pipes → ant → boids → … → tetris → … |
| `n` | next track |
| `p` | play / pause music |
| `t` | status bar on / off |
| `m` | notices: collapse / expand (collapsed, the status bar counts them) |
| `b` | blank: plain black on every monitor, scene paused; `b` again brings it back |
| `r` | replay the title |
| `?` | list the keys (any key closes the list, not the saver) |
| `esc`, `q`, mouse, any other key | close it |

`n` and `p` go to whichever media player is playing, or a paused one if none
is. With more than one monitor, only one window has focus, and you can't move
focus without closing the saver. So the keys that change the scene (`space`,
`1`–`9`, `c`, `s`, `b`, `r`) apply to every monitor at once, and `t`, `m` and `?` always
act on the primary monitor, where the status bar is.

## Usage

```sh
cmatrix-saver now                             # show it straight away
cmatrix-saver now "back at 3"                 # ...with an away message
cmatrix-saver blank                           # straight to plain black, any key closes it
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

### Away message

`cmatrix-saver now "back at 3"` shows the message in the status bar, in place
of the hostname. Messages longer than 40 characters are cut short. You can also
bind a second shortcut with a fixed message, like `cmatrix-saver now "lunch"`.

## Claude Code notices

Add the `claude` source as a hook in `~/.claude/settings.json`, on three
events:

```json
{
  "hooks": {
    "Stop": [
      { "hooks": [{ "type": "command", "command": "\"$HOME\"/.config/cmatrix-saver/sources/claude hook" }] }
    ],
    "UserPromptSubmit": [
      { "hooks": [{ "type": "command", "command": "\"$HOME\"/.config/cmatrix-saver/sources/claude hook" }] }
    ],
    "Notification": [
      {
        "matcher": "permission_prompt|elicitation_dialog",
        "hooks": [{ "type": "command", "command": "\"$HOME\"/.config/cmatrix-saver/sources/claude hook" }]
      }
    ]
  }
}
```

If you already have hooks on these events, add the command next to them. If you
installed with `--link`, point it at the clone's `sources/claude`. While the
saver is up, the strip along the top of the primary monitor shows each
session's latest state, sessions waiting for input first:

- **needs input:** a permission prompt or a question, with what it's asking.
- **done:** the session finished its turn.

A session drops off again once you reply to it from anywhere, such as your
phone. Each session is listed under its working directory's name, and sessions
in a Claude Code worktree (`.claude/worktrees/`) under the repo they came from.

## Calendar

The `calendar` source shows your next event today: its start time, its name
and location, and how soon (`in 25m`). Timetable feeds that shorten the title
and put the full name in the description (`Description: …`) show the full
name. It turns red 10 minutes before the start. All-day,
cancelled and declined events are left out, and it shows nothing once the
day's events are over.

It reads from evolution-data-server, the store behind GNOME Calendar and the
calendar in the top bar. So there's nothing to set up beyond having your
calendar in GNOME:

1. **Settings → Online Accounts**, add your Google, Microsoft 365 or Nextcloud
   account, and leave **Calendar** switched on. A local calendar made in GNOME
   Calendar works too.
2. Check the events show up in GNOME Calendar (`sudo apt install
   gnome-calendar` if you don't have it) or in the top bar's calendar.

It reads the calendars ticked in GNOME Calendar's list. To narrow that, set
`CMATRIX_SAVER_CALENDARS` to their names, comma-separated, e.g.
`Work,Family`. To turn it off, leave `calendar` out of
`CMATRIX_SAVER_SOURCES`. Repeating events need `python3-dateutil`
(`sudo apt install python3-dateutil` if it's missing).

## Scenes

Besides cmatrix and pipes, these come with it. Each game ends by itself
(or after a few minutes at most), dissolves, and a new one starts. Where
there's a score, it's in the top right corner, with the best kept across
runs in `~/.local/state/cmatrix-saver/best.json`.

| scene | what it is | score |
|---|---|---|
| `ant` | Langton's ant and other turmites: ten thousand steps of mess, then a highway out of nowhere; speeds up until an ant walks off the screen | rule, steps |
| `boids` | a flock of arrows, and a hunter that grows hungrier until it has caught them all | caught |
| `eca` | elementary cellular automata (rule 30, 110, 90...) scrolling up the screen, a new rule every minute and a half | rule, generation |
| `life` | Game of Life from famous patterns or a symmetric soup, now and then under another rule; cells shaded by age; ends when it loops | generation, population |
| `maze` | a maze carves itself (backtracker, Prim, Kruskal or Wilson), then A* searches it and draws the way through | explored, path |
| `plasma` | plasma, or a lava lamp, in the scheme's shades | |
| `pong` | two players that play themselves; every return is faster, until one can't reach it; first to 5 | rally, best rally |
| `snake` | a snake that steers itself to the nearest `%`, never trapping itself, until it does | eaten, best |
| `sort` | nine sorting algorithms as bars, each paced to about half a minute | comparisons, writes |
| `tetris` | Tetris that plays itself, one move a tick against gravity that speeds up every 10 lines, until it tops out | score, lines, level, best |

## Your own scenes and notices

A **scene** is any executable in `~/.config/cmatrix-saver/scenes/`. It draws to
its terminal until it's killed. The saver passes it `1`–`9` (speed) and `c`
(colour) as plain keypresses on stdin, and pauses it by stopping its process
and everything under it. If it exits on its own, it's started again a second
later. It joins the random pick and the `s` cycle under its file name. A
name starting with `_` isn't a scene. In Python, `scenes/_scene.py` does the
work the scenes here share (the keys, resizes, drawing only what changed,
the dissolve between games, the score): subclass its `Scene`, fill in
`new_game()` and `step()`, and see `scenes/eca` for a short example. A scene
imports it from its own directory: `install.sh` copies it there, but with
`--link` it stays in the clone, so link it into `~/.config/cmatrix-saver/scenes/`
too.

A **notice source** is any executable in `~/.config/cmatrix-saver/sources/`.
The saver runs `<source> list <since>` every 2 seconds, where `<since>` is when
the saver came up, in epoch milliseconds. The source prints one tab-separated
line per notice:

```
<epoch ms>	<urgent|info>	<title>	<detail>
```

Urgent notices are listed first and get a red label. Each line ends with how
long ago its time was, or how soon for a time still to come (`in 25m`). If the source also needs
to collect events in the background (watching D-Bus, say), it can answer
`<source> watch` with a long-running process, which the service starts once,
alongside itself.

A file with the same name as one in the repo's `scenes/` or `sources/` replaces
it. The `cmatrix` and `pipes` scenes can't be replaced.

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
| `CMATRIX_SAVER_GREY` | `0` | `1` maps the window's ANSI green and white to greys, so cmatrix's default green rain shows grey (dark grey trail, off-white heads), whatever your kitty colours are |
| `CMATRIX_SAVER_NOWPLAYING` | `1` | `0` hides the now-playing track |
| `CMATRIX_SAVER_LOW_BATTERY` | `20` | at or below this battery %, while discharging, show plain black instead |
| `CMATRIX_SAVER_SCENES` | all of them | scenes to pick from and cycle through, in order, e.g. `cmatrix snake` |
| `CMATRIX_SAVER_SOURCES` | all of them | notice sources to show, e.g. `claude` |
| `CMATRIX_SAVER_CALENDARS` | ticked in GNOME Calendar | calendars the `calendar` source reads, by name, comma-separated |
| `CMATRIX_SAVER_NOTICES` | `5` | rows the notices strip can take before it shows `+N more` |
| `CMATRIX_SAVER_AWAY` | | away message for every run, in place of the hostname |
| `CMATRIX_SAVER_SINGLE` | `0` | `1` opens one native Wayland window instead of one per monitor |

## How it works

- **`cmatrix-saver`** checks Mutter's idle time every 2 seconds. Once the idle
  time passes the threshold, it opens one kitty window per monitor. When you
  touch the keyboard or mouse, the idle time resets and it closes them.
- **`cmatrix-saver-scene`** runs inside each window. It fades the window in
  through kitty's remote control, plays the decrypt title, then starts the
  scene under a throwaway tmux server. That server draws the status bar and
  holds the key bindings. On the primary monitor, a second pane above the scene
  shows the notices, with a thin line between it and the scene. It stays
  zoomed out of the way until there's something to show, or while `m` has it
  collapsed.
- **Notices start when the saver does:** Mutter's idle time also counts the
  minutes you spend reading the screen without touching anything. So anything
  that happened before the saver covered the screen, you might already have
  seen.
- **One key, every monitor:** each monitor's window has its own tmux server, and
  only the focused one gets keypresses. The key handler works out what to do
  from that window, then does it on every saver window's tmux server.
- **Keys vs. closing:** Mutter's idle time resets for any input, so on its own
  a key press looks the same as the mouse moving. Each saver key leaves a
  timestamp. When the idle time resets within 1.5 s of that timestamp, the
  saver stays open. Otherwise it closes.
- **Multiple monitors:** Mutter ignores the position a native Wayland window
  asks for. So each window runs under XWayland with `--position` set inside its
  monitor, then goes fullscreen there. Mutter can ignore that position too
  (seen with a fractionally scaled monitor: every window opened on the same
  one), so once each window is up the saver also asks Mutter to fullscreen it
  on its own monitor (`_NET_WM_FULLSCREEN_MONITORS`). The trade-off is that
  XWayland renders at 1×, so text is slightly soft on monitors with fractional
  scaling.
  `CMATRIX_SAVER_SINGLE=1` swaps this for a single, sharp native window.
- **Pipes clears as a dissolve:** pipes.sh's own reset is a `tput reset`,
  which snaps the screen to black in one frame. So it runs without one, and
  every so often the saver pauses it, blanks the screen's cells in a random
  order over about a second, and lets it carry on.
- **Why not `cmatrix -s`:** kitty answers terminal queries when it starts,
  `cmatrix -s` counts those answers as a key press, and quits immediately.

## License

[MIT](LICENSE)
