import os

from mutwo import c9p4_interfaces
import pyo
import walkman


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
                    self.sound_file_player.setPath(
                        new_sound_file_path
                    )
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
