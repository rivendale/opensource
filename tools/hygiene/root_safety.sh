#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Run each line of COMMANDS as root from WORKDIR, then fail if a system file or directory that existed before
# is gone, or changed mode, owner, type or symlink target, or (for executables in the bin directories) content.
# The mark of a cleanup that chmods, deletes or writes through a symlink. New files are not failures.
#
#   root_safety.sh COMMANDS WORKDIR
#
# The workflow runs it in a throwaway container. Both snapshots stay in this shell's variables, out of reach of
# the commands, and any failure to take or compare them fails the run instead of passing it.
# ROOT_SAFETY_DIRS and ROOT_SAFETY_HASH_DIRS override the directories (tests/tools/test_repo_hygiene.py uses them).
set -u -o pipefail
commands=$1 workdir=$2
dirs=() bins=()
for d in ${ROOT_SAFETY_DIRS:-/bin /sbin /usr/bin /usr/sbin /usr/local/bin /usr/lib /usr/libexec /usr/local/lib /usr/share /opt /etc /root /home}; do
  [ -e "$d" ] && dirs+=("$d")
done
for d in ${ROOT_SAFETY_HASH_DIRS:-/usr/bin /usr/local/bin /bin}; do
  [ -d "$d" ] && [ ! -L "$d" ] && bins+=("$d")  # /bin is usually a link to /usr/bin
done
if [ ${#dirs[@]} -eq 0 ]; then echo "::error::root safety: none of the snapshot directories exist"; exit 1; fi

snap() {
  {
    find -H "${dirs[@]}" -xdev \( -type f -o -type d -o -type l \) -printf '%m %u:%g %y %p -> %l\n' &&
    if [ ${#bins[@]} -gt 0 ]; then find "${bins[@]}" -xdev -type f -exec sha256sum {} +; fi
  } | LC_ALL=C sort
}

before=$(snap) || { echo "::error::root safety: the snapshot before the commands failed"; exit 1; }
[ -n "$before" ] || { echo "::error::root safety: the snapshot before the commands is empty"; exit 1; }

status=0
cd "$workdir" || exit 1
while IFS= read -r cmd || [ -n "$cmd" ]; do
  [ -z "$cmd" ] && continue
  echo "::group::$cmd"
  bash -c "$cmd" < /dev/null || { echo "::error::root_safety command failed: $cmd"; status=1; }
  echo "::endgroup::"
done < "$commands"

after=$(snap) || { echo "::error::root safety: the snapshot after the commands failed (a snapshot directory was removed?)"; exit 1; }
[ -n "$after" ] || { echo "::error::root safety: the snapshot after the commands is empty"; exit 1; }
lost=$(LC_ALL=C comm -23 <(printf '%s\n' "$before") <(printf '%s\n' "$after")) \
  || { echo "::error::root safety: comparing the snapshots failed"; exit 1; }
if [ -n "$lost" ]; then
  echo "::error::system files were deleted, or their mode, owner, target or content changed, while running as root:"
  printf '%s\n' "$lost" | head -50
  status=1
fi
if [ -z "${ROOT_SAFETY_DIRS:-}" ]; then
  /usr/bin/env true || { echo "::error::/usr/bin/env no longer runs"; status=1; }
fi
exit $status
