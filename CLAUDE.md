# CLAUDE.md

Guidance for Claude Code in this repo. Public repo that runs only on Zain's machine: commit and push
straight to main, no PRs or worktree branches left behind (an unmerged worktree branch once held the
title-centre fix and the bug came back).

## Install and layout

- `install.sh` copies the scripts to `~/.local/bin` unless run as `./install.sh --link`. Re-run the
  installer after changes, or keep the link install.
- Scenes live in `scenes/`; files starting with `_` are skipped. `best.json` is in
  `~/.local/state/cmatrix-saver/`. CI runs shellcheck.
- Claude-session notices are a pluggable source (`sources/`) shown in a top strip. The calendar source
  reads GNOME's Evolution data server; Scientia ICS titles are shortened codes, so the full module name
  comes from the Description line and the room from location. Google-subscribed URL calendars do not
  sync to GNOME.
- Keys that change the background apply to every monitor; `t` and `?` act on the primary monitor.

## Style

- Red and grey, small green accents allowed. No emoji indicators: charging state is green `BAT n%` text.
- Notice labels line up flush-left with the valhalla host label.
- Every scene dissolves and restarts on its own, and shows a score where it makes sense.

## Gotchas

- Pipes runs `tput reset` at the limit and blanks in one frame. Fix: `-r 0` plus a scripted dissolve
  wipe of about 1.3 s.
- tmux 3.4 does not support `pane-border-lines spaces`; use `simple`.
