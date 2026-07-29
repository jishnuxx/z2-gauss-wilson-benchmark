# Source this file from zsh: source scripts/activate_iqm_emerald.zsh

if ! command -v security >/dev/null 2>&1; then
  echo "macOS security command is unavailable" >&2
  return 1
fi

export IQM_SERVER_URL="https://resonance.meetiqm.com"
export IQM_QUANTUM_COMPUTER="emerald"
export IQM_TOKEN="$(security find-generic-password -a "$USER" -s "IQM_TOKEN" -w)" || return 1

if [[ -z "$IQM_TOKEN" ]]; then
  echo "IQM token retrieved from Keychain is empty" >&2
  return 1
fi

echo "IQM environment loaded for $IQM_QUANTUM_COMPUTER (token hidden)."
