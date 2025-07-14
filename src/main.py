# src/main.py
import sys
import os
import json
from functools import partial
from PySide6.QtGui import QActionGroup
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QHeaderView, QMessageBox, QPushButton, QLineEdit, QLabel
)

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
        self.current_feature_index = -1
        
        self.model = GeoJsonTableModel()
        self.button_delegate = ButtonDelegate(self)
        self.ui.table_view.setModel(self.model)
        self.ui.table_view.setItemDelegateForColumn(0, self.button_delegate)
        
        self.setup_view_switcher()
        self.connect_signals()
        self.load_app_config()

    def setup_view_switcher(self):
        self.view_action_group = QActionGroup(self)
        self.view_action_group.addAction(self.ui.actionViewTable)
        self.view_action_group.addAction(self.ui.actionViewForm)
        self.view_action_group.setExclusive(True)
        self.ui.actionViewTable.setChecked(True)

    def connect_signals(self):
        # LA LIGNE FAUTIVE A ÉTÉ SUPPRIMÉE ICI.
        
        self.ui.add_button.clicked.connect(self.add_row)
        self.model.dataChanged.connect(self.mark_as_unsaved)
        self.button_delegate.delete_row_requested.connect(self.handle_delete_request)
        self.ui.table_view.selectionModel().selectionChanged.connect(self.on_table_selection_changed)
        
        # Fiche
        self.ui.form_prev_button.clicked.connect(self.show_previous_feature)
        self.ui.form_next_button.clicked.connect(self.show_next_feature)

        # Menus et barre d'outils
        self.view_action_group.triggered.connect(self.on_view_mode_changed)
        self.ui.actionAccueil.triggered.connect(self.show_welcome_view)
        self.ui.actionEnregistrer.triggered.connect(self.save_data)
        self.ui.actionQuitter.triggered.connect(self.close)
        self.ui.actionConfigurer.triggered.connect(self.open_config_dialog)
        self.ui.actionAPropos.triggered.connect(self.show_about_dialog)

    # --- LA MÉTHODE load_selected_file_data A ÉTÉ SUPPRIMÉE CAR INUTILE ---

    # --- LE RESTE DU FICHIER EST IDENTIQUE À LA VERSION PRÉCÉDENTE ---
    def on_view_mode_changed(self, action):
        if action == self.ui.actionViewTable: self.ui.editor_stacked_widget.setCurrentIndex(0)
        else: self.ui.editor_stacked_widget.setCurrentIndex(1); self.update_form_view(self.current_feature_index)
    def on_table_selection_changed(self, selected, deselected):
        indexes = selected.indexes()
        if indexes: self.update_form_view(indexes[0].row())
    def update_form_view(self, row_index):
        if not (0 <= row_index < self.model.rowCount()):
            while self.ui.form_layout.count(): self.ui.form_layout.takeAt(0).widget().deleteLater()
            return
        self.current_feature_index = row_index
        while self.ui.form_layout.count():
            item = self.ui.form_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        properties = self.model.get_all_features()[row_index].get('properties', {})
        for key, value in properties.items():
            label, editor = QLabel(key), QLineEdit(str(value))
            editor.textChanged.connect(partial(self.on_form_field_changed, row_index, key))
            self.ui.form_layout.addRow(label, editor)
        total_rows = self.model.rowCount()
        self.ui.form_nav_label.setText(f"Fiche {row_index + 1} / {total_rows}")
        self.ui.form_prev_button.setEnabled(row_index > 0)
        self.ui.form_next_button.setEnabled(row_index < total_rows - 1)
    def on_form_field_changed(self, row, key, text):
        try:
            col = self.model._headers.index(key)
            self.model.setData(self.model.index(row, col + 1), text, Qt.ItemDataRole.EditRole)
        except ValueError: pass
    def show_previous_feature(self):
        if self.current_feature_index > 0: self.ui.table_view.selectRow(self.current_feature_index - 1)
    def show_next_feature(self):
        if self.current_feature_index < self.model.rowCount() - 1: self.ui.table_view.selectRow(self.current_feature_index + 1)
    def on_data_source_selected(self, file_path_relative):
        if not self.git_handler or not self.git_handler.repo: return
        file_path_absolute = os.path.join(self.config["LOCAL_REPO_PATH"], file_path_relative)
        file_name = next((f['name'] for f in self.config['FILES'] if f['path'] == file_path_relative), "Fichier")
        try:
            with open(file_path_absolute, 'r', encoding='utf-8') as f: geojson_data = json.load(f)
            self.model.load_data(geojson_data)
            self.ui.editor_title_label.setText(f"<h2>{file_name}</h2>")
            self.ui.table_view.setColumnWidth(0, 50)
            self.ui.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            for i in range(1, self.model.columnCount()): self.ui.table_view.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            self.ui.status_label.setText(f"Fichier '{file_name}' chargé.")
            self.unsaved_changes = False
            self.setWindowTitle(self.base_title)
            if self.model.rowCount() > 0: self.ui.table_view.selectRow(0)
            else: self.update_form_view(-1)
            self.show_editor_view()
        except Exception as e: QMessageBox.critical(self, "Erreur de chargement", str(e)); self.model.load_data({})
    def show_welcome_view(self): self.ui.main_stacked_widget.setCurrentIndex(0); self.ui.actionEnregistrer.setEnabled(False); self.ui.actionAccueil.setEnabled(False); self.ui.viewToolBar.setVisible(False)
    def show_editor_view(self): self.ui.main_stacked_widget.setCurrentIndex(1); self.ui.actionEnregistrer.setEnabled(True); self.ui.actionAccueil.setEnabled(True); self.ui.viewToolBar.setVisible(True)
    def load_app_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f: self.config = json.load(f)
            if all(k in self.config for k in ["REPO_URL", "LOCAL_REPO_PATH", "FILES"]): self.populate_welcome_buttons(); self.initialize_repo(); self.show_welcome_view()
            else: raise FileNotFoundError
        except (FileNotFoundError, json.JSONDecodeError): QMessageBox.warning(self, "Configuration Requise", "Bienvenue ! La configuration est manquante ou invalide.\n\nVeuillez utiliser le menu 'Édition > Configuration...' pour commencer."); self.show_welcome_view()
    def populate_welcome_buttons(self):
        while self.ui.welcome_buttons_layout.count():
            child = self.ui.welcome_buttons_layout.takeAt(0);
            if child.widget(): child.widget().deleteLater()
        for file_info in self.config.get("FILES", []):
            button = QPushButton(f"Modifier : {file_info['name']}"); button.setMinimumHeight(40); button.setStyleSheet("font-size: 16px;"); button.clicked.connect(partial(self.on_data_source_selected, file_info['path'])); self.ui.welcome_buttons_layout.addWidget(button)
    def initialize_repo(self):
        self.git_handler = GitHandler(self.config["LOCAL_REPO_PATH"])
        if not self.git_handler.repo:
            reply = QMessageBox.question(self, "Dépôt non trouvé", f"Le dépôt local n'existe pas.\nVoulez-vous le cloner maintenant ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes: self.ui.status_label.setText(f"Clonage du dépôt..."); QApplication.processEvents(); result = self.git_handler.clone(self.config["REPO_URL"], self.config["GITHUB_USERNAME"], self.config["GITHUB_TOKEN"]); self.ui.status_label.setText("Dépôt cloné avec succès." if result is True else "Échec du clonage.")
    def open_config_dialog(self):
        dialog = ConfigDialog(self);
        if dialog.exec(): self.config = dialog.get_config(); save_config(self.config); QMessageBox.information(self, "Configuration Enregistrée", "La configuration a été mise à jour."); self.load_app_config()
    def save_data(self):
        if not self.unsaved_changes: self.ui.status_label.setText("Aucune modification à enregistrer."); return
        file_path_relative = next((f['path'] for f in self.config['FILES'] if f['name'] == self.ui.editor_title_label.text().replace("<h2>","").replace("</h2>","")), None)
        if not file_path_relative: QMessageBox.critical(self, "Erreur", "Impossible de retrouver le chemin du fichier actuel."); return
        absolute_path = os.path.join(self.config["LOCAL_REPO_PATH"], file_path_relative)
        new_geojson_data = self.model.get_base_struct()
        new_geojson_data['features'] = self.model.get_all_features()
        with open(absolute_path, 'w', encoding='utf-8') as f: json.dump(new_geojson_data, f, indent=2, ensure_ascii=False)
        self.ui.status_label.setText("Envoi vers GitHub..."); QApplication.processEvents()
        result = self.git_handler.commit_and_push(file_path_relative, f"Mise à jour de {file_path_relative} via l'éditeur")
        if result is True: QMessageBox.information(self, "Succès", "Modifications poussées sur GitHub !"); self.unsaved_changes = False; self.setWindowTitle(self.base_title); self.ui.status_label.setText("Prêt.")
        else: QMessageBox.critical(self, "Erreur Git", str(result)); self.ui.status_label.setText("Échec de l'envoi.")
    def mark_as_unsaved(self):
        if not self.unsaved_changes: self.unsaved_changes = True; self.setWindowTitle(self.base_title + " *"); self.ui.status_label.setText("Modifications non enregistrées.")
    def add_row(self):
        if self.model.insert_row(): self.mark_as_unsaved(); self.ui.status_label.setText("Nouvelle ligne ajoutée."); self.ui.table_view.scrollToBottom()
    def handle_delete_request(self, row):
        if 0 <= row < self.model.rowCount(): self.model.remove_rows([row]); self.mark_as_unsaved(); self.ui.status_label.setText(f"Ligne {row + 1} supprimée.")
    def show_about_dialog(self): QMessageBox.about(self, "À propos de l'Éditeur GeoJSON", "<b>Éditeur GeoJSON</b>")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())