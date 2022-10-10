import os
import unittest

from mutwo import c9p4_converters


class SequentialEventToSoundFilePathTupleTest(unittest.TestCase):
    def test_convert(self):
        test_text = "hello how are you?"
        sequential_event = c9p4_converters.TextToSequentialEvent().convert(test_text)
        sound_file_path_tuple = (
            c9p4_converters.SequentialEventToSoundFilePathTuple().convert(
                sequential_event
            )
        )
        for sound_file_path in sound_file_path_tuple:
            self.assertTrue(os.path.exists(sound_file_path))

            try:
                os.remove(sound_file_path)
            except FileNotFoundError:
                pass
