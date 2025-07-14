# src/main.py
import sys
import os
import json
from functools import partial
from PySide6.QtWidgets import QApplication, QMainWindow, QHeaderView, QMessageBox, QPushButton

from ui_main_window import Ui_MainWindow
from models import GeoJsonTableModel
from widgets import ButtonDelegate
from config_dialog import ConfigDialog, save_config, CONFIG_FILE
from git_handler import GitHandler

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.base_title = self.windowTitle()
        self.unsaved_changes = False
        self.config = {}
        self.git_handler = None
        
        self.model = GeoJsonTableModel()
        self.button_delegate = ButtonDelegate(self)
        self.ui.table_view.setModel(self.model)
        self.ui.table_view.setItemDelegateForColumn(0, self.button_delegate)

        self.connect_signals()
        self.load_app_config()

    def connect_signals(self):
        """Connecte les signaux de l'UI à la logique de cette classe."""
        # LA LIGNE FAUTIVE A ÉTÉ SUPPRIMÉE ICI
        
        self.ui.file_selector.currentIndexChanged.connect(self.load_selected_file_data)
        self.ui.add_button.clicked.connect(self.add_row)
        self.model.dataChanged.connect(self.mark_as_unsaved)
        self.button_delegate.delete_row_requested.connect(self.handle_delete_request)
        
        # Actions de la barre de menus
        self.ui.actionAccueil.triggered.connect(self.show_welcome_view)
        self.ui.actionEnregistrer.triggered.connect(self.save_data)
        self.ui.actionQuitter.triggered.connect(self.close)
        self.ui.actionConfigurer.triggered.connect(self.open_config_dialog)
        self.ui.actionAPropos.triggered.connect(self.show_about_dialog)

    # --- LE RESTE DU FICHIER EST IDENTIQUE ---

    def show_welcome_view(self):
        self.ui.stacked_widget.setCurrentIndex(0)
        self.ui.actionEnregistrer.setEnabled(False)
        self.ui.actionAccueil.setEnabled(False)

    def show_editor_view(self):
        self.ui.stacked_widget.setCurrentIndex(1)
        self.ui.actionEnregistrer.setEnabled(True)
        self.ui.actionAccueil.setEnabled(True)

    def load_app_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                self.config = json.load(f)
            
            if all(k in self.config for k in ["REPO_URL", "LOCAL_REPO_PATH", "FILES"]):
                self.populate_file_selector()
                self.populate_welcome_buttons()
                self.initialize_repo()
                self.show_welcome_view()
            else:
                raise FileNotFoundError
        except (FileNotFoundError, json.JSONDecodeError):
            self.ui.status_label.setText("Configuration manquante ou invalide.")
            QMessageBox.warning(
                self, 
                "Configuration Requise",
                "Bienvenue ! La configuration de l'application est manquante ou invalide.\n\n"
                "Veuillez utiliser le menu 'Édition > Configuration...' pour commencer."
            )
            self.show_welcome_view()

    def populate_welcome_buttons(self):
        while self.ui.welcome_buttons_layout.count():
            child = self.ui.welcome_buttons_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        for file_info in self.config.get("FILES", []):
            button = QPushButton(f"Modifier : {file_info['name']}")
            button.setMinimumHeight(40)
            button.setStyleSheet("font-size: 16px;")
            button.clicked.connect(partial(self.on_data_source_selected, file_info['path']))
            self.ui.welcome_buttons_layout.addWidget(button)

    def on_data_source_selected(self, file_path_relative):
        index = self.ui.file_selector.findData(file_path_relative)
        if index != -1:
            self.ui.file_selector.setCurrentIndex(index)
            self.show_editor_view()
        else:
            QMessageBox.critical(self, "Erreur", f"Impossible de trouver le fichier '{file_path_relative}' dans la configuration.")

    def initialize_repo(self):
        local_path = self.config["LOCAL_REPO_PATH"]
        self.git_handler = GitHandler(local_path)

        if not self.git_handler.repo:
            reply = QMessageBox.question(self, "Dépôt non trouvé", 
                f"Le dépôt local n'existe pas à l'emplacement:\n{local_path}\n\nVoulez-vous le cloner maintenant ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.ui.status_label.setText(f"Clonage du dépôt...")
                QApplication.processEvents()
                result = self.git_handler.clone(
                    self.config["REPO_URL"],
                    self.config["GITHUB_USERNAME"],
                    self.config["GITHUB_TOKEN"]
                )
                if result is not True:
                    QMessageBox.critical(self, "Erreur de Clonage", str(result))
                    self.ui.status_label.setText("Échec du clonage.")
                else:
                    self.ui.status_label.setText("Dépôt cloné avec succès.")
            else:
                self.ui.status_label.setText("Opération de clonage annulée.")
    
    def open_config_dialog(self):
        dialog = ConfigDialog(self)
        if dialog.exec():
            self.config = dialog.get_config()
            save_config(self.config)
            QMessageBox.information(self, "Configuration Enregistrée", "La configuration a été mise à jour. L'application va se recharger.")
            self.load_app_config()

    def show_about_dialog(self): QMessageBox.about(self, "À propos de l'Éditeur GeoJSON", "<b>Éditeur de Données GeoJSON v1.0</b><br>" "Une application de bureau pour éditer et synchroniser " "des fichiers GeoJSON avec un dépôt GitHub.<br><br>" "Développé pour simplifier la mise à jour des données géographiques.")
    def populate_file_selector(self): self.ui.file_selector.blockSignals(True); self.ui.file_selector.clear(); [self.ui.file_selector.addItem(f["name"], userData=f["path"]) for f in self.config.get("FILES", [])]; self.ui.file_selector.blockSignals(False)
    def load_selected_file_data(self, index=None):
        if not self.git_handler or not self.git_handler.repo: self.show_welcome_view(); return
        file_path_relative = self.ui.file_selector.currentData()
        if not file_path_relative: return
        file_path_absolute = os.path.join(self.config["LOCAL_REPO_PATH"], file_path_relative)
        try:
            with open(file_path_absolute, 'r', encoding='utf-8') as f: geojson_data = json.load(f)
            self.model.load_data(geojson_data)
            self.ui.table_view.setColumnWidth(0, 50)
            self.ui.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            for i in range(1, self.model.columnCount()):
                 self.ui.table_view.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            self.ui.status_label.setText(f"Fichier '{self.ui.file_selector.currentText()}' chargé.")
            self.unsaved_changes = False
            self.setWindowTitle(self.base_title)
        except Exception as e: self.ui.status_label.setText(f"Erreur de chargement : {e}"); self.model.load_data({})
    def save_data(self):
        if not self.unsaved_changes: self.ui.status_label.setText("Aucune modification à enregistrer."); return
        if not self.git_handler or not self.git_handler.repo: QMessageBox.warning(self, "Erreur", "Le dépôt Git n'est pas configuré."); return
        relative_path = self.ui.file_selector.currentData()
        absolute_path = os.path.join(self.config["LOCAL_REPO_PATH"], relative_path)
        new_geojson_data = self.model.get_base_struct()
        new_geojson_data['features'] = self.model.get_all_features()
        with open(absolute_path, 'w', encoding='utf-8') as f: json.dump(new_geojson_data, f, indent=2, ensure_ascii=False)
        self.ui.status_label.setText("Envoi vers GitHub..."); QApplication.processEvents()
        commit_message = f"Mise à jour de {relative_path} via l'éditeur"
        result = self.git_handler.commit_and_push(relative_path, commit_message)
        if result is True: QMessageBox.information(self, "Succès", "Modifications poussées sur GitHub !"); self.unsaved_changes = False; self.setWindowTitle(self.base_title); self.ui.status_label.setText("Prêt.")
        else: QMessageBox.critical(self, "Erreur Git", str(result)); self.ui.status_label.setText("Échec de l'envoi.")
    def mark_as_unsaved(self):
        if not self.unsaved_changes: self.unsaved_changes = True; self.setWindowTitle(self.base_title + " *"); self.ui.status_label.setText("Modifications non enregistrées.")
    def add_row(self):
        if self.model.insert_row(): self.mark_as_unsaved(); self.ui.status_label.setText("Nouvelle ligne ajoutée."); self.ui.table_view.scrollToBottom()
    def handle_delete_request(self, row):
        if 0 <= row < self.model.rowCount(): self.model.remove_rows([row]); self.mark_as_unsaved(); self.ui.status_label.setText(f"Ligne {row + 1} supprimée.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())