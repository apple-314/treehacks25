import os
import fitz  # PyMuPDF
import requests

# List of arXiv IDs for your 15 papers
arxiv_ids = [
    "1706.03762",  # Attention Is All You Need
    "2001.08361",  # Scaling Laws for Neural Language Models
    "2303.08774",  # GPT-4 Technical Report
    "1412.6980",   # Adam: A Method for Stochastic Optimization
    "1904.00962",  # LAMB: Optimizer for Large-Scale Distributed Training
    "1803.03635",  # Lottery Ticket Hypothesis: Finding Sparse, Trainable Neural Networks
    "2002.08909",  # REALM: Retrieval-Augmented Language Model Pre-Training
    "2005.11401",  # Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
    "2311.06605",  # Contrastive Learning for Many-to-Many RAG
    "2103.00020",  # CLIP: Learning Transferable Visual Models from Natural Language Supervision
    "2104.14294",  # DINO: Self-Supervised Vision Transformers Without Labels
    "2106.04560",  # Scaling Vision Transformers
    "1706.08947",  # Deep Reinforcement Learning with Human Preferences
    "2203.02155",  # RLHF: InstructGPT
    "2303.12712"   # Sparks of AGI
]

# Create folders to store PDFs and extracted text
pdf_folder = "arxiv_papers"
text_folder = "arxiv_text"
os.makedirs(pdf_folder, exist_ok=True)
os.makedirs(text_folder, exist_ok=True)

def download_pdf(arxiv_id):
    """Download an arXiv PDF and save it locally."""
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    pdf_path = os.path.join(pdf_folder, f"{arxiv_id}.pdf")

    if not os.path.exists(pdf_path):  # Avoid re-downloading
        response = requests.get(pdf_url)
        if response.status_code == 200:
            with open(pdf_path, "wb") as f:
                f.write(response.content)
            print(f"Downloaded: {pdf_path}")
        else:
            print(f"Failed to download: {pdf_url}")

    return pdf_path

def extract_text_from_pdf(pdf_path):
    """Extract text from a given PDF file."""
    try:
        doc = fitz.open(pdf_path)
        text = "\n".join([page.get_text("text") for page in doc])
        return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""

# Process all papers
for arxiv_id in arxiv_ids:
    pdf_path = download_pdf(arxiv_id)
    extracted_text = extract_text_from_pdf(pdf_path)

    # Save extracted text
    text_path = os.path.join(text_folder, f"{arxiv_id}.txt")
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(extracted_text)

    print(f"Extracted and saved text for {arxiv_id}")

print("All papers processed successfully.")
