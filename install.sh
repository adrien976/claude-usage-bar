#!/bin/bash
# Claude Usage Bar — installation en une commande
set -e
APPDIR="$HOME/Library/Application Support/ClaudeUsageBar"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

command -v brew >/dev/null 2>&1 || { echo "❌ Homebrew est requis : https://brew.sh"; exit 1; }
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
