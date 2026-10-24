from .base_mode_window import (  # noqa: F401  (WorkerThread re-exported for older callers)
    Check, Color, Gap, ModeWindow, Spin, WorkerThread, set_enabled,
)


class SkeletonWindow(ModeWindow):
    MODE_NAME = "Skeleton"
    TITLE = "Skeleton Mode"
    CHAIN_CHECK = "colorByChainCheck"
    OPTION_COLUMNS = [[
        Color("backboneColorBox", "Select backbone color:", "gray_concrete"),
        Check("showBackboneCheck", "Show backbone", True, "Show the N-C-C backbone of the main models."),
        Check("colorByChainCheck", "Color backbone by chain", False,
              "Color the backbones of the main models by the molecule number."),
        Spin("backboneScaleSpinBox", "Backbone scale:", 1.0, "Scale the width of the backbone by this factor."),
        Spin("pScaleSpinBox", "Protein scale:", 1.0, "Scale the entire model by this factor."),
        Gap(8),
        Color("sidechainColorBox", "Select sidechain color:", "gray_concrete"),
        Check("showSidechainCheck", "Show sidechain", True, "Show amino acid R-groups"),
        Gap(8),
        Color("otherColorBox", "Select other color:", "pink_concrete"),
        Check("otherMoleculeCheck", "Show other molecules", True,
              "Check to show other non-protein, DNA, or RNA molecules."),
        Spin("aScaleSpinBox", "Atom scale:", 1.5, "Change the diameter (rounded up) of each atom."),
    ]]

    def refresh_enabled(self, *_):
        by_chain = self.colorByChainCheck.isChecked()
        set_enabled(self.showBackboneCheck.isChecked() and not by_chain, self.backboneColorBox)
        set_enabled(self.showBackboneCheck.isChecked(), self.backboneScaleSpinBox)
        set_enabled(self.showSidechainCheck.isChecked() and not by_chain, self.sidechainColorBox)
        set_enabled(self.otherMoleculeCheck.isChecked(), self.otherColorBox, self.aScaleSpinBox)

    def mode_config(self, config):
        config['atoms'].update(other_atom=self.otherColorBox.currentText(),
                               backbone_atom=self.backboneColorBox.currentText(),
                               sidechain_atom=self.sidechainColorBox.currentText())
        config.update(backbone_size=self.backboneScaleSpinBox.value(),
                      atom_scale=self.aScaleSpinBox.value(),
                      show_hetatm=self.otherMoleculeCheck.isChecked(),
                      backbone=self.showBackboneCheck.isChecked(),
                      sidechain=self.showSidechainCheck.isChecked(),
                      by_chain=self.colorByChainCheck.isChecked())
