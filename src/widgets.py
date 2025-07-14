# src/widgets.py
from PySide6.QtWidgets import QStyledItemDelegate, QStyle, QApplication, QStyleOptionButton
from PySide6.QtCore import Signal, QEvent, Qt

class ButtonDelegate(QStyledItemDelegate):
    """
    Un délégué pour afficher et gérer un bouton "poubelle" dans une cellule de QTableView.
    """
    delete_row_requested = Signal(int)

    def paint(self, painter, option, index):
        if not index.isValid():
            return
        
        button_option = QStyleOptionButton()
        button_option.rect = option.rect
        button_option.text = ""
        button_option.state = QStyle.StateFlag.State_Enabled
        
        style = QApplication.style()
        icon = style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon)
        button_option.icon = icon
        button_option.iconSize = option.rect.size() / 2
        
        style.drawControl(QStyle.ControlElement.CE_PushButton, button_option, painter)

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            if option.rect.contains(event.pos()):
                self.delete_row_requested.emit(index.row())
                return True
        return False