import os
import tempfile

os.environ.setdefault("RODOVIA_DATA", tempfile.mkdtemp(prefix="studio-integracao-"))
