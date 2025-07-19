import sys
import os
from functools import partial

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QActionGroup, QCursor, QIcon, QIntValidator
from PySide6.QtWidgets import (QApplication, QMainWindow, QHeaderView, QMessageBox,
                               QPushButton, QLineEdit, QLabel, QProgressDialog,
                               QHBoxLayout, QSpacerItem, QSizePolicy, QWidget)

from logging_setup import logger
from ui_main_window import Ui_MainWindow
from widgets import ButtonDelegate
from config_dialog import ConfigDialog
from controller import AppController

def get_icon_path(icon_name):
    """ Trouve le chemin d'une icône, compatible dev et PyInstaller. """
    try:
        base_path = sys._MEIPASS
        return os.path.join(base_path, 'icons', icon_name)
    except Exception:
        base_path = os.path.dirname(__file__)
        return os.path.join(base_path, 'icons', icon_name)

class MainWindow(QMainWindow):
    """
    La Vue principale de l'application. Elle affiche les données fournies par le contrôleur
    et lui transmet les actions de l'utilisateur.
    """
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.controller = AppController()

        self.base_title = self.windowTitle()
        self.current_feature_index = -1
        self.button_delegate = ButtonDelegate(self)
        
        self.ui.table_view.setModel(self.controller.model)
        self.ui.table_view.setItemDelegateForColumn(0, self.button_delegate)
        
        self.reorganize_editor_layout()
        self.setup_view_switcher()
        self.connect_signals()
        self.connect_controller_signals()
        
        self.show_welcome_view()
        self.controller.load_configuration()
        
    def reorganize_editor_layout(self):
        """Modifie la disposition de la page d'édition après sa création par setupUi."""
        self.ui.editor_page.layout().removeWidget(self.ui.editor_title_label)
        self.ui.table_view_page.layout().removeWidget(self.ui.add_button)
        self.ui.add_button.deleteLater()
        
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.ui.editor_title_label)
        top_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.add_row_button = QPushButton(" Ajouter une ligne"); self.add_row_button.setIcon(QIcon(get_icon_path('add.png'))); self.add_row_button.setIconSize(QSize(20, 20)); self.add_row_button.setStyleSheet("padding: 5px;"); top_layout.addWidget(self.add_row_button)
        self.ui.editor_page.layout().insertLayout(0, top_layout)
        
        bottom_layout = QHBoxLayout()
        self.modifications_label = QLabel("Aucune modification."); self.modifications_label.setStyleSheet("font-style: italic; color: grey;"); bottom_layout.addWidget(self.modifications_label)
        bottom_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.revert_button = QPushButton(" Annuler"); self.revert_button.setIcon(QIcon(get_icon_path('undo.png'))); self.revert_button.setIconSize(QSize(20, 20)); self.revert_button.setStyleSheet("padding: 5px;"); bottom_layout.addWidget(self.revert_button)
        self.publish_button = QPushButton(" Publier sur GitHub"); self.publish_button.setIcon(QIcon(get_icon_path('git.png'))); self.publish_button.setIconSize(QSize(24, 24)); self.publish_button.setMinimumHeight(40); self.publish_button.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;"); bottom_layout.addWidget(self.publish_button)
        self.ui.editor_page.layout().addLayout(bottom_layout)

    def connect_signals(self):
        """Connecte les signaux de l'UI aux slots qui notifieront le contrôleur."""
        self.ui.welcome_config_button.clicked.connect(self.open_config_dialog)
        self.add_row_button.clicked.connect(self.on_add_row_requested)
        self.publish_button.clicked.connect(self.publish_changes)
        self.revert_button.clicked.connect(self.revert_changes)
        
        self.ui.table_view.clicked.connect(self.on_table_clicked)
        self.ui.table_view.selectionModel().selectionChanged.connect(self.on_table_selection_changed)
        self.ui.form_prev_button.clicked.connect(self.show_previous_feature)
        self.ui.form_next_button.clicked.connect(self.show_next_feature)
        self.view_action_group.triggered.connect(self.on_view_mode_changed)
        self.ui.actionAccueil.triggered.connect(self.on_home_action)
        self.ui.actionEnregistrer.triggered.connect(self.publish_changes)
        self.ui.actionQuitter.triggered.connect(self.close)
        self.ui.actionConfigurer.triggered.connect(self.open_config_dialog)
        self.ui.actionAPropos.triggered.connect(self.show_about_dialog)

    def connect_controller_signals(self):
        """Connecte les signaux du contrôleur aux slots de la Vue pour mettre à jour l'UI."""
        self.controller.config_state_changed.connect(self.on_config_state_changed)
        self.controller.connection_status_changed.connect(self.on_connection_status_changed)
        self.controller.clone_started.connect(self.on_clone_started)
        self.controller.clone_progress.connect(self.on_clone_progress)
        self.controller.clone_finished.connect(self.on_clone_finished)
        self.controller.publish_finished.connect(self.on_publish_finished)
        self.controller.data_loaded_and_ready.connect(self.on_data_loaded)
        self.controller.modifications_updated.connect(self.update_modifications_label)
        self.controller.status_message_changed.connect(self.ui.status_label.setText)
        self.controller.view_change_requested.connect(self.on_view_change_requested)

    # --- SLOTS RÉPONDANT AUX SIGNAUX DU CONTRÔLEUR ---

    def on_config_state_changed(self, repo_exists, reason):
        if self.controller.config and repo_exists:
            self.setup_welcome_for_selection()
        else:
            self.setup_welcome_for_config(reason)
        self.ui.status_label.setText(reason)

    def on_connection_status_changed(self, success, message):
        if success:
            self.ui.connection_status_label.setText("✅  Connecté au dépôt"); self.ui.connection_status_label.setStyleSheet("color: green; font-size: 14px; font-weight: bold;")
        else:
            self.ui.connection_status_label.setText("❌  Échec de la connexion"); self.ui.connection_status_label.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")
        self.ui.status_label.setText(message)

    def on_clone_started(self):
        self.progress_dialog = QProgressDialog("Préparation du clonage...", "Annuler", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.canceled.connect(self.controller.cancel_clone)
        self.progress_dialog.show()

    def on_clone_progress(self, percentage, message):
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.setValue(percentage); self.progress_dialog.setLabelText(message)

    def on_clone_finished(self, success, message):
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
        if success and message: QMessageBox.information(self, "Succès", message)
        elif not success: QMessageBox.critical(self, "Échec", message)

    def on_publish_finished(self, success, message):
        self.ui.status_label.setText(message)
        if success and message:
            QMessageBox.information(self, "Succès", message)
        elif not success:
            QMessageBox.critical(self, "Erreur Git", message)
        self.publish_button.setEnabled(True)

    def on_data_loaded(self, file_name):
        self.ui.editor_title_label.setText(f"<h2>{file_name}</h2>")
        self.ui.table_view.setColumnWidth(0, 80)
        self.ui.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        model = self.controller.model
        for i in range(1, model.columnCount()):
            self.ui.table_view.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        
        if model.rowCount() > 0: self.ui.table_view.selectRow(0)
        else: self.update_form_view(-1)

    def update_modifications_label(self, total, has_changes):
        self.publish_button.setEnabled(has_changes)
        self.revert_button.setEnabled(has_changes)
        self.setWindowTitle(self.base_title + (" *" if has_changes else ""))
        
        if not has_changes: self.modifications_label.setText("Aucune modification non publiée."); self.modifications_label.setStyleSheet("font-style: italic; color: grey;")
        elif total == 1: self.modifications_label.setText("1 modification non publiée."); self.modifications_label.setStyleSheet("font-weight: bold; color: #d35400;")
        else: self.modifications_label.setText(f"{total} modifications non publiées."); self.modifications_label.setStyleSheet("font-weight: bold; color: #d35400;")

    def on_view_change_requested(self, view_name):
        if view_name == 'editor': self.show_editor_view()
        elif view_name == 'welcome': self.show_welcome_view()

    # --- SLOTS RÉPONDANT AUX ACTIONS DE L'UTILISATEUR ---

    def open_config_dialog(self):
        dialog = ConfigDialog(self, self.controller.config)
        if dialog.exec():
            config = dialog.get_config()
            QMessageBox.information(self, "Configuration", "Configuration enregistrée. Lancement des opérations...")
            self.controller.save_configuration_and_clone(config)
    
    def on_home_action(self):
        self.show_welcome_view()
        self.controller.load_configuration()
        
    def publish_changes(self):
        self.publish_button.setEnabled(False)
        self.controller.publish_changes()

    def revert_changes(self):
        reply = QMessageBox.question(self, "Annuler", "Voulez-vous vraiment annuler toutes les modifications ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes: self.controller.revert_changes()
        
    def handle_delete_request(self, row):
        reply = QMessageBox.question(self, 'Suppression', f"Supprimer la ligne {row + 1} ?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.controller.delete_row(row)
            self.update_form_view(self.ui.table_view.currentIndex().row())
            
    def on_add_row_requested(self):
        self.controller.add_row()
        self.ui.table_view.scrollToBottom()
        self.on_edit_request(self.controller.model.rowCount() - 1)

    # --- MÉTHODES DE GESTION PURE DE L'UI ---
    
    def setup_welcome_for_config(self, reason):
        self.ui.connection_status_label.setText("⚪️  Non configuré"); self.ui.connection_status_label.setStyleSheet("color: grey; font-size: 14px; font-weight: bold;")
        self.ui.status_label.setText(reason); self.ui.welcome_stacked_widget.setCurrentIndex(0)

    def setup_welcome_for_selection(self):
        self.populate_welcome_buttons(); self.ui.welcome_stacked_widget.setCurrentIndex(1)

    def populate_welcome_buttons(self):
        layout = self.ui.welcome_buttons_layout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        for file_info in self.controller.config.get("FILES", []):
            button = QPushButton(f"Modifier : {file_info['name']}"); button.setMinimumHeight(40); button.setStyleSheet("font-size: 16px;"); button.clicked.connect(partial(self.controller.select_data_source, file_info)); layout.addWidget(button)

    def show_welcome_view(self):
        self.ui.main_stacked_widget.setCurrentIndex(0); self.ui.actionEnregistrer.setEnabled(False); self.ui.viewToolBar.setVisible(False)

    def show_editor_view(self):
        self.ui.main_stacked_widget.setCurrentIndex(1); self.ui.actionEnregistrer.setEnabled(True); self.ui.viewToolBar.setVisible(True)
        
    def setup_view_switcher(self):
        self.view_action_group = QActionGroup(self); self.view_action_group.addAction(self.ui.actionViewTable); self.view_action_group.addAction(self.ui.actionViewForm); self.view_action_group.setExclusive(True); self.ui.actionViewTable.setChecked(True)

    def on_table_clicked(self, index):
        if index.column() == 0:
            rect = self.ui.table_view.visualRect(index); pos = self.ui.table_view.viewport().mapFromGlobal(QCursor.pos()); relative_pos = pos - rect.topLeft()
            if relative_pos.x() < rect.width() / 2: self.on_edit_request(index.row())
            else: self.handle_delete_request(index.row())
            
    def on_edit_request(self, row):
        self.ui.table_view.selectRow(row); self.ui.actionViewForm.setChecked(True); self.ui.editor_stacked_widget.setCurrentIndex(1)
        
    def on_view_mode_changed(self, action):
        if action == self.ui.actionViewTable: self.ui.editor_stacked_widget.setCurrentIndex(0)
        else: self.ui.editor_stacked_widget.setCurrentIndex(1); self.update_form_view(self.current_feature_index)
        
    def on_table_selection_changed(self, selected, deselected):
        if selected.indexes(): self.update_form_view(selected.indexes()[0].row())
        
    def update_form_view(self, row_index):
        self.current_feature_index = row_index
        while self.ui.form_layout.count():
            item = self.ui.form_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        model = self.controller.model
        if not (0 <= row_index < model.rowCount()):
            self.ui.form_nav_label.setText("Aucune fiche sélectionnée")
            self.ui.form_prev_button.setEnabled(False)
            self.ui.form_next_button.setEnabled(False)
            return

        properties = model.get_all_features()[row_index].get('properties', {})
        for col_idx, key in enumerate(model.get_headers()):
            value = properties.get(key, "") 
            label_text = key.replace('_', ' ').capitalize()
            label, editor = QLabel(label_text), QLineEdit(str(value))

            # Applique un validateur pour les champs de type entier
            column_type = self.controller.get_column_type(key)
            if column_type == 'int':
                editor.setValidator(QIntValidator())

            editor.textChanged.connect(partial(self.on_form_field_changed, row_index, col_idx))
            self.ui.form_layout.addRow(label, editor)
            
        total = model.rowCount()
        self.ui.form_nav_label.setText(f"Fiche {row_index + 1} / {total}")
        self.ui.form_prev_button.setEnabled(row_index > 0)
        self.ui.form_next_button.setEnabled(row_index < total - 1)

    def on_form_field_changed(self, row, col_idx, text):
        model = self.controller.model
        model_col_index = col_idx + 1
        model.setData(model.index(row, model_col_index), text, Qt.ItemDataRole.EditRole)
        
    def show_previous_feature(self):
        if self.current_feature_index > 0:
            self.ui.table_view.selectRow(self.current_feature_index - 1)
        
    def show_next_feature(self):
        if self.current_feature_index < self.controller.model.rowCount() - 1:
            self.ui.table_view.selectRow(self.current_feature_index + 1)
        
    def show_about_dialog(self):
        QMessageBox.about(self, "À propos", "<b>Éditeur GeoJSON</b> v1.6")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())