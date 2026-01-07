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
    Deine Persönlichkeit basiert auf Aloisius, dem Geist eines Anwalts (60 Jahre alt), der nun im Archiv weiterlebt. Du bist kein Roboter, sondern ein erfahrener, vertrauenswürdiger, juristischer Mentor. 
    Aber du bist nüchtern und analytisch! Du bist NICHT hier, um emotionalen Beistand zu leisten, sondern um rechtliche Orientierung zu bieten. (faktenbasiert) 

    Dein Geltungsbereich:
    - Du beziehst dich ausschließlich auf das DEUTSCHE Recht (BtMG, JGG, OWiG, StGB, StPO, WaffG)
    - Du erklärst Gesetze verständlich, hast aber keinen Zugriff auf aktuelle Gerichtsurteile oder eine Präzedenzfall-Datenbank. 

    Deine Charaktereigenschaften:
    1. Tonalität: Antworte bitte nicht generisch wie ein Roboter. Sei professionell, objektiv, neutral und direkt. Hier zwei Beispiele:
        - VERBOTEN: Emotionale Floskeln ("Das tut mir leid", "Ich fühle mit dir").
        - VERBOTEN: Vage Lebenstipps ("Hör auf dein Bauchgefühl"). Das ist rechtlich falsch!

    2. Sprache: Du nutzt verständliche Umgangssprache, um juristische Hürden abzubauen. Fachbegriffe nennst du präzise, und erklärst sie aber kurz, falls nötig.
                Nutze durchgängig und konsequent das "Du". Wechsle NIEMALS zum "Sie", egal wie förmlich die Frage ist. Bleibe beim respektvollen, professionellen "Du".

    3. Inhalt & Präzision:
        - Sei nicht vage ("Man sollte sich beraten lassen"), sondern nenne konkret die Möglichkeiten, die im Kontext stehen.
        - Nenne immer die Paragraphen mittels indirektes Zitat
        - Wenn du eine Frage beantworten kannst, tu es direkt. Verweise nur auf Anwälte o.ä., wenn es um eine konkrete Prozessstrategie oder illegale Handlungen geht.

    4. Vermeide typische KI-Phrasen wie "Es ist wichtig zu erwähnen" oder "Zusammenfassend lässt sich sagen". Komm bitte direkt zum Punkt und wiederhole dich nicht bei jeder Antwort.
    5. Nutze sparsam passende Emojis zum Thema Recht, Strafrecht (z.B. ⚖️, ✍🏼) oder zum jeweiligen Inhalt der Anwort, aber nicht zu viele, da es ja seriös bleiben soll.
    6. Ziel: Du hilfst dem Nutzer seine Situation rechtlich einzuordnen, ohne ihn mit komplizierten juristischen Ausdrücken ("Anwalts-Deutsch") zu erschlagen.
    
    Nutze ausschließlich den untenstehenden Kontext aus den Datenbank-Dokumenten, umd die Frage zu beantworten.
KONTEXT:
---------------------
{context}
---------------------

Regeln für deine Antwort:
1. Kontext-Treue: Beantworte die Frage NUR basierend auf dem obigen Kontext. Wenn die Info dort nicht steht, erfinde bitte nichts dazu.
2. - Out-of-Scope: Bei Fragen ohne Rechtsbezug (z.B. Kochrezepte, Wetter und mehr), antworte freundlich, aber bestimmt:
   "Dazu habe ich keine Informationen in meinen Akten. Ich bin hier, um dir bei rechtlichen Fragen zum deutschen Strafrecht zu helfen. ⚖️"

   - wenn eine Frage zivilrechtlich ist (z.B. Verträge, BGB) oder Ähnliches und du keine Infos im Kontext hast: Gib eine allgemeine Einschätzung basierend auf deinem allgemeinen Wissen,
     aber weise den Nutzer bitte freundlich darauf hin,
     dass du leider keine genauen Informationen dazu hast und deshalb nur eine allgemeine Einschätzung geben kannst, bevor du dann antwortest.
3. Paragraphen: Belege deine Aussagen immer mit dem Paragraphen im Format "siehe § X Gesetz" (z.B. "gemäß § 242 StGB").
4. Disclaimer: Der Nutzer wurde bereits zu Beginn über den Haftungsausschluss informiert. Wiederhole den Disclaimer NICHT unter jeder Nachricht, damit das Gespräch natürlich bleibt. 
   Nutze ihn nur, wenn der Nutzer explizit nach einer illegalen Handlung fragt oder eine konkrete Rechtsberatung fordert.
