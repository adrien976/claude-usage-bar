# Claude Usage Bar - version Windows (BETA)

> ⚠️ **Version bêta, non encore testée sur une vraie machine Windows.**
> Le cœur (autorisation Claude + récupération des données) est identique à la
> version macOS. Retours et corrections bienvenus via les *issues* GitHub !

Affiche tes limites d'utilisation Claude (session 5 h, semaine, par modèle comme
Fable) dans la **zone de notification** de Windows (en bas à droite, près de
l'horloge).

## Installation

1. Télécharge ce dossier `windows/` (ou tout le dépôt).
2. Double-clique sur **`Installer-Claude-Usage-Bar.bat`**.
   - Il installe Python si besoin (via winget), les composants nécessaires,
     copie l'app et la configure au démarrage de Windows.
   - Windows peut afficher un avertissement SmartScreen : clique sur
     « Informations complémentaires » puis « Exécuter quand même ».
3. Une fenêtre s'ouvre : clique sur **Autoriser** dans le navigateur, copie le
   code affiché et colle-le dans la petite fenêtre. Terminé.

L'icône apparaît alors dans la zone de notification. **Clic droit** dessus pour
voir le détail, actualiser, ouvrir la page d'utilisation ou te reconnecter.

## Fonctionnement

- Icône colorée avec le pourcentage le plus critique (verte < 75 %, orange
  ≥ 75 %, rouge ≥ 90 %) ; détail complet au survol et dans le menu clic droit.
- Jeton OAuth stocké dans le **Gestionnaire d'identifiants Windows**, renouvelé
  automatiquement : jamais déconnecté.
- Mise à jour toutes les 2 minutes.

## Installation manuelle (développeurs)

```bat
pip install -r requirements.txt
pythonw claude_usage_tray.pyw
```

## Limites connues

- Non testée : des ajustements sont probables (police d'icône, chemin de
  `pythonw`, comportement de winget selon la version de Windows).
- L'app tourne avec Python (pas encore de `.exe` autonome) : Python doit rester
  installé. Un packaging PyInstaller pourra venir plus tard.
