import os
import markdown
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextBrowser
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6 import QtCore, QtGui, QtWidgets
import sys
import re
import pkg_resources

class HelpWindow(QMainWindow):
    _instance = None  # Class variable to hold the single instance

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if self._instance is not None:
            raise RuntimeError("Call instance() instead")
        super().__init__()

        self.setObjectName("ReadmeWindow")
        self.setWindowTitle("Help")
        self.setFixedSize(900, 600)

        # current_directory = os.path.basename(os.getcwd())
        # if current_directory == "PDB2MC":
        #     mcpdb_directory = os.path.join(os.getcwd(), "..", "UI")
        #     os.chdir(mcpdb_directory)
        os.chdir(get_images_path())
        test = os.path.isfile(os.path.join(os.getcwd(), 'images/icons/logo.png'))

        self.setWindowIcon(QIcon('images/icons/logo.png'))

        self.centralwidget = QtWidgets.QWidget(parent=self)
        self.centralwidget.setObjectName("centralwidget")

        self.textBrowser = QTextBrowser(self.centralwidget)
        self.textBrowser.setGeometry(QtCore.QRect(10, 10, 880, 580))
        self.textBrowser.setStyleSheet("background-color: #f2f2f2; color: #000000;")

        # Enable external links
        self.textBrowser.setOpenExternalLinks(True)

        self.setCentralWidget(self.centralwidget)

        self.load_readme()

    def load_readme(self):
        # Get the directory of the current Python file
        start_dir = os.path.dirname(os.path.abspath(__file__))

        current_directory = os.path.basename(os.getcwd())
        if current_directory == "PDB2MC":
            mcpdb_directory = os.path.join(os.getcwd(), ".." "UI")
            os.chdir(mcpdb_directory)
            readme_path = os.path.join(mcpdb_directory, "README.md")
        else:
            readme_path = os.path.join(start_dir, "..", "README.md")

        #readme_path = pkg_resources.resource_filename('PDB2MC', 'README.md')

        # Read the README.md file
        readme_content = self.read_file(readme_path)

        # Convert the markdown to HTML
        html = self.convert_markdown_to_html(readme_content, start_dir)

        # Set the HTML to the QTextBrowser
        self.textBrowser.setHtml(html)

    def read_file(self, file_path):
        try:
            with open(file_path, "r") as file:
                return file.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return ""

    def convert_markdown_to_html(self, markdown_text, start_dir):
        try:
            # Replace Mermaid diagram
            markdown_text = replace_mermaid_diagram(markdown_text)

            # Convert alert boxes to HTML
            markdown_text = convert_alert_boxes(markdown_text)

            # Adjust list indentation
            markdown_text = adjust_list_indentation(markdown_text)

            # Highlight code
            markdown_text = highlight_code(markdown_text)

            # Convert the markdown to HTML
            html = markdown.markdown(markdown_text, extensions=['tables', 'toc', 'fenced_code', 'nl2br', 'extra'])

            html = adjust_image_paths(html)
            return html

            # Replace relative image paths with absolute paths
            #return html.replace('src="images/', 'src="' + os.path.join(start_dir, "..",'images/'))

        except Exception as e:
            print(f"Error converting markdown to HTML: {e}")
            return ""

# def adjust_image_paths(html):
#     # Check if the program is running as a compiled executable
#     if getattr(sys, 'frozen', False):
#         # Define a regular expression pattern for the img tags
#         pattern = r'<img src="(UI/images/[^"]+)"'
#         # Define a function that takes a match object and returns the replacement string
#         def replacer(match):
#             # Get the relative path to the image from the match object
#             relative_path = match.group(1)
#
#             # Use pkg_resources to get the absolute path to the image in the installed package
#             absolute_path = pkg_resources.resource_filename('PDB2MC', relative_path)
#             #absolute_path = pkg_resources.resource_filename('UI', relative_path)
#
#             # Return the img tag with the src attribute replaced with the absolute path
#             return f'<img src="{absolute_path}"'
#
#         # Use the sub function to replace the img tags
#         html = re.sub(pattern, replacer, html)
#     return html
def adjust_image_paths(html):
    # Define a regular expression pattern for the img tags
    pattern = r'<img src="(UI/images/[^"]+)"'

    # Define a function that takes a match object and returns the replacement string
    def replacer(match):
        # Get the relative path to the image from the match object
        relative_path = match.group(1)

        # Replace 'UI/images' with 'images' in the relative path
        new_path = relative_path.replace('UI/images', 'images')

        # Return the img tag with the src attribute replaced with the new path
        return f'<img src="{new_path}"'

    # Use the sub function to replace the img tags
    html = re.sub(pattern, replacer, html)

    return html

def adjust_list_indentation(markdown_text):
    return markdown_text.replace("\n   ", "\n    ")

def highlight_code(markdown_text):
    # Use a regular expression to find text surrounded by backticks
    pattern = r" `([^`]+)` "

    # Define a function that takes a match object and returns the replacement string
    def replacer(match):
        return f' <code style="background-color: #e0e0e0; font-family: Courier;">{match.group(1)}</code> '

    # Use the sub function to replace the matched text
    return re.sub(pattern, replacer, markdown_text)

def convert_alert_boxes(markdown_text):
    # Define a dictionary with the alert box types and their corresponding HTML
    alert_boxes = {
        '[!NOTE]': '<div style="border: 1px solid blue; padding: 10px; background-color: #e8f5ff;"><strong>Note:</strong>',
        '[!TIP]': '<div style="border: 1px solid green; padding: 10px; background-color: #e8ffe8;"><strong>Tip:</strong>',
        '[!WARNING]': '<div style="border: 1px solid red; padding: 10px; background-color: #ffe8e8;"><strong>Warning:</strong>'
    }

    # Replace each alert box type with its corresponding HTML
    for alert_box, html in alert_boxes.items():
        markdown_text = markdown_text.replace(alert_box, html)

    # Replace ] that directly follow an alert box with </div>
    pattern = r"(</strong>.*?)(?=\])\]"
    markdown_text = re.sub(pattern, r"\1</div>", markdown_text)

    return markdown_text

def replace_mermaid_diagram(markdown_text):
    # Define the start and end of the Mermaid diagram
    start_marker = "```mermaid"
    end_marker = "\n```"

    # Find the start and end of the Mermaid diagram
    start = markdown_text.find(start_marker)
    end = markdown_text.find(end_marker, start)

    # If the Mermaid diagram was found, replace it with the statement and link
    if start != -1 and end != -1:
        # Define the replacement text
        replacement = "**Cannot display here, please visit the GitHub page for the program flowchart**\n\n[GitHub Page](https://github.com/markus-nevil/mcpdb#generalized-flowchart-of-program-procedure)"

        # Replace the Mermaid diagram with the replacement text
        markdown_text = markdown_text[:start] + replacement + markdown_text[end + len(end_marker):]

    return markdown_text

def get_images_path():
    if getattr(sys, 'frozen', False):
        # The program is running as a compiled executable
        images_dir = sys._MEIPASS
        images_dir = os.path.join(images_dir, "UI")

        #images_dir = os.path.join(images_dir, '..')
        return images_dir
    else:
        # The program is running as a Python script or it's installed in the Python environment
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to the UI/images directory
        images_dir = os.path.join(current_dir, '..', 'UI')
        return images_dir

if __name__ == "__main__":
    app = QApplication([])
    readme_window = HelpWindow()
    readme_window.show()
    app.exec()