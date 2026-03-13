#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
-Cozy times nodal playground - note_editor.py cozy note editing dialog
-Sophisticated note editor with title field, word count, and emoji insertion
-Built using a single shared braincell by Yours Truly and various Intelligences
"""

import random
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, 
    QLineEdit, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QColor, QFont
from utils.spellchecker import DebouncedSpellHighlighter, show_spell_suggestions, SPELL_CHECKER_TYPE


class CozyNoteEditor(QDialog):
    """Cozy note editor with dedicated title field, word count, and emoji insertion 🌱📝"""

    def __init__(self, node_id: int, current_title: str, current_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Edit Note {node_id} 🌿")
        self.setMinimumSize(940, 680)
        self.setObjectName("CozyNoteEditor")

        # Track original state for unsaved changes detection
        self.current_text = current_text
        self.original_title = current_title.strip()
        self.original_text = current_text.strip()
        self.has_unsaved_changes = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(18)

        # === Title row ===
        title_row = QHBoxLayout()
        self.title_edit = QLineEdit(current_title)
        self.title_edit.setObjectName("cozyTitleEdit")
        self.title_edit.setFont(QFont("Chandler42", 14, QFont.Bold))
        self.title_edit.setMinimumHeight(48)

        # Emoji button for inserting random emojis
        from widgets import CozyButton
        emoji_btn = CozyButton("🌸")
        emoji_btn.setMinimumHeight(48)
        emoji_btn.setFixedWidth(48)
        emoji_btn.clicked.connect(self._insert_random_emoji)

        title_row.addWidget(self.title_edit, 1)
        title_row.addWidget(emoji_btn)
        layout.addLayout(title_row)

        # === Main text area ===
        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("cozyTextEdit")
        self.text_edit.setPlainText(current_text)
        self.text_edit.setFont(QFont("Lato", 13))
        self.text_edit.setMinimumHeight(420)
        layout.addWidget(self.text_edit)

        # === Spell checking (debounced, with size awareness) ===
        self.spell_highlighter = None
        if SPELL_CHECKER_TYPE:
            self.spell_highlighter = DebouncedSpellHighlighter(self.text_edit.document())

        # Enable right-click context menu for spell suggestions
        self.text_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text_edit.customContextMenuRequested.connect(self._on_text_edit_context_menu)

        # === Word count label ===
        self.word_count = QLabel("Gentle words")
        self.word_count.setObjectName("wordCountLabel")
        self.word_count.setFont(QFont("Chandler42", 11))
        self.word_count.setStyleSheet("color: #a8d0ff;")

        # Spell check status indicator
        self.spell_check_indicator = QLabel("")
        self.spell_check_indicator.setObjectName("spellCheckIndicator")
        self.spell_check_indicator.setFont(QFont("Lato", 10))
        self._update_spell_check_indicator()

        # === Button row ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.spell_check_indicator)
        button_layout.addSpacing(15)
        button_layout.addWidget(self.word_count)

        from widgets import CozyButton
        self.save_btn = CozyButton("Save Note 🌿")
        self.save_btn.setObjectName("cozySaveBtn")
        self.save_btn.setDefault(True)
        self.save_btn.setMinimumHeight(48)
        self.save_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.save_btn)
        layout.addLayout(button_layout)

        # === Pulse animation for word count heartbeat ===
        self.pulse_anim = QVariantAnimation(self)
        self.pulse_anim.setDuration(160)
        self.pulse_anim.setStartValue(11)
        self.pulse_anim.setEndValue(14.5)
        self.pulse_anim.setEasingCurve(QEasingCurve.OutBack)

        # Connections
        self.text_edit.textChanged.connect(self._on_content_changed)
        self.title_edit.textChanged.connect(self._on_content_changed)
        self.last_word_count = 0
        self._update_word_count()

    def _on_content_changed(self):
        """Detect unsaved changes and update word count"""
        has_changes = (self.title_edit.text().strip() != self.original_title or 
                       self.text_edit.toPlainText().strip() != self.original_text)

        if has_changes != self.has_unsaved_changes:
            self.has_unsaved_changes = has_changes
            if has_changes:
                self.save_btn.setText("Save Changes 🌿")
            else:
                self.save_btn.setText("Save Note 🌿")

        self._update_word_count()

    def mark_as_saved(self):
        """Called after successful save so the button resets"""
        self.original_title = self.title_edit.text().strip()
        self.original_text = self.text_edit.toPlainText().strip()
        self.has_unsaved_changes = False
        self.save_btn.setText("Save Note 🌿")

    def _update_word_count(self):
        """Update word count display with heartbeat animation on increase"""
        words = len(self.text_edit.toPlainText().split())
        self.word_count.setText(f"{words} Gentle words")
        self._update_spell_check_indicator()

        if words > self.last_word_count:
            self._happy_word_heartbeat()
        self.last_word_count = words

    def _happy_word_heartbeat(self):
        """Joyful little pop when word count increases"""
        anim = QVariantAnimation(self)
        anim.setDuration(160)
        anim.setStartValue(11)
        anim.setEndValue(14.5)
        anim.setEasingCurve(QEasingCurve.OutBack)

        def return_to_normal():
            back = QVariantAnimation(self)
            back.setDuration(240)
            back.setStartValue(14.5)
            back.setEndValue(11)
            back.setEasingCurve(QEasingCurve.OutQuad)
            back.valueChanged.connect(lambda s: self.word_count.setStyleSheet(
                f"color: #a8d0ff; font-family: 'Chandler42'; font-size: {s}px;"
            ))
            back.start()

        anim.valueChanged.connect(lambda s: self.word_count.setStyleSheet(
            f"color: #ff9ab5; font-family: 'Chandler42'; font-size: {s}px;"
        ))
        anim.finished.connect(return_to_normal)
        anim.start()

    def _insert_random_emoji(self):
        """Sprinkle a little joy into the writing ✨"""
        emojis = ["🪴", "💭", "🌸", "✨", "🤗", "😍", "☕", "💛", "❤", "📌", "💖", "🌼"]
        self.text_edit.insertPlainText(random.choice(emojis) + " ")

    def _update_spell_check_indicator(self):
        """Update spell check status indicator based on document size and state."""
        if not self.spell_highlighter:
            self.spell_check_indicator.setText("")
            return

        if self.spell_highlighter.is_document_too_large():
            self.spell_check_indicator.setText("📋 (spell check disabled - doc too large)")
            self.spell_check_indicator.setStyleSheet("color: #ffaa66;")
        elif self.spell_highlighter.is_spell_check_enabled():
            self.spell_check_indicator.setText("✓ (spell check active)")
            self.spell_check_indicator.setStyleSheet("color: #66ff99;")
        else:
            self.spell_check_indicator.setText("✗ (spell check disabled)")
            self.spell_check_indicator.setStyleSheet("color: #ff6666;")

    def _on_text_edit_context_menu(self, pos):
        """Handle right-click context menu on text edit."""
        show_spell_suggestions(self.text_edit, pos)

    def get_title(self):
        return self.title_edit.text().strip()

    def get_text(self):
        return self.text_edit.toPlainText()
