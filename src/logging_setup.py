# src/logging_setup.py
import logging
import sys

# Créer un logger
logger = logging.getLogger('GeoJSONEditor')
logger.setLevel(logging.DEBUG)  # On capture tous les niveaux de messages

# Créer un gestionnaire qui écrit les logs dans la console
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)

# Créer un formateur pour rendre les logs lisibles
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s (%(filename)s:%(lineno)d)'
)
handler.setFormatter(formatter)

# Ajouter le gestionnaire au logger
# (Vérifier pour ne pas en ajouter plusieurs si ce module est importé plusieurs fois)
if not logger.handlers:
    logger.addHandler(handler)