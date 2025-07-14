# src/ui_main_window.py
from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QTableView, QStackedWidget,
    QPushButton, QLabel, QMenuBar, QSpacerItem, QSizePolicy, QFormLayout, QStyle
)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1200, 700)
        
        self.main_stacked_widget = QStackedWidget()
        MainWindow.setCentralWidget(self.main_stacked_widget)

        # --- Page d'Accueil (index 0) ---
        self.welcome_page = QWidget()
        welcome_layout = QVBoxLayout(self.welcome_page)
        welcome_layout.setContentsMargins(30, 30, 30, 30)
        
        title_label = QLabel("<h1>Éditeur de Données GeoJSON</h1>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Nouvel indicateur de statut de connexion
        self.connection_status_label = QLabel("Vérification de la configuration...")
        self.connection_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.connection_status_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 20px;")
        
        # StackedWidget interne pour l'état de la page d'accueil
        self.welcome_stacked_widget = QStackedWidget()
        
        # État 1 : Configuration requise (index 0)
        self.config_needed_page = QWidget()
        config_needed_layout = QVBoxLayout(self.config_needed_page)
        config_needed_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        config_msg = QLabel("La configuration est manquante ou invalide.")
        config_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_config_button = QPushButton("Configurer l'application maintenant")
        self.welcome_config_button.setMinimumHeight(40)
        self.welcome_config_button.setStyleSheet("font-size: 16px;")
        config_needed_layout.addWidget(config_msg)
        config_needed_layout.addWidget(self.welcome_config_button)
        self.welcome_stacked_widget.addWidget(self.config_needed_page)
        
        # État 2 : Prêt à sélectionner (index 1)
        self.selection_page = QWidget()
        selection_layout = QVBoxLayout(self.selection_page)
        selection_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        selection_msg = QLabel("Veuillez sélectionner une source de données à modifier :")
        selection_msg.setStyleSheet("margin-bottom: 10px;")
        self.welcome_buttons_layout = QVBoxLayout()
        self.welcome_buttons_layout.setSpacing(15)
        selection_layout.addWidget(selection_msg)
        selection_layout.addLayout(self.welcome_buttons_layout)
        self.welcome_stacked_widget.addWidget(self.selection_page)

        welcome_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        welcome_layout.addWidget(title_label)
        welcome_layout.addWidget(self.connection_status_label)
        welcome_layout.addWidget(self.welcome_stacked_widget)
        welcome_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        self.main_stacked_widget.addWidget(self.welcome_page)

        # --- Page d'Édition (index 1) ---
        # (Aucun changement dans cette section)
        self.editor_page = QWidget()
        editor_page_layout = QVBoxLayout(self.editor_page)
        self.editor_title_label = QLabel("<h2></h2>") 
        editor_page_layout.addWidget(self.editor_title_label)
        self.editor_stacked_widget = QStackedWidget()
        editor_page_layout.addWidget(self.editor_stacked_widget)
        self.table_view_page = QWidget(); table_layout = QVBoxLayout(self.table_view_page); table_layout.setContentsMargins(0,0,0,0); self.table_view = QTableView(); self.add_button = QPushButton("Ajouter une ligne"); table_layout.addWidget(self.table_view); table_layout.addWidget(self.add_button, 0, Qt.AlignmentFlag.AlignLeft); self.editor_stacked_widget.addWidget(self.table_view_page)
        self.form_view_page = QWidget(); form_page_layout = QVBoxLayout(self.form_view_page); self.form_scroll_area = QWidget(); self.form_layout = QFormLayout(self.form_scroll_area); form_page_layout.addWidget(self.form_scroll_area); nav_layout = QHBoxLayout(); self.form_prev_button = QPushButton("Précédent"); self.form_next_button = QPushButton("Suivant"); self.form_nav_label = QLabel("Fiche 1 / 10"); nav_layout.addStretch(); nav_layout.addWidget(self.form_prev_button); nav_layout.addWidget(self.form_nav_label); nav_layout.addWidget(self.form_next_button); nav_layout.addStretch(); form_page_layout.addLayout(nav_layout); self.editor_stacked_widget.addWidget(self.form_view_page)
        self.main_stacked_widget.addWidget(self.editor_page)
        
        # --- Barres, Menus, etc. (Aucun changement ici non plus) ---
        self.status_label = QLabel(); MainWindow.statusBar().addWidget(self.status_label); self.menubar = QMenuBar(); MainWindow.setMenuBar(self.menubar)
        style = MainWindow.style(); self.actionViewTable = QAction("Vue Tableau", MainWindow); self.actionViewTable.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)); self.actionViewTable.setCheckable(True); self.actionViewForm = QAction("Vue Fiche", MainWindow); self.actionViewForm.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView)); self.actionViewForm.setCheckable(True)
        self.viewToolBar = QToolBar("Vues"); MainWindow.addToolBar(self.viewToolBar); self.viewToolBar.addAction(self.actionViewTable); self.viewToolBar.addAction(self.actionViewForm)
        self.menuFichier = self.menubar.addMenu("&Fichier"); self.actionAccueil = QAction("&Accueil", MainWindow); self.actionEnregistrer = QAction("Enregistrer et Pousser", MainWindow); self.actionEnregistrer.setShortcut("Ctrl+S"); self.actionQuitter = QAction("&Quitter", MainWindow); self.menuFichier.addAction(self.actionAccueil); self.menuFichier.addSeparator(); self.menuFichier.addAction(self.actionEnregistrer); self.menuFichier.addSeparator(); self.menuFichier.addAction(self.actionQuitter)
        self.menuEdition = self.menubar.addMenu("&Édition"); self.actionConfigurer = QAction("&Configuration...", MainWindow); self.actionConfigurer.setShortcut("Ctrl+,"); self.menuEdition.addAction(self.actionConfigurer)
        self.menuAide = self.menubar.addMenu("&Aide"); self.actionAPropos = QAction("À &propos...", MainWindow); self.menuAide.addAction(self.actionAPropos)
        
        # --- Attribution des widgets ---
        MainWindow.main_stacked_widget = self.main_stacked_widget; MainWindow.welcome_stacked_widget = self.welcome_stacked_widget; MainWindow.connection_status_label = self.connection_status_label; MainWindow.welcome_config_button = self.welcome_config_button; MainWindow.welcome_buttons_layout = self.welcome_buttons_layout; MainWindow.editor_stacked_widget = self.editor_stacked_widget; MainWindow.editor_title_label = self.editor_title_label; MainWindow.table_view = self.table_view; MainWindow.add_button = self.add_button; MainWindow.form_layout = self.form_layout; MainWindow.form_prev_button = self.form_prev_button; MainWindow.form_next_button = self.form_next_button; MainWindow.form_nav_label = self.form_nav_label; MainWindow.status_label = self.status_label; MainWindow.actionAccueil = self.actionAccueil; MainWindow.actionEnregistrer = self.actionEnregistrer; MainWindow.actionQuitter = self.actionQuitter; MainWindow.actionConfigurer = self.actionConfigurer; MainWindow.actionAPropos = self.actionAPropos; MainWindow.actionViewTable = self.actionViewTable; MainWindow.actionViewForm = self.actionViewForm
        
        self.retranslateUi(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "Éditeur GeoJSON", None))