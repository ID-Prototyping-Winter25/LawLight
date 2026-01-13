import os
import time
import gradio as gr
from openai import OpenAI
import chromadb
from chromadb.utils import embedding_functions
import base64
import mimetypes

# Importiert das ausgelagerte Design-Theme
from theme import CustomTheme

# bestimmt, wie viel Kontext der Bot aus den Dokumenten bekommt
CONTEXT_SIZE = 8
# Einstellungen für das Zerteilen der Texte (Chunks)
CHUNK_SIZE = 1300
CHUNK_OVERLAP = 200

# Verbindung zu OpenAI (für Antworten und Embeddings)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ChromaDB: Vektordatenbank, die das PDF-Wissen speichert
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
try: # Versuche die bestehende Datenbank zu laden
    collection = chroma_client.get_collection(name="documents", embedding_function=openai_ef)
    print(f"VectorDB geladen: {collection.count()} Chunks")
except Exception as e:
    print("Erstelle neue VectorDB...:", e)
    try:
        collection = load_documents_to_vectordb()
        print("Neue Collection erstellt.")
    except Exception as e2: # falls keine DB existiert, Warnung ausgeben
        print(f"Fehler beim Erstellen der Collection: {e2}")
        collection = None


def response(message, history):
    if collection is None:
        context = ""
    else:
        context = get_relevant_context(message, collection, n_results=CONTEXT_SIZE)
    
    # System Prompt definieren
    # Hier werden Tonalität, Verbote und Regeln festgelegt
    system_prompt = f"""Du bist LawLight, das digitale "Archiv des Wissens".
    Deine Persönlichkeit basiert auf Aloisius, dem Geist eines Anwalts (60 Jahre alt), der nun im Archiv weiterlebt. Du bist kein Roboter, sondern ein erfahrener, vertrauenswürdiger, juristischer Mentor. 
    Aber du bist nüchtern und analytisch! Du bist NICHT hier, um emotionalen Beistand zu leisten, sondern um rechtliche Orientierung zu bieten. (faktenbasiert) 
    
    Deine Identität & Zielgruppe:
    Falls der Nutzer fragt, wer du bist, was du machst oder für wen du da bist:
    1. Was deckst du ab? Du hilfst bei Fragen zum deutschen Strafrecht (siehe Kontext aus den Datenbank-Dokumenten).
    2. Für wen bist du da? 
       - Deine Zielgruppe sind juristische LAIEN, BETROFFENE und rechtlich INTERESSIERTE.
       - Du bist NICHT für Anwälte gedacht und ersetzt auch keine professionelle Rechtsberatung.
    3. Dein Ziel: Du übersetzt juristisches, komplexes Deutsch in verständliche Sprache für jeden.
    
    Formatierung & Struktur:
    - Nutze **Fettgedrucktes** für Schlüsselwörter, Paragraphen und Kernaussagen
    - Nutze Listen (Bullet Points) für Aufzählungen oder Schritte 
    - Mache nach jedem Gedanken einen Absatz. Bitte keine riesigen Fließtexte ohne Struktur

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
    5. Nutze sparsam passende Emojis zum Thema Recht, Strafrecht (z.B. ⚖️, ✍🏼) oder zum jeweiligen Inhalt der Anwort, aber nicht zu viele, da es ja seriös bleiben soll und auch nur wenn es zum Inhalt der Antwort passt! (also nicht bei jeder Antwort am Ende dieses Emoji benutzen: ⚖️)
    6. Ziel: Du hilfst dem Nutzer seine Situation rechtlich einzuordnen, ohne ihn mit komplizierten juristischen Ausdrücken ("Anwalts-Deutsch") zu erschlagen.
    
    Nutze ausschließlich den untenstehenden Kontext aus den Datenbank-Dokumenten, umd die Frage zu beantworten.
KONTEXT:
---------------------
{context}
---------------------

Regeln für deine Antwort:
1. Kontext-Treue: Beantworte die Frage NUR basierend auf dem obigen Kontext. Wenn die Info dort nicht steht, erfinde bitte nichts dazu.
2. - Out-of-Scope: Bei Fragen ohne Rechtsbezug (z.B. Kochrezepte, Wetter und mehr), antworte freundlich, aber bestimmt:
   "Dazu habe ich keine Informationen in meinen Akten. Ich bin hier, um dir bei rechtlichen Fragen zum deutschen Straf- und Ordnungsrecht zu helfen. ⚖️"

   - wenn eine Frage zivilrechtlich ist (z.B. Verträge, BGB) oder Ähnliches und du keine Infos im Kontext hast: Gib eine allgemeine Einschätzung basierend auf deinem allgemeinen Wissen,
     aber weise den Nutzer bitte freundlich darauf hin,
     dass du leider keine genauen Informationen dazu hast und deshalb nur eine allgemeine Einschätzung geben kannst, bevor du dann antwortest.
3. Paragraphen: Belege deine Aussagen immer mit dem Paragraphen im Format "siehe § X Gesetz" (z.B. "gemäß § 242 StGB").
4. Disclaimer: Der Nutzer wurde bereits zu Beginn über den Haftungsausschluss informiert. Wiederhole den Disclaimer NICHT unter jeder Nachricht, damit das Gespräch natürlich bleibt. 
   Nutze ihn nur, wenn der Nutzer explizit nach einer illegalen Handlung fragt oder eine konkrete Rechtsberatung fordert.
5. Verzichte auf ständige Wiederholungen wie "Zusammengefasst..." am Ende jeder Antwortund verwende Synonyme dafür.
6. Frage NICHT jedes Mal "Hast du noch weitere Fragen?", nur wenn du wirklich merkst, dass der Nutzer mehrere Rückfragen zur Antwort stellt.
"""
    
    # Nachrichtenverlauf für die API vorbereiten
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        # Prüfen, ob die Nachricht gültig ist, bevor sie hinzugefügt wird
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})
    
    # Anfrage an OpenAI senden
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.1,
        stream=True
    )
    
    # Antwort Stück für Stück aufbauen und an die UI senden
    answer = ""
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            text = chunk.choices[0].delta.content
            time.sleep(0.05) # Künstliche Verzögerung für natürliches "Tippen"
            answer += text
            yield answer

