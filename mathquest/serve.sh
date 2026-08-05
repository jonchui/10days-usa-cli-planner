#!/usr/bin/env bash
#
# Serve Math Quest on the house wifi.
#
#   ./serve.sh          -> http://<your-ip>        (port 80, asks for sudo)
#   ./serve.sh 8080     -> http://<your-ip>:8080   (no sudo needed)
#
# Port 80 is the one worth using: the kids type a bare IP address with no
# ":8080" on the end, which is a lot easier to get right on an iPad. Ports
# below 1024 are privileged, so that path needs sudo.

set -euo pipefail

PORT="${1:-80}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find the LAN address, trying each interface in turn (en0 is wifi on most
# Macs, en1 on some, and Linux boxes need a different lookup entirely).
find_ip() {
  local ip=""
  for iface in en0 en1 en2; do
    ip="$(ipconfig getifaddr "$iface" 2>/dev/null || true)"
    [ -n "$ip" ] && { echo "$ip"; return; }
  done
  ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
  [ -n "$ip" ] && { echo "$ip"; return; }
  echo "<your-ip>"
}

IP="$(find_ip)"
# Port 80 is the default for http://, so it is left off the printed address.
if [ "$PORT" = "80" ]; then
  SUFFIX=""
else
  SUFFIX=":$PORT"
fi

echo
echo "  Math Quest is serving from: $DIR"
echo
echo "    On this computer:   http://localhost$SUFFIX"
echo "    On the house wifi:  http://$IP$SUFFIX"
echo
echo "  On the iPhone or iPad: open that second address in Safari, then"
echo "  Share -> Add to Home Screen so it launches like a real app."
echo
echo "  Press Ctrl-C to stop."
echo

# Port 80 needs root. Re-exec under sudo rather than failing with a confusing
# "Permission denied" from the bind.
if [ "$PORT" -lt 1024 ] && [ "$(id -u)" -ne 0 ]; then
  echo "  (port $PORT is privileged, so this needs your password)"
  echo
  exec sudo python3 -m http.server "$PORT" --directory "$DIR"
fi

exec python3 -m http.server "$PORT" --directory "$DIR"
