"""
Choices shared by all mode windows during one run of the program, so switching modes keeps the
selected model, its name, the Minecraft save, residue modifications and chain colours.
"""


class Session:
    def __init__(self):
        self.pdb_file = None
        self.save_path = None
        # Residue modifications belong to one structure file; they are dropped when the file changes
        self.residue_mods = {}
        self.chain_blocks = None
        # The model's name in Minecraft; a new structure file starts over with that file's own name
        self.model_name = None

    def set_pdb_file(self, path):
        if path != self.pdb_file:
            self.residue_mods = {}
            self.model_name = None
        self.pdb_file = path

    def reset(self):
        self.__init__()


SESSION = Session()
