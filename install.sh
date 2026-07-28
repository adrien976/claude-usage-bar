#!/bin/bash
# Claude Usage Bar — installation en une commande
set -e
APPDIR="$HOME/Library/Application Support/ClaudeUsageBar"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

# Homebrew (installé automatiquement si absent)
if ! command -v brew >/dev/null 2>&1; then
  if [ -x /opt/homebrew/bin/brew ]; then eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [ -x /usr/local/bin/brew ]; then eval "$(/usr/local/bin/brew shellenv)"
  else
    echo "➡️  Installation de Homebrew (une seule fois, ~2 min)…"
    echo "🔑  Ton mot de passe Mac va t'être demandé (il ne s'affiche pas quand tu tapes, c'est normal). Il faut être administrateur du Mac."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    [ -x /opt/homebrew/bin/brew ] && eval "$(/opt/homebrew/bin/brew shellenv)"
    [ -x /usr/local/bin/brew ] && eval "$(/usr/local/bin/brew shellenv)"
  fi
fi

[ -d /Applications/SwiftBar.app ] || brew install --cask swiftbar

mkdir -p "$APPDIR/Plugins"
cp "$REPO_DIR/plugin/claude_usage.2m.py" "$APPDIR/Plugins/"
cp "$REPO_DIR/plugin/render.js" "$APPDIR/"
cp "$REPO_DIR/plugin/reauth.command" "$APPDIR/"
chmod +x "$APPDIR/Plugins/claude_usage.2m.py" "$APPDIR/reauth.command"

defaults write com.ameba.SwiftBar PluginDirectory -string "$APPDIR/Plugins"
defaults write com.ameba.SwiftBar LaunchAtLogin -bool true
defaults write com.ameba.SwiftBar MakePluginExecutable -bool true

# Autorisation OAuth (une seule fois)
if ! security find-generic-password -s "ClaudeUsageBar-credentials" >/dev/null 2>&1; then
  echo "🔑 Autorisation du compte Claude…"
  "$APPDIR/reauth.command"
fi

open -a SwiftBar
sleep 2
open -g "swiftbar://refreshallplugins" 2>/dev/null || true
echo "✅ Claude Usage Bar est installé ! Regarde en haut de ton écran."
