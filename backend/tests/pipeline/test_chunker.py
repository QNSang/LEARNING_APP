"""Tests for sentence-aware chunk creation."""

import unittest

from app.core.errors import AppError
from app.pipeline.chunker import (
    chunk_page_text,
    clean_text,
    create_chunks,
    split_sentences,
)
from app.pipeline.parser import ParsedPage


class ChunkerTest(unittest.TestCase):
    def test_clean_text_normalizes_repeated_whitespace(self) -> None:
        self.assertEqual(clean_text(" A   b\r\n\r\n\r\n\tC  "), "A b\n\nC")

    def test_split_sentences_keeps_sentence_endings(self) -> None:
        self.assertEqual(
            split_sentences("One. Two? Three! Four: Five; Six"),
            ["One.", "Two?", "Three!", "Four:", "Five;", "Six"],
        )

    def test_chunk_page_text_uses_two_sentence_overlap(self) -> None:
        chunks = chunk_page_text(
            "One. Two. Three. Four. Five.",
            chunk_size_chars=14,
            overlap_sentence_count=2,
        )

        self.assertTrue(chunks[1].startswith("One.\n\nTwo."))
        self.assertTrue(chunks[2].startswith("Two.\n\nThree."))

    def test_long_sentence_is_not_cut_or_reused_as_overlap(self) -> None:
        long_sentence = (
            "This is a very long sentence without a split point " * 10
        ).strip()
        chunks = chunk_page_text(
            f"Intro short. {long_sentence}. Tail one. Tail two.",
            chunk_size_chars=80,
            overlap_sentence_count=2,
        )

        self.assertIn(long_sentence, chunks[1])
        self.assertNotIn(long_sentence, chunks[2])
        self.assertEqual(chunks[2], "Tail one.\n\nTail two.")

    def test_create_chunks_raises_for_empty_pages(self) -> None:
        with self.assertRaises(AppError):
            create_chunks(
                [
                    ParsedPage(
                        page_num=1,
                        content="   \n\n ",
                        source="txt",
                        file_name="empty.txt",
                        source_ref="empty.txt - text",
                    )
                ],
                chunk_size_chars=100,
                chunk_overlap_chars=0,
            )


if __name__ == "__main__":
    unittest.main()
