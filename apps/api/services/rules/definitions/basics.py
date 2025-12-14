
from schemas.slide_spec import SlideSpec
from schemas.template_spec import TemplateSpec
from base import BaseRule, FindingSpec
from registry import registry


@registry.register
class FontRule(BaseRule):
    id = "FONT_MISMATCH"
    description = "Text uses a font not defined in the template theme."
    severity = "HIGH"

    def check(self, slide: SlideSpec, template: TemplateSpec) -> list[FindingSpec]:
        findings = []
        allowed_fonts = {template.theme_fonts.major.lower(), template.theme_fonts.minor.lower()}
        
        # Add some standard safe fonts usually allowed implicitly? 
        # For V1 strict mode: only exact theme matches.
        
        for elem in slide.elements:
            if elem.type == "TEXT_BOX" and elem.text_style and elem.text_style.font_family:
                font = elem.text_style.font_family.lower()
                if font not in allowed_fonts:
                    findings.append(FindingSpec(
                        rule_id=self.id,
                        slide_index=slide.index,
                        element_id=elem.id,
                        severity=self.severity,
                        message=f"Font family '{elem.text_style.font_family}' is not compliant.",
                        expected=f"{template.theme_fonts.major} or {template.theme_fonts.minor}",
                        actual=elem.text_style.font_family,
                        suggestion="Change font to Theme Body or Heading."
                    ))
        return findings

@registry.register
class ImageQualityRule(BaseRule):
    id = "IMG_QUALITY"
    description = "Image quality issues (stretched, low res)."
    severity = "MEDIUM"

    def check(self, slide: SlideSpec, template: TemplateSpec) -> list[FindingSpec]:
        findings = []
        for elem in slide.elements:
            if elem.type == "IMAGE" and elem.is_stretched:
                 findings.append(FindingSpec(
                        rule_id=self.id,
                        slide_index=slide.index,
                        element_id=elem.id,
                        severity=self.severity,
                        message=f"Image {elem.name} appears stretched (aspect ratio distortion).",
                        suggestion="Reset image aspect ratio."
                    ))
        return findings

@registry.register
class ColorRule(BaseRule):
    id = "COLOR_MISMATCH"
    description = "Color is outside the corporate palette."
    severity = "MEDIUM"

    def check(self, slide: SlideSpec, template: TemplateSpec) -> list[FindingSpec]:
        findings = []
        # Construct palette set for O(1) lookup
        # Naive implementation: Exact Hex Match
        # In real world: Hex -> RGB -> DeltaE comparison < threshold
        
        palette = set()
        t = template.theme_colors
        # Add all theme colors if present
        for c in [t.dark1, t.light1, t.dark2, t.light2, t.accent1, t.accent2, t.accent3, t.accent4, t.accent5, t.accent6]:
             if c:
                 # Convert RGB to Hex for comparison with SlideSpec (which uses Hex)
                 # Assumption: SlideSpec provides Hex without # usually or with. Let's normalize.
                 # RgbColor Pydantic model: r, g, b
                 hex_val = f"{c.r:02x}{c.g:02x}{c.b:02x}".upper()
                 palette.add(hex_val)
        
        # Checking logic
        for elem in slide.elements:
             if elem.text_style and elem.text_style.color_hex:
                 color = elem.text_style.color_hex.upper().replace("#", "")
                 if color not in palette and color != "000000" and color != "FFFFFF": # Whitelist Black/White?
                      findings.append(FindingSpec(
                        rule_id=self.id,
                        slide_index=slide.index,
                        element_id=elem.id,
                        severity=self.severity,
                        message=f"Color #{color} is not in the theme palette.",
                        actual=f"#{color}",
                        suggestion="Use a Theme Color."
                    ))
        return findings
