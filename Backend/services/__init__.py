"""Services module initialization"""

from .claude_service import claude_service
from .cadquery_service import cadquery_service
from .parametric_cad_service import parametric_cad_service
from .product_library import search_products, lookup as product_lookup

# Database service (requires supabase package)
try:
    from .database_service import database_service
    DB_IMPORT_OK = True
except ImportError:
    database_service = None
    DB_IMPORT_OK = False

# Phase 4: Optional S3 service (requires boto3)
try:
    from .s3_service import s3_service
    S3_AVAILABLE = True
except ImportError:
    s3_service = None
    S3_AVAILABLE = False

# Phase 4: Optional GLB service (requires trimesh)
try:
    from .glb_service import glb_service
    GLB_AVAILABLE = True
except ImportError:
    glb_service = None
    GLB_AVAILABLE = False

# CAD Import service (file upload support)
from .cad_import_service import cad_import_service, SUPPORTED_FORMATS as CAD_SUPPORTED_FORMATS

# PCB Design service (electronics + enclosure integration)
from .pcb_design_service import pcb_design_service
from .pcb_component_library import (
    search_components as pcb_search_components,
    get_component as pcb_get_component,
    list_categories as pcb_list_categories,
    COMPONENTS as PCB_COMPONENTS,
)

__all__ = [
    'claude_service', 
    'cadquery_service', 
    'parametric_cad_service', 
    'database_service',
    'DB_IMPORT_OK',
    'search_products',
    'product_lookup',
    's3_service', 
    'S3_AVAILABLE',
    'glb_service',
    'GLB_AVAILABLE',
    'cad_import_service',
    'CAD_SUPPORTED_FORMATS',
    'pcb_design_service',
    'pcb_search_components',
    'pcb_get_component',
    'pcb_list_categories',
    'PCB_COMPONENTS',
]
