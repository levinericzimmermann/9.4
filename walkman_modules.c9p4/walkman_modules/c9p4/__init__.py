from __future__ import annotations
import os
import random
import typing
import sys

import numpy as np
from mutwo import c9p4_interfaces
import pyo
import walkman

# http://ajaxsoundstudio.com/pyodoc/perftips.html#adjust-the-interpreter-s-check-interval
# AttributeError: module 'sys' has no attribute 'setcheckinterval'
# sys.setcheckinterval(500)


class Speaker(
    walkman.ModuleWithDecibel,
    audio_input=walkman.Catch(walkman.constants.EMPTY_MODULE_INSTANCE_NAME),
    threshold=walkman.AutoSetup(walkman.Value, module_kwargs={"value": -12}),
):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.speech_sound_file_stack = c9p4_interfaces.SpeechSoundFileStack()
        self.path_to_remove_list = []

    def _setup_pyo_object(self):
        def play():
            if not self.sound_file_player.isPlaying():
                try:
                    new_sound_file_path = self.speech_sound_file_stack.popleft()
                except IndexError:
                    pass
                else:
                    old_sound_file_path = self.sound_file_player.path
                    self.sound_file_player.setPath(new_sound_file_path)
                    self.path_to_remove_list.append(old_sound_file_path)
                self.sound_file_player.play()

        def stop():
            self.sound_file_player.stop()

        super()._setup_pyo_object()
        self.sound_file_player = pyo.SfPlayer(
            self.speech_sound_file_stack[0],
            mul=self.amplitude_signal_to,
            interp=1,
        ).stop()
        self.sound_file_player_stop_trigger = pyo.TrigFunc(
            self.sound_file_player["trig"][0], stop
        )
        self.amplitude_follower = pyo.Follower(self.audio_input.pyo_object)
        self.sound_file_player.stop()
        self.threshold_value_in_amplitude = pyo.DBToA(self.threshold.pyo_object)
        self.threshold_trigger = pyo.Thresh(
            self.amplitude_follower, threshold=self.threshold_value_in_amplitude
        )
        self.trigger_function = pyo.TrigFunc(self.threshold_trigger, play)
        self.internal_pyo_object_list.extend(
            [
                self.sound_file_player,
                self.amplitude_follower,
                self.trigger_function,
                self.threshold_value_in_amplitude,
            ]
        )

    @property
    def _pyo_object(self) -> pyo.PyoObject:
        return self.sound_file_player

    def close(self):
        super().close()
        self.speech_sound_file_stack.close()
        for path in self.path_to_remove_list:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass


class Degrader(
    walkman.ModuleWithDecibel,
    audio_input=walkman.Catch(walkman.constants.EMPTY_MODULE_INSTANCE_NAME),
    bitdepth=walkman.AutoSetup(walkman.Value, module_kwargs={"value": 4}),
    sample_rate_scale=walkman.AutoSetup(walkman.Value, module_kwargs={"value": 0.8}),
):
    def _setup_pyo_object(self):
        super()._setup_pyo_object()
        self.degrade = pyo.Degrade(
            self.audio_input.pyo_object,
            bitdepth=self.bitdepth.pyo_object_or_float,
            srscale=self.sample_rate_scale.pyo_object_or_float,
            mul=self.amplitude_signal_to,
        )
        self.internal_pyo_object_list.extend([self.degrade])

    @property
    def _pyo_object(self) -> pyo.PyoObject:
        return self.degrade


class MidiLogger(walkman.Module):
    def _setup_pyo_object(self):
        super()._setup_pyo_object()

        def ctl_scan(control_number: int, midi_channel: int):
            print("Control number:", control_number, "Midi channel:", midi_channel)

        self.midi_control_scanner = pyo.CtlScan2(ctl_scan)

        self.internal_pyo_object_list.extend([self.midi_control_scanner])

    @property
    def _pyo_object(self) -> pyo.PyoObject:
        return self.midi_control_scanner


Frequency = float
Amplitude = float
DecayRate = float
Partial = tuple[Frequency, Amplitude, DecayRate]


class Resonator(
    walkman.ModuleWithDecibel,
    decibel=walkman.AutoSetup(walkman.Parameter),
    pitch_ratio=walkman.AutoSetup(walkman.Value, module_kwargs={"value": 1}),
    audio_input=walkman.Catch(walkman.constants.EMPTY_MODULE_INSTANCE_NAME),
):
    default_frequency = 220

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _setup_pyo_object(self):
        super()._setup_pyo_object()

        self.pick_octave = pyo.Choice([0.5, 1, 2], freq=random.uniform(0.4, 0.9))
        self.octave = pyo.Port(self.pick_octave)
        self.base_pitch = (
            self.octave * self.default_frequency * self.pitch_ratio.pyo_object_or_float
        )

        internal_pyo_object_list = [self.pick_octave, self.octave, self.base_pitch]

        frequency_list = []
        decay_list = []
        amplitude_list = []

        partial_count = 8
        for partial_index in range(partial_count):
            positive_partial_index = partial_index + 1

            frequency = self.base_pitch * partial_index
            decay = 1 / positive_partial_index
            amplitude = (
                (
                    pyo.LFO(
                        freq=random.uniform(0.9, 7), type=int(random.uniform(0, 7)) + 1
                    )
                )
                / 2
            ) * (1 / positive_partial_index)

            frequency_list.append(frequency)
            decay_list.append(decay)
            amplitude_list.append(amplitude)

        complex_resonator = pyo.ComplexRes(
            self.audio_input.pyo_object,
            freq=frequency_list,
            decay=decay_list,
            mul=amplitude_list,
        ).stop()
        mixed_resonator = complex_resonator.mix(1) * self.amplitude_signal_to
        complex_resonator_with_applied_amplitude = mixed_resonator

        internal_pyo_object_list.extend(
            [
                mixed_resonator,
                complex_resonator_with_applied_amplitude,
                complex_resonator,
            ]
        )

        self.internal_pyo_object_list.extend(internal_pyo_object_list)

        self.resonator = complex_resonator_with_applied_amplitude

    @property
    def _pyo_object(self) -> pyo.PyoObject:
        return self.resonator


class PitchRatioDetector(
    walkman.Module,
    audio_input=walkman.Catch(walkman.constants.EMPTY_MODULE_INSTANCE_NAME),
):
    def __init__(
        self,
        *args,
        min_frequency=walkman.AutoSetup(walkman.Value, module_kwargs={"value": 100}),
        max_frequency=walkman.AutoSetup(walkman.Value, module_kwargs={"value": 400}),
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.min_frequency = min_frequency
        self.max_frequency = max_frequency

    def _setup_pyo_object(self):
        super()._setup_pyo_object()
        self.yin = pyo.Yin(
            self.audio_input.pyo_object,
            minfreq=self.min_frequency,
            maxfreq=self.max_frequency,
            cutoff=self.max_frequency,
        )
        self.midi_note = pyo.FToM(self.yin)
        self.midi_pitch_class = self.midi_note % 12
        self.pitch_class_frequency = pyo.MToF(self.midi_pitch_class)
        self.pitch_ratio = self.midi_pitch_class / 13.5

        self.internal_pyo_object_list.extend(
            [self.yin, self.midi_pitch_class, self.pitch_ratio]
        )

    @property
    def _pyo_object(self) -> pyo.PyoObject:
        return self.pitch_ratio
