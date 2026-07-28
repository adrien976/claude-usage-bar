#!/bin/bash
# Désinstallation de Claude Usage Bar
APPDIR="$HOME/Library/Application Support/ClaudeUsageBar"
rm -rf "$APPDIR"
security delete-generic-password -s "ClaudeUsageBar-credentials" >/dev/null 2>&1 || true
echo "✅ Désinstallé (SwiftBar reste en place : brew uninstall --cask swiftbar pour le retirer)."
