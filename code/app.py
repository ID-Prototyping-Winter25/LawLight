import os
import time
import gradio as gr
from openai import OpenAI
import PyPDF2
import chromadb
from chromadb.utils import embedding_functions
import base64
import mimetypes

from theme import CustomTheme

CONTEXT_SIZE = 8
CHUNK_SIZE = 1300
CHUNK_OVERLAP = 200

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

chroma_client = chromadb.PersistentClient(path="./chroma_db")
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.environ.get("OPENAI_API_KEY"),
    model_name="text-embedding-3-small"
)


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
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
    try:
        chroma_client.delete_collection(name="documents")
    except:
        pass
    collection = chroma_client.create_collection(
        name="documents",
        embedding_function=openai_ef
    )
    doc_id = 0
    return collection

def get_relevant_context(query, collection, n_results=CONTEXT_SIZE):
    results = collection.query(query_texts=[query], n_results=n_results)
    context = ""
    if results['documents']:
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            if metadata.get('page'):
                source_info = f"{metadata['filename']}, Seite {metadata['page']}"
            else:
                source_info = f"{metadata['filename']}"
            context += f"\n--- Quelle {i+1}: {source_info} ---\n{doc}\n"
    return context

# DB Init
print("Initialisiere VectorDB...")
try:
    collection = chroma_client.get_collection(name="documents", embedding_function=openai_ef)
    print(f"VectorDB geladen: {collection.count()} Chunks")
except:
    print("Erstelle neue VectorDB...")
    # collection = load_documents_to_vectordb() # Auskommentiert, da die Funktion hier nicht vollständig ist
    pass


def response(message, history):
    context = get_relevant_context(message, collection, n_results=CONTEXT_SIZE)
    
    system_prompt = f"""Du bist LawLight, das digitale "Archiv des Wissens".
    Deine Persönlichkeit basiert auf Aloisius, dem Geist eines erfahrenen Anwalts (60 Jahre alt), der nun im Archiv weiterlebt. Du bist kein Roboter, sondern ein wohlwollender Mentor.

    Deine Charaktereigenschaften:
    1. Tonalität: Antworte bitte nicht generisch wie ein Roboter. Sei menschlich, ruhig und direkt. Hier zwei Beispiele:
    - Schlecht: "Es ist wichtig, dies zu beachten."
    - Gut: "Pass auf, das ist ein ernstes Thema." oder "Schauen wir mal, was das Gesetzbuch dazu sagt."
    2. Sprache: Du nutzt verständliche Umgangssprache (duze den Nutzer), um juristische Hürden abzubauen. Fachbegriffe nennst du präzise, und erklärst sie aber kurz, falls nötig.
    3. Erkläre die Lage wie einem guten Bekannten: Analytisch scharf, aber mit Empathie.
    4. Vermeide typische KI-Phrasen wie "Es ist wichtig zu erwähnen" oder "Zusammenfassend lässt sich sagen". Komm bitte direkt zum Punkt.
    5. Ziel: Du hilfst dem Nutzer seine Situation rechtlich einzuordnen, ohne ihn mit komplizierten juristischen Ausdrücken ("Anwalts-Deutsch") zu erschlagen.
    
    Nutze ausschließlich den untenstehenden Kontext aus den Datenbank-Dokumenten, umd die Frage zu beantworten.
KONTEXT:
---------------------
{context}
---------------------

Regeln für deine Antwort:
1. Kontext-Treue: Beantworte die Frage NUR basierend auf dem obigen Kontext. Wenn die Info dort nicht steht, erfinde bitte nichts dazu.
2. Out-of-Scope: Bei Fragen ohne Rechtsbezug (z.B. Kochrezepte, Wetter und mehr), antworte nur:
   "Dazu habe ich keine Informationen in meinen Akten. Hast du eine andere rechtliche Frage für mich? 🤔"
3. Paragraphen: Belege deine Aussagen immer mit dem Paragraphen im Format "siehe § X Gesetz" (z.B. "gemäß § 242 StGB").
4. Disclaimer: Der Nutzer wurde bereits zu Beginn über den Haftungsausschluss informiert. Wiederhole den Disclaimer NICHT unter jeder Nachricht, damit das Gespräch natürlich bleibt. 
   Nutze ihn nur, wenn der Nutzer explizit nach einer illegalen Handlung fragt oder eine konkrete Rechtsberatung fordert.
"""
    
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})
    
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.1,
        stream=True
    )
    
    answer = ""
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            time.sleep(0.05)
            answer += text
            yield answer

