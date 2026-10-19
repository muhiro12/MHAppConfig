#!/usr/bin/env bash
set -euo pipefail

script_directory=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repository_root=$(cd "$script_directory/.." && pwd)
cd "$repository_root"
revision=$(tr -d '\n' < .mhplatform-revision)
if [[ ! "$revision" =~ ^[0-9a-f]{40}$ ]]; then
  echo "Invalid pinned MHPlatform revision." >&2
  exit 1
fi

checkout="${MHPLATFORM_CHECKOUT:-$repository_root/.build/MHPlatform}"
if [[ ! -d "$checkout/.git" && ! -f "$checkout/.git" ]]; then
  if [[ -n "${MHPLATFORM_CHECKOUT:-}" ]]; then
    echo "MHPLATFORM_CHECKOUT must name an existing checkout." >&2
    exit 1
  fi
  mkdir -p "$repository_root/.build"
  git clone --filter=blob:none --no-checkout https://github.com/muhiro12/MHPlatform.git "$checkout"
fi
if [[ -z "${MHPLATFORM_CHECKOUT:-}" ]]; then
  git -C "$checkout" fetch --depth=1 origin "$revision"
  git -C "$checkout" checkout --detach "$revision"
fi
if [[ "$(git -C "$checkout" rev-parse HEAD)" != "$revision" ]] || \
   [[ -n "$(git -C "$checkout" status --porcelain --untracked-files=all -- Sources/MHRemoteConfig Sources/MHRemoteUpdate Tools/RemoteConfigValidator.swift ci_scripts/tasks/build_remote_config_validator.sh)" ]]; then
  echo "The validator requires the pinned, unchanged MHPlatform source revision." >&2
  exit 1
fi

output="$repository_root/.build/validator/$revision"
validator="$output/mh-validate-remote-config"
if [[ ! -x "$validator" ]]; then
  bash "$checkout/ci_scripts/tasks/build_remote_config_validator.sh" "$output"
fi
python3 scripts/verify.py --validator "$validator" "$@"
