import webview
import os
    
html_file = os.path.join(os.path.dirname(__file__), 'main/index.html')

window = webview.create_window('Gestionnaire de Stock', html_file)
webview.start(window)
