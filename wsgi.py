# -*- coding: utf-8 -*-
"""
    wsgi
    ~~~~

    entrypoint wsgi script
"""

import app

application = app.create_app()

if __name__ == "__main__":
    application.run(debug=True)
