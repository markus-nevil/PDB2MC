from PDB2MC import color_schemes, defaults
from .base_mode_window import Check, Choice, Color, Gap, ModeWindow, Spin, set_enabled

ELEMENT_ROWS = [("C", "cColorBox"), ("O", "oColorBox"), ("N", "nColorBox"), ("S", "sColorBox"), ("P", "pColorBox")]


def atom_column(colors):
    """Element colours and atom options; `colors` maps C/O/N/S/P/other_atom to default blocks."""
    rows = [Color(name, f"Select {element} atom color:", colors[element]) for element, name in ELEMENT_ROWS]
    return rows + [
        Color("otherColorBox", "Select other color:", colors['other_atom']),
        Gap(8),
        Check("showAtomsCheck", "Show model atoms", True),
        Check("otherMoleculeCheck", "Show other molecules", True),
        Check("meshCheck", 'Use "mesh-style" atoms', False),
        Spin("aScaleSpinBox", "Atom scale:", 1.5),
    ]


BACKBONE_COLUMN = [
    Color("backboneColorBox", "Select backbone color:", "gray_concrete"),
    Check("showBackboneCheck", "Show backbone", True),
    Check("colorByChainCheck", "Color backbone by:", False),
    Choice("colorSchemeBox", "Color scheme:", list(color_schemes.SCHEMES), "Chain"),
    Spin("backboneScaleSpinBox", "Backbone scale:", 1.0),
    Gap(8),
    Color("sidechainColorBox", "Select sidechain color:", "gray_concrete"),
    Check("showSidechainCheck", "Show sidechain", True),
    Gap(8),
    Spin("pScaleSpinBox", "Protein scale:", 1.0),
]


class CustomWindow(ModeWindow):
    MODE_NAME = "Custom"
    TITLE = "Custom Mode"
    CHAIN_CHECK = "colorByChainCheck"
    OPTION_COLUMNS = [atom_column(defaults.CONCRETE_ELEMENTS), BACKBONE_COLUMN]

    def refresh_enabled(self, *_):
        atoms_on = self.showAtomsCheck.isChecked() or self.otherMoleculeCheck.isChecked()
        set_enabled(atoms_on, self.otherColorBox, self.aScaleSpinBox, self.meshCheck,
                    *(getattr(self, name) for _, name in ELEMENT_ROWS))
        by_chain = self.colorByChainCheck.isChecked()
        set_enabled(self.showBackboneCheck.isChecked() and not by_chain, self.backboneColorBox)
        set_enabled(self.showBackboneCheck.isChecked(), self.backboneScaleSpinBox)
        set_enabled(self.showSidechainCheck.isChecked() and not by_chain, self.sidechainColorBox)

    def mode_config(self, config):
        atoms = config['atoms']
        for element, name in ELEMENT_ROWS:
            atoms[element] = getattr(self, name).currentText()
        atoms.update(other_atom=self.otherColorBox.currentText(),
                     backbone_atom=self.backboneColorBox.currentText(),
                     sidechain_atom=self.sidechainColorBox.currentText())
        config.update(backbone_size=self.backboneScaleSpinBox.value(),
                      atom_scale=self.aScaleSpinBox.value(),
                      show_atoms=self.showAtomsCheck.isChecked(),
                      show_hetatm=self.otherMoleculeCheck.isChecked(),
                      mesh=self.meshCheck.isChecked(),
                      backbone=self.showBackboneCheck.isChecked(),
                      sidechain=self.showSidechainCheck.isChecked(),
                      by_chain=self.colorByChainCheck.isChecked())
