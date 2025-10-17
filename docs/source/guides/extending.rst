Extending the Project
=====================

#. Add a model entry to ``config.yaml`` with provider, identifiers, endpoints, and env vars.
#. Implement a ``BaseModelClient`` subclass in ``wk4_excercise/models`` and override :meth:`stream_code`.
#. Register the provider in ``wk4_excercise/models/registry.py``.
#. Document new configuration/env requirements in the setup guide; update the CLI guide if options change.
#. Add tests that mock external APIs so CI runs without hitting real services.

Since the repository remains private, distribute docs internally by running
``make -C docs html`` and sharing ``docs/build/html`` via trusted channels or CI artefacts.
