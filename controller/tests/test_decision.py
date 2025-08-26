import os
import importlib
import types

# We import the controller module to access adjust and thresholds
mod = importlib.import_module('app')


def test_adjust_bounds_and_step():
    # Ensure step and bounds work
    old = 0.5
    up = mod.adjust(old, up=True)
    assert up == round(min(mod.MAX_RATE, old + mod.STEP), 3)
    down = mod.adjust(old, up=False)
    assert down == round(max(mod.MIN_RATE, old - mod.STEP), 3)


def test_err_high_triggers_bump(monkeypatch):
    # Simulate state
    mod.rate = 0.5
    mod.last_change_ts = 0

    # Monkeypatch query functions to return high error, low latency
    monkeypatch.setattr(mod, 'prom_query', lambda q: 0.1)

    # With high err, should bump (cooldown satisfied)
    now = 10_000
    monkeypatch.setattr(mod, 'time', types.SimpleNamespace(time=lambda: now))
    before = mod.rate
    nr = mod.adjust(before, up=True)
    assert nr > before


def test_low_err_low_lat_triggers_decay(monkeypatch):
    mod.rate = 1.0
    mod.last_change_ts = 0

    def fake_query(q):
        if 'histogram_quantile' in q:
            return 0.05
        return 0.0

    monkeypatch.setattr(mod, 'prom_query', fake_query)
    now = 10_000
    import types as t
    monkeypatch.setattr(mod, 'time', t.SimpleNamespace(time=lambda: now))

    before = mod.rate
    nr = mod.adjust(before, up=False)
    assert nr < before

