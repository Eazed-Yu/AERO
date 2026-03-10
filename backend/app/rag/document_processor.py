from abc import ABC, abstractmethod


class AbstractDocumentProcessor(ABC):
    """
    Abstract interface for document preprocessing before LightRAG ingestion.
    Implementations will handle specific formats (PDF, DOCX, etc.)
    and extract text suitable for knowledge graph construction.
    """

    @abstractmethod
    async def process(self, file_path: str) -> list[str]:
        """
        Parse a document into text chunks for LightRAG insertion.

        Args:
            file_path: Path to the document file.

        Returns:
            List of text segments ready for insertion.
        """
        ...

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """Return list of supported file extensions (e.g., ['.pdf', '.docx'])."""
        ...


class PlainTextProcessor(AbstractDocumentProcessor):
    """Simple processor for plain text files."""

    async def process(self, file_path: str) -> list[str]:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        # Simple chunking by paragraphs
        chunks = [p.strip() for p in text.split("\n\n") if p.strip()]
        return chunks if chunks else [text]

    def supported_extensions(self) -> list[str]:
        return [".txt", ".md"]


class PDFProcessor(AbstractDocumentProcessor):
    """Placeholder for PDF processing. Not yet implemented."""

    async def process(self, file_path: str) -> list[str]:
        raise NotImplementedError(
            "PDF processing not yet implemented. "
            "Will integrate with external parsing pipeline."
        )

    def supported_extensions(self) -> list[str]:
        return [".pdf"]


class DOCXProcessor(AbstractDocumentProcessor):
    """Placeholder for DOCX processing. Not yet implemented."""

    async def process(self, file_path: str) -> list[str]:
        raise NotImplementedError(
            "DOCX processing not yet implemented. "
            "Will integrate with external parsing pipeline."
        )

    def supported_extensions(self) -> list[str]:
        return [".docx"]
