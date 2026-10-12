"""The commonforms/rfdetr workaround, on fake predictions (no model weights)."""

import sys
from types import ModuleType, SimpleNamespace

import pytest

from app.services.commonforms_compat import _one_page_batches, patch_commonforms_detector


class FakeDetector:
    def __init__(self, predict):
        self.model = SimpleNamespace(predict=predict)

    def extract_widgets(self, pages, confidence=0.4, image_size=1120, batch_size=3):
        # Same batching as commonforms 0.2.1 FFDetrDetector.extract_widgets
        results = []
        for i in range(0, len(pages), batch_size):
            predictions = self.model.predict(pages[i:i + batch_size], threshold=confidence)
            if len(pages) == 1 or batch_size == 1:
                predictions = [predictions]
            results.extend(predictions)
        return results


def rfdetr_1_9(images, threshold):
    # >= 1.9: a list in always gives a list out
    return [f"det-{img}" for img in images]


def rfdetr_1_8(images, threshold):
    # < 1.9: a one-image result comes back unwrapped
    out = [f"det-{img}" for img in images]
    return out if len(out) > 1 else out[0]


@pytest.mark.parametrize("predict", [rfdetr_1_9, rfdetr_1_8])
@pytest.mark.parametrize("n_pages", [1, 2, 4, 7])
def test_one_detection_result_per_page(predict, n_pages):
    pages = list(range(n_pages))
    extract_widgets = _one_page_batches(FakeDetector.extract_widgets)

    results = extract_widgets(FakeDetector(predict), pages, confidence=0.4)

    assert results == [f"det-{p}" for p in pages]


def _fake_commonforms(monkeypatch, detector_cls):
    module = ModuleType("commonforms.inference")
    module.FFDetrDetector = detector_cls
    monkeypatch.setitem(sys.modules, "commonforms.inference", module)


def test_patch_applies_once(monkeypatch):
    class Detector(FakeDetector):
        pass

    _fake_commonforms(monkeypatch, Detector)
    patch_commonforms_detector()
    patched = Detector.extract_widgets
    patch_commonforms_detector()

    assert patched._fireform_compat
    assert Detector.extract_widgets is patched
    assert Detector(rfdetr_1_9).extract_widgets([0]) == ["det-0"]


def test_patch_is_a_noop_when_commonforms_changes(monkeypatch):
    class Renamed:
        def extract_widgets(self, pages):
            return "untouched"

    _fake_commonforms(monkeypatch, Renamed)
    patch_commonforms_detector()
    assert Renamed().extract_widgets([0]) == "untouched"

    monkeypatch.setitem(sys.modules, "commonforms.inference", None)
    patch_commonforms_detector()  # ImportError is logged, not raised
