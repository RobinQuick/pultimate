from services.ingestion import ingestor
from pptx import Presentation


def create_synthetic_template(path):
    prs = Presentation()
    # Add a master/layout structure (default empty prs has one)
    # Add placeholders to first layout
    _layout = prs.slide_masters[0].slide_layouts[0]  # noqa: F841
    # layout has a title placeholder by default usually
    prs.save(path)


def test_ingestion(tmp_path):
    pptx_path = tmp_path / "template.pptx"
    create_synthetic_template(pptx_path)

    spec = ingestor.ingest(str(pptx_path))

    assert spec.name == "Ingested Template"
    assert len(spec.masters) >= 1
    assert len(spec.masters[0].layouts) >= 1

    # Check JSON serialization
    json_output = spec.model_dump(mode="json")
    assert "theme_colors" in json_output
    assert "masters" in json_output