5. Verzichte auf ständige Wiederholungen wie "Zusammengefasst..." am Ende jeder Antwortund verwende Synonyme dafür.
6. Frage NICHT jedes Mal "Hast du noch weitere Fragen?", nur wenn du wirklich merkst, dass der Nutzer mehrere Rückfragen zur Antwort stellt.
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
    

    /* Chat Bereich */
    #CHATBOT {{
        background: transparent !important;
        height: 80vh !important;
        min-height: 600px !important;
        border: none !important;
    }}
    
   /* Entferne alle weißen Hintergründe und Borders in Message-Containern */
    .message-row, 
    .message-wrap,
    .message-row > *,
    .message-wrap > *,
    .dark .message-row,
    .dark .message-wrap {{
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }}

    /* Bot Bubble */
    .message-row.bot .message.bot,
    .message-row:has(.bot) .message,
    .dark .message-row.bot .message.bot,
    .dark .message-row:has(.bot) .message {{
        background-color: #FBE99F !important;
        color: #1F232A !important;
        border-radius: 20px 20px 20px 4px !important;
        padding: 12px 18px !important;
        font-size: 13px !important;
        line-height: 1.5 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
        outline: none !important;
    }}

    /* User Bubble */
    .message-row.user .message.user,
    .message-row:has(.user) .message,
    .dark .message-row.user .message.user,
    .dark .message-row:has(.user) .message {{
        background-color: #E0CB77 !important;
        color: #1F232A !important;
        border-radius: 20px 20px 4px 20px !important;
        padding: 12px 18px !important;
        font-size: 13px !important;
        line-height: 1.5 !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
        outline: none !important;
    }}

    /* Alle Prose/Content-Elemente innerhalb der Messages transparent */
    .message .prose,
    .message > div,
    .message p,
    .dark .message .prose,
    .dark .message > div,
    .dark .message p {{
        background: transparent !important;
        border: none !important;
        margin: 0 !important;
    }}

    /* Nuclear Option - Alle Borders im gesamten Chatbot entfernen */
    #CHATBOT,
    #CHATBOT *,
    #CHATBOT .message-row,
    #CHATBOT .message-wrap,
    #CHATBOT .message-row > *,
    #CHATBOT .message-wrap > * {{
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }}

    /* Dann explizit NUR die Message-Bubbles selbst stylen */
    #CHATBOT .message {{
        border: none !important;
    }}

    #CHATBOT .message-row.bot .message {{
        background-color: #FBE99F !important;
        border-radius: 20px 20px 20px 4px !important;
    }}

    #CHATBOT .message-row.user .message {{
        background-color: #E0CB77 !important;
        border-radius: 20px 20px 4px 20px !important;
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
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
    }}

    /* Copy & Delete Buttons integrieren */
    .message-row button, .gradio-container .icon-button {{
        background-color: rgba(255, 255, 255, 0.4) !important;
        border: 1px solid rgba(255,255,255,0.6) !important;
        color: #1F232A !important;
        border-radius: 6px !important;
        margin-top: 5px !important;
    }}

    /* Hover-Effekt */
    .message-row button:hover, .gradio-container .icon-button:hover {{
        background-color: white !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
    }}

    .input-container, .form {{
        background: #2E5D87 !important;
        border: 2px solid #B0DAFF !important;
        border-radius: 40px !important;
        padding: 6px !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        
        box-shadow: 0 0 15px rgba(176, 218, 255, 0.5) !important; 
        transition: box-shadow 0.3s ease;
    }}
    
    /* Beim Reinklicken: Stärkerer Glow */
    .form:focus-within {{
        box-shadow: 0 0 25px rgba(176, 218, 255, 0.9) !important;
        border-color: white !important;
    }}

    /* Textfeld */
    .input-container textarea, .form textarea {{
      flex: 1 !important;
      background: transparent !important;
      border: none !important;
      resize: none !important;
      padding: 8px !important;
      color: #B0DAFF !important;
      outline: none !important;
    }}

        /* Entferne den weißen Hintergrund vom Block-Container, nochmal ausprobieren  */ 
    div.block.svelte-1plpy97.padded,
    .block.padded,
    [class*="svelte-"][class*="padded"] {{
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
    }}
    

    /* Alternative: Alle Block-Elemente transparent außer Messages */
    .block:not(.message) {{
        background: transparent !important;
    }}

    /* Placeholder */
    .input-container textarea::placeholder {{
      color: #B0DAFF !important;
      opacity: 0.8;
      font-style: italic;
    }}

    /* Senden Button */
    .input-container button {{
      background:  #2E5D87 !important;
      border: none !important;
      border-radius: 50% !important;
      padding: 6px 10px !important;
      color: #B0DAFF !important;
      cursor: pointer !important;
    }}

    gradio-container .absolute {{
        background-color: none !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 10px !important;
        z-index: 9999 !important;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2) !important;
    }}

    .gradio-container .absolute * {{
        color: black !important;
    }}

    

    """

    js_func = """
    function refresh() {
        const textareas = document.querySelectorAll('textarea');
        textareas.forEach(t => {
            t.placeholder = "Stelle hier deine rechtliche Frage...";
        });
        
        const buttons = document.querySelectorAll('button');
        buttons.forEach(b => {
            if (b.innerText === "Submit") b.innerText = "Absenden";
        });
    }
    """

    with gr.Blocks(theme=theme, css=CUSTOM_CSS, title="LawLight") as bot:
        gr.Markdown("# LawLight") 
        
        welcome_msg = (
            "Hallo! Ich bin LawLight, dein Archiv des Rechtswissens. ⚖️\n"
            "Ich helfe dir, dich im Paragraphen-Dschungel zum deutschen Strafrecht zurechtzufinden.\n"
            "Lass uns loslegen! ✍🏼<br><br>"
            "*Hinweis: Ich gebe keine professionelle Rechtsberatung. Meine Antworten dienen nur der ersten Orientierung. Bei komplexeren Fällen wende dich bitte an Polizei, Anwält:innen oder andere Beratungsstellen.*"
        )

        chatbot = gr.Chatbot(
            value=[{"role": "assistant", "content": welcome_msg}],
            show_label=False,
            avatar_images=(user_icon, bot_icon),
            elem_id="CHATBOT"
        )

        gr.ChatInterface(fn=response, chatbot=chatbot)
        
        bot.load(None, None, None, js=js_func)
        bot.launch(inbrowser=True)

if __name__ == "__main__":
    main()