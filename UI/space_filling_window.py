from PDB2MC import defaults
from .base_mode_window import Check, Color, Gap, ModeWindow, Spin, set_enabled
from .custom_window import ELEMENT_ROWS


class SpaceFillingWindow(ModeWindow):
    MODE_NAME = "Space Filling"
    TITLE = "Space Filling Mode"
    CHAIN_CHECK = "colorByChainCheck"
    OPTION_COLUMNS = [[
        *(Color(name, f"Select {element} atom color:", defaults.CONCRETE_ELEMENTS[element])
          for element, name in ELEMENT_ROWS),
        Color("otherColorBox", "Select other color:", defaults.CONCRETE_ELEMENTS['other_atom']),
        Gap(8),
        Check("colorByChainCheck", "Color model by chain", False, "Color the surface by molecule (chain)."),
        Check("otherMoleculeCheck", "Show other molecules", True,
              "Check to show other non-protein, DNA, or RNA molecules."),
        Check("meshCheck", 'Use "mesh-style" atoms', False,
              "Place only some of the surface blocks, so the skeleton inside shows"),
        Spin("pScaleSpinBox", "Protein scale:", 1.0, "Scale the entire model by this factor."),
    ]]

    def refresh_enabled(self, *_):
        set_enabled(not self.colorByChainCheck.isChecked(), *(getattr(self, name) for _, name in ELEMENT_ROWS),
                    self.otherColorBox)

    def mode_config(self, config):
        atoms = config['atoms']
        for element, name in ELEMENT_ROWS:
            atoms[element] = getattr(self, name).currentText()
        atoms.update(other_atom=self.otherColorBox.currentText(), H='white_concrete')
        config.update(atom_scale=1.0,
                      show_hetatm=self.otherMoleculeCheck.isChecked(),
                      mesh=self.meshCheck.isChecked(),
                      by_chain=self.colorByChainCheck.isChecked())
