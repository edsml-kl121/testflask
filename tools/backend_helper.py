import os
from langchain.document_loaders import PyPDFLoader
from .translation import translate_large_text, translate_to_thai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pymilvus import connections, utility, Collection, CollectionSchema, FieldSchema, DataType

base_folder_path='assets/pdfs'
def listing_docs(folder_path='assets/pdfs'):
    ## Specify the relative path to the 'pdfs' folder from your script's location
    # Get a list of files in the 'pdfs' directory
    files_in_directory = os.listdir(base_folder_path)

    # Filter out directories, leaving only files
    file_names = [file for file in files_in_directory if os.path.isfile(os.path.join(folder_path, file))]

    print(file_names)
    return file_names


def read_pdfs(file_names):
    translated_docs = []
    new_translated_docs = []
    page_contents = []
    pagesno = []
    sources = []

    # Assume file_names is a list of filenames that you have defined elsewhere
    print(file_names)
    for file in file_names:
        print("current file: ", file)
        loader = PyPDFLoader(f"{base_folder_path}/{file}")
        pages = loader.load()
        print(file, len(pages))

        # Temporary storage for the pages of the current file
        temp_translated_docs = []

        for page in pages:
            content = page.page_content
            translated_content = content # change with a translater
            page.page_content = translated_content
            temp_translated_docs.append(page)

        # Initialize the text splitter
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        # Split the documents into chunks
        docs = text_splitter.split_documents(temp_translated_docs)
        
        # Enhance each chunk with the file title
        for doc in docs:
            chunk_text = doc.page_content
            enhanced_chunk = f"title: {file}\n" + chunk_text  # Add the file title in front of each chunk
            doc.page_content = enhanced_chunk
            translated_content = translate_large_text(enhanced_chunk, translate_to_thai, False)
            page_contents.append(doc.page_content)
            new_translated_docs.append(translated_content)
            pagesno.append(doc.metadata["page"])
            sources.append(doc.metadata["source"])

        # After enhancing each chunk, we can add them to the translated_docs list
        translated_docs.extend(docs)
    return new_translated_docs, page_contents, pagesno, sources

# database_manager.py

# Constants for schema configuration
ID_MAX_LENGTH = 50000
TEXT_MAX_LENGTH = 50000
EMBEDDINGS_DIMENSION = 384

def create_field_schema():
    """Create field schemas for the collection."""
    return [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="new_translated_docs", dtype=DataType.VARCHAR, max_length=TEXT_MAX_LENGTH),
        FieldSchema(name="page_content", dtype=DataType.VARCHAR, max_length=TEXT_MAX_LENGTH),
        FieldSchema(name="embeddings", dtype=DataType.FLOAT_VECTOR, dim=EMBEDDINGS_DIMENSION),
        FieldSchema(name="pagesno", dtype=DataType.INT64, default_value=0),
        FieldSchema(name="sources", dtype=DataType.VARCHAR, max_length=TEXT_MAX_LENGTH),
    ]

def create_collection_schema(fields, description="Search promotional events"):
    """Create a collection schema with the provided fields."""
    return CollectionSchema(fields=fields, description=description, enable_dynamic_field=True)

def initialize_collection(collection_name, schema, using='default'):
    """Initialize a collection with the given name and schema."""
    return Collection(name=collection_name, schema=schema, using=using)

def manage_collection(collection_name):
    """Manage the creation or replacement of a collection."""
    if collection_name in utility.list_collections():
        utility.drop_collection(collection_name)
        print("Dropped old collection")

    fields = create_field_schema()
    schema = create_collection_schema(fields)
    collection = initialize_collection(collection_name, schema)
    print("Initialized new collection")

    return collection
