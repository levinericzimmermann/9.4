import concurrent.futures
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
    ) -> core_events.SequentialEvent[
        core_events.SequentialEvent[music_events.NoteLike]
    ]:
        for string_to_replace in self.string_to_replace_tuple:
            text_to_convert.replace(string_to_replace, "")

        word_list = text_to_convert.split(" ")
        sequential_event = core_events.SequentialEvent([])
        for word in word_list:
            word_sequential_event = core_events.SequentialEvent([])
            for phoneme in word:
                duration = random.uniform(0.2, 0.4)
                note_like = music_events.NoteLike(
                    [
                        music_parameters.DirectPitch(random.uniform(0.25, 3) * 200)
                        # music_parameters.JustIntonationPitch(
                        #     "1/2",
                        #     # envelope=[
                        #     #     [0, music_parameters.DirectPitchInterval(0)],
                        #     #     [1, music_parameters.DirectPitchInterval(-400)],
                        #     # ],
                        # )
                    ],
                    duration,
                    "mp",
                    lyric=music_parameters.LanguageBasedLyric(phoneme),
                )
                word_sequential_event.append(note_like)
            sequential_event.append(word_sequential_event)
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

        event_to_phoneme_list = mbrola_converters.EventToPhonemeList(
            simple_event_to_phoneme_string=simple_event_to_phoneme_string
        )
        event_to_phoneme_list_convert = event_to_phoneme_list.convert

        def event_to_phoneme_list_convert_new(self, *args, **kwargs):
            return_value = event_to_phoneme_list_convert(self, *args, **kwargs)
            # Optional logging
            if 0:
                print("phoneme list")
                for phoneme in return_value:
                    print(phoneme.name)
                    print(phoneme.duration)
                    print(phoneme.pitch_modifiers)
                print("")
            return return_value

        event_to_phoneme_list.convert = event_to_phoneme_list_convert_new

        self.event_to_speak_synthesis = mbrola_converters.EventToSpeakSynthesis(
            event_to_phoneme_list=event_to_phoneme_list
        )

    def convert(
        self,
        sequential_event_to_convert: core_events.SequentialEvent[
            core_events.SequentialEvent[music_events.NoteLike]
        ],
        base_path: typing.Optional[str] = None,
    ) -> tuple[str, ...]:
        if not base_path:
            base_path = str(uuid.uuid4())

        sound_file_path_list = []
        future_list = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            for sequential_event_index, sequential_event in enumerate(
                sequential_event_to_convert
            ):
                path = f"{base_path}_{sequential_event_index}.wav"
                future = executor.submit(
                    self.event_to_speak_synthesis.convert, sequential_event, path
                )
                future_list.append(future)
                sound_file_path_list.append(path)

        return tuple(sound_file_path_list)
