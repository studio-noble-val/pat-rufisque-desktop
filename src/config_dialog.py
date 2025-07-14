# src/config_dialog.py
import json
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QDialogButtonBox, QLabel, QFileDialog
)
from PySide6.QtCore import Qt

# --- DÉBUT DE LA MODIFICATION ---

# Définir un nom pour le dossier de configuration de notre application
APP_NAME = "EditeurGeoJSON"

# Construire un chemin qui fonctionne sur tous les systèmes d'exploitation (Windows, macOS, Linux)
# os.path.expanduser("~") récupère le dossier personnel de l'utilisateur (ex: C:\Users\VotreNom)
CONFIG_DIR = os.path.join(os.path.expanduser("~"), f".{APP_NAME}")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# S'assurer que le dossier de configuration existe avant de lire ou écrire dedans
os.makedirs(CONFIG_DIR, exist_ok=True)

# --- FIN DE LA MODIFICATION ---


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration de l'accès GitHub")

        # Widgets du formulaire
        self.repo_url_edit = QLineEdit()
        self.local_path_edit = QLineEdit()
        self.browse_button = QPushButton("Parcourir...")
        self.username_edit = QLineEdit()
        self.token_edit = QLineEdit()
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)

        # Layout pour le chemin local avec le bouton parcourir
        local_path_layout = QVBoxLayout()
        local_path_layout.setContentsMargins(0,0,0,0)
        local_path_layout.addWidget(self.local_path_edit)
        local_path_layout.addWidget(self.browse_button, 0, Qt.AlignmentFlag.AlignRight)

        # Layout principal du formulaire
        layout = QFormLayout(self)
        layout.addRow(QLabel("Veuillez entrer les informations de votre dépôt GitHub."))
        layout.addRow("URL du dépôt (HTTPS):", self.repo_url_edit)
        layout.addRow("Dossier local pour le dépôt:", local_path_layout)
        layout.addRow("Nom d'utilisateur GitHub:", self.username_edit)
        layout.addRow("Personal Access Token (PAT):", self.token_edit)

        # Boutons OK et Annuler
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addRow(self.button_box)

        # Connexions
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.browse_button.clicked.connect(self.browse_local_path)

        self.load_config()

    def browse_local_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Choisir un dossier pour le dépôt local")
        if directory:
            self.local_path_edit.setText(directory)

    def load_config(self):
        try:
            # On utilise maintenant la variable globale CONFIG_FILE qui contient le chemin complet
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            self.repo_url_edit.setText(config.get("REPO_URL", ""))
            # On propose un dossier par défaut dans le dossier de l'utilisateur
            default_repo_path = os.path.join(os.path.expanduser("~"), "geojson_editor_repo")
            self.local_path_edit.setText(config.get("LOCAL_REPO_PATH", default_repo_path))
            self.username_edit.setText(config.get("GITHUB_USERNAME", ""))
            self.token_edit.setText(config.get("GITHUB_TOKEN", ""))
        except FileNotFoundError:
            # Si le fichier n'existe pas, on propose un chemin par défaut
            default_repo_path = os.path.join(os.path.expanduser("~"), "geojson_editor_repo")
            self.local_path_edit.setText(default_repo_path)
            print(f"Fichier de configuration non trouvé à l'emplacement '{CONFIG_FILE}'. Utilisation des valeurs par défaut.")
    
    def get_config(self):
        return {
            "REPO_URL": self.repo_url_edit.text(),
            "LOCAL_REPO_PATH": self.local_path_edit.text(),
            "GITHUB_USERNAME": self.username_edit.text(),
            "GITHUB_TOKEN": self.token_edit.text(),
            "FILES": [ 
                {"name": "Cantines Scolaires", "path": "mviewer/apps/public/cantines/cantines_scolaires.geojson"},
                {"name": "Cuisines Centrales", "path": "mviewer/apps/public/cantines/cuisine_centrale.geojson"},
                {"name": "Fournisseurs", "path": "mviewer/apps/public/gouvernance/fournisseurs.geojson"}
            ]
        }

def save_config(config):
    # On utilise maintenant la variable globale CONFIG_FILE qui contient le chemin complet
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)