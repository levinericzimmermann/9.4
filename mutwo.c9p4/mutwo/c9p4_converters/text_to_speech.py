import random
import typing
import uuid

from mutwo import core_converters
from mutwo import core_events
from mutwo import mbrola_converters
from mutwo import music_events
from mutwo import music_parameters


class TextToSequentialEvent(core_converters.abc.Converter):
    string_to_replace_tuple = tuple("? ! .".split(" "))

    def convert(
        self, text_to_convert: str
    ) -> core_events.SequentialEvent[music_events.NoteLike]:
        for string_to_replace in self.string_to_replace_tuple:
            text_to_convert.replace(string_to_replace, "")

        word_list = text_to_convert.split(" ")
        sequential_event = core_events.SequentialEvent([])
        for word in word_list:
            duration = random.uniform(0.5, 2)
            note_like = music_events.NoteLike(
                "1/1", duration, "mp", lyric=music_parameters.LanguageBasedLyric(word)
            )
            sequential_event.append(note_like)
        return sequential_event


class SequentialEventToSoundFilePathTuple(core_converters.abc.Converter):
    def __init__(self):
        def simple_event_to_phoneme_string(
            event_to_convert: music_events.NoteLike,
        ) -> str:
            lyric = getattr(
                event_to_convert, "lyric", music_parameters.LanguageBasedLyric("")
            )
            phoneme_string = lyric.phonetic_representation
            if not phoneme_string:
                phoneme_string = "_"
            return phoneme_string

        self.event_to_speak_synthesis = mbrola_converters.EventToSpeakSynthesis(
            event_to_phoneme_list=mbrola_converters.EventToPhonemeList(
                simple_event_to_phoneme_string=simple_event_to_phoneme_string
            )
        )

    def convert(
        self,
        sequential_event_to_convert: core_events.SequentialEvent[music_events.NoteLike],
        base_path: typing.Optional[str] = None,
    ) -> tuple[str, ...]:
        if not base_path:
            base_path = str(uuid.uuid4())

        sound_file_path_list = []
        for note_like_index, note_like in enumerate(sequential_event_to_convert):
            path = f"{base_path}_{note_like_index}.wav"
            self.event_to_speak_synthesis.convert(note_like, path)

        return tuple(sound_file_path_list)
