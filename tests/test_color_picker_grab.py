import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_SOURCE = ROOT / "app_source"
if str(APP_SOURCE) not in sys.path:
    sys.path.insert(0, str(APP_SOURCE))

import omne_footage_lab as lab


class _PreviousGrab:
    def __init__(self, status="local"):
        self.status = status
        self.local_calls = 0
        self.global_calls = 0

    def winfo_exists(self):
        return True

    def grab_status(self):
        return self.status

    def grab_set(self):
        self.local_calls += 1

    def grab_set_global(self):
        self.global_calls += 1


class _Parent:
    def __init__(self, previous=None):
        self.previous = previous
        self.parent_grab_calls = 0

    def grab_current(self):
        return self.previous

    def wait_window(self, _dialog):
        return None

    def winfo_exists(self):
        return True

    def grab_set(self):
        self.parent_grab_calls += 1


class _Dialog:
    def __init__(self, _parent, _initial, _title):
        self.result = "#123456"


class AdvancedColorPickerGrabTests(unittest.TestCase):
    def choose(self, parent):
        return lab.AdvancedColorPicker.choose.__func__(_Dialog, parent, "#FFFFFF", "Choose")

    def test_closing_picker_without_prior_grab_leaves_interface_ungrabbed(self):
        parent = _Parent()
        self.assertEqual(self.choose(parent), "#123456")
        self.assertEqual(parent.parent_grab_calls, 0)

    def test_closing_picker_restores_existing_local_modal_grab(self):
        previous = _PreviousGrab("local")
        parent = _Parent(previous)
        self.choose(parent)
        self.assertEqual(previous.local_calls, 1)
        self.assertEqual(previous.global_calls, 0)
        self.assertEqual(parent.parent_grab_calls, 0)

    def test_closing_picker_restores_existing_global_modal_grab(self):
        previous = _PreviousGrab("global")
        parent = _Parent(previous)
        self.choose(parent)
        self.assertEqual(previous.local_calls, 0)
        self.assertEqual(previous.global_calls, 1)
        self.assertEqual(parent.parent_grab_calls, 0)


if __name__ == "__main__":
    unittest.main()
