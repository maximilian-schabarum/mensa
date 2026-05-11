#!/usr/bin/env python3
"""Test-Script zur Validierung der Refactoring-Änderungen."""
import sys
sys.path.insert(0, '/workspaces/mensa')

try:
    print("1. Testing imports...", end=" ")
    from speierlingshof.config import (
        PDF_IGNORED_WORDS, 
        CLOSURE_KEYWORDS,
        DATE_WINDOW_DAYS,
        WEEKDAYS
    )
    from speierlingshof.helpers import (
        parse_json_menu,
        parse_pdf_menu,
        classify_pdf_line,
        clean_title
    )
    from speierlingshof import Parser
    print("✓")

    print("2. Testing PDF_IGNORED_WORDS...", end=" ")
    assert "brueckentag" in PDF_IGNORED_WORDS
    assert "montag" in PDF_IGNORED_WORDS
    print("✓")

    print("3. Testing classify_pdf_line...", end=" ")
    # Sollte None zurückgeben (wird ignoriert)
    result = classify_pdf_line("Montag")
    assert result is None, f"Expected None for 'Montag', got {result}"
    
    # Sollte ein Gericht zurückgeben
    result = classify_pdf_line("Spaghetti Bolognese")
    assert result is not None and "title" in result, f"Expected meal dict, got {result}"
    print("✓")

    print("4. Testing Parser creation...", end=" ")
    parser = Parser("http://localhost/{metaOrFeed}/test_{mensaReference}.xml")
    assert parser is not None
    print("✓")

    print("\n✅ Alle Tests bestanden!")
    
except Exception as e:
    print(f"\n❌ Fehler: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
