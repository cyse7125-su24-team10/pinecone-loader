# pinecone-loader

This project downloads CVE records from a [CVE](https://github.com/CVEProject/cvelistV5/releases) URL, processes them, and stores their embeddings in a Pinecone vector database using HuggingFace's `BAAI/bge-small-en-v1.5` model. The workflow handles downloading, unzipping, processing, embedding, and cleaning up after the data has been processed.

## Requirements

- **Languages**: Python 3.9
- **Dependencies**:
   - streamlit
   - python-dotenv
   - langchain
   - langchain_community
   - faiss-cpu
   - langchain-groq
   - pinecone-client
   - langchain-pinecone
  - HuggingFace embeddings model `BAAI/bge-small-en-v1.5`
  - Pinecone vector store

## Workflow

1. **Downloading and Unzipping**:
   - Downloads a zip file containing JSON files with CVE data, unzips the contents, and processes the JSON files.
   
2. **Moving Files**:
   - Moves JSON files into a `data` folder for further processing.
   
3. **Processing CVE Data**:
   - Parses JSON files, skips "REJECTED" CVEs, and processes the remaining ones to extract descriptions and metadata.
   
4. **Embedding with HuggingFace**:
   - Uses HuggingFace’s `bge-small-en-v1.5` model to generate embeddings for storage in Pinecone.
   
5. **Pinecone Integration**:
   - Stores embeddings in Pinecone using `langchain.vectorstores.Pinecone`.
   
6. **Cleanup**:
   - Removes extracted files and the original zip file after processing.

## Setup Instructions

1. **Environment Setup**:
   - Ensure you have Python 3.9 installed.
   - Create and activate a virtual environment:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - Install the required dependencies:
     ```bash
     pip install -r requirements.txt
     pip install torch --index-url https://download.pytorch.org/whl/cpu
     pip install sentence-transformers
     ```

2. **Environment Variables**:
   - Create a `.env` file in the root directory with the following variables:
     ```bash
     PINECONE_API_KEY=your_pinecone_api_key
     PINECONE_CLOUD=aws
     PINECONE_REGION=us-east-1
     URL=https://your_download_link.com/deltaCves.zip
     ```

3. **Running the Application**:
   - To execute the script, run:
     ```bash
     python pinecone_db.py
     ```

## Docker Instructions

1. **Docker Build**:
   - Build the Docker image using the following command:
     ```bash
     docker build -t cve-processor:latest .
     ```

2. **Running the Docker Container**:
   - Run the container with the necessary environment variables:
     ```bash
     docker run --env-file .env cve-processor:latest
     ```

## Key Components

### `pinecone_db.py`

This script handles:
- Downloading and unzipping CVE data.
- Moving JSON files to the `data` directory.
- Processing and embedding CVE data using HuggingFace models.
- Storing embeddings in Pinecone and cleaning up resources.

### `Dockerfile`

The `Dockerfile` sets up the environment, installs dependencies, and defines the entry point to run the `pinecone_db.py` script inside a containerized environment.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

