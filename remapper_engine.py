"""Background keyboard listener that applies key remappings."""

from threading import Event, Thread

from pynput import keyboard
from pynput._util import AbstractListener

from key_utils import key_to_id, parse_key_id


class RemapperListener(keyboard.Listener):
    """Keyboard listener that suppresses only mapped source keys.

    pynput's ``suppress=True`` blocks every key on Windows. This listener
    posts events to the remapper callbacks first, then suppresses only keys
    that appear in the active mapping table.
    """

    def __init__(self, should_suppress, **kwargs):
        self._should_suppress = should_suppress
        super().__init__(suppress=False, **kwargs)

    @AbstractListener._emitter
    def _handler(self, code, msg, lpdata):
        suppress_this = False
        try:
            converted = self._convert(code, msg, lpdata)
            if converted is not None:
                suppress_this = self._should_suppress(*converted)
                self._message_loop.post(self._WM_PROCESS, *converted)
        except NotImplementedError:
            self._handle_message(code, msg, lpdata)

        if suppress_this:
            self.suppress_event()


class RemapperEngine:
    def __init__(self, mappings: dict[str, str]):
        self.mappings = dict(mappings)
        self.controller = keyboard.Controller()
        self._active_sources: set[str] = set()
        self._listener: RemapperListener | None = None
        self._thread: Thread | None = None
        self._stop_event = Event()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def set_mappings(self, mappings: dict[str, str]) -> None:
        self.mappings = dict(mappings)

    def start(self) -> None:
        if self.running:
            return
        self._stop_event.clear()
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._listener is not None:
            self._listener.stop()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
        self._release_all()

    def _release_all(self) -> None:
        for source_id in list(self._active_sources):
            target_id = self.mappings.get(source_id)
            if target_id:
                try:
                    self.controller.release(parse_key_id(target_id))
                except (ValueError, KeyError):
                    pass
        self._active_sources.clear()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self._listener = RemapperListener(
                should_suppress=self._should_suppress,
                on_press=self._on_press,
                on_release=self._on_release,
            )
            with self._listener:
                self._listener.join()
            if not self._stop_event.is_set():
                self._release_all()

    def _should_suppress(self, message: int, vk: int) -> bool:
        key = self._message_to_key(self._listener, message, vk)
        if key is None:
            return False
        source_id = key_to_id(key)
        return source_id is not None and source_id in self.mappings

    @staticmethod
    def _message_to_key(listener: RemapperListener | None, message: int, vk: int):
        if listener is None:
            return None
        if message & listener._INJECTED_FLAG:
            return None

        is_utf16 = message & listener._UTF16_FLAG
        msg = message & ~(listener._UTF16_FLAG | listener._INJECTED_FLAG)
        if is_utf16:
            import six

            return keyboard.KeyCode.from_char(six.unichr(vk))

        try:
            return listener._event_to_key(msg, vk)
        except OSError:
            return None

    def _on_press(self, key, injected: bool = False) -> None:
        if injected:
            return None
        source_id = key_to_id(key)
        if source_id is None or source_id not in self.mappings:
            return None
        if source_id in self._active_sources:
            return None
        try:
            self.controller.press(parse_key_id(self.mappings[source_id]))
            self._active_sources.add(source_id)
        except (ValueError, KeyError):
            return None
        return None

    def _on_release(self, key, injected: bool = False) -> None:
        if injected:
            return None
        source_id = key_to_id(key)
        if source_id is None or source_id not in self.mappings:
            return None
        if source_id not in self._active_sources:
            return None
        try:
            self.controller.release(parse_key_id(self.mappings[source_id]))
        except (ValueError, KeyError):
            pass
        self._active_sources.discard(source_id)
        return None


def capture_key(timeout: float | None = None, cancel: Event | None = None) -> str | None:
    """Block until the user presses a key and return its string identifier."""
    captured: list[str | None] = [None]
    done = Event()

    def on_press(key, injected: bool = False):
        if injected:
            return None
        key_id = key_to_id(key)
        if key_id is not None:
            captured[0] = key_id
            done.set()
            return False
        return None

    listener = keyboard.Listener(on_press=on_press, suppress=False)
    listener.start()

    if cancel is not None:
        while not done.wait(timeout=0.1):
            if cancel.is_set():
                listener.stop()
                listener.join(timeout=1)
                return None
            if timeout is not None:
                timeout -= 0.1
                if timeout <= 0:
                    break
        finished = done.is_set()
    else:
        finished = done.wait(timeout=timeout)

    listener.stop()
    listener.join(timeout=1)
    return captured[0] if finished else None
