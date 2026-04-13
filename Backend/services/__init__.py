"""Services module initialization"""

from .claude_service import claude_service
from .parametric_cad_service import parametric_cad_service

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

__all__ = [
    'claude_service', 
    'parametric_cad_service', 
    'database_service',
    'DB_IMPORT_OK',
    's3_service', 
    'S3_AVAILABLE',
    'glb_service',
    'GLB_AVAILABLE',
    'cad_import_service',
    'CAD_SUPPORTED_FORMATS',
]
