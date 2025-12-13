from apps.api.schemas.slide_spec import DeckSpec, ElementSpec, SlideSpec, SlideStats, TextStyle
from apps.api.schemas.template_spec import RgbColor, TemplateSpec, ThemeColors, ThemeFonts
from apps.api.services.audit import audit_engine


def test_audit_engine():
    # 1. Setup Template
    template = TemplateSpec(
        name="Corp Template",
        theme_fonts=ThemeFonts(major="Arial", minor="Inter"),
        theme_colors=ThemeColors(
            accent1=RgbColor(r=255, g=0, b=0) # Red #FF0000
        ),
        masters=[]
    )
    
    # 2. Setup Bad Slide
    slide = SlideSpec(
        index=0,
        layout_name="Title",
        stats=SlideStats(),
        elements=[
            # Bad Font
            ElementSpec(
                id="1", type="TEXT_BOX", name="Title", z_order=1,
                bbox={"x":0,"y":0,"width":100,"height":100},
                text_content="Hello",
                text_style=TextStyle(font_family="Times New Roman", color_hex="FF0000")
            ),
            # Bad Color
            ElementSpec(
                 id="2", type="TEXT_BOX", name="Subtitle", z_order=2,
                 bbox={"x":0,"y":0,"width":100,"height":100},
                 text_content="World",
                 text_style=TextStyle(font_family="Inter", color_hex="00FF00") # Green (Bad)
            ),
             # Stretched Image
            ElementSpec(
                 id="3", type="IMAGE", name="Logo", z_order=3,
                 bbox={"x":0,"y":0,"width":100,"height":100},
                 is_stretched=True
            )
        ]
    )
    
    deck = DeckSpec(filename="test.pptx", slide_count=1, slides=[slide])
    
    # 3. Run Audit
    findings = audit_engine.audit(deck, template)
    
    # 4. Verify Findings
    assert len(findings) == 3
    
    # Check Font Finding
    f_font = next(f for f in findings if f.rule_id == "FONT_MISMATCH")
    assert f_font.element_id == "1"
    assert "Times New Roman" in f_font.message
    
    # Check Color Finding
    f_color = next(f for f in findings if f.rule_id == "COLOR_MISMATCH")
    assert f_color.element_id == "2"
    assert "00FF00" in f_color.message
    
    # Check Image Finding
    f_img = next(f for f in findings if f.rule_id == "IMG_QUALITY")
    assert f_img.element_id == "3"
