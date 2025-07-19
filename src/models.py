# src/models.py
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from logging_setup import logger

class GeoJsonTableModel(QAbstractTableModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._geojson_data = {}
        self._features = []
        self._headers = []
        self._column_types = {} # Pour stocker les types attendus

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section == 0: return "Actions"
            try:
                header_text = self._headers[section - 1].replace('_', ' ')
                return header_text.capitalize()
            except IndexError: return None
        return None

    def rowCount(self, parent=QModelIndex()): return len(self._features)
    def columnCount(self, parent=QModelIndex()): return len(self._headers) + 1

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid(): return None
        row, col = index.row(), index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return None
            try:
                prop_name = self._headers[col - 1]
                return self._features[row]['properties'].get(prop_name, "")
            except (IndexError, KeyError): return None
        return None
    
    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid() or role != Qt.ItemDataRole.EditRole: return False
        row, col = index.row(), index.column()
        if col == 0: return False
        try:
            prop_name = self._headers[col - 1]
            final_value = value

            # --- VALIDATION DE TYPE ICI ---
            if prop_name in self._column_types:
                if self._column_types[prop_name] == 'int':
                    try:
                        final_value = int(value) if value else 0
                    except (ValueError, TypeError):
                        logger.warning(f"Conversion en entier échouée pour '{value}'. Utilisation de 0.")
                        final_value = 0 # Valeur par défaut en cas d'erreur
            
            if 'properties' not in self._features[row]: self._features[row]['properties'] = {}
            self._features[row]['properties'][prop_name] = final_value
            self.dataChanged.emit(index, index, [Qt.ItemDataRole.EditRole])
            return True
        except IndexError: return False

    def flags(self, index):
        if not index.isValid(): return Qt.ItemFlag.NoItemFlags
        if index.column() > 0: return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled

    def load_data(self, geojson_data, visible_headers=None, column_types=None):
        self.beginResetModel()
        self._geojson_data = geojson_data
        self._features = self._geojson_data.get('features', [])
        self._column_types = column_types or {}
        
        if visible_headers is not None: self._headers = visible_headers
        else:
            all_keys = set()
            for feature in self._features:
                if 'properties' in feature and isinstance(feature['properties'], dict):
                    all_keys.update(feature['properties'].keys())
            self._headers = sorted(list(all_keys))
        self.endResetModel()
        logger.info(f"Données chargées. {len(self._features)} features, types: {self._column_types}")

    def insert_row(self):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        new_properties = {}
        for header in self._headers:
            if self._column_types.get(header) == 'int':
                new_properties[header] = 0
            else:
                new_properties[header] = ""
        new_feature = {"type": "Feature", "properties": new_properties, "geometry": None}
        self._features.append(new_feature)
        self.endInsertRows()
        return True

    def remove_rows(self, rows_to_remove):
        rows_to_remove.sort(reverse=True)
        for row in rows_to_remove:
            self.beginRemoveRows(QModelIndex(), row, row)
            if 0 <= row < len(self._features): del self._features[row]
            self.endRemoveRows()
        return True
    
    def get_all_features(self): return self._features
    def get_headers(self): return self._headers
    def get_geojson_data(self):
        data = self._geojson_data.copy()
        data['features'] = self.get_all_features()
        return data