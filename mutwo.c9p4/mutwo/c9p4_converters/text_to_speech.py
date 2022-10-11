import concurrent.futures
import functools
import random
import typing
import uuid

import voxpopuli

from mutwo import core_converters
from mutwo import core_events
from mutwo import mbrola_converters
from mutwo import music_events
from mutwo import music_parameters

VOWEL_SET = functools.reduce(
    lambda set0, set1: set0.union(set1),
    (
        phoneme_set.VOWELS
        for phoneme_set in (
            voxpopuli.FrenchPhonemes,
            voxpopuli.BritishEnglishPhonemes,
            voxpopuli.AmericanEnglishPhonemes,
            voxpopuli.SpanishPhonemes,
            voxpopuli.GermanPhonemes,
            voxpopuli.ItalianPhonemes,
            voxpopuli.PortuguesePhonemes,
            voxpopuli.GreekPhonemes,
            voxpopuli.ArabicPhonemes,
        )
    ),
)


def is_vowel(phonetic_string: str) -> bool:
    return phonetic_string in VOWEL_SET


class TextToSequentialEvent(core_converters.abc.Converter):
    string_to_replace_tuple = tuple("? ! .".split(" "))

    def convert(
        self, text_to_convert: str, language_code: typing.Optional[str] = None
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
                if is_vowel(phoneme):
                    duration = random.uniform(0.25, 0.5)
                    pitch = music_parameters.JustIntonationPitch(
                        random.choice("1/2 1/4".split(" "))
                    )
                else:
                    duration = random.uniform(0.1, 0.3)
                    pitch = None
                note_like = music_events.NoteLike(
                    [
                        pitch
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
                    lyric=music_parameters.LanguageBasedLyric(
                        phoneme, language_code=language_code
                    ),
                )
                word_sequential_event.append(note_like)
            sequential_event.append(word_sequential_event)
        return sequential_event


class EventToPhonemeList(mbrola_converters.EventToPhonemeList):
    def _pitch_to_pitch_modification_list(
        self, pitch: typing.Optional[music_parameters.abc.Pitch]
    ) -> list[tuple[int, int]]:
        pitch_modification_list = []
        if pitch:
            frequency = pitch.frequency
            if choosen := random.choice([True, False, None]):
                pitch_modification_list = [
                    [0, frequency],
                    [random.uniform(40, 80), frequency],
                    [100, frequency * random.uniform(0.85, 1.35)],
                ]
            elif choosen is None:
                pitch_modification_list = [[0, frequency], [100, frequency]]
            else:
                pitch_modification_list = [
                    [0, frequency * random.uniform(0.85, 1.35)],
                    [random.uniform(20, 50), frequency],
                    [100, frequency],
                ]
        return pitch_modification_list


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

        event_to_phoneme_list = EventToPhonemeList(
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
        self.event_to_phoneme_list = event_to_phoneme_list

    def convert(
        self,
        sequential_event_to_convert: core_events.SequentialEvent[
            core_events.SequentialEvent[music_events.NoteLike]
        ],
        base_path: typing.Optional[str] = None,
        language: str = "de",
    ) -> tuple[str, ...]:
        if not base_path:
            base_path = str(uuid.uuid4())

        self.event_to_speak_synthesis = mbrola_converters.EventToSpeakSynthesis(
            event_to_phoneme_list=self.event_to_phoneme_list,
            voice=voxpopuli.Voice(lang=language),
        )

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
