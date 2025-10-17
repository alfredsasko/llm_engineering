Setup & Configuration
=====================

Environment
-----------

#. Create a virtual environment and install the requirements.
#. Provide API credentials through environment variables or a ``.env`` file
   (``OPENAI_API_KEY``, ``ANTHROPIC_API_KEY``, ``HF_TOKEN``, ``GEMINI_API_KEY`` if needed).
#. Run ``python -m wk4_excercise --help`` to confirm the CLI starts.

Configuration
-------------

Adjust ``wk4_excercise/config.yaml`` to add/update providers. Launch parameters
and UI assets also live there.

Build the docs with ``make -C docs html`` (see the Makefile below); HTML appears
under ``docs/build/html``.
