# IntelligentSearchEngine
CADISE Backend API
What's Here
-----------

* README.md - this file
* requirements.txt - this file is used install Python dependencies needed by the API
* /resources  - this folder contains the resources to be indexed.

Getting Started
---------------

1. Create a Python virtual environment for the project.

        $ virtualenv .venv

2. Activate the virtual environment:

        a) For Windows
        $ ./.venv/Scripts/activate

        b) For Linux
        $ source ./.venv/Scripts/activate

3. Install Python dependencies for the project:

        $ pip install -r requirements.txt

        $ python -m spacy download en_core_web_md

4. Start the Flask development server:

        $ python app.py 

5. Open http://127.0.0.1:8500/ in a web browser to view the output of your
   service.
