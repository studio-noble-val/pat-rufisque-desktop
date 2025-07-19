# src/main.py
import sys
import os
import json
from functools import partial

from PySide6.QtCore import Qt, QObject, Signal, QThread, QSize
from PySide6.QtGui import QActionGroup, QCursor, QIcon
from PySide6.QtWidgets import (QApplication, QMainWindow, QHeaderView, QMessageBox,
                               QPushButton, QLineEdit, QLabel, QProgressDialog,
                               QHBoxLayout, QSpacerItem, QSizePolicy, QWidget)

from logging_setup import logger
from ui_main_window import Ui_MainWindow
from models import GeoJsonTableModel
from widgets import ButtonDelegate
from config_dialog import ConfigDialog, save_config, CONFIG_FILE
from git_handler import GitHandler

# --- CLASSE WORKER (INCHANGÉE) ---
class GitCloneWorker(QObject):
    finished = Signal(bool, str)
    progress = Signal(int, str)
    def __init__(self, config):
        super().__init__()
        self.config = config
        self._is_cancelled = False
    def run(self):
        try:
            git_handler = GitHandler(self.config["LOCAL_REPO_PATH"])
            clone_result = git_handler.clone(self.config["REPO_URL"], self.config.get("GITHUB_USERNAME", ""), self.config.get("GITHUB_TOKEN", ""), progress_callback=self.progress.emit)
            if self._is_cancelled: self.finished.emit(False, "Clonage annulé par l'utilisateur."); return
            if clone_result is True: self.finished.emit(True, "Le dépôt a été cloné avec succès.")
            else: self.finished.emit(False, str(clone_result))
        except Exception as e:
            logger.error(f"Erreur inattendue dans le worker de clonage : {e}", exc_info=True)
            if not self._is_cancelled: self.finished.emit(False, f"Erreur inattendue : {e}")
    def cancel(self): self._is_cancelled = True

