from langchain_community.document_loaders import ArxivLoader

test_paper = ["1706.03762"]  # Test with 'Attention Is All You Need'
loader = ArxivLoader(query="", arxiv_ids=test_paper)
docs = loader.load()

print(docs)  # Check if the document has actual content
