# src/models.py
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from logging_setup import logger

class GeoJsonTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._features = []; self._base_geojson_struct = {}; self._headers = []
        logger.info("GeoJsonTableModel initialisé.")

    def flags(self, index):
        if not index.isValid(): return Qt.ItemFlag.NoItemFlags
        if index.column() == 0: return Qt.ItemFlag.ItemIsEnabled
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    # Le reste du fichier est correct et inchangé, je le copie pour être complet.
    def get_all_features(self): return self._features
    def get_base_struct(self): return self._base_geojson_struct
    def load_data(self, geojson_data): self.beginResetModel(); logger.info("Chargement de nouvelles données dans le modèle."); self._base_geojson_struct = {k: v for k, v in geojson_data.items() if k != 'features'}; self._features = geojson_data.get('features', []); self._headers = sorted(list(set().union(*(f.get('properties', {}).keys() for f in self._features)))) if self._features else []; self.endResetModel()
    def rowCount(self, parent=QModelIndex()): return len(self._features)
    def columnCount(self, parent=QModelIndex()): return len(self._headers) + 1
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if section == 0: return "Actions"; return self._headers[section - 1]
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid(): return None
        if index.column() == 0: return ""
        if role == Qt.ItemDataRole.DisplayRole: properties = self._features[index.row()].get('properties', {}); header = self._headers[index.column() - 1]; return str(properties.get(header, ""))
        return None
    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if role != Qt.ItemDataRole.EditRole or not index.isValid() or index.column() == 0: return False
        row, col = index.row(), index.column() - 1; header = self._headers[col]
        if 'properties' not in self._features[row]: self._features[row]['properties'] = {}
        self._features[row]['properties'][header] = value; self.dataChanged.emit(index, index, [role]); return True
    def insert_row(self): position = self.rowCount(); self.beginInsertRows(QModelIndex(), position, position); new_blank_feature = {"type": "Feature", "properties": {header: "" for header in self._headers}, "geometry": None}; self._features.append(new_blank_feature); self.endInsertRows(); return True
    def remove_rows(self, rows_to_delete):
        for row_index in sorted(rows_to_delete, reverse=True): self.beginRemoveRows(QModelIndex(), row_index, row_index); del self._features[row_index]; self.endRemoveRows()
        return True