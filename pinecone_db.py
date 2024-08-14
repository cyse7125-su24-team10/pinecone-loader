import os
import json
import logging
import requests
import zipfile
from io import BytesIO
from shutil import move, rmtree
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain.vectorstores import Pinecone as LangchainPinecone

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom document class to match expected format
class CustomDocument:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata

# Function to download and unzip the file
def download_and_unzip(url, extract_to):
    response = requests.get(url)
    if response.status_code == 200:
        with zipfile.ZipFile(BytesIO(response.content)) as z:
            z.extractall(extract_to)
            logger.info(f"Downloaded and extracted the zip file to {extract_to}")
    else:
        logger.error(f"Failed to download the zip file: Status code {response.status_code}")
        raise Exception(f"Failed to download the zip file: Status code {response.status_code}")

# Function to create directory if it doesn't exist
def create_directory_if_not_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

# Function to move JSON files to the data directory
def move_json_files(src_dir, dest_dir):
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.json'):
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_dir, file)
                move(src_file, dest_file)
                logger.info(f"Moved {src_file} to {dest_file}")

# Function to clean up the extracted files and folders
def clean_up(directories, zip_file):
    for directory in directories:
        rmtree(directory, ignore_errors=True)
        logger.info(f"Removed directory: {directory}")
    if os.path.exists(zip_file):
        os.remove(zip_file)
        logger.info(f"Removed zip file: {zip_file}")

# Function to load and parse JSON files from data directory
def load_json_files(data_dir):
    documents = []
    for filename in os.listdir(data_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(data_dir, filename)
            try:
                with open(file_path) as f:
                    data = json.load(f)
                
                cve_id = data.get('cveMetadata', {}).get('cveId', 'Unknown CVE ID')
                cve_state = data.get('cveMetadata', {}).get('state', '').upper()
                
                # Skip if the CVE state is REJECTED
                if cve_state == 'REJECTED':
                    logger.info(f"Skipping REJECTED CVE: {cve_id}")
                    continue
                
                logger.info(f"Processing CVE: {cve_id}")
                description = data['containers']['cna']['descriptions'][0]['value']
                
                doc = CustomDocument(page_content=description, metadata={"cve_id": cve_id})
                documents.append(doc)
            except KeyError as e:
                logger.error(f"KeyError in file {filename}: {str(e)}")
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in file: {filename}")
            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}")
    
    logger.info(f"Total documents processed: {len(documents)}")
    return documents

# Initialize Pinecone
pinecone_api_key = os.getenv("PINECONE_API_KEY")
cloud = os.getenv("PINECONE_CLOUD", "aws")
region = os.getenv("PINECONE_REGION", "us-east-1")

spec = ServerlessSpec(cloud=cloud, region=region)
pc = Pinecone(api_key=pinecone_api_key)

# Initialize Pinecone index
index_name = "cve"
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name, 
        dimension=384,  # 384 is the dimension for BAAI/bge-small-en-v1.5
        metric='cosine', 
        spec=spec
    )

# Download and unzip the file
zip_url = os.getenv("URL")
logger.info(f"Downloading and extracting the zip file from {zip_url}")
zip_file_name = os.path.basename(zip_url)
download_and_unzip(zip_url, '.')

# Create the data directory if it doesn't exist
create_directory_if_not_exists('data')

# Move JSON files to the data directory
move_json_files('deltaCves', 'data')

# Load and prepare documents
data_dir = 'data'
embeddings = HuggingFaceBgeEmbeddings(
    model_name="BAAI/bge-small-en-v1.5",
    model_kwargs={'device':'cpu'},
    encode_kwargs={'normalize_embeddings':True}
)

try:
    docs = load_json_files(data_dir)
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    final_documents = text_splitter.split_documents(docs)

    # Create or update Pinecone vectorstore using LangChain's Pinecone wrapper
    vectorstore = LangchainPinecone.from_documents(
        documents=final_documents, 
        embedding=embeddings, 
        index_name=index_name
    )

    logger.info("Pinecone index updated successfully.")
    
    # Clean up the data, deltacves folder, and zip file
    clean_up(['deltaCves', 'data'], zip_file_name)
    
except Exception as e:
    logger.error(f"An error occurred in the main script: {str(e)}")
    raise
