def test_dagster_definitions_import():
    """Smoke test: the Dagster code location loads.

    Catches broken wiring (bad module path, missing dependency, syntax error in
    definitions.py) on push rather than the next time `dagster dev` is run.
    """
    from ccpmargin.orchestrate.definitions import defs

    assert defs is not None