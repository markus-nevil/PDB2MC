from .base_mode_window import Check, Color, Gap, ModeWindow, Spin, set_enabled


class RibbonWindow(ModeWindow):
    MODE_NAME = "Ribbon"
    TITLE = "Ribbon Mode"
    CHAIN_CHECK = "colorByChainCheck"
    OPTION_COLUMNS = [[
        Color("ribbonColorBox", "Select ribbon color:", "red_concrete"),
        Check("colorByChainCheck", "Color backbone by chain", True,
              "Color the backbones of the main models by the molecule number."),
        Check("barStyleCheck", "Alpha helices as rods", False,
              "Check to show Alpha Helices as a rod or bar instead of a spiraling ribbon."),
        Gap(8),
        Color("backboneColorBox", "Select backbone color:", "gray_concrete"),
        Check("showBackboneCheck", "Show backbone", True, "Show the backbone between the ribbons."),
        Spin("pScaleSpinBox", "Protein scale:", 1.0, "Scale the entire model by this factor."),
        Gap(8),
        Check("otherMoleculeCheck", "Show other molecules", True,
              "Check to show other non-protein, DNA, or RNA molecules."),
        Spin("aScaleSpinBox", "Atom scale:", 1.5, "Change the diameter (rounded up) of each atom."),
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