def get_icon_path(icon_name):
    try:
        base_path = sys._MEIPASS
        return os.path.join(base_path, 'icons', icon_name)
    except Exception:
        base_path = os.path.dirname(__file__)
        return os.path.join(base_path, 'icons', icon_name)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.thread, self.worker = None, None
        self.base_title = self.windowTitle()
        self.unsaved_changes = False
        self.config, self.git_handler = {}, None
        self.current_feature_index = -1
        self.model = GeoJsonTableModel()
        self.button_delegate = ButtonDelegate(self)
        self.ui.table_view.setModel(self.model)
        self.ui.table_view.setItemDelegateForColumn(0, self.button_delegate)
        
        self.session_adds = 0
        self.session_deletes = 0
        self.session_edits = set()
        
        self.reorganize_editor_layout()
        
        self.setup_view_switcher()
        self.connect_signals()
        self.show_welcome_view()
        
    def reorganize_editor_layout(self):
        """Modifie la mise en page de l'éditeur pour ajouter/déplacer les boutons."""
        
        # --- CORRECTION DE LA LOGIQUE DE MANIPULATION DE L'UI ---
        
        # 1. On déplace le titre du fichier (self.ui.editor_title_label)
        # Il est dans le layout principal de la page d'édition. On l'enlève pour le réutiliser.
        self.ui.editor_page.layout().removeWidget(self.ui.editor_title_label)
        
        # 2. On supprime l'ancien bouton "Ajouter une ligne" qui est en bas du tableau
        # On trouve son layout parent (celui de la page de la table) et on le supprime.
        layout_table_page = self.ui.table_view_page.layout()
        layout_table_page.removeWidget(self.ui.add_button)
        self.ui.add_button.deleteLater() # On le supprime définitivement

        # 3. On crée la nouvelle barre du haut (titre + bouton d'ajout)
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.ui.editor_title_label)
        top_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        self.add_row_button = QPushButton(" Ajouter une ligne")
        self.add_row_button.setIcon(QIcon(get_icon_path('add.png')))
        self.add_row_button.setIconSize(QSize(20, 20))
        self.add_row_button.setStyleSheet("padding: 5px;")
        top_layout.addWidget(self.add_row_button)
        
        # 4. On insère cette nouvelle barre en haut du layout de la page d'édition
        self.ui.editor_page.layout().insertLayout(0, top_layout)

        # 5. On crée la nouvelle barre du bas (compteur + bouton de publication)
        bottom_layout = QHBoxLayout()
        self.modifications_label = QLabel("Aucune modification.")
        self.modifications_label.setStyleSheet("font-style: italic; color: grey;")
        bottom_layout.addWidget(self.modifications_label)
        bottom_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        self.publish_button = QPushButton(" Publier sur GitHub")
        self.publish_button.setIcon(QIcon(get_icon_path('git.png')))
        self.publish_button.setIconSize(QSize(24, 24))
        self.publish_button.setMinimumHeight(40)
        self.publish_button.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        bottom_layout.addWidget(self.publish_button)
        
        # 6. On ajoute cette barre en bas du layout de la page d'édition
        self.ui.editor_page.layout().addLayout(bottom_layout)


    def connect_signals(self):
        self.ui.table_view.clicked.connect(self.on_table_clicked)
        self.ui.welcome_config_button.clicked.connect(self.open_config_dialog)
        
        self.model.dataChanged.connect(self.on_data_changed)
        self.add_row_button.clicked.connect(self.add_row)
        self.publish_button.clicked.connect(self.save_data)

        self.ui.table_view.selectionModel().selectionChanged.connect(self.on_table_selection_changed)
        self.ui.form_prev_button.clicked.connect(self.show_previous_feature)
        self.ui.form_next_button.clicked.connect(self.show_next_feature)
        self.view_action_group.triggered.connect(self.on_view_mode_changed)
        self.ui.actionAccueil.triggered.connect(self.show_welcome_view)
        self.ui.actionEnregistrer.triggered.connect(self.save_data)
        self.ui.actionQuitter.triggered.connect(self.close)
        self.ui.actionConfigurer.triggered.connect(self.open_config_dialog)
        self.ui.actionAPropos.triggered.connect(self.show_about_dialog)
        
    def _update_modifications_label(self):
        total_modifs = self.session_adds + self.session_deletes + len(self.session_edits)
        
        if total_modifs == 0:
            self.modifications_label.setText("Aucune modification non publiée.")
            self.modifications_label.setStyleSheet("font-style: italic; color: grey;")
            self.publish_button.setEnabled(False)
        elif total_modifs == 1:
            self.modifications_label.setText("1 modification non publiée.")
            self.modifications_label.setStyleSheet("font-weight: bold; color: #d35400;")
            self.publish_button.setEnabled(True)
        else:
            self.modifications_label.setText(f"{total_modifs} modifications non publiées.")
            self.modifications_label.setStyleSheet("font-weight: bold; color: #d35400;")
            self.publish_button.setEnabled(True)

    def on_data_source_selected(self, file_info):
        self.session_adds = 0
        self.session_deletes = 0
        self.session_edits.clear()
        self._update_modifications_label()
        
        file_path_relative = file_info['path']
        file_name = file_info['name']
        logger.info(f"Chargement de la source de données: {file_name}")
        if not self.git_handler or not self.git_handler.repo:
            QMessageBox.critical(self, "Erreur", "Le dépôt Git n'est pas initialisé.")
            return
        file_path_absolute = os.path.join(self.config["LOCAL_REPO_PATH"], file_path_relative)
        try:
            with open(file_path_absolute, 'r', encoding='utf-8') as f: geojson_data = json.load(f)
            self.model.load_data(geojson_data)
            self.ui.editor_title_label.setText(f"<h2>{file_name}</h2>")
            self.ui.table_view.setColumnWidth(0, 80)
            self.ui.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            for i in range(1, self.model.columnCount()): self.ui.table_view.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            self.ui.status_label.setText(f"Fichier '{file_name}' chargé.")
            self.unsaved_changes = False
            self.setWindowTitle(self.base_title)
            if self.model.rowCount() > 0: self.ui.table_view.selectRow(0)
            else: self.update_form_view(-1)
            self.ui.table_view.viewport().update()
            logger.info("Viewport de la table mis à jour pour forcer le redessin.")
            self.show_editor_view()
        except Exception as e:
            logger.error(f"Erreur de chargement du fichier : {e}", exc_info=True)
            QMessageBox.critical(self, "Erreur de chargement", str(e))
            self.model.load_data({})

    def add_row(self):
        logger.info("Ajout d'une nouvelle ligne demandée.")
        if self.model.insert_row():
            self.mark_as_unsaved()
            self.ui.status_label.setText("Nouvelle ligne ajoutée.")
            self.ui.table_view.scrollToBottom()
            new_row_index = self.model.rowCount() - 1
            self.ui.table_view.viewport().update()
            
            self.session_adds += 1
            self._update_modifications_label()
            
            self.on_edit_request(new_row_index)

    def handle_delete_request(self, row):
        reply = QMessageBox.question(self, 'Confirmation de suppression', f"Êtes-vous sûr de vouloir supprimer la ligne {row + 1} ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            logger.info(f"Suppression confirmée pour la ligne {row}")
            if 0 <= row < self.model.rowCount():
                self.model.remove_rows([row])
                self.mark_as_unsaved()
                self.ui.status_label.setText(f"Ligne {row + 1} supprimée.")
                
                self.session_deletes += 1
                self._update_modifications_label()
                
                self.update_form_view(self.ui.table_view.currentIndex().row())
        else:
            logger.info(f"Suppression annulée pour la ligne {row}")

    def on_data_changed(self, top_left, bottom_right, roles):
        self.mark_as_unsaved()
        for row in range(top_left.row(), bottom_right.row() + 1):
            self.session_edits.add(row)
        self._update_modifications_label()

    def save_data(self):
        total_modifs = self.session_adds + self.session_deletes + len(self.session_edits)
        if total_modifs == 0:
            self.ui.status_label.setText("Aucune modification à publier.")
            return

        file_name = self.ui.editor_title_label.text().replace("<h2>","").replace("</h2>","")
        file_path_relative = next((f['path'] for f in self.config['FILES'] if f['name'] == file_name), None)
        if not file_path_relative:
            QMessageBox.critical(self, "Erreur", "Impossible de retrouver le chemin du fichier actuel.")
            return
        absolute_path = os.path.join(self.config["LOCAL_REPO_PATH"], file_path_relative)
        new_geojson_data = self.model.get_base_struct()
        new_geojson_data['features'] = self.model.get_all_features()
        with open(absolute_path, 'w', encoding='utf-8') as f:
            json.dump(new_geojson_data, f, indent=2, ensure_ascii=False)
        self.ui.status_label.setText("Envoi vers GitHub...")
        QApplication.processEvents()
        result = self.git_handler.commit_and_push(file_path_relative, f"Mise à jour de {file_path_relative} via l'éditeur")
        if result is True:
            QMessageBox.information(self, "Succès", "Modifications poussées sur GitHub !")
            self.unsaved_changes = False
            self.setWindowTitle(self.base_title)
            self.ui.status_label.setText("Prêt.")
            self.session_adds = 0
            self.session_deletes = 0
            self.session_edits.clear()
            self._update_modifications_label()
        else:
            QMessageBox.critical(self, "Erreur Git", str(result))
            self.ui.status_label.setText("Échec de l'envoi.")

    def setup_view_switcher(self):
        self.view_action_group = QActionGroup(self)
        self.view_action_group.addAction(self.ui.actionViewTable)
        self.view_action_group.addAction(self.ui.actionViewForm)
        self.view_action_group.setExclusive(True)
        self.ui.actionViewTable.setChecked(True)

    def on_table_clicked(self, index):
        if index.column() == 0:
            logger.info(f"Clic détecté sur la colonne Actions, ligne {index.row()}")
            rect = self.ui.table_view.visualRect(index)
            pos = self.ui.table_view.viewport().mapFromGlobal(QCursor.pos())
            relative_pos = pos - rect.topLeft()
            if relative_pos.x() < rect.width() / 2:
                logger.info("-> Clic sur le bouton ÉDITER")
                self.on_edit_request(index.row())
            else:
                logger.info("-> Clic sur le bouton SUPPRIMER")
                self.handle_delete_request(index.row())

    def on_edit_request(self, row):
        logger.info(f"Demande d'édition pour la ligne {row}")
        self.ui.table_view.selectRow(row)
        self.ui.actionViewForm.setChecked(True)
        self.ui.editor_stacked_widget.setCurrentIndex(1)
        logger.info(f"Passage à la vue Fiche (index 1)")

    def load_app_config(self):
        try:
            with open(CONFIG_FILE, 'r') as f: self.config = json.load(f)
            repo_path = self.config.get("LOCAL_REPO_PATH")
            if repo_path and os.path.exists(os.path.join(repo_path, '.git')): self.initialize_repo()
            else: self.setup_welcome_for_config("Dépôt local non trouvé. Veuillez le cloner à nouveau via la configuration.")
        except (FileNotFoundError, json.JSONDecodeError):
            self.setup_welcome_for_config("Bienvenue ! Veuillez configurer l'application pour commencer.")

    def initialize_repo(self):
        self.git_handler = GitHandler(self.config["LOCAL_REPO_PATH"])
        connection_result = self.git_handler.test_connection()
        if connection_result is True:
            self.ui.connection_status_label.setText("✅  Connecté au dépôt")
            self.ui.connection_status_label.setStyleSheet("color: green; font-size: 14px; font-weight: bold;")
            self.ui.status_label.setText("Prêt. Sélectionnez un fichier à modifier.")
            self.setup_welcome_for_selection()
        else:
            self.ui.connection_status_label.setText("❌  Échec de la connexion")
            self.ui.connection_status_label.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")
            self.ui.status_label.setText(str(connection_result))
            self.setup_welcome_for_selection()

    def setup_welcome_for_config(self, reason):
        self.ui.connection_status_label.setText("⚪️  Non configuré")
        self.ui.connection_status_label.setStyleSheet("color: grey; font-size: 14px; font-weight: bold;")
        self.ui.status_label.setText(reason)
        self.ui.welcome_stacked_widget.setCurrentIndex(0)

    def setup_welcome_for_selection(self):
        self.populate_welcome_buttons()
        self.ui.welcome_stacked_widget.setCurrentIndex(1)

    def populate_welcome_buttons(self):
        while self.ui.welcome_buttons_layout.count():
            child = self.ui.welcome_buttons_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        for file_info in self.config.get("FILES", []):
            button = QPushButton(f"Modifier : {file_info['name']}")
            button.setMinimumHeight(40)
            button.setStyleSheet("font-size: 16px;")
            button.clicked.connect(partial(self.on_data_source_selected, file_info))
            self.ui.welcome_buttons_layout.addWidget(button)

    def open_config_dialog(self):
        dialog = ConfigDialog(self)
        if dialog.exec():
            self.config = dialog.get_config()
            save_config(self.config)
            QMessageBox.information(self, "Configuration Enregistrée", "La configuration a été enregistrée. Lancement du clonage du dépôt...")
            self.attempt_initial_clone()
    
    def attempt_initial_clone(self):
        self.progress_dialog = QProgressDialog("Préparation du clonage...", "Annuler", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.setWindowTitle("Clonage en cours")
        self.progress_dialog.show()
        self.thread = QThread()
        self.worker = GitCloneWorker(self.config)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_clone_finished)
        self.worker.progress.connect(self.update_clone_progress)
        self.progress_dialog.canceled.connect(self.cancel_clone)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def update_clone_progress(self, percentage, message):
        self.progress_dialog.setValue(percentage)
        self.progress_dialog.setLabelText(message)

    def on_clone_finished(self, success, message):
        self.progress_dialog.close()
        if success:
            QMessageBox.information(self, "Succès", message)
            self.show_welcome_view()
        else:
            QMessageBox.critical(self, "Échec du clonage", message)
            self.setup_welcome_for_config("Échec du clonage. Veuillez vérifier la configuration.")
        self.thread = None
        self.worker = None

    def cancel_clone(self):
        logger.warning("Demande d'annulation du clonage...")
        if self.worker: self.worker.cancel()
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait(1000)
            if self.thread.isRunning(): logger.warning("Le thread ne s'est pas arrêté, forçage de l'arrêt."); self.thread.terminate()
        self.on_clone_finished(False, "Clonage annulé.")

    def on_view_mode_changed(self, action):
        if action == self.ui.actionViewTable:
            logger.info("Passage à la vue Tableau via la barre d'outils.")
            self.ui.editor_stacked_widget.setCurrentIndex(0)
        else:
            logger.info("Passage à la vue Fiche via la barre d'outils.")
            self.ui.editor_stacked_widget.setCurrentIndex(1)
            self.update_form_view(self.current_feature_index)

    def on_table_selection_changed(self, selected, deselected):
        if selected.indexes():
            logger.debug(f"Sélection de la table changée, mise à jour de la fiche pour la ligne {selected.indexes()[0].row()}")
            self.update_form_view(selected.indexes()[0].row())

    def update_form_view(self, row_index):
        self.current_feature_index = row_index
        while self.ui.form_layout.count():
            item = self.ui.form_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        if not (0 <= row_index < self.model.rowCount()): return
        properties = self.model.get_all_features()[row_index].get('properties', {})
        for key, value in properties.items():
            label, editor = QLabel(key), QLineEdit(str(value))
            editor.textChanged.connect(partial(self.on_form_field_changed, row_index, key))
            self.ui.form_layout.addRow(label, editor)
        total = self.model.rowCount()
        self.ui.form_nav_label.setText(f"Fiche {row_index + 1} / {total}")
        self.ui.form_prev_button.setEnabled(row_index > 0)
        self.ui.form_next_button.setEnabled(row_index < total - 1)

    def on_form_field_changed(self, row, key, text):
        try:
            col = self.model._headers.index(key)
            self.model.setData(self.model.index(row, col + 1), text, Qt.ItemDataRole.EditRole)
        except ValueError:
            pass

    def show_previous_feature(self):
        if self.current_feature_index > 0: self.ui.table_view.selectRow(self.current_feature_index - 1)

    def show_next_feature(self):
        if self.current_feature_index < self.model.rowCount() - 1: self.ui.table_view.selectRow(self.current_feature_index + 1)

    def show_welcome_view(self):
        self.ui.main_stacked_widget.setCurrentIndex(0)
        self.ui.actionEnregistrer.setEnabled(False)
        self.ui.actionAccueil.setEnabled(True)
        self.ui.viewToolBar.setVisible(False)
        self.load_app_config()

    def show_editor_view(self):
        self.ui.main_stacked_widget.setCurrentIndex(1)
        self.ui.actionEnregistrer.setEnabled(True)
        self.ui.actionAccueil.setEnabled(True)
        self.ui.viewToolBar.setVisible(True)

    def mark_as_unsaved(self):
        if not self.unsaved_changes:
            self.unsaved_changes = True
            self.setWindowTitle(self.base_title + " *")
            self.ui.status_label.setText("Modifications non enregistrées.")

    def show_about_dialog(self):
        QMessageBox.about(self, "À propos de l'Éditeur GeoJSON", "<b>Éditeur GeoJSON</b>")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())