"""
Cada dimensión tiene su propio Blueprint en un archivo aparte.
Así cada integrante trabaja solo en su archivo y se evitan conflictos
al momento de unir las ramas en main.
"""

from routes.poblacional import bp as poblacional_bp
from routes.territorial import bp as territorial_bp
from routes.temporal import bp as temporal_bp
from routes.multivariada import bp as multivariada_bp

BLUEPRINTS = [poblacional_bp, territorial_bp, temporal_bp, multivariada_bp]
