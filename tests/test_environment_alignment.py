from pathlib import Path


def test_model_compatibility_version_is_pinned():
    requirements = Path("requirements.txt").read_text(encoding="utf-8")
    assert "scikit-learn==1.6.1" in requirements
