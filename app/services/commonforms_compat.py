"""Workaround for commonforms 0.2.1 with rfdetr >= 1.9 (remove once fixed upstream).

rfdetr 1.9.0 made predict() return a list whenever it is given a list, even a
one-image list. commonforms 0.2.1 (FFDetrDetector.extract_widgets) predicts
pages in batches of 3 and wraps the result in a list itself for one-page PDFs,
so those fail with "'list' object has no attribute 'with_nms'". With rfdetr
< 1.9 the same code fails instead for 4, 7, 10... pages (last batch of one).

Running one page per batch (commonforms then always wraps) and unwrapping
predict()'s one-element list is correct with either rfdetr behaviour.
"""

import inspect
import logging

logger = logging.getLogger(__name__)


def _one_page_batches(extract_widgets):
    def wrapper(self, pages, *args, **kwargs):
        predict = getattr(getattr(self, "model", None), "predict", None)
        if predict is None:  # upstream changed shape: run it unpatched
            return extract_widgets(self, pages, *args, **kwargs)

        def predict_one(images, *a, **kw):
            out = predict(images, *a, **kw)
            return out[0] if isinstance(out, list) and len(out) == 1 else out

        self.model.predict = predict_one
        kwargs["batch_size"] = 1
        return extract_widgets(self, pages, *args, **kwargs)

    wrapper._fireform_compat = True
    return wrapper


def patch_commonforms_detector() -> None:
    # Never let the workaround itself break make-fillable: if commonforms
    # renamed what we patch, log it and leave commonforms as it is.
    try:
        from commonforms.inference import FFDetrDetector

        extract_widgets = FFDetrDetector.extract_widgets
        if getattr(extract_widgets, "_fireform_compat", False):
            return
        if "batch_size" not in inspect.signature(extract_widgets).parameters:
            raise AttributeError("extract_widgets() has no batch_size parameter")
    except (ImportError, AttributeError) as e:
        logger.warning("commonforms compat patch not applied: %s", e)
        return

    FFDetrDetector.extract_widgets = _one_page_batches(extract_widgets)
