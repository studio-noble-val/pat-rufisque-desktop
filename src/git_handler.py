# src/git_handler.py
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

    # --- NOUVELLE MÉTHODE INTÉGRÉE ---
    def test_connection(self):
        """
        Tente de contacter le dépôt distant pour vérifier la connexion et l'authentification.
        Renvoie True en cas de succès, ou un message d'erreur en cas d'échec.
        """
        if not self.repo:
            return "Dépôt local non initialisé."
        try:
            print("Test de la connexion au dépôt distant...")
            # 'fetch' est une opération légère qui ne modifie pas les fichiers locaux
            self.repo.remotes.origin.fetch()
            print("Connexion réussie.")
            return True
        except GitCommandError as e:
            error_msg = str(e)
            print(f"Échec de la connexion : {error_msg}")
            if 'Authentication failed' in error_msg:
                return "Échec de l'authentification. Vérifiez le nom d'utilisateur et le Personal Access Token."
            elif 'could not resolve host' in error_msg:
                return "Impossible de contacter le serveur. Vérifiez l'URL du dépôt et votre connexion internet."
            else:
                return f"Erreur Git inattendue : {e}"
    # --- FIN DE LA NOUVELLE MÉTHODE ---

    def clone(self, repo_url, username, token):
        """ Clone un dépôt distant. """
        if os.path.exists(self.local_path):
            return "Le dossier local existe déjà."

        # Votre logique de construction d'URL robuste avec urllib est conservée
        parsed_url = urlparse(repo_url)
        netloc_with_auth = f"{username}:{token}@{parsed_url.netloc}"
        remote_url_with_auth = urlunparse(parsed_url._replace(scheme="https", netloc=netloc_with_auth))

        try:
            print(f"Tentative de clonage depuis l'URL : {repo_url}")
            self.repo = Repo.clone_from(remote_url_with_auth, self.local_path)
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