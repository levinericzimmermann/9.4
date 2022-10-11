import collections
import concurrent.futures
import os

from mutwo import c9p4_converters
from mutwo import c9p4_generators


class SpeechSoundFileStack(collections.deque):
    def __init__(
        self,
        text_generator: c9p4_generators.TextGenerator = c9p4_generators.OfflineTextGenerator(),
        text_to_sequential_event: c9p4_converters.TextToSequentialEvent = c9p4_converters.TextToSequentialEvent(),
        sequential_event_to_sound_file_path_tuple: c9p4_converters.SequentialEventToSoundFilePathTuple = c9p4_converters.SequentialEventToSoundFilePathTuple(),
        recreate_limit: int = 40,
    ):
        super().__init__([])
        self._is_working = False
        self.text_generator = text_generator
        self.text_to_sequential_event = text_to_sequential_event
        self.sequential_event_to_sound_file_path_tuple = (
            sequential_event_to_sound_file_path_tuple
        )
        self.recreate_limit = recreate_limit
        self.thread_pool_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        self._fill(thread=False)

    def _fill(self, thread: bool = True):
        def get_sound_file_path_tuple():
            text = self.text_generator()
            sequential_event = self.text_to_sequential_event(text)
            sound_file_path_tuple = self.sequential_event_to_sound_file_path_tuple(
                sequential_event
            )
            return sound_file_path_tuple

        if thread:
            self._is_working = True
            future = self.thread_pool_executor.submit(get_sound_file_path_tuple)
            future.add_done_callback(lambda future: self.extend(future.result()))
            future.add_done_callback(lambda _: setattr(self, "_is_working", False))

        else:
            sound_file_path_tuple = get_sound_file_path_tuple()
            self.extend(sound_file_path_tuple)

    def fill(self):
        if len(self) <= self.recreate_limit:
            if not self._is_working:
                self._fill()

    def close(self):
        self.thread_pool_executor.shutdown()
        for sound_file_path in self:
            os.remove(sound_file_path)

    def pop(self, *args, **kwargs) -> str:
        self.fill()
        return super().pop(*args, **kwargs)

    def popleft(self, *args, **kwargs) -> str:
        self.fill()
        return super().popleft(*args, **kwargs)
