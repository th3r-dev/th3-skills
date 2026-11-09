#!/bin/sh
# Capture the config every HAProxy container on one host is ACTUALLY running, into <out>/<host>/.
#
#   snapshot_haproxy.sh <host> [<out dir>] [<config path in container>]
#   snapshot_haproxy.sh 10.0.0.48 snapshots /usr/local/etc/haproxy/haproxy.cfg
#
# Reads from inside the container, not the file on the host: a single-file bind mount keeps the OLD
# inode after an editor saves a new file (vim, nano, sed -i), so the host file is not what runs.
# container.txt carries mount_source_in_kernel — if it ends in //deleted, the container must be
# restarted before it reads the new file (HUP will not help). Uses jssh.py --sudo (same folder).
set -eu
HOST=${1:?host}
OUT=${2:-snapshots}/$HOST
CFG=${3:-/usr/local/etc/haproxy/haproxy.cfg}
HERE=$(cd "$(dirname "$0")" && pwd)
rm -rf "$OUT" && mkdir -p "$OUT"

"$HERE/jssh.py" --sudo --host "$HOST" '
cd /tmp && rm -rf hasnap && mkdir hasnap
for c in $(docker ps --format "{{.Names}} {{.Image}}" | awk "/haproxy/{print \$1}"); do
  mkdir -p hasnap/$c
  docker exec $c cat '"$CFG"' > hasnap/$c/haproxy.cfg
  docker inspect $c --format "name={{.Name}}
image={{.Config.Image}}
started={{.State.StartedAt}}
restart={{.HostConfig.RestartPolicy.Name}}
ports={{range \$p,\$b := .HostConfig.PortBindings}}{{\$p}}->{{(index \$b 0).HostPort}} {{end}}
mounts={{range .Mounts}}{{.Source}}->{{.Destination}} {{end}}" > hasnap/$c/container.txt
  grep haproxy /proc/$(docker inspect -f {{.State.Pid}} $c)/mountinfo | cut -d" " -f4 | sed "s/^/mount_source_in_kernel=/" >> hasnap/$c/container.txt
  md5sum hasnap/$c/haproxy.cfg | cut -d" " -f1 | sed "s/^/running_cfg_md5=/" >> hasnap/$c/container.txt
done
tar czf - hasnap' | tar xzf - -C "$OUT" --strip-components=1

date -u +%FT%TZ > "$OUT/CAPTURED_AT"
grep -l '//deleted' "$OUT"/*/container.txt 2>/dev/null && echo "!! a container is running a config whose host file was replaced (stale inode)" || true
find "$OUT" -type f | sort
