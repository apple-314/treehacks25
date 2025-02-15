import os
import requests
import tarfile
import glob
import json

# Updated list of arXiv IDs (replacing "Adam" paper with "The Rise and Potential of Large Language Model Based Agents: A Survey")
arxiv_ids = [
    "1706.03762",  # Attention Is All You Need
    "2001.08361",  # Scaling Laws for Neural Language Models
    "2303.08774",  # GPT-4 Technical Report
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
    "2303.12712",  # Sparks of AGI
    "2309.07864"   # The Rise and Potential of Large Language Model Based Agents: A Survey
]

# Directories
source_dir = "arxiv_sources"
text_output_dir = "arxiv_tex_text"
metadata_output_file = "arxiv_metadata.json"
os.makedirs(source_dir, exist_ok=True)
os.makedirs(text_output_dir, exist_ok=True)

def download_and_extract_source(arxiv_id):
    """Download and extract LaTeX source from arXiv."""
    url = f"https://arxiv.org/e-print/{arxiv_id}"
    tar_path = os.path.join(source_dir, f"{arxiv_id}.tar.gz")
    extract_path = os.path.join(source_dir, arxiv_id)

    if os.path.exists(extract_path):
        print(f"Skipping {arxiv_id}, already downloaded.")
        return extract_path

    response = requests.get(url, stream=True)
    if response.status_code ==         200:
            with open(tar_path, "wb") as f:
                f.write(response.content)

            try:
                with tarfile.open(tar_path, "r:gz") as tar:
                    tar.extractall(path=extract_path)
                print(f"Extracted {arxiv_id} successfully.")
            except tarfile.ReadError:
                print(f"Error extracting {arxiv_id}. Skipping.")
                return None

    return extract_path

def extract_latex_to_text(arxiv_id):
    """Extract all .tex files from extracted LaTeX source and save as a .txt file."""
    extract_path = os.path.join(source_dir, arxiv_id)
    tex_files = glob.glob(os.path.join(extract_path, "**/*.tex"), recursive=True)

    if not tex_files:
        print(f"No .tex files found for {arxiv_id}.")
        return

    output_text_path = os.path.join(text_output_dir, f"{arxiv_id}.txt")

    with open(output_text_path, "w", encoding="utf-8") as output_file:
        for tex_file in tex_files:
            with open(tex_file, "r", encoding="utf-8", errors="ignore") as f:
                output_file.write(f"\n%%% FILE: {tex_file} %%%\n")
                output_file.write(f.read())

    print(f"Saved LaTeX text for {arxiv_id} to {output_text_path}")

def fetch_metadata(arxiv_id):
    """Fetch metadata from arXiv API."""
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    response = requests.get(url)

    if response.status_code == 200:
        try:
            data = response.text
            title_start = data.find("<title>") + len("<title>")
            title_end = data.find("</title>", title_start)
            title = data[title_start:title_end].strip()

            author_list = []
            author_start = 0
            while "<author><name>" in data[author_start:]:
                author_start = data.find("<author><name>", author_start) + len("<author><name>")
                author_end = data.find("</name>", author_start)
                author_list.append(data[author_start:author_end].strip())

            abstract_start = data.find("<summary>") + len("<summary>")
            abstract_end = data.find("</summary>", abstract_start)
            abstract = data[abstract_start:abstract_end].strip()

            year_start = data.find("<published>") + len("<published>")
            year_end = data.find("</published>", year_start)
            year = data[year_start:year_end].strip()[:4]

            return {
                "arxiv_id": arxiv_id,
                "title": title,
                "authors": author_list,
                "abstract": abstract,
                "year": year,
                "url": f"https://arxiv.org/abs/{arxiv_id}"
            }
        except Exception as e:
            print(f"Error parsing metadata for {arxiv_id}: {e}")
            return None
    else:
        print(f"Failed to fetch metadata for {arxiv_id}")
        return None

# Process each arXiv paper
metadata_list = []

for arxiv_id in arxiv_ids:
    extract_path = download_and_extract_source(arxiv_id)
    if extract_path:
        extract_latex_to_text(arxiv_id)

    metadata = fetch_metadata(arxiv_id)
    if metadata:
        metadata_list.append(metadata)

# Save metadata to JSON
with open(metadata_output_file, "w", encoding="utf-8") as f:
    json.dump(metadata_list, f, indent=4)

print("All papers processed. Metadata saved to arxiv_metadata.json.")