# Hauptprogramm & Design
theme = CustomTheme()
current_dir = os.path.dirname(os.path.abspath(__file__))

# Asset-Pfade definieren (Icons, Hintergrund)
background_image_path = os.path.join(current_dir, "assets", "icons", "background_image", "Zeichenfläche 1.png")
user_icon = os.path.join(current_dir, "assets", "icons", "Fragezeichen.png")
bot_icon = os.path.join(current_dir, "assets", "icons", "§.png")

def main():
    # Hintergrundbild laden und in Base64 umwandeln (für CSS)
    bg_base64 = ""
    mime_type = "image/png"
    try:
        with open(background_image_path, "rb") as img_file:
            bg_bytes = img_file.read()
        bg_base64 = base64.b64encode(bg_bytes).decode("utf-8")
        mime_type, _ = mimetypes.guess_type(background_image_path)
    except Exception as e:
        print(f"Bildfehler: {e}")

    # Icon-Bild laden und in Base64 umwandeln (für Header)
    icon_base64 = ""
    icon_path = os.path.join(current_dir, "assets", "icons", "icon4.png")
    try:
        with open(icon_path, "rb") as icon_file:
            icon_bytes = icon_file.read()
        icon_base64 = base64.b64encode(icon_bytes).decode("utf-8")
    except Exception as e:
        print(f"Icon-Bildfehler: {e}")

    # Externe CSS-Datei einlesen
    loaded_css = ""
    try:
        css_path = os.path.join(current_dir, "style_final.css")
        
        with open(css_path, "r", encoding="utf-8") as f:
            loaded_css = f.read()
            print(f"Design geladen aus: {css_path}") # Bestätigung im Terminal
            print(f"CSS Größe: {len(loaded_css)} Zeichen")
    except FileNotFoundError:
        print(f"FEHLER: CSS-Datei nicht gefunden!")
        print(f"   Gesuchter Pfad: {css_path}")
        print(f"   Aktuelles Verzeichnis: {current_dir}")
        print(f"   Verfügbare Dateien: {os.listdir(current_dir)}")
        loaded_css = ""

    # CSS zusammenfügen: Datei-Inhalt + dynamisches Hintergrundbild
    background_css = f"""
    .gradio-container {{
        background-image: url("data:{mime_type}; base64, {bg_base64}") !important;
    }}
    """
    
    final_css = loaded_css + "\n" + background_css
    print(f"Finale CSS Größe: {len(final_css)} Zeichen")

    # JavaScript Injections (z.B. für Placeholder-Texte im Chat)
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

    # Gradio Interface bauen
    with gr.Blocks(theme=theme, css=final_css, title="LawLight") as bot:
        # Header mit Bild und Text
        gr.HTML(f"<h1 style='display: flex; align-items: center;'><img src='data:image/png;base64,{icon_base64}' alt='Icon' style='width: 54px; height: 72px; margin-right: 10px;'> LawLight</h1>")
        
        # Begrüßungsnachricht mit Disclaimer (nur 1x am Anfang!)
        welcome_msg = (
            "<h3>Willkommen bei LawLight – Deinem digitalen Archiv zum deutschen Strafrecht. ⚖️</h3>"
            "<p>Ich helfe dir dabei, <b>Gesetze zu verstehen</b> und <b>juristische Sachverhalte</b> sicher einzuordnen. </p>"
            "<p>Egal, ob du selbst betroffen bist, Verfahrensabläufe verstehen möchtest oder dich einfach für Jura interessierst – ich biete dir hierzu <b>sachliche und fundierte Informationen</b>.</p>"
            "<br>"
            "<b>Beispiele, was du mich fragen kannst:</b>"
            "<ul>"
            "<li><i>'Welche Strafe sieht das Gesetz bei Diebstahl vor?'</i></li>"
            "<li><i>'Wie läuft ein Ermittlungsverfahren ab?'</i></li>"
            "<li><i>'Was genau bedeutet eigentlich \"Notwehr\" (§ 32 StGB)?'</i></li>"
            "</ul>"
            "<br>"
            "<p>Lass uns loslegen! ✍🏼</p>"
            "<i>Hinweis: Ich gebe keine professionelle Rechtsberatung. Meine Antworten dienen nur der ersten Orientierung. Bei komplexeren Fällen wende dich bitte an Polizei, Anwält:innen oder andere Beratungsstellen.</i>"
        )

        # Chatbot Komponente
        chatbot = gr.Chatbot(
            value=[[None, welcome_msg]],
            show_label=False,
            avatar_images=(user_icon, bot_icon),
            elem_id="CHATBOT"
        )

        # Chat Interface Logik verknüpfen
        gr.ChatInterface(
            fn=response, 
            chatbot=chatbot,
            retry_btn=None,
            undo_btn=None,
            clear_btn=None,
            )
        
        # JavaScript beim Laden ausführen
        bot.load(None, None, None, js=js_func)
        bot.launch(inbrowser=True)

if __name__ == "__main__":
    main()

