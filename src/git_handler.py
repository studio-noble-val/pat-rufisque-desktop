# git_handler.py
import os
from git import Repo, GitCommandError
from urllib.parse import urlparse, urlunparse

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

    def clone(self, repo_url, username, token):
        """ Clone un dépôt distant. """
        if os.path.exists(self.local_path):
            return "Le dossier local existe déjà."

        # Logique de construction d'URL plus robuste avec urllib
        parsed_url = urlparse(repo_url)
        # Insère les identifiants dans la partie 'netloc' (network location) de l'URL
        netloc_with_auth = f"{username}:{token}@{parsed_url.netloc}"
        # Reconstruit l'URL complète en s'assurant que le schéma est https
        # et en conservant le reste de l'URL (chemin, etc.)
        remote_url_with_auth = urlunparse(parsed_url._replace(scheme="https", netloc=netloc_with_auth))

        try:
            print(f"Tentative de clonage depuis l'URL : {repo_url}")
            self.repo = Repo.clone_from(remote_url_with_auth, self.local_path)
            return True
        except GitCommandError as e:
            # Fournir un message d'erreur plus utile
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
                print("Pull des derniers changements...")
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
            # Il est crucial de faire un pull avant de pousser pour éviter les conflits
            pull_result = self.pull()
            if pull_result is not True:
                return f"Impossible de pousser les changements car le pull a échoué : {pull_result}"
                
            self.repo.index.add([os.path.join(self.local_path, file_path)])
            
            if self.repo.is_dirty(index=True, working_tree=False):
                print(f"Création du commit : {commit_message}")
                self.repo.index.commit(commit_message)
                
                print("Poussée des changements vers l'origine...")
                self.repo.remotes.origin.push()
                return True
            else:
                return "Aucun changement détecté à commiter."
        except GitCommandError as e:
            return f"Erreur Git : {e}"