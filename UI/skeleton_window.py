from .base_mode_window import (  # noqa: F401  (WorkerThread re-exported for older callers)
    Check, Color, Gap, ModeWindow, Spin, WorkerThread, set_enabled,
)


class SkeletonWindow(ModeWindow):
    MODE_NAME = "Skeleton"
    TITLE = "Skeleton Mode"
    CHAIN_CHECK = "colorByChainCheck"
    OPTION_COLUMNS = [[
        Color("backboneColorBox", "Select backbone color:", "gray_concrete"),
        Check("showBackboneCheck", "Show backbone", True),
        Check("colorByChainCheck", "Color backbone by chain", False),
        Spin("backboneScaleSpinBox", "Backbone scale:", 1.0),
        Spin("pScaleSpinBox", "Protein scale:", 1.0),
        Gap(8),
        Color("sidechainColorBox", "Select sidechain color:", "gray_concrete"),
        Check("showSidechainCheck", "Show sidechain", True),
        Gap(8),
        Color("otherColorBox", "Select other color:", "pink_concrete"),
        Check("otherMoleculeCheck", "Show other molecules", True),
        Spin("aScaleSpinBox", "Atom scale:", 1.5),
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
