"""Monkey patch music_parameters to make LanguageBasedLyric more performant."""

import typing

import epitran

from mutwo import music_parameters


class LanguageBasedLyric(music_parameters.abc.Lyric):
    """Lyric based on a natural language.

    :param written_representation: The text.
    :type written_representation: str
    :param language_code: The code for the language of the text.
        If this is `None` the constant
        `mutwo.music_parameters.configurations.DEFAULT_LANGUAGE_CODE`
        will be used. Default to `None`.
    :type language_code: typing.Optional[str]
    """

    language_code_to_epitran_dict: dict[str, epitran.Epitran] = {}

    def __init__(
        self, written_representation: str, language_code: typing.Optional[str] = None
    ):
        if language_code is None:
            language_code = music_parameters.configurations.DEFAULT_LANGUAGE_CODE

        self.written_representation = written_representation
        self.language_code = language_code

    @property
    def language_code(self) -> str:
        return self._language_code

    @language_code.setter
    def language_code(self, language_code: str):
        # Epitran will raise an error (FileNotFound) in case
        # the language_code doesn't exist.
        if language_code not in self.language_code_to_epitran_dict:
            self.language_code_to_epitran_dict.update(
                {language_code: epitran.Epitran(language_code)}
            )

        self._epitran = self.language_code_to_epitran_dict[language_code]
        self._language_code = language_code

    @property
    def written_representation(self) -> str:
        return self._written_representation

    @written_representation.setter
    def written_representation(self, written_representation: str):
        self._written_representation = written_representation

    @property
    def phonetic_representation(self) -> str:
        word_tuple = self.written_representation.split(" ")
        return " ".join(
            ["".join(self._epitran.xsampa_list(word)) for word in word_tuple]
        )


music_parameters.LanguageBasedLyric = LanguageBasedLyric