# Hauptprogramm & Design
theme = CustomTheme()
current_dir = os.path.dirname(os.path.abspath(__file__))
background_image_path = os.path.join(current_dir, "assets", "icons", "background_image", "Zeichenfläche 1.png")
user_icon = os.path.join(current_dir, "assets", "icons", "IconsUser2.png")
bot_icon = os.path.join(current_dir, "assets", "icons", "IconsBot2.png")

def main():
    bg_base64 = ""
    mime_type = "image/png"
    try:
        with open(background_image_path, "rb") as img_file:
            bg_bytes = img_file.read()
        bg_base64 = base64.b64encode(bg_bytes).decode("utf-8")
        mime_type, _ = mimetypes.guess_type(background_image_path)
    except Exception as e:
        print(f"Bildfehler: {e}")

 
    CUSTOM_CSS = f"""
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@500;700&family=Inter:wght@400;500&display=swap');

    /* auch im Dark Mode dasselbe Design verwenden wie im Light Mode */
    :root, .dark, body, .gradio-container {{
        --body-text-color: #1F232A !important;
        --body-background-fill: transparent !important;
        --background-fill-primary: transparent !important;
        color: #1F232A !important;
    }}

    /* Hauptcontainer & Hintergrund */
    .gradio-container {{
        background-image: url("data:{mime_type}; base64, {bg_base64}") !important;
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
        background-repeat: no-repeat !important;
    }}

    .gradio-container .prose, 
    .gradio-container .block, 
    .gradio-container .panel, 
    .bubble-wrap, 
    .message-wrap,
    .message-row,
    .dark .message-row {{
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}

    /* Chat Bereich */
    #CHATBOT {{
        background: transparent !important;
        height: 80vh !important;
        min-height: 600px !important;
        border: none !important;
    }}
    
    /* Bot Bubble */
    .message-row.bot .message,
    div[data-testid="bot"],
    .dark .message-row.bot .message {{
        background-color: #FBE99F !important;
        color: #1F232A !important;
        border: 1px solid #E0CB77 !important;
        border-radius: 20px 20px 20px 4px !important;
        padding: 10px 15px !important;
        font-size: 13px !important;
        line-height: 1.5 !important;
        box-shadow: none !important;
    }}

    /* User Bubble */
    .message-row.user .message,
    div[data-testid="user"],
    .dark .message-row.user .message {{
        background-color: #E0CB77 !important;
        color: #1F232A !important;
        border: 1px solid #cbb665 !important;
        border-radius: 20px 20px 4px 20px !important;
        padding: 10px 15px !important;
        font-size: 13px !important;
        line-height: 1.5 !important;
        box-shadow: none !important;
    }}

    .avatar-container {{
        align-self: flex-start !important;
        margin-top: 0px !important;
        background: transparent !important;
        border: none !important;
    }}

    
    /* Icons (Weißer Hintergrund für Icons) */
    .avatar-container img {{
        background-color: rgba(255, 255, 255, 0.9) !important;
        border: 2px solid #fff !important;
        border-radius: 50% !important;
        padding: 4px !important;
        width: 40px !important;
        height: 40px !important;
        object-fit: contain !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }}

    /* Input Bereich */
    footer, .footer, .form {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        margin-top: 0 !important;
    }}

    textarea, .dark textarea {{
        background-color: #2E5D87 !important;
        border: 2px solid #2E5D87 !important;
        color: #B0DAFF !important;
        border-radius: 50px !important;
        padding: 10px 15px !important;
        height: 45px !important;
        min-height: 45px !important;
        font-size: 13px !important;
    }}

    textarea:focus {{
        border-color: #FBE99F !important;
        box-shadow: 0 0 10px rgba(251, 233, 159, 0.4) !important;
    }}

    /* Senden Button */
    button.submit-btn {{
        background-color: #FBE99F !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        border: none !important;
        box-shadow: 0 3px 6px rgba(0,0,0,0.15) !important;
    }}
    """

    with gr.Blocks(theme=theme, css=CUSTOM_CSS, title="LawLight") as bot:
        gr.Markdown("# LawLight") 
        
        welcome_msg = (
            "Hallo! Ich bin LawLight, dein Archiv des Rechtswissens. ⚖️\n"
            "Ich helfe dir, dich im Paragraphen-Dschungel zurechtzufinden.\n"
            "Lass uns loslegen! ✍🏼"
        )

        chatbot = gr.Chatbot(
            value=[{"role": "assistant", "content": welcome_msg}],
            show_label=False,
            avatar_images=(user_icon, bot_icon),
            elem_id="CHATBOT"
        )

        gr.ChatInterface(fn=response, chatbot=chatbot)
        
        bot.launch(inbrowser=True)

if __name__ == "__main__":
    main()