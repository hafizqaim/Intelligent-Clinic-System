import logging
from pathlib import Path


from langchain_core.documents import Document
from langchain.document_loaders import DirectoryLoader
from langchain.comunity.document_loaders import PyPDFLoader, TextLoader, UnstructuredmarkdownLoader


logger = logging.getLogger(__name__)

def load_documents(directory: str) -> list[Document]:
    """
    Load documents from a directory.
    Supports: .txt, .pdf, .md
    Returns a flat list of LangChain Document objects.
    """
    docs: list[Document] = []
    dir_path = Path(directory)

    for file_path in dir_path.glob("*"):
        try:
            if file_path.suffix == ".txt":
                loader = TextLoader(str(file_path))
            elif file_path.suffix == ".pdf":
                loader = PyPDFLoader(str(file_path))
            elif file_path.suffix == ".md":
                loader = UnstructuredmarkdownLoader(str(file_path))
            else:
                continue  # skip unsupported files

            loaded = loader.load()
            docs.extend(loaded)

        except Exception as e:
            logger.warning(f"Failed to load {file_path}: {e}")

    logger.info(f"Loaded {len(docs)} documents from {directory}")
    if docs:
        logger.info(f"First doc preview: {docs[0].page_content[:200]}...")

    return docs
