from PDB2MC import defaults
from .base_mode_window import Check, Choice, Color, Gap, ModeWindow, Spin, set_combobox_by_text, set_enabled


def residue_box(code):
    return code.capitalize() + "ColorBox"


_RESIDUE_ROWS = [Color(residue_box(code), f"{defaults.AMINO_ACID_NAMES[code]}:",
                       defaults.AMINO_ACID_STYLES["Residue"][code]) for code in defaults.AMINO_ACIDS]


class AminoAcidsWindow(ModeWindow):
    MODE_NAME = "Amino Acids"
    TITLE = "Amino Acid Mode"
    OPTION_COLUMNS = [
        _RESIDUE_ROWS[:10],
        _RESIDUE_ROWS[10:],
        [
            Choice("colorStyleBox", "Color style:", list(defaults.AMINO_ACID_STYLES), "Residue",
                   "Fill in the residue colours from a preset style"),
            Gap(8),
            Color("backboneColorBox", "Select backbone:", "gray_concrete"),
            Check("showBackboneCheck", "Show backbone", True, "Show the N-C-C backbone of the main models."),
            Spin("backboneScaleSpinBox", "Backbone scale:", 1.0, "Scale the width of the backbone by this factor."),
            Gap(8),
            Spin("aScaleSpinBox", "Residue scale:", 1.5, "Change the diameter (rounded up) of each residue."),
            Spin("pScaleSpinBox", "Protein scale:", 1.0, "Scale the entire model by this factor."),
            Check("otherMoleculeCheck", "Show other molecules", True,
                  "Check to show other non-protein, DNA, or RNA molecules."),
        ],
    ]

    def connect_options(self):
        self.colorStyleBox.currentTextChanged.connect(self.apply_color_style)

    def apply_color_style(self, style):
        for code, block in defaults.AMINO_ACID_STYLES.get(style, {}).items():
            set_combobox_by_text(getattr(self, residue_box(code)), block)

    def refresh_enabled(self, *_):
        set_enabled(self.showBackboneCheck.isChecked(), self.backboneColorBox, self.backboneScaleSpinBox)

    def mode_config(self, config):
        config['atoms']['backbone_atom'] = self.backboneColorBox.currentText()
        config.update(amino_acids={code: getattr(self, residue_box(code)).currentText()
                                   for code in defaults.AMINO_ACIDS},
                      color_style=self.colorStyleBox.currentText(),
                      backbone_size=self.backboneScaleSpinBox.value(),
                      atom_scale=self.aScaleSpinBox.value(),
                      show_hetatm=self.otherMoleculeCheck.isChecked(),
                      backbone=self.showBackboneCheck.isChecked(),
                      sidechain=False,
                      by_chain=False)
