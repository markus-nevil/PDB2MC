from PDB2MC import defaults
from PDB2MC.space_filling import SASA_radius
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
        Check("colorByChainCheck", "Color model by chain", False),
        Check("otherMoleculeCheck", "Show other molecules", True),
        Check("meshCheck", 'Use "mesh-style" atoms', False),
        Spin("pScaleSpinBox", "Protein scale:", 1.0),
        Spin("sasaRadiusSpinBox", "SASA radius (\u00c5):", SASA_radius, minimum=0.0, maximum=10.0, step=0.1, decimals=2),
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
                      by_chain=self.colorByChainCheck.isChecked(),
                      sasa_radius=self.sasaRadiusSpinBox.value())
