# src/git_handler.py
import os
from git import Repo, GitCommandError, remote
from urllib.parse import urlparse, urlunparse

class CloneProgressHandler(remote.RemoteProgress):
    """
    Classe pour intercepter les signaux de progression de GitPython
    et les transmettre à une fonction de rappel (callback).
    Cette version est compatible avec les versions récentes de GitPython
    qui utilisent des constantes directement sur l'instance (ex: self.END).
    """
    def __init__(self, progress_callback):
        super().__init__()
        self.progress_callback = progress_callback

    def update(self, op_code, cur_count, max_count=None, message=''):
        # op_code est un masque de bits. Nous vérifions les drapeaux (flags).
        
        # Calcul du pourcentage
        percentage = int((cur_count / (max_count or 100.0)) * 100)
        
        # On vérifie quel type d'opération est en cours en utilisant
        # les nouvelles constantes (self.END, self.COUNTING, etc.)
        if op_code & self.END:
            self.progress_callback(100, "Terminé.")
        elif op_code & self.COUNTING:
            self.progress_callback(percentage, f"Comptage des objets : {cur_count}/{max_count}")
        elif op_code & self.COMPRESSING:
            self.progress_callback(percentage, f"Compression des objets : {cur_count}/{max_count}")
        elif op_code & self.RECEIVING:
            self.progress_callback(percentage, f"Réception des objets : {cur_count}/{max_count}")
        elif op_code & self.RESOLVING:
            self.progress_callback(percentage, f"Résolution des deltas : {cur_count}/{max_count}")


class GitHandler:
    def __init__(self, local_path):
        """
        Initialise le gestionnaire avec le chemin local du dépôt.
        :param local_path: Chemin du dossier local du dépôt.
        """
        self.local_path = local_path
        self.repo = None
        # Vérifie si un dépôt git existe déjà à cet endroit
        if os.path.exists(os.path.join(self.local_path, '.git')):
            self.repo = Repo(self.local_path)

    def test_connection(self):
        """
        Tente de contacter le dépôt distant pour vérifier la connexion et l'authentification.
        Renvoie True en cas de succès, ou un message d'erreur en cas d'échec.
        """
        if not self.repo:
            return "Dépôt local non initialisé."
        try:
            self.repo.remotes.origin.fetch()
            return True
        except GitCommandError as e:
            error_msg = str(e)
            if 'Authentication failed' in error_msg:
                return "Échec de l'authentification. Vérifiez le nom d'utilisateur et le Personal Access Token."
            elif 'could not resolve host' in error_msg:
                return "Impossible de contacter le serveur. Vérifiez l'URL du dépôt et votre connexion internet."
            else:
                return f"Erreur Git inattendue : {e}"

    def clone(self, repo_url, username, token, progress_callback=None):
        """ Clone un dépôt distant avec un suivi de progression optionnel. """
        parsed_url = urlparse(repo_url)
        netloc_with_auth = f"{username}:{token}@{parsed_url.netloc}"
        remote_url_with_auth = urlunparse(parsed_url._replace(scheme="https", netloc=netloc_with_auth))

        progress_handler = None
        if progress_callback:
            progress_handler = CloneProgressHandler(progress_callback)

        try:
            self.repo = Repo.clone_from(
                remote_url_with_auth,
                self.local_path,
                progress=progress_handler
            )
            return True
        except GitCommandError as e:
            error_message = (f"Échec du clonage. Vérifiez que :\n"
                             f"1. L'URL du dépôt est correcte.\n"
                             f"2. Le nom d'utilisateur est correct.\n"
                             f"3. Le Personal Access Token est valide et a les droits 'repo'.\n\n"
                             f"Détail de l'erreur Git : {e}")
            return error_message

    def pull(self):
        """ Récupère les derniers changements. """
        if self.repo:
            try:
                self.repo.remotes.origin.pull()
                return True
            except GitCommandError as e:
                return f"Échec du pull : {e}"
        return "Dépôt non initialisé."

    def commit_and_push(self, file_path, commit_message):
        """ Commit et pousse un fichier. """
        if not self.repo:
            return "Dépôt non initialisé."
        try:
            pull_result = self.pull()
            if pull_result is not True:
                return f"Impossible de pousser les changements car le pull a échoué : {pull_result}"

            self.repo.index.add([os.path.join(self.local_path, file_path)])

            if self.repo.is_dirty(index=True, working_tree=False):
                self.repo.index.commit(commit_message)
                self.repo.remotes.origin.push()
                return True
            else:
                return "Aucun changement détecté à commiter."
        except GitCommandError as e:
            return f"Erreur Git : {e}"