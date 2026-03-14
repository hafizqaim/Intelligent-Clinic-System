
from langchain_core.documents import Document
from langchain.community.text_splitters import RecursiveCharacterTextSplitter

def chunk_documents(documents: list[Document], chunk_size: int = 1000, chunk_overlap: int = 200) -> list[Document]:
    """
    Chunk documents into smaller pieces using RecursiveCharacterTextSplitter.
    Returns a flat list of chunked Document objects.
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, 
                                                   chunk_overlap=chunk_overlap,
                                                   separators=["\n\n", "\n",". " ," ", ""])
    chunked_docs: list[Document] = []

    for doc in documents:
        chunks = text_splitter.split_text(doc.page_content)
        for i, chunk in enumerate(chunks):
            chunked_doc = Document(
                page_content=chunk,
                metadata={**doc.metadata, "chunk_index": i}
            )
            chunked_docs.append(chunked_doc)

    lengths = [len(d.page_content) for d in chunked_docs]
    print(f"Total chunks: {len(chunked_docs)}")
    if lengths:
        print(f"Avg length: {sum(lengths)/len(lengths):.1f}, "
              f"Min: {min(lengths)}, Max: {max(lengths)}")

    return chunked_docs
