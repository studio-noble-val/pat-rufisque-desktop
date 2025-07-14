# src/ui_main_window.py
from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QTableView,
    QPushButton, QLabel, QHeaderView, QStackedWidget, QMenuBar, QSpacerItem, QSizePolicy
)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1200, 700)
        
        self.stacked_widget = QStackedWidget()
        MainWindow.setCentralWidget(self.stacked_widget)

        # --- Page d'Accueil (index 0) ---
        self.welcome_page = QWidget()
        welcome_layout = QVBoxLayout(self.welcome_page)
        welcome_layout.setContentsMargins(50, 50, 50, 50)
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("<h1>Éditeur de Données GeoJSON</h1>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Ce layout contiendra les boutons de sélection de fichier
        self.welcome_buttons_layout = QVBoxLayout()
        self.welcome_buttons_layout.setSpacing(15)

        # Message d'aide
        help_label = QLabel(
            "Si la configuration n'est pas correcte, utilisez le menu <b>Édition > Configuration...</b>"
        )
        help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        help_label.setStyleSheet("font-size: 11px; color: grey; margin-top: 30px;")

        welcome_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        welcome_layout.addWidget(title_label)
        welcome_layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        welcome_layout.addLayout(self.welcome_buttons_layout)
        welcome_layout.addWidget(help_label)
        welcome_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.stacked_widget.addWidget(self.welcome_page)

        # --- Page d'Édition (index 1) ---
        self.editor_page = QWidget()
        main_editor_layout = QVBoxLayout(self.editor_page)
        self.file_selector = QComboBox()
        self.table_view = QTableView()
        self.add_button = QPushButton("Ajouter une ligne")
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Fichier à modifier:"))
        top_layout.addWidget(self.file_selector, 1)
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.add_button)
        bottom_layout.addStretch()
        main_editor_layout.addLayout(top_layout)
        main_editor_layout.addWidget(self.table_view)
        main_editor_layout.addLayout(bottom_layout)
        self.stacked_widget.addWidget(self.editor_page)

        # --- Barre de Menus et de Statut ---
        self.status_label = QLabel()
        MainWindow.statusBar().addWidget(self.status_label)
        self.menubar = QMenuBar()
        MainWindow.setMenuBar(self.menubar)
        
        self.menuFichier = self.menubar.addMenu("&Fichier")
        self.actionAccueil = QAction("&Accueil", MainWindow) # NOUVEAU : Action pour retourner à l'accueil
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
        
        # --- Attribution des widgets à l'instance de MainWindow ---
        MainWindow.stacked_widget = self.stacked_widget
        MainWindow.welcome_buttons_layout = self.welcome_buttons_layout # On expose le layout des boutons
        MainWindow.file_selector = self.file_selector
        MainWindow.table_view = self.table_view
        MainWindow.add_button = self.add_button
        MainWindow.status_label = self.status_label
        MainWindow.actionAccueil = self.actionAccueil
        MainWindow.actionEnregistrer = self.actionEnregistrer
        MainWindow.actionQuitter = self.actionQuitter
        MainWindow.actionConfigurer = self.actionConfigurer
        MainWindow.actionAPropos = self.actionAPropos

        self.retranslateUi(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "Éditeur GeoJSON", None))