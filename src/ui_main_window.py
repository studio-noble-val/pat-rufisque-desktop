# src/ui_main_window.py
from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QTableView, QStackedWidget,
    QPushButton, QLabel, QMenuBar, QSpacerItem, QSizePolicy, QFormLayout, QStyle # <-- QStyle A ÉTÉ AJOUTÉ ICI
)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1200, 700)
        
        # --- Conteneur principal (Accueil / Éditeur) ---
        self.main_stacked_widget = QStackedWidget()
        MainWindow.setCentralWidget(self.main_stacked_widget)

        # --- Page d'Accueil (index 0) ---
        self.welcome_page = QWidget()
        # (Le code de la page d'accueil ne change pas)
        welcome_layout = QVBoxLayout(self.welcome_page)
        welcome_layout.setContentsMargins(50, 50, 50, 50)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label = QLabel("<h1>Éditeur de Données GeoJSON</h1>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_buttons_layout = QVBoxLayout()
        self.welcome_buttons_layout.setSpacing(15)
        help_label = QLabel("Si la configuration n'est pas correcte, utilisez le menu <b>Édition > Configuration...</b>")
        help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        help_label.setStyleSheet("font-size: 11px; color: grey; margin-top: 30px;")
        welcome_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        welcome_layout.addWidget(title_label)
        welcome_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        welcome_layout.addLayout(self.welcome_buttons_layout)
        welcome_layout.addWidget(help_label)
        welcome_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        self.main_stacked_widget.addWidget(self.welcome_page)


        # --- Page d'Édition (index 1) ---
        self.editor_page = QWidget()
        editor_page_layout = QVBoxLayout(self.editor_page)
        
        # Le nom du fichier sera affiché en grand
        self.editor_title_label = QLabel("<h2></h2>") 
        editor_page_layout.addWidget(self.editor_title_label)
        
        # StackedWidget interne pour basculer entre Tableau et Fiche
        self.editor_stacked_widget = QStackedWidget()
        editor_page_layout.addWidget(self.editor_stacked_widget)
        
        # Vue Tableau (index 0 de l'éditeur)
        self.table_view_page = QWidget()
        table_layout = QVBoxLayout(self.table_view_page)
        table_layout.setContentsMargins(0,0,0,0)
        self.table_view = QTableView()
        self.add_button = QPushButton("Ajouter une ligne")
        table_layout.addWidget(self.table_view)
        table_layout.addWidget(self.add_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.editor_stacked_widget.addWidget(self.table_view_page)
        
        # Vue Fiche (index 1 de l'éditeur)
        self.form_view_page = QWidget()
        form_page_layout = QVBoxLayout(self.form_view_page)
        self.form_scroll_area = QWidget() # On mettra le formulaire ici
        self.form_layout = QFormLayout(self.form_scroll_area) # Le layout pour les champs
        form_page_layout.addWidget(self.form_scroll_area)
        
        nav_layout = QHBoxLayout()
        self.form_prev_button = QPushButton("Précédent")
        self.form_next_button = QPushButton("Suivant")
        self.form_nav_label = QLabel("Fiche 1 / 10")
        nav_layout.addStretch()
        nav_layout.addWidget(self.form_prev_button)
        nav_layout.addWidget(self.form_nav_label)
        nav_layout.addWidget(self.form_next_button)
        nav_layout.addStretch()
        form_page_layout.addLayout(nav_layout)
        self.editor_stacked_widget.addWidget(self.form_view_page)

        self.main_stacked_widget.addWidget(self.editor_page)

        # --- Barre de Menus, Statut et Outils ---
        self.status_label = QLabel()
        MainWindow.statusBar().addWidget(self.status_label)
        self.menubar = QMenuBar()
        MainWindow.setMenuBar(self.menubar)
        
        style = MainWindow.style()
        self.actionViewTable = QAction("Vue Tableau", MainWindow)
        self.actionViewTable.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.actionViewTable.setCheckable(True)
        self.actionViewForm = QAction("Vue Fiche", MainWindow)
        self.actionViewForm.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView))
        self.actionViewForm.setCheckable(True)
        
        self.viewToolBar = QToolBar("Vues")
        MainWindow.addToolBar(self.viewToolBar)
        self.viewToolBar.addAction(self.actionViewTable)
        self.viewToolBar.addAction(self.actionViewForm)

        # (Le code de la barre de menu ne change pas)
        self.menuFichier = self.menubar.addMenu("&Fichier")
        self.actionAccueil = QAction("&Accueil", MainWindow)
        self.actionEnregistrer = QAction("Enregistrer et Pousser", MainWindow)
        self.actionEnregistrer.setShortcut("Ctrl+S")
        self.actionQuitter = QAction("&Quitter", MainWindow)
        self.menuFichier.addAction(self.actionAccueil)
        self.menuFichier.addSeparator()
        self.menuFichier.addAction(self.actionEnregistrer)
        self.menuFichier.addSeparator()
        self.menuFichier.addAction(self.actionQuitter)
        self.menuEdition = self.menubar.addMenu("&Édition")
        self.actionConfigurer = QAction("&Configuration...", MainWindow)
        self.actionConfigurer.setShortcut("Ctrl+,")
        self.menuEdition.addAction(self.actionConfigurer)
        self.menuAide = self.menubar.addMenu("&Aide")
        self.actionAPropos = QAction("À &propos...", MainWindow)
        self.menuAide.addAction(self.actionAPropos)

        # --- Attribution des widgets ---
        MainWindow.main_stacked_widget = self.main_stacked_widget
        MainWindow.welcome_buttons_layout = self.welcome_buttons_layout
        MainWindow.editor_stacked_widget = self.editor_stacked_widget
        MainWindow.editor_title_label = self.editor_title_label
        MainWindow.table_view = self.table_view
        MainWindow.add_button = self.add_button
        MainWindow.form_layout = self.form_layout
        MainWindow.form_prev_button = self.form_prev_button
        MainWindow.form_next_button = self.form_next_button
        MainWindow.form_nav_label = self.form_nav_label
        MainWindow.status_label = self.status_label
        MainWindow.actionAccueil = self.actionAccueil
        MainWindow.actionEnregistrer = self.actionEnregistrer
        MainWindow.actionQuitter = self.actionQuitter
        MainWindow.actionConfigurer = self.actionConfigurer
        MainWindow.actionAPropos = self.actionAPropos
        MainWindow.actionViewTable = self.actionViewTable
        MainWindow.actionViewForm = self.actionViewForm
        
        self.retranslateUi(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "Éditeur GeoJSON", None))