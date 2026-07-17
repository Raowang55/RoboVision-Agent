"""PPE statistics only use explicit negative detector classes."""

from app.runtime.unified_pipeline import _has_explicit_ppe_violation


def test_positive_items_do_not_imply_violation():
    detections = [{"class_name": "person"}, {"class_name": "helmet"}]
    assert not _has_explicit_ppe_violation(detections)


def test_negative_classes_are_violations():
    assert _has_explicit_ppe_violation([{"class_name": "no-helmet"}])
    assert _has_explicit_ppe_violation([{"class_name": "no-vest"}])
