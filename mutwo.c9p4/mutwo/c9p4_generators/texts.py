import abc
import itertools
import typing

from mutwo import c9p4_generators


class TextGenerator(abc.ABC):
    @abc.abstractmethod
    def __call__(self) -> str:
        ...


class OfflineTextGenerator(TextGenerator):
    def __init__(
        self, offline_text: typing.Optional[str] = None, word_count_per_call: int = 100
    ):
        if offline_text is None:
            offline_text = c9p4_generators.configurations.DEFAULT_OFFLINE_TEXT
        self.word_cycle = itertools.cycle(offline_text.split(" "))
        self.word_count_per_call = word_count_per_call

    def __call__(self) -> str:
        return " ".join(
            [next(self.word_cycle) for _ in range(self.word_count_per_call)]
        )
