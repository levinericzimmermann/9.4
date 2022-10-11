def fix_mbrola_voices_path():
    import voxpopuli
    import shutil

    mbrola_binary_path = shutil.which("mbrola")
    voxpopuli.Voice.mbrola_voices_folder = (
        "/".join(mbrola_binary_path.split("/")[:-2]) + "/share/mbrola/voices/"
    )


fix_mbrola_voices_path()
del fix_mbrola_voices_path

# XXX: Ensure music monkey patch is applied!
from mutwo import c9p4_parameters
del c9p4_parameters

from .text_to_speech import *
