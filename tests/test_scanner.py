import pytest
import os
from scanner import ZAP_PORT, API_KEY

# Test muy basico para verificar que las constantes se cargan (o tienen defaults)
def test_config_defaults():
    assert ZAP_PORT is not None
    assert API_KEY is not None

# Test para verificar que el archivo existe (Sanity Check)
def test_files_exist():
    assert os.path.exists("scanner.py")
    assert os.path.exists("requirements.txt")
