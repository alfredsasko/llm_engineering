Command-Line Usage
==================

Top-Level
---------

::

   usage: python -m wk4_excercise [-h] [--env-file ENV_FILE]
                                  {serve,optimize,stream} ...

   Python to C++ optimizer supporting both CLI and Gradio UI modes

   positional arguments:
     {serve,optimize,stream}
       serve               Launch the Gradio web UI
       optimize            Convert a Python file to C++ and print it
       stream              Read Python code from stdin and stream converted
                           C++ to stdout

   options:
     -h, --help            show this help message and exit
     --env-file ENV_FILE   Path to .env file with API keys (defaults to loading
                           .env from cwd)

Serve
-----

::

   usage: python -m wk4_excercise serve [-h] [--share]

   Launch the Gradio web UI

   options:
     -h, --help  show this help message and exit
     --share     Enable public Gradio sharing when launching the app

Optimize
--------

::

   usage: python -m wk4_excercise optimize [-h] [--model MODEL] path

   Convert a Python file to C++ and print it

   positional arguments:
     path           Path to the Python file

   options:
     -h, --help     show this help message and exit
     --model MODEL  Override the configured default model

Stream
------

::

   usage: python -m wk4_excercise stream [-h] [--model MODEL]

   Read Python code from stdin and stream converted C++ to stdout

   options:
     -h, --help     show this help message and exit
     --model MODEL  Override the configured default model

Debugging Tips
--------------

- Configure VS Code launch entries with ``"module": "wk4_excercise"`` plus the desired subcommand.
- Append ``--share`` during remote development to expose Gradio via a public link.
