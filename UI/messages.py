"""
The wording and formatting of every message window. To change how a message reads or looks, edit this file.

A body is HTML, using the part of HTML that Qt supports:
https://doc.qt.io/qt-6/richtext-html-subset.html
{name} in a body is filled in when the message is shown. Values are escaped, so an error message or a
file path containing < or & shows as written. Write {{ and }} for a literal brace.

STYLE applies to all messages. A Message can also set its own width, font_size, button and icon.
"""
import html
import string
from dataclasses import dataclass
from typing import Optional

# --- the look of all messages ---
FONT_FAMILY = "Segoe UI"
FONT_SIZE = 12          # points
WIDTH = 480             # pixels, of the whole window; text wraps to fit
MAX_TEXT_HEIGHT = 500   # pixels; longer messages scroll
ICON_SIZE = 75          # pixels
BUTTON_STYLE = "background-color: rgba(255, 255, 255, 220); padding: 4px 18px;"

STYLE = """
h2   { font-size: 15pt; font-weight: bold; margin-bottom: 6px; }
h3   { font-size: 11pt; font-weight: bold; margin-top: 10px; margin-bottom: 2px; }
p    { margin-top: 2px; margin-bottom: 4px; }
code { font-family: Consolas, monospace; font-weight: bold; }
.cmd { margin-left: 16px; margin-top: 0px; margin-bottom: 2px; }
"""

## Reminder: here's how to customize windows:
# MODEL_FINISHED = Message(
#     title="Model generated",
#     icon="good",
#     width=560,
#     font_size=12,
#     body="""


@dataclass(frozen=True)
class Message:
    title: str
    body: str
    icon: str = "info"                  # good, bad or info: images/icons/icon_<icon>.png
    width: int = WIDTH
    font_size: int = FONT_SIZE
    button: Optional[str] = "Okay"      # None for no button
    copy_text: Optional[str] = None     # plain text; adds a button that copies it to the clipboard
    copy_button: str = "Copy commands"

    def placeholders(self):
        """The names this message needs to be shown."""
        fields = string.Formatter().parse(self.body + (self.copy_text or ""))
        return {name for _, name, _, _ in fields if name}

    def render(self, **values):
        """The body with its placeholders filled in, ready for a rich text label."""
        escaped = {name: html.escape(str(value)).replace("\n", "<br>") for name, value in values.items()}
        return f"<style>{STYLE}</style>{self.body.format(**escaped)}"

    def plain_copy_text(self, **values):
        return self.copy_text.format(**values) if self.copy_text else None


# --- starting up ---
NEW_VERSION = Message(
    title="New Version Available!",
    icon="good",
    body="<p>There is a new PDB2MC version available.</p>"
         "<p>Download Release v{version} from Github.</p>"
         "<p>https://github.com/markus-nevil/PDB2MC</p>",
)

# --- building a model ---
MODEL_FINISHED = Message(
    title="Model generated",
    icon="good",
    width=650,
    body="""

<h3 align="center">Finished!</h3>
<h3>Instructions for {name}:</h3>
<p class="cmd">Reload the world with <code>{reload}</code></p>
<p class="cmd">Build your model with:</p>
<p class="cmd"><code>{function}</code></p>
<p class="cmd">(works in all Minecraft versions)</p>
<h3>or use Trigger functions:</h3>
<p class="cmd">Build your model with <code>{build_trigger}</code></p>
<p class="cmd">List your models with <code>{list_models}</code></p>
<p class="cmd">Delete it from anywhere with <code>{delete}</code></p>
<p class="cmd">Teleport to it with <code>{teleport}</code></p>
""",
    copy_text="{reload}\n{function}\n{build_trigger}\n{list_models}\n{delete}\n{teleport}\n",
)

BUILD_ERROR = Message(
    title="Error encountered",
    icon="bad",
    body="<p>Model has not generated!</p><p>Error: {error}</p>",
)

BUILD_PROGRESS = Message(
    title="Building your model",
    body="Processing, please wait...",
)

NO_PDB_FILE = Message(
    title="Error: No PDB file",
    icon="bad",
    body="<p>Please select a PDB file.</p>",
)

