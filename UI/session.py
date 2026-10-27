"""
Choices shared by all mode windows during one run of the program, so switching modes keeps the
selected model, Minecraft save, residue modifications and chain colours.
"""


class Session:
    def __init__(self):
        self.pdb_file = None
        self.save_path = None
        # Residue modifications belong to one structure file; they are dropped when the file changes
        self.residue_mods = {}
        self.chain_blocks = None

    def set_pdb_file(self, path):
        if path != self.pdb_file:
            self.residue_mods = {}
        self.pdb_file = path

    def reset(self):
        self.__init__()


SESSION = Session()
