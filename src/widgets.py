# src/widgets.py
from PySide6.QtWidgets import QStyledItemDelegate, QStyle, QApplication, QStyleOptionButton
from logging_setup import logger

class ButtonDelegate(QStyledItemDelegate):
    """
    Un délégué qui se contente de dessiner deux boutons dans une cellule.
    La logique de clic est gérée par la vue elle-même.
    """
    def paint(self, painter, option, index):
        logger.debug(f"paint() appelé pour la ligne {index.row()}. État de l'option: {option.state}")

        # --- CORRECTION FINALE ET ROBUSTE ---
        # On passe une copie de l'option de la cellule aux options des boutons.
        # Cela garantit qu'ils héritent de l'état (sélectionné, focus, etc.).
        
        edit_option = QStyleOptionButton(option)
        edit_option.rect = option.rect
        edit_option.rect.setWidth(option.rect.width() // 2)

        delete_option = QStyleOptionButton(option)
        delete_option.rect = option.rect
        delete_option.rect.setLeft(edit_option.rect.right())

        # Utiliser le style du widget parent (la table) si disponible
        style = option.widget.style() if option.widget else QApplication.style()

        # Dessin du bouton Éditer
        edit_icon = style.standardIcon(QStyle.StandardPixmap.SP_FileDialogInfoView)
        edit_option.icon = edit_icon
        edit_option.iconSize = edit_option.rect.size() * 0.6
        style.drawControl(QStyle.ControlElement.CE_PushButton, edit_option, painter)

        # Dessin du bouton Supprimer
        delete_icon = style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
        delete_option.icon = delete_icon
        delete_option.iconSize = delete_option.rect.size() * 0.6
        style.drawControl(QStyle.ControlElement.CE_PushButton, delete_option, painter)