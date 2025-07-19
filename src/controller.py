import os
import json
import copy

from PySide6.QtCore import QObject, Signal, QThread

from logging_setup import logger
from git_handler import GitHandler
from config_dialog import CONFIG_FILE, save_config
from models import GeoJsonTableModel

# Le worker pour le clonage en arrière-plan. Il est privé au contrôleur.
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
            clone_result = git_handler.clone(
                self.config["REPO_URL"], 
                self.config.get("GITHUB_USERNAME", ""), 
                self.config.get("GITHUB_TOKEN", ""), 
                progress_callback=self.progress.emit
            )
            if self._is_cancelled:
                self.finished.emit(False, "Clonage annulé par l'utilisateur.")
                return
            if clone_result is True:
                self.finished.emit(True, "Le dépôt a été cloné avec succès.")
            else:
                self.finished.emit(False, str(clone_result))
        except Exception as e:
            logger.error(f"Erreur inattendue dans le worker de clonage : {e}", exc_info=True)
            if not self._is_cancelled:
                self.finished.emit(False, f"Erreur inattendue : {e}")

    def cancel(self):
        self._is_cancelled = True


class AppController(QObject):
    """
    Contient toute la logique applicative. Il possède le modèle de données,
    gère l'état de la session d'édition et communique avec la vue via des signaux.
    """
    # --- Signaux pour la communication avec la Vue ---
    config_state_changed = Signal(bool, str)
    connection_status_changed = Signal(bool, str)
    clone_started = Signal()
    clone_progress = Signal(int, str)
    clone_finished = Signal(bool, str)
    publish_finished = Signal(bool, str)
    data_loaded_and_ready = Signal(str)
    modifications_updated = Signal(int, bool)
    status_message_changed = Signal(str)
    view_change_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.config = {}
        self.git_handler = None
        self.thread = None
        self.worker = None

        self.model = GeoJsonTableModel()
        self.original_geojson_data = None
        self.session_adds = 0
        self.session_deletes = 0
        self.session_edits = set()
        self.current_file_info = None
        self.current_column_types = {} # Pour stocker les types du fichier actuel

        self.model.dataChanged.connect(self.on_data_changed_in_model)

    def load_configuration(self):
        """Charge la configuration et vérifie l'état du dépôt local."""
        try:
            with open(CONFIG_FILE, 'r') as f:
                self.config = json.load(f)
            repo_path = self.config.get("LOCAL_REPO_PATH")
            repo_exists = repo_path and os.path.exists(os.path.join(repo_path, '.git'))
            self.config_state_changed.emit(repo_exists, "Configuration chargée.")
            if repo_exists:
                self.initialize_repo()
        except (FileNotFoundError, json.JSONDecodeError):
            self.config = {}
            self.config_state_changed.emit(False, "Bienvenue ! Veuillez configurer l'application.")
    
    def save_configuration_and_clone(self, new_config):
        """Sauvegarde la nouvelle configuration et lance le clonage."""
        self.config = new_config
        save_config(self.config)
        self._start_clone_process()

    def initialize_repo(self):
        """Initialise le gestionnaire Git et teste la connexion au dépôt distant."""
        if not self.config.get("LOCAL_REPO_PATH"):
            self.connection_status_changed.emit(False, "Chemin du dépôt local manquant.")
            return
        self.git_handler = GitHandler(self.config["LOCAL_REPO_PATH"])
        connection_result = self.git_handler.test_connection()
        is_success = connection_result is True
        message = "Connecté au dépôt" if is_success else str(connection_result)
        self.connection_status_changed.emit(is_success, message)

    def select_data_source(self, file_info):
        """Charge les données et la configuration des types de colonnes."""
        self.current_file_info = file_info
        self.reset_modification_counters()
        
        # Récupère la config des types pour le fichier actuel
        self.current_column_types = file_info.get('types', {})
        
        file_path_absolute = os.path.join(self.config["LOCAL_REPO_PATH"], file_info['path'])
        try:
            with open(file_path_absolute, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)

            visible_cols = file_info.get('columns', None)
            
            self.original_geojson_data = copy.deepcopy(geojson_data)
            # Passe la config des types au modèle
            self.model.load_data(copy.deepcopy(geojson_data), visible_headers=visible_cols, column_types=self.current_column_types)
            
            self.status_message_changed.emit(f"Fichier '{file_info['name']}' chargé.")
            self.data_loaded_and_ready.emit(file_info['name'])
            self.view_change_requested.emit('editor')

        except Exception as e:
            logger.error(f"Erreur de chargement du fichier : {e}", exc_info=True)
            self.model.load_data({})
            self.original_geojson_data = None
            self.clone_finished.emit(False, f"Erreur de chargement du fichier : {str(e)}")

    def add_row(self):
        """Ajoute une ligne vide au modèle et met à jour l'état des modifications."""
        if self.model.insert_row():
            self.session_adds += 1
            self._update_modifications()
            self.status_message_changed.emit("Nouvelle ligne ajoutée.")

    def delete_row(self, row_index):
        """Supprime une ligne du modèle et met à jour l'état des modifications."""
        if 0 <= row_index < self.model.rowCount():
            self.model.remove_rows([row_index])
            self.session_deletes += 1
            self._update_modifications()
            self.status_message_changed.emit(f"Ligne {row_index + 1} supprimée.")

    def revert_changes(self):
        """Restaure les données du modèle en ré-appliquant les filtres et types."""
        data_to_load = copy.deepcopy(self.original_geojson_data) if self.original_geojson_data else {}
        
        visible_cols = self.current_file_info.get('columns', None) if self.current_file_info else None
        types = self.current_file_info.get('types', {}) if self.current_file_info else {}
        self.model.load_data(data_to_load, visible_headers=visible_cols, column_types=types)
        
        self.reset_modification_counters()
        self.status_message_changed.emit("Modifications annulées.")
        
    def publish_changes(self):
        """Sauvegarde le fichier, commit et pousse les changements sur GitHub."""
        if not self.has_changes():
            self.status_message_changed.emit("Aucune modification à publier.")
            self.publish_finished.emit(True, "") 
            return
        if not self.git_handler or not self.current_file_info:
            self.publish_finished.emit(False, "Erreur : Git ou les informations du fichier sont manquantes.")
            return

        self.status_message_changed.emit("Publication en cours...")
        
        file_path_relative = self.current_file_info['path']
        absolute_path = os.path.join(self.config["LOCAL_REPO_PATH"], file_path_relative)
        
        try:
            with open(absolute_path, 'w', encoding='utf-8') as f:
                json.dump(self.model.get_geojson_data(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.publish_finished.emit(False, f"Erreur d'écriture du fichier : {e}")
            return
        
        result = self.git_handler.commit_and_push(file_path_relative, f"Mise à jour de {file_path_relative} via l'éditeur")
        
        if result is True:
            self.original_geojson_data = copy.deepcopy(self.model.get_geojson_data())
            self.reset_modification_counters()
            self.publish_finished.emit(True, "Modifications poussées sur GitHub !")
        else:
            self.publish_finished.emit(False, str(result))

    def get_column_type(self, column_name):
        """Permet à la vue de connaître le type d'une colonne."""
        return self.current_column_types.get(column_name, 'string') # 'string' par défaut

    def on_data_changed_in_model(self, top_left, bottom_right, roles):
        """Réagit aux éditions dans le modèle pour suivre les changements."""
        for row in range(top_left.row(), bottom_right.row() + 1):
            self.session_edits.add(row)
        self._update_modifications()
        
    def reset_modification_counters(self):
        """Réinitialise tous les compteurs de modification."""
        self.session_adds, self.session_deletes, self.session_edits = 0, 0, set()
        self._update_modifications()
        
    def has_changes(self):
        """Vérifie s'il y a des modifications non publiées."""
        return bool(self.session_adds or self.session_deletes or self.session_edits)

    def _update_modifications(self):
        """Calcule le total des modifications et notifie la vue."""
        total = self.session_adds + self.session_deletes + len(self.session_edits)
        self.modifications_updated.emit(total, self.has_changes())

    def _start_clone_process(self):
        """Gère la création du thread et du worker pour le clonage."""
        self.clone_started.emit()
        self.thread = QThread()
        self.worker = GitCloneWorker(self.config)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.clone_progress)
        self.worker.finished.connect(self.on_clone_worker_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_clone_worker_finished(self, success, message):
        """Gère la fin du thread de clonage."""
        self.clone_finished.emit(success, message)
        if success:
            self.load_configuration()
        self.thread = None
        self.worker = None
        
    def cancel_clone(self):
        """Demande l'annulation du clonage en cours."""
        logger.warning("Demande d'annulation du clonage...")
        if self.worker:
            self.worker.cancel()