NO_MINECRAFT_SAVE = Message(
    title="Error: No Minecraft save",
    icon="bad",
    body="<p>Please select a Minecraft save.</p>",
)

# --- choosing a structure ---
PREVIEW = Message(
    title="Preview",
    button="Close",
    body="<h3>About {width} x {depth} blocks, {height} high</h3>"
         "<p>At protein scale {scale}, covering about {chunks} chunks. {atoms} atoms.</p>"
         "<p>The turning model shows the shape and colours, not every block.</p>",
)

PREVIEW_TOO_TALL = Message(
    title="Preview",
    body="<p><b>Too tall:</b> {height} blocks is more than the {limit} the world has room for. Lower the "
         "protein scale.</p>",
)

PREVIEW_LARGE = Message(
    title="Preview",
    body="<p><b>Very wide:</b> loading {chunks} chunks for the build can take minutes. A lower protein scale "
         "builds much faster.</p>",
)

ASK_PDB_ID = Message(
    title="Load by PDB ID",
    # Shown as plain text in the question box
    body="PDB ID of the structure (for example 1GFL or 4HHB):",
)

DOWNLOADING = Message(
    title="Please wait",
    button=None,
    body="<p>Downloading {pdb_id} from the RCSB Protein Data Bank...</p>",
)

INVALID_PDB_ID = Message(
    title="Not a PDB ID",
    icon="bad",
    body="<p>'{text}' is not a PDB ID.</p><p>PDB IDs are four characters, starting with a number, such as "
         "1GFL. Search for structures at rcsb.org.</p>",
)

DOWNLOAD_ERROR = Message(
    title="Download failed",
    icon="bad",
    body="<p>Could not download {pdb_id}.</p><p>{error}</p>",
)

CALCULATING_SIZE = Message(
    title="Please wait",
    button=None,
    body="<p>Calculating model size...</p>",
)

FILE_LOAD_ERROR = Message(
    title="File Error",
    icon="bad",
    body="<p>Failed to load file:</p><p>{error}</p>",
)

NO_FILE_SELECTED = Message(
    title="No file selected",
    icon="bad",
    body="<p>Please select a file.</p>",
)

NOTHING_SELECTED = Message(
    title="Nothing Selected",
    icon="bad",
    body="<p>Nothing selected!</p>",
)

SCALE_ERROR = Message(
    title="Scale error",
    icon="bad",
    body="<p>Could not determine recommended scale.</p><p>Error: {error}</p>",
)

MODEL_TOO_LARGE = Message(
    title="Model too large!",
    icon="bad",
    body="<p>The chosen model is too large for Minecraft.</p>",
)

MAXIMUM_SCALE = Message(
    title="Maximum scale",
    font_size=12,
    body="<p>The suggested maximum protein scale is: <b>{maximum}x</b></p>"
         "<p></p>"
         "<p>'Protein Scale' has been set to <b>{scale}</b>.</p>",
)

# --- choosing a Minecraft save ---
SAVE_REMINDER = Message(
    title="Error",
    icon="bad",
    body="<p>Remember to select a Minecraft save.</p>",
)

INVALID_DIRECTORY = Message(
    title="Invalid directory",
    icon="bad",
    body="<p>Please select a valid Minecraft save directory.</p>",
)

# --- options and residues ---
INVALID_BLOCK = Message(
    title="Invalid block input",
    icon="bad",
    body="<p>{block_name} is not a valid block option.</p>",
)

NO_STRUCTURE = Message(
    title="No structure selected",
    icon="bad",
    body="<p>Please select a PDB or mmCIF file first.</p>",
)

STRUCTURE_LOAD_ERROR = Message(
    title="File Error",
    icon="bad",
    body="<p>Failed to load structure for sequence selection:</p><p>{error}</p>",
)

NO_SEQUENCE_SELECTION = Message(
    title="No selection",
    icon="bad",
    body="<p>Please select a sequence region.</p>",
)

# --- tools ---
FILES_REMOVED = Message(
    title="Files removed",
    icon="good",
    body="<p>Removed the PDB2MC models from</p><p>{folder}</p>",
)

BLANK_WORLD_COPIED = Message(
    title="Blank World Copied!",
    icon="good",
    body="<p>The blank world will now be found in your saves.</p><p>Run again to overwrite with this world.</p>",
)
