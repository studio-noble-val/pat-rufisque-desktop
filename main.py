# main.py
import sys
import os
import json
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QTableView, QPushButton, QLabel, QHeaderView, 
    QStyledItemDelegate, QStyle, QStyleOptionButton, QMessageBox
)
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, Signal, QEvent

# Nouvelles importations
from config_dialog import ConfigDialog, save_config, CONFIG_FILE
from git_handler import GitHandler

# ... (La classe ButtonDelegate reste identique)
class ButtonDelegate(QStyledItemDelegate):
    delete_row_requested = Signal(int)
    def paint(self, painter, option, index):
        if not index.isValid(): return
        button_option = QStyleOptionButton(); button_option.rect = option.rect; button_option.text = ""; button_option.state = QStyle.StateFlag.State_Enabled
        style = QApplication.style(); icon = style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon); button_option.icon = icon; button_option.iconSize = option.rect.size() / 2 
        style.drawControl(QStyle.ControlElement.CE_PushButton, button_option, painter)
    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            if option.rect.contains(event.pos()): self.delete_row_requested.emit(index.row()); return True
        return False

# --- Modèle de Table pour les données GeoJSON ---
class GeoJsonTableModel(QAbstractTableModel):
    # --- MODIFICATION MAJEURE : On gère l'objet "feature" entier ---
    def __init__(self, parent=None):
        super().__init__(parent)
        self._features = [] # Stocke la liste complète des features, pas juste les properties
        self._base_geojson_struct = {} # Stocke la structure de base du geojson
        self._headers = []

    # Le modèle doit maintenant renvoyer les objets feature complets
    def get_all_features(self):
        return self._features

    def get_base_struct(self):
        return self._base_geojson_struct

    def load_data(self, geojson_data):
        self.beginResetModel()
        # On stocke la structure de base (tout sauf les features)
        self._base_geojson_struct = {k: v for k, v in geojson_data.items() if k != 'features'}
        # On stocke les features
        self._features = geojson_data.get('features', [])
        
        if not self._features:
            self._headers = []
        else:
            # Les en-têtes sont les clés des "properties"
            all_keys = set().union(*(f.get('properties', {}).keys() for f in self._features))
            self._headers = sorted(list(all_keys))
        self.endResetModel()

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.column() == 0: return None
        if role == Qt.ItemDataRole.DisplayRole:
            # On va chercher la donnée dans les 'properties' de la feature
            properties = self._features[index.row()].get('properties', {})
            header = self._headers[index.column() - 1]
            return str(properties.get(header, ""))
        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role != Qt.ItemDataRole.EditRole or not index.isValid() or index.column() == 0: return False
        
        row, col = index.row(), index.column() - 1
        header = self._headers[col]
        
        # On modifie directement dans les 'properties' de la feature
        if 'properties' not in self._features[row]:
            self._features[row]['properties'] = {}
        self._features[row]['properties'][header] = value
        
        self.dataChanged.emit(index, index, [role])
        return True

    def insert_row(self):
        position = self.rowCount()
        self.beginInsertRows(QModelIndex(), position, position)
        # Crée une feature vide avec la structure correcte
        new_blank_feature = {
            "type": "Feature",
            "properties": {header: "" for header in self._headers},
            "geometry": None # Ou une géométrie par défaut
        }
        self._features.append(new_blank_feature)
        self.endInsertRows()
        return True

    def remove_rows(self, rows_to_delete):
        for row_index in sorted(rows_to_delete, reverse=True):
            self.beginRemoveRows(QModelIndex(), row_index, row_index)
            del self._features[row_index]
            self.endRemoveRows()
        return True
    
    # Les autres méthodes (columnCount, headerData, flags, rowCount) restent les mêmes
    def columnCount(self, parent=None): return len(self._headers) + 1
    def rowCount(self, parent=None): return len(self._features)
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if section == 0: return "Action"
            return self._headers[section - 1]
        return None
    def flags(self, index):
        if not index.isValid(): return Qt.ItemFlag.NoItemFlags
        if index.column() == 0: return Qt.ItemFlag.ItemIsEnabled
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable
class ButtonDelegate(QStyledItemDelegate):
    delete_row_requested = Signal(int)
    def paint(self, painter, option, index):
        if not index.isValid(): return
        button_option = QStyleOptionButton(); button_option.rect = option.rect; button_option.text = ""; button_option.state = QStyle.StateFlag.State_Enabled
        style = QApplication.style(); icon = style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon); button_option.icon = icon; button_option.iconSize = option.rect.size() / 2 
        style.drawControl(QStyle.ControlElement.CE_PushButton, button_option, painter)
    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            if option.rect.contains(event.pos()): self.delete_row_requested.emit(index.row()); return True
        return False
class GeoJsonTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._features = []
        self._base_geojson_struct = {}
        self._headers = []
    def get_all_features(self): return self._features
    def get_base_struct(self): return self._base_geojson_struct
    def load_data(self, geojson_data):
        self.beginResetModel()
        self._base_geojson_struct = {k: v for k, v in geojson_data.items() if k != 'features'}
        self._features = geojson_data.get('features', [])
        if not self._features: self._headers = []
        else: self._headers = sorted(list(set().union(*(f.get('properties', {}).keys() for f in self._features))))
        self.endResetModel()
    def columnCount(self, parent=None): return len(self._headers) + 1
    def rowCount(self, parent=None): return len(self._features)
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if section == 0: return "Action"
            return self._headers[section - 1]
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.column() == 0: return None
        if role == Qt.ItemDataRole.DisplayRole:
            properties = self._features[index.row()].get('properties', {})
            header = self._headers[index.column() - 1]
            return str(properties.get(header, ""))
    def flags(self, index):
        if not index.isValid(): return Qt.ItemFlag.NoItemFlags
        if index.column() == 0: return Qt.ItemFlag.ItemIsEnabled
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable
    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role != Qt.ItemDataRole.EditRole or not index.isValid() or index.column() == 0: return False
        row, col = index.row(), index.column() - 1; header = self._headers[col]
        if 'properties' not in self._features[row]: self._features[row]['properties'] = {}
        self._features[row]['properties'][header] = value
        self.dataChanged.emit(index, index, [role]); return True
    def insert_row(self):
        position = self.rowCount()
        self.beginInsertRows(QModelIndex(), position, position)
        new_blank_feature = {"type": "Feature", "properties": {header: "" for header in self._headers}, "geometry": None}
        self._features.append(new_blank_feature); self.endInsertRows(); return True
    def remove_rows(self, rows_to_delete):
        for row_index in sorted(rows_to_delete, reverse=True):
            self.beginRemoveRows(QModelIndex(), row_index, row_index)
            del self._features[row_index]; self.endRemoveRows()
        return True

