# Éditeur de Données GeoJSON

Cet outil est une application de bureau pour Windows conçue pour permettre une édition simple et rapide de fichiers de données au format GeoJSON, directement hébergés sur un dépôt GitHub.

Il s'adresse aux utilisateurs qui ont besoin de modifier des données géographiques (ajouter, modifier ou supprimer des entrées) sans avoir à manipuler directement les fichiers texte ou à utiliser les commandes Git.

## Fonctionnalités

*   **Interface Graphique Intuitive** : Toutes les opérations se font via une interface simple, sans ligne de commande.
*   **Configuration Unique** : L'utilisateur configure une seule fois ses accès au dépôt GitHub.
*   **Édition en Tableau** : Les données des fichiers GeoJSON sont présentées dans un tableau facile à lire et à modifier.
*   **Actions Simples** : Ajout et suppression de lignes en un clic.
*   **Synchronisation Automatisée** : Un seul bouton "Enregistrer et Pousser" met à jour le fichier local, le "commit" (enregistre la version) et le "push" (envoie sur GitHub) de manière transparente.
*   **Autonome** : L'outil est distribué comme un unique fichier `.exe` qui ne nécessite aucune installation de Python ou d'autres dépendances sur le poste de l'utilisateur.

## Installation et Première Utilisation

L'outil est un simple exécutable. Aucune installation n'est requise.

1.  Téléchargez le fichier `EditeurGeoJSON.exe`.
2.  Placez-le dans un dossier de votre choix sur votre ordinateur.
3.  Double-cliquez sur `EditeurGeoJSON.exe` pour le lancer.

La première fois que vous lancez l'application, vous serez accueilli par un message vous invitant à configurer l'outil.

## Configuration Initiale

Avant de pouvoir utiliser l'outil, vous devez le connecter à votre dépôt GitHub. Cliquez sur le bouton **"Configurer"** pour ouvrir la fenêtre de configuration.

Vous devrez y renseigner les champs suivants :

*   **URL du dépôt (HTTPS)** : C'est l'adresse de votre dépôt GitHub. Vous pouvez la trouver sur la page principale de votre dépôt sur GitHub, en cliquant sur le bouton vert "Code". Assurez-vous de copier l'URL HTTPS.
    *   *Exemple : `https://github.com/votre-compte/votre-depot.git`*

*   **Dossier local pour le dépôt** : C'est le dossier sur votre ordinateur où l'application va télécharger une copie de votre dépôt. Un chemin par défaut est proposé, mais vous pouvez cliquer sur "Parcourir..." pour en choisir un autre.

*   **Nom d'utilisateur GitHub** : Votre nom d'utilisateur public sur GitHub.

*   **Personal Access Token (PAT)** : C'est l'équivalent d'un mot de passe sécurisé pour les applications. **GitHub n'autorise plus l'utilisation du mot de passe de votre compte pour ce genre d'opération.** Vous devez générer un token. Voir la section ci-dessous pour la procédure détaillée.

Une fois tous les champs remplis, cliquez sur "OK". L'application va enregistrer la configuration et tenter de cloner (télécharger) votre dépôt.

### Comment Générer un Personal Access Token (PAT) sur GitHub

Suivez ces étapes scrupuleusement :

1.  Connectez-vous à votre compte sur **[github.com](https://github.com)**.
2.  Cliquez sur votre photo de profil en haut à droite, puis sur **Settings**.
3.  Dans le menu de gauche, faites défiler tout en bas et cliquez sur **Developer settings**.
4.  Dans le nouveau menu de gauche, cliquez sur **Personal access tokens**, puis sur **Tokens (classic)**.
5.  Cliquez sur le bouton **Generate new token**, puis confirmez en cliquant sur **Generate new token (classic)**.
6.  **Note** : Donnez un nom explicite à votre token pour vous souvenir de son utilité (par exemple : `Editeur-GeoJSON-App`).
7.  **Expiration** : Choisissez une durée de validité pour votre token (par exemple, 90 jours).
8.  **Select scopes** : C'est l'étape la plus importante. Vous devez donner les permissions nécessaires à votre token. Cochez la case principale **`repo`**. Cela lui donnera tous les droits nécessaires pour lire et écrire dans vos dépôts.
    
9.  Cliquez sur le bouton vert **Generate token** tout en bas de la page.
10. **⚠️ ATTENTION** : GitHub n'affichera le token qu'**une seule fois**. Copiez-le immédiatement et collez-le dans le champ correspondant de l'application. Si vous perdez ce token, vous devrez en générer un nouveau.

## Utilisation Quotidienne

Une fois la configuration terminée :

1.  **Sélectionnez** le fichier que vous souhaitez modifier dans le menu déroulant.
2.  **Modifiez** les données en double-cliquant sur les cellules.
3.  **Supprimez** une ligne en cliquant sur l'icône de poubelle correspondante.
4.  **Ajoutez** une nouvelle ligne vide avec le bouton "Ajouter une ligne".
5.  Lorsque vous avez terminé, cliquez sur **"Enregistrer et Pousser sur GitHub"**. Vos modifications seront envoyées sur le dépôt distant.

---

## Pour les Développeurs

Ce projet est développé en Python avec la bibliothèque `PySide6` pour l'interface graphique et `GitPython` pour l'interaction avec Git.

### Prérequis

*   Python 3.10 ou supérieur
*   Un environnement virtuel (recommandé)

### Installation des dépendances

1.  Clonez le dépôt.
2.  Activez votre environnement virtuel.
3.  Créez le fichier `requirements.txt` avec `pip freeze > requirements.txt` si il n'est pas présent.
4.  Installez les paquets nécessaires :

        pip install -r requirements.txt

### Lancement en mode développement

    python src/main.py

### Génération de l'exécutable

L'exécutable est généré avec PyInstaller.

1.  Installez PyInstaller :

        pip install pyinstaller

2.  Lancez la commande de packaging depuis la racine du projet :

        pyinstaller --onefile --windowed --name="EditeurGeoJSON" --add-data "src/icons:icons" src/main.py

3.  L'exécutable final se trouvera dans le dossier `dist/`.