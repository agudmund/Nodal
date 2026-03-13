#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - spellchecker.py spell checking with debounce
-Highlights misspelled words with configurable delay and document size limits
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

from PySide6.QtCore import QRegularExpression, Qt, QTimer
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QTextCursor
from PySide6.QtWidgets import QMenu

try:
    import enchant
    ENCHANT_AVAILABLE = True
except ImportError:
    ENCHANT_AVAILABLE = False

SPELL_CHECKER_TYPE = "enchant" if ENCHANT_AVAILABLE else None


class DebouncedSpellHighlighter(QSyntaxHighlighter):
    """Highlights misspelled words with red wavy underline and debounce delay."""

    # Configuration constants
    DEBOUNCE_DELAY_MS = 5000  # 5 second delay before checking (testing)
    SIZE_THRESHOLD_KB = 50    # Disable spell check for documents larger than this

    def __init__(self, document):
        super().__init__(document)
        self.dictionary = enchant.Dict("en_US") if ENCHANT_AVAILABLE else None

        # Debounce timer
        self._check_timer = QTimer()
        self._check_timer.setSingleShot(True)
        self._check_timer.timeout.connect(self._perform_spell_check)

        # Track spell check state
        self.spell_check_enabled = True
        self._document_too_large = False
        self._last_was_word_boundary = True
        self._should_highlight = False  # Flag to control if highlightBlock actually highlights

        # Format for misspelled words
        self.misspelled_format = QTextCharFormat()
        self.misspelled_format.setUnderlineColor(QColor("#ff5555"))
        self.misspelled_format.setUnderlineStyle(QTextCharFormat.SpellCheckUnderline)

        # Connect document changes to debounce timer
        self.document().contentsChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        """Called when document text changes - only check at word boundaries or after pause."""
        if not self.spell_check_enabled or not ENCHANT_AVAILABLE:
            return

        # Check document size
        doc_size_kb = len(self.document().toPlainText().encode('utf-8')) / 1024
        if doc_size_kb > self.SIZE_THRESHOLD_KB:
            if not self._document_too_large:
                self._document_too_large = True
                self._check_timer.stop()
                self.rehighlight()  # Clear existing highlights
            return
        else:
            self._document_too_large = False

        text = self.document().toPlainText()
        if not text:
            return

        # Check if last character is a word boundary (space, punctuation, newline)
        last_char = text[-1]
        is_word_boundary = last_char.isspace() or last_char in '.,;:!?\n'

        # If transitioning from typing to word boundary, check with minimal delay
        if is_word_boundary and not self._last_was_word_boundary:
            self._check_timer.stop()
            self._check_timer.start(10)  # Very short delay to avoid recursion
            self._last_was_word_boundary = True
        elif not is_word_boundary:
            # Still typing in a word
            self._last_was_word_boundary = False
            if not self._check_timer.isActive():
                # Start timer for inactivity check only if not already running
                self._check_timer.start(self.DEBOUNCE_DELAY_MS)

    def _perform_spell_check(self):
        """Execute the actual spell check after debounce period."""
        if self.spell_check_enabled and not self._document_too_large:
            self._should_highlight = True
            self.rehighlight()
            self._should_highlight = False

    def highlightBlock(self, text):
        """Highlight misspelled words in this block."""
        # Only highlight if timer has fired, not on every keystroke
        if not self.spell_check_enabled or not self.dictionary or self._document_too_large or not self._should_highlight:
            return

        expression = QRegularExpression(r"\b[a-zA-Z']+\b")
        iterator = expression.globalMatch(text)

        while iterator.hasNext():
            match = iterator.next()
            word = match.captured(0)
            start = match.capturedStart()
            length = match.capturedLength()

            # Enchant returns True if word is correct, False if misspelled
            if not self.dictionary.check(word):
                self.setFormat(start, length, self.misspelled_format)

    def set_spell_check_enabled(self, enabled: bool):
        """Enable or disable spell checking."""
        self.spell_check_enabled = enabled
        self._check_timer.stop()
        self.rehighlight()

    def is_spell_check_enabled(self) -> bool:
        """Return whether spell checking is currently enabled."""
        return self.spell_check_enabled and not self._document_too_large

    def is_document_too_large(self) -> bool:
        """Return whether document exceeds size threshold."""
        return self._document_too_large

    def get_spell_checker_type(self) -> str:
        """Return the type of spell checker being used."""
        return SPELL_CHECKER_TYPE or "none"


def show_spell_suggestions(text_edit, pos):
    """Show right-click context menu with spell suggestions."""
    if not ENCHANT_AVAILABLE:
        return

    cursor = text_edit.cursorForPosition(pos)
    cursor.select(QTextCursor.WordUnderCursor)
    word = cursor.selectedText().strip()

    if not word:
        return

    dictionary = enchant.Dict("en_US")
    if dictionary.check(word):
        return  # Correct word → no menu

    suggestions = dictionary.suggest(word)

    menu = QMenu(text_edit)
    if suggestions:
        for suggestion in suggestions[:10]:
            action = menu.addAction(suggestion)
            action.triggered.connect(lambda checked, s=suggestion, c=cursor: replace_word(c, s))
    else:
        menu.addAction("(no suggestions)").setEnabled(False)

    menu.exec(text_edit.mapToGlobal(pos))


def replace_word(cursor, suggestion):
    """Replace selected word with suggestion."""
    cursor.beginEditBlock()
    cursor.removeSelectedText()
    cursor.insertText(suggestion)
    cursor.endEditBlock()

