#!/usr/bin/env bash
# Install cmatrix-saver for the current user, or take it out again.
#
#   ./install.sh              copy it in and start the service (again: update
#                             it and restart the service)
#   ./install.sh --link       symlink this clone instead, so edits here take
#                             effect on the next run
#   ./install.sh --uninstall  stop the service and remove what was installed;
#                             scenes and sources you changed are left alone
#
# BIN=dir puts the scripts somewhere other than ~/.local/bin; the service
# file's ExecStart is pointed at it.
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"
BIN=${BIN:-$HOME/.local/bin}
CONF=${XDG_CONFIG_HOME:-$HOME/.config}/cmatrix-saver
UNIT=${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user
SCRIPTS=(cmatrix-saver cmatrix-saver-scene)

# the service file, with ExecStart pointing into $BIN
unit() {
  sed "s|^ExecStart=.*|ExecStart=$BIN/cmatrix-saver|" cmatrix-saver.service
}

install_() {
  local link=$1 f
  mkdir -p "$BIN" "$CONF/scenes" "$CONF/sources" "$UNIT"
  for f in "${SCRIPTS[@]}"; do
    rm -f "$BIN/$f"
    if ((link)); then ln -s "$PWD/$f" "$BIN/$f"; else install -m755 "$f" "$BIN/$f"; fi
  done
  # a linked clone finds its own scenes/ and sources/ next to the scripts;
  # copies from an earlier install would override them, so they go
  for f in scenes/* sources/*; do
    [[ -f $f ]] || continue # e.g. a __pycache__
    if ((link)); then
      cmp -s "$f" "$CONF/$f" && rm "$CONF/$f"
    else
      install -m755 "$f" "$CONF/$f"
    fi
  done
  unit >"$UNIT/cmatrix-saver.service"
  systemctl --user daemon-reload
  systemctl --user enable cmatrix-saver
  systemctl --user restart cmatrix-saver
  echo "installed to $BIN$( ((link)) && echo " (linked to $PWD)")"
  [[ :$PATH: == *:$BIN:* ]] || echo "note: $BIN isn't on your PATH"
}

uninstall() {
  local f
  systemctl --user disable --now cmatrix-saver 2>/dev/null || true
  rm -f "$UNIT/cmatrix-saver.service"
  systemctl --user daemon-reload
  for f in "${SCRIPTS[@]}"; do
    rm -f "$BIN/$f"
  done
  # only the repo's own scenes and sources, and only unchanged ones
  for f in scenes/* sources/*; do
    [[ -f $f ]] || continue
    if cmp -s "$f" "$CONF/$f"; then
      rm "$CONF/$f"
    elif [[ -e $CONF/$f ]]; then
      echo "kept $CONF/$f (changed)"
    fi
  done
  rmdir "$CONF/scenes" "$CONF/sources" "$CONF" 2>/dev/null || true
  echo "uninstalled"
}

case ${1:-} in
'') install_ 0 ;;
--link) install_ 1 ;;
--uninstall) uninstall ;;
*) sed -n '2,12s/^# \{0,1\}//p' "$0" >&2; exit 2 ;;
esac
