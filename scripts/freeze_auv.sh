#!/usr/bin/env bash
# Freeze orca4_heavy in place by re-asserting its captured pose at high rate.
# Ctrl-C to release (physics/thrusters resume immediately).
# Run inside the cosma_auv_sim container.
set -eu

WORLD=sand
MODEL=orca4_heavy
RATE_HZ=10

# Capture current pose (position + quaternion) from the dynamic pose stream.
read -r X Y Z QX QY QZ QW < <(
  gz topic -e -t "/world/${WORLD}/dynamic_pose/info" -n 20 2>/dev/null \
  | awk -v m="$MODEL" '
      $0 ~ "name: \""m"\"" {hit=1}
      hit && /position/ {inpos=1}
      hit && inpos && /x:/ {x=$2}
      hit && inpos && /y:/ {y=$2}
      hit && inpos && /z:/ {z=$2; inpos=0}
      hit && /orientation/ {inori=1}
      hit && inori && /x:/ {qx=$2}
      hit && inori && /y:/ {qy=$2}
      hit && inori && /z:/ {qz=$2}
      hit && inori && /w:/ {qw=$2; print x,y,z,qx,qy,qz,qw; exit}
    '
)

echo "Freezing ${MODEL} at z=${Z} (x=${X} y=${Y}). Ctrl-C to release."
REQ="name: \"${MODEL}\", position: {x: ${X}, y: ${Y}, z: ${Z}}, orientation: {x: ${QX}, y: ${QY}, z: ${QZ}, w: ${QW}}"

trap 'echo; echo "Released ${MODEL}."; exit 0' INT
while true; do
  gz service -s "/world/${WORLD}/set_pose" \
    --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean \
    --timeout 100 --req "${REQ}" >/dev/null 2>&1 || true
  sleep "$(awk -v r="$RATE_HZ" 'BEGIN{print 1/r}')"
done
