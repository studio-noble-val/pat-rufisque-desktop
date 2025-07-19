# src/widgets.py
import sys
import os
from PySide6.QtWidgets import QStyledItemDelegate, QStyle, QApplication, QStyleOptionButton
from PySide6.QtCore import QRect
from PySide6.QtGui import QIcon

def resource_path(relative_path):
    """
    Obtient le chemin absolu de la ressource, fonctionne pour le développement
    et pour l'exécutable PyInstaller.
    """
    try:
        # PyInstaller crée un dossier temporaire et stocke le chemin dans sys._MEIPASS.
        # La commande --add-data "src/icons:icons" place les fichiers dans un dossier "icons" à la racine.
        base_path = sys._MEIPASS
        final_path = os.path.join(base_path, "icons", relative_path)
    except Exception:
        # sys._MEIPASS n'existe pas, nous sommes donc en mode développement.
        # Le dossier 'icons' se trouve dans le même répertoire que ce script (src/).
        base_path = os.path.dirname(os.path.abspath(__file__))
        final_path = os.path.join(base_path, "icons", relative_path)
        
    return final_path


class ButtonDelegate(QStyledItemDelegate):
    """
    Un délégué qui dessine deux boutons avec des icônes personnalisées dans une cellule.
    La logique de clic est gérée par la vue elle-même (main.py).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Charger les icônes une seule fois lors de la création pour une meilleure performance.
        # La fonction resource_path garantit que les icônes sont trouvées.
        try:
            self.edit_icon = QIcon(resource_path("edit.png"))
            self.delete_icon = QIcon(resource_path("delete.png"))
        except Exception as e:
            # En cas de problème de chargement, on utilise des icônes vides pour éviter un crash.
            print(f"Erreur de chargement des icônes : {e}")
            self.edit_icon = QIcon()
            self.delete_icon = QIcon()


    def paint(self, painter, option, index):
        # Diviser la cellule en deux rectangles, un pour chaque bouton.
        half_width = option.rect.width() // 2
        edit_rect = QRect(option.rect.left(), option.rect.top(), half_width, option.rect.height())
        delete_rect = QRect(option.rect.left() + half_width, option.rect.top(), half_width, option.rect.height())

        # --- Configuration et dessin du bouton "Éditer" ---
        edit_option = QStyleOptionButton()
        edit_option.rect = edit_rect
        edit_option.state = option.state | QStyle.StateFlag.State_Enabled # Hériter l'état (sélection, etc.)
        edit_option.icon = self.edit_icon
        edit_option.iconSize = edit_rect.size() * 0.5 # Icône à 50% de la taille du bouton
        # CORRECTION : Utiliser QStyleOptionButton.ButtonFeature.Flat
        edit_option.features = QStyleOptionButton.ButtonFeature.Flat

        # --- Configuration et dessin du bouton "Supprimer" ---
        delete_option = QStyleOptionButton()
        delete_option.rect = delete_rect
        delete_option.state = option.state | QStyle.StateFlag.State_Enabled
        delete_option.icon = self.delete_icon
        delete_option.iconSize = delete_rect.size() * 0.5
        # CORRECTION : Utiliser QStyleOptionButton.ButtonFeature.Flat
        delete_option.features = QStyleOptionButton.ButtonFeature.Flat

        # Utiliser le style de l'application pour dessiner les contrôles
        style = option.widget.style() if option.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_PushButton, edit_option, painter)
        style.drawControl(QStyle.ControlElement.CE_PushButton, delete_option, painter)