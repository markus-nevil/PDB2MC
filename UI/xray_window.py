from PDB2MC import defaults
from .custom_window import BACKBONE_COLUMN, CustomWindow, atom_column


class XrayWindow(CustomWindow):
    """Custom mode with see-through stained glass atoms, so the backbone shows inside."""
    MODE_NAME = "X-Ray"
    TITLE = "X-Ray Mode"
    OPTION_COLUMNS = [atom_column(defaults.GLASS_ELEMENTS), BACKBONE_COLUMN]
