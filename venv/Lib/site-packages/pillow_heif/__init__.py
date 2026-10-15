"""Provide all possible stuff that can be used."""


# start delvewheel patch
def _delvewheel_patch_1_13_1():
    import os
    if os.path.isdir(libs_dir := os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, '.'))):
        os.add_dll_directory(libs_dir)


_delvewheel_patch_1_13_1()
del _delvewheel_patch_1_13_1
# end delvewheel patch

from . import options
from ._lib_info import libheif_info, libheif_version
from ._version import __version__
from .as_plugin import (
    HeifImageFile,
    register_heif_opener,
)
from .constants import (
    HeifColorPrimaries,
    HeifDepthRepresentationType,
    HeifMatrixCoefficients,
    HeifTransferCharacteristics,
)
from .heif import (
    HeifAuxImage,
    HeifDepthImage,
    HeifFile,
    HeifImage,
    HeifThumbnail,
    encode,
    from_bytes,
    from_pillow,
    is_supported,
    open_heif,
    read_heif,
)
from .misc import get_file_mimetype, load_libheif_plugin, set_orientation

__all__ = [
    "HeifAuxImage",
    "HeifColorPrimaries",
    "HeifDepthImage",
    "HeifDepthRepresentationType",
    "HeifFile",
    "HeifImage",
    "HeifImageFile",
    "HeifMatrixCoefficients",
    "HeifThumbnail",
    "HeifTransferCharacteristics",
    "__version__",
    "encode",
    "from_bytes",
    "from_pillow",
    "get_file_mimetype",
    "is_supported",
    "libheif_info",
    "libheif_version",
    "load_libheif_plugin",
    "open_heif",
    "options",
    "read_heif",
    "register_heif_opener",
    "set_orientation",
]
