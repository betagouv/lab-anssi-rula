#!/usr/bin/env bash

set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
REPORTS="$ROOT/.harness/rapports"

usage() {
  echo "Usage: bash scripts/harness.sh {rapide|complet|audit} [--cible backend|frontend|tous]" >&2
}

resolve_command() {
  command -v "$1" 2>/dev/null || command -v "$1.exe" 2>/dev/null || command -v "$1.cmd" 2>/dev/null
}

run_in() {
  local repertoire="$1"
  local commande="$2"
  shift 2
  local executable
  executable=$(resolve_command "$commande") || {
    echo "Commande introuvable : $commande" >&2
    return 1
  }
  echo "\$ $commande $*" >&2
  (cd "$repertoire" && "$executable" "$@")
}

verifie_sarif() {
  local rapport="$1"
  local node
  node=$(resolve_command node) || {
    echo "Node est requis pour vérifier le rapport SARIF : $rapport" >&2
    return 1
  }
  "$node" -e 'JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"))' "$rapport"
}

audit() {
  local qlty
  qlty=$(resolve_command qlty) || {
    echo "Qlty est requis pour le profil audit." >&2
    return 1
  }
  mkdir -p "$REPORTS"
  local resultats=0
  local rapport_smells="$REPORTS/qlty-smells.sarif"
  local rapport_bandit="$REPORTS/qlty-bandit.sarif"

  echo "\$ qlty smells --all --sarif --no-upgrade-check" >&2
  (cd "$ROOT" && "$qlty" smells --all --sarif --no-upgrade-check > "$rapport_smells") || resultats=1
  echo "\$ qlty check --all --filter=bandit --no-fail --sarif --no-upgrade-check" >&2
  (cd "$ROOT" && "$qlty" check --all --filter=bandit --no-fail --sarif --no-upgrade-check > "$rapport_bandit") || resultats=1

  for rapport in "$rapport_smells" "$rapport_bandit"; do
    if [[ ! -s "$rapport" ]] || ! verifie_sarif "$rapport"; then
      echo "Rapport SARIF invalide : $rapport" >&2
      resultats=1
    fi
  done
  return "$resultats"
}

if [[ $# -lt 1 || $# -gt 3 ]]; then
  usage
  exit 2
fi

profil="$1"
cible="tous"
if [[ $# -eq 3 && "$2" == "--cible" ]]; then
  cible="$3"
elif [[ $# -ne 1 ]]; then
  usage
  exit 2
fi

case "$profil" in
  rapide|complet|audit) ;;
  *) usage; exit 2 ;;
esac

case "$cible" in
  backend|frontend|tous) ;;
  *) usage; exit 2 ;;
esac

if [[ "$profil" == "audit" ]]; then
  [[ "$cible" == "tous" ]] || { echo "Le profil audit s'exécute sur l'ensemble du dépôt." >&2; exit 2; }
  audit
  exit $?
fi

if [[ "$cible" == "backend" || "$cible" == "tous" ]]; then
  if [[ "$profil" == "rapide" ]]; then
    run_in "$ROOT" uv run ruff check src/ tests/ || exit 1
  else
    run_in "$ROOT" uv run ruff check . || exit 1
  fi
  run_in "$ROOT" uv run mypy || exit 1
  if [[ "$profil" == "complet" ]]; then
    run_in "$ROOT" uv run pytest || exit 1
  fi
fi

if [[ "$cible" == "frontend" || "$cible" == "tous" ]]; then
  if [[ "$profil" == "rapide" ]]; then
    run_in "$ROOT/ui" pnpm lint:check || exit 1
    run_in "$ROOT/ui" pnpm format:check || exit 1
    run_in "$ROOT/ui" pnpm svelte:check || exit 1
  else
    run_in "$ROOT/ui" pnpm test || exit 1
    run_in "$ROOT/ui" pnpm check || exit 1
    run_in "$ROOT/ui" pnpm lint:check || exit 1
    run_in "$ROOT/ui" pnpm format:check || exit 1
    run_in "$ROOT/ui" pnpm build || exit 1
  fi
fi
