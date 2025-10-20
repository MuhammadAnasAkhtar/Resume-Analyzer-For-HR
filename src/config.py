# src/config.py
import os
import logging
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

load_dotenv()
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger("resume_analyzer")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "anas")

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# initialize pinecone client but do not auto-create indexes to avoid quota issues
pc = None
index = None
NAMESPACE = f"dim{EMBEDDING_DIM}"

try:
    if PINECONE_API_KEY:
        pc = Pinecone(api_key=PINECONE_API_KEY)
        index_list = [i["name"] for i in pc.list_indexes()]
        if PINECONE_INDEX_NAME in index_list:
            index = pc.Index(PINECONE_INDEX_NAME)
            LOG.info("Using existing pinecone index '%s'", PINECONE_INDEX_NAME)
        else:
            LOG.warning("Pinecone index '%s' not found. Pinecone features disabled.", PINECONE_INDEX_NAME)
            index = None
    else:
        LOG.warning("PINECONE_API_KEY not set. Pinecone features disabled.")
except Exception as e:
    LOG.exception("Pinecone initialization error: %s", e)
    index = None
