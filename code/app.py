import os
import time
import gradio as gr
from openai import OpenAI
import PyPDF2
import chromadb
from chromadb.utils import embedding_functions

from theme import CustomTheme

# Konfiguration
CONTEXT_SIZE = 8  # Anzahl der relevantesten Dokument-Chunks
CHUNK_SIZE = 1300  # Größe der Text-Chunks in Zeichen
CHUNK_OVERLAP = 200  # Überlappung zwischen Chunks

# OpenAI Client initialisieren
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ChromaDB initialisieren
chroma_client = chromadb.PersistentClient(path="./chroma_db")
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.environ.get("OPENAI_API_KEY"),
    model_name="text-embedding-3-small"
)


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Teilt Text in überlappende Chunks"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    return chunks


def load_documents_to_vectordb(path="./Dokumente/"):
    """Lädt Dokumente und speichert sie in ChromaDB"""
    
    # Lösche alte Collection und erstelle neue
    try:
        chroma_client.delete_collection(name="documents")
    except:
        pass
    
    collection = chroma_client.create_collection(
        name="documents",
        embedding_function=openai_ef
    )
    
    doc_id = 0
    
    for filename in os.listdir(path):
        filepath = os.path.join(path, filename)
        
        if os.path.isdir(filepath):
            continue
        
        print(f"Verarbeite: {filename}")
        
        try:
            text = ""
            
            # PDF-Dateien
            if filename.endswith('.pdf'):
                with open(filepath, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    # Verarbeite jede Seite einzeln
                    for page_num, page in enumerate(pdf_reader.pages, 1):
                        page_text = page.extract_text()
                        if page_text.strip():
                            # Erstelle Chunks für diese Seite
                            page_chunks = chunk_text(page_text)
                            
                            for i, chunk in enumerate(page_chunks):
                                collection.add(
                                    documents=[chunk],
                                    metadatas=[{
                                        "filename": filename,
                                        "page": page_num,
                                        "chunk_id": i,
                                        "total_chunks": len(page_chunks),
                                        "source_type": "pdf"
                                    }],
                                    ids=[f"doc_{doc_id}"]
                                )
                                doc_id += 1
                            
                    print(f"  → PDF mit {len(pdf_reader.pages)} Seiten verarbeitet")
            
            # Text-Dateien
            elif filename.endswith(('.txt', '.md')):
                with open(filepath, 'r', encoding='utf-8') as f:
                    text = f.read()
                
                if text.strip():
                    chunks = chunk_text(text)
                    
                    for i, chunk in enumerate(chunks):
                        collection.add(
                            documents=[chunk],
                            metadatas=[{
                                "filename": filename,
                                "page": None,
                                "chunk_id": i,
                                "total_chunks": len(chunks),
                                "source_type": "text"
                            }],
                            ids=[f"doc_{doc_id}"]
                        )
                        doc_id += 1
                    
                    print(f"  → {len(chunks)} Chunks erstellt")
                    
        except Exception as e:
            print(f"Fehler beim Laden von {filename}: {e}")
    
    print(f"\nGesamt: {doc_id} Chunks in VectorDB gespeichert")
    return collection


def get_relevant_context(query, collection, n_results=CONTEXT_SIZE):
    """Sucht die relevantesten Dokument-Chunks für eine Anfrage"""
    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )
    
    context = ""
    if results['documents']:
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            # Zeige Seitenzahl für PDFs
            if metadata.get('page'):
                source_info = f"{metadata['filename']}, Seite {metadata['page']}"
            else:
                source_info = f"{metadata['filename']}"
            
            context += f"\n--- Quelle {i+1}: {source_info} (Chunk {metadata['chunk_id']+1}/{metadata['total_chunks']}) ---\n"
            context += doc + "\n"
    
    return context


# VectorDB beim Start initialisieren
print("Initialisiere VectorDB...")
try:
    # Versuche bestehende Collection zu laden
    collection = chroma_client.get_collection(
        name="documents",
        embedding_function=openai_ef
    )
    print(f"VectorDB geladen mit {collection.count()} Chunks")
except:
    # Falls Collection nicht existiert, erstelle neue
    print("Erstelle neue VectorDB und lade Dokumente...")
    collection = load_documents_to_vectordb()


def response(message, history):
    """Generiert eine Antwort mit OpenAI Streaming und RAG"""
    
    # Hole relevanten Kontext aus VectorDB
    context = get_relevant_context(message, collection, n_results=CONTEXT_SIZE)
    
    system_prompt = f"""Du bist ein hilfreicher Assistent, der Fragen basierend auf bereitgestellten Dokumenten beantwortet.

KONTEXT:
---------------------
{context}
---------------------

Beantworte die Frage NUR basierend auf dem obigen Kontext.
Wenn die Antwort nicht im Kontext zu finden ist, sage das klar und deutlich.
Antworte immer auf Deutsch und präzise aber verwende umgangsprache sodass der rechtliche Kontext leicht zu verstehen ist. Nenne aber alle Fachbegriffe.
Antworte möglichst kurz ohne wichtige Informationen wegzulassen.
Gib zu jeder Antwort an, in welchen Paragraphen die Informationen gefunden wurden!
"""
    
    # Konvertiere Gradio history Format zu OpenAI messages Format
    messages = [{"role": "system", "content": system_prompt}]
    
    for msg in history:
        if msg["role"] == "user":
            messages.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "assistant":
            messages.append({"role": "assistant", "content": msg["content"]})
    
    messages.append({"role": "user", "content": message})
    
    # Streaming-Anfrage an OpenAI mit stream_options
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.1,
        stream=True,
        stream_options={"include_usage": True}
    )
    
    answer = ""
    usage_info = None
    
    for chunk in stream:
        # Token-Usage kommt im letzten Chunk
        if hasattr(chunk, 'usage') and chunk.usage:
            usage_info = chunk.usage
        
        # Prüfe ob choices existiert und nicht leer ist
        if chunk.choices and len(chunk.choices) > 0 and chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            time.sleep(0.05)
            answer += text
            yield answer
    
    # Füge Token-Information am Ende hinzu
   # if usage_info:
   #     token_info = f"\n\n---\n💡 **Token-Usage:** Input: {usage_info.prompt_tokens} | Output: {usage_info.completion_tokens} | Total: {usage_info.total_tokens}"
   #     print(f"\n📊 Token-Usage für diese Anfrage:")
   #     print(f"   Input Tokens: {usage_info.prompt_tokens}")
   #     print(f"   Output Tokens: {usage_info.completion_tokens}")
   #     print(f"   Total Tokens: {usage_info.total_tokens}")
   #     answer += token_info
   #     yield answer


theme = CustomTheme()

def main():
    with gr.Blocks(title="LawLight") as bot:
        gr.Markdown("# LawLight")
        
        with gr.Tabs():
            with gr.TabItem("Chat"):
                chatbot = gr.Chatbot(
                    value=[{"role": "assistant", "content": "Wie kann ich dir helfen?"}],
                    show_label=False,
                    avatar_images=("./assets/icons/Icons User2.png", "./assets/icons/Icons bot2.png"),
                    elem_id="CHATBOT"
                )

                chatinterface = gr.ChatInterface(
                    fn=response,
                    chatbot=chatbot
                )
        
        bot.launch(inbrowser=True)


if __name__ == "__main__":
    main()