# --- Fenêtre Principale de l'Application ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.base_title = "Éditeur GeoJSON"
        self.setWindowTitle(self.base_title)
        self.setGeometry(100, 100, 1200, 700)
        self.unsaved_changes = False
        self.config = {}
        self.git_handler = None
        
        # --- Widgets ---
        self.config_button = QPushButton("Configurer")
        self.file_selector = QComboBox()
        self.status_label = QLabel("Veuillez configurer l'application.")
        self.table_view = QTableView()
        self.model = GeoJsonTableModel()
        self.table_view.setModel(self.model)
        self.button_delegate = ButtonDelegate(self)
        self.add_button = QPushButton("Ajouter une ligne")
        self.save_button = QPushButton("Enregistrer et Pousser sur GitHub")

        # --- Layouts ---
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Fichier à modifier:"))
        top_layout.addWidget(self.file_selector, 1)
        top_layout.addWidget(self.config_button)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_button)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.table_view)
        main_layout.addWidget(self.status_label)
        main_layout.addLayout(button_layout)
        central_widget = QWidget(); central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # --- Connexions ---
        self.config_button.clicked.connect(self.open_config_dialog)
        self.file_selector.currentIndexChanged.connect(self.load_selected_file_data)
        self.add_button.clicked.connect(self.add_row)
        self.save_button.clicked.connect(self.save_data)
        self.model.dataChanged.connect(self.mark_as_unsaved)
        self.table_view.setItemDelegateForColumn(0, self.button_delegate)
        self.button_delegate.delete_row_requested.connect(self.handle_delete_request)

        # --- Initialisation ---
        self.load_app_config()

    def load_app_config(self):
        """ Charge la configuration au démarrage et initialise l'app. """
        try:
            with open(CONFIG_FILE, 'r') as f:
                self.config = json.load(f)
            
            # Vérifier que les clés essentielles sont là
            if all(k in self.config for k in ["REPO_URL", "LOCAL_REPO_PATH", "FILES"]):
                self.initialize_repo()
            else:
                self.status_label.setText("Fichier de configuration incomplet. Veuillez configurer.")
        except FileNotFoundError:
            self.status_label.setText("Bienvenue ! Veuillez configurer l'application pour commencer.")
    
    def initialize_repo(self):
        """ Initialise le GitHandler et clone le dépôt si nécessaire. """
        local_path = self.config["LOCAL_REPO_PATH"]
        self.git_handler = GitHandler(local_path)

        if not self.git_handler.repo:
            self.status_label.setText(f"Clonage du dépôt vers {local_path}...")
            QApplication.processEvents() # Met à jour l'UI
            result = self.git_handler.clone(
                self.config["REPO_URL"],
                self.config["GITHUB_USERNAME"],
                self.config["GITHUB_TOKEN"]
            )
            if result is not True:
                QMessageBox.critical(self, "Erreur de Clonage", str(result))
                self.status_label.setText("Échec du clonage. Vérifiez la configuration.")
                return

        self.status_label.setText("Dépôt prêt. Chargement des données...")
        self.populate_file_selector()
        self.load_selected_file_data()


    def open_config_dialog(self):
        """ Ouvre la boîte de dialogue de configuration. """
        dialog = ConfigDialog(self)
        if dialog.exec(): # L'utilisateur a cliqué sur OK
            self.config = dialog.get_config()
            save_config(self.config)
            QMessageBox.information(self, "Configuration Enregistrée", "La configuration a été enregistrée. Le dépôt va être initialisé.")
            self.initialize_repo()

    def populate_file_selector(self):
        """ Remplit le menu déroulant avec les fichiers de la config. """
        self.file_selector.clear()
        for file_info in self.config.get("FILES", []):
            self.file_selector.addItem(file_info["name"], userData=file_info["path"])

    def load_selected_file_data(self, index=-1):
        """ Charge le fichier sélectionné dans le menu déroulant. """
        if not self.git_handler or not self.git_handler.repo:
            return
        
        file_path_relative = self.file_selector.currentData()
        if not file_path_relative: return

        file_path_absolute = os.path.join(self.config["LOCAL_REPO_PATH"], file_path_relative)
        
        try:
            with open(file_path_absolute, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
            self.model.load_data(geojson_data)
            self.table_view.setColumnWidth(0, 50)
            self.table_view.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            for i in range(1, self.model.columnCount()):
                 self.table_view.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            self.status_label.setText(f"Fichier '{self.file_selector.currentText()}' chargé.")
            self.unsaved_changes = False
            self.setWindowTitle(self.base_title)
        except Exception as e:
            self.status_label.setText(f"Erreur de chargement : {e}")
            self.model.load_data({})
    
    def save_data(self):
        """ Sauvegarde les données, commit et push. """
        if not self.unsaved_changes:
            self.status_label.setText("Aucune modification à enregistrer."); return
        if not self.git_handler or not self.git_handler.repo:
            QMessageBox.warning(self, "Erreur", "Le dépôt Git n'est pas configuré."); return

        # Reconstruire le fichier
        relative_path = self.file_selector.currentData()
        absolute_path = os.path.join(self.config["LOCAL_REPO_PATH"], relative_path)
        new_geojson_data = self.model.get_base_struct()
        new_geojson_data['features'] = self.model.get_all_features()
        with open(absolute_path, 'w', encoding='utf-8') as f:
            json.dump(new_geojson_data, f, indent=2, ensure_ascii=False)

        # Commit et Push
        self.status_label.setText("Envoi vers GitHub..."); QApplication.processEvents()
        commit_message = f"Mise à jour de {relative_path}"
        result = self.git_handler.commit_and_push(relative_path, commit_message)
        
        if result is True:
            QMessageBox.information(self, "Succès", "Modifications poussées sur GitHub !")
            self.unsaved_changes = False
            self.setWindowTitle(self.base_title)
            self.status_label.setText("Prêt.")
        else:
            QMessageBox.critical(self, "Erreur Git", str(result))
            self.status_label.setText("Échec de l'envoi.")

    # Les autres méthodes (add_row, handle_delete, mark_as_unsaved) sont identiques
    def mark_as_unsaved(self):
        if not self.unsaved_changes: self.unsaved_changes = True; self.setWindowTitle(self.base_title + " *"); self.status_label.setText("Modifications non enregistrées.")
    def add_row(self):
        if self.model.insert_row(): self.mark_as_unsaved(); self.status_label.setText("Nouvelle ligne ajoutée."); self.table_view.scrollToBottom()
    def handle_delete_request(self, row):
        if 0 <= row < self.model.rowCount(): self.status_label.setText(f"Ligne {row + 1} supprimée."); self.model.remove_rows([row]); self.mark_as_unsaved()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())