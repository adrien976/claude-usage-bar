#!/bin/bash
# Installeur double-clic — Claude Usage Bar
cd "$(dirname "$0")"
clear
echo "☕  Installation de Claude Usage Bar"
echo "-----------------------------------"
APPDIR="$HOME/Library/Application Support/ClaudeUsageBar"

# 1. Homebrew
if ! command -v brew >/dev/null 2>&1; then
  if [ -x /opt/homebrew/bin/brew ]; then eval "$(/opt/homebrew/bin/brew shellenv)";
  elif [ -x /usr/local/bin/brew ]; then eval "$(/usr/local/bin/brew shellenv)";
  else
    echo "➡️  Installation de Homebrew (une seule fois, ~2 min)…"
    echo "🔑  Ton mot de passe Mac va t'être demandé (il ne s'affiche pas quand tu tapes, c'est normal). Il faut être administrateur du Mac."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    [ -x /opt/homebrew/bin/brew ] && eval "$(/opt/homebrew/bin/brew shellenv)"
    [ -x /usr/local/bin/brew ] && eval "$(/usr/local/bin/brew shellenv)"
  fi
fi

# 2. SwiftBar
[ -d /Applications/SwiftBar.app ] || { echo "➡️  Installation de SwiftBar…"; brew install --cask swiftbar; }

# 3. Fichiers du plugin (téléchargés depuis GitHub)
echo "➡️  Installation du plugin…"
mkdir -p "$APPDIR/Plugins"
BASE="https://raw.githubusercontent.com/adrien976/claude-usage-bar/main/plugin"
curl -fsSL "$BASE/claude_usage.2m.py" -o "$APPDIR/Plugins/claude_usage.2m.py"
curl -fsSL "$BASE/render.js"          -o "$APPDIR/render.js"
curl -fsSL "$BASE/reauth.command"     -o "$APPDIR/reauth.command"
chmod +x "$APPDIR/Plugins/claude_usage.2m.py" "$APPDIR/reauth.command"

defaults write com.ameba.SwiftBar PluginDirectory -string "$APPDIR/Plugins"
defaults write com.ameba.SwiftBar LaunchAtLogin -bool true
defaults write com.ameba.SwiftBar MakePluginExecutable -bool true

# 4. Autorisation Claude (une seule fois)
if ! security find-generic-password -s "ClaudeUsageBar-credentials" >/dev/null 2>&1; then
  echo ""
  echo "🔑  Dernière étape : autoriser ton compte Claude."
  "$APPDIR/reauth.command"
fi

open -a SwiftBar
sleep 2
open -g "swiftbar://refreshallplugins" 2>/dev/null || true
echo ""
echo "✅  C'est installé ! Regarde en haut à droite de ton écran."
echo "    (Tu peux fermer cette fenêtre.)"
