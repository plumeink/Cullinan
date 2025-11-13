import traceback

print('Running IoC smoke tests...')

try:
    from tests import test_string_annotation_injection as tsi
except Exception:
    # Try relative import fallback
    import importlib
    tsi = importlib.import_module('tests.test_string_annotation_injection')

for name in ('test_string_annotation_injection', 'test_mixed_annotations'):
    print(f'Running {name}...')
    try:
        func = getattr(tsi, name)
        res = func()
        print(f'{name} returned: {res}\n')
    except Exception as e:
        print(f'{name} failed: {e}')
        traceback.print_exc()
        print('\n')

print('Done')

