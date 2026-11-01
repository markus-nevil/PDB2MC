from .base_mode_window import Check, Color, Gap, ModeWindow, Spin, set_enabled


class RibbonWindow(ModeWindow):
    MODE_NAME = "Ribbon"
    TITLE = "Ribbon Mode"
    CHAIN_CHECK = "colorByChainCheck"
    OPTION_COLUMNS = [[
        Color("ribbonColorBox", "Select ribbon color:", "red_concrete"),
        Check("colorByChainCheck", "Color backbone by chain", True),
        Check("barStyleCheck", "Alpha helices as rods", False),
        Gap(8),
        Color("backboneColorBox", "Select backbone color:", "gray_concrete"),
        Check("showBackboneCheck", "Show backbone", True),
        Spin("pScaleSpinBox", "Protein scale:", 1.0),
        Gap(8),
        Check("otherMoleculeCheck", "Show other molecules", True),
        Spin("aScaleSpinBox", "Atom scale:", 1.5),
    ]]

    def refresh_enabled(self, *_):
        by_chain = self.colorByChainCheck.isChecked()
        set_enabled(not by_chain, self.ribbonColorBox)
        set_enabled(self.showBackboneCheck.isChecked() and not by_chain, self.backboneColorBox)
        set_enabled(self.otherMoleculeCheck.isChecked(), self.aScaleSpinBox)

    def mode_config(self, config):
        config['atoms'].update(ribbon_atom=self.ribbonColorBox.currentText(),
                               backbone_atom=self.backboneColorBox.currentText())
        config.update(atom_scale=self.aScaleSpinBox.value(),
                      show_hetatm=self.otherMoleculeCheck.isChecked(),
                      backbone=self.showBackboneCheck.isChecked(),
                      sidechain=False,
                      by_chain=self.colorByChainCheck.isChecked(),
                      bar_style=self.barStyleCheck.isChecked())
