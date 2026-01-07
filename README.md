# LawLight – Chatbot für deutsches Recht

**LawLight** ist ein Semesterprojekt von drei Studierenden des Studiengangs *Informatik und Design* an der Hochschule München.  
Unser Ziel: Ein Chatbot, der mithilfe von OpenAI-Technologie Fragen rund um das **deutsche Recht** beantwortet – verständlich für alle, ohne juristisches Fachwissen vorauszusetzen.

⚠️ **Wichtiger Hinweis:**  
LawLight bietet **keine Rechtsberatung** und ersetzt nicht den Rat einer qualifizierten Rechtsanwältin oder eines Rechtsanwalts. Die Antworten dienen ausschließlich zu Informationszwecken.

***

## Probiere LawLight aus
https://huggingface.co/spaces/Neele2/LawLight

***

## Installation & Nutzung

### Voraussetzungen

*   **Python 3.10+**
*   **pip** (Python-Paketmanager)
*   Ein **OpenAI API Key** (erforderlich für die Nutzung des Chatbots)

### Schritte

1.  **Repository klonen**
    ```bash
    git clone https://github.com/dein-github-username/LawLight.git
    cd LawLight
    ```

2.  **Virtuelle Umgebung erstellen (optional, empfohlen)**
    ```bash
    python -m venv venv
    source venv/bin/activate   # macOS/Linux
    venv\Scripts\activate      # Windows
    ```

3.  **Abhängigkeiten installieren**
    ```bash
    pip install -r requirements.txt
    ```

4.  **API Key konfigurieren**
    Erstelle eine `.env`-Datei im Projektverzeichnis und füge deinen OpenAI API Key hinzu:
        OPENAI_API_KEY=dein_api_key

5.  **Chatbot starten**
    ```bash
    python code/app.py
    ```
    Danach kannst du den Chatbot lokal nutzen.

## Weitere Infos
Figma Präsentation
https://www.figma.com/slides/UwW9SFU3DMqpcK2UF4aECe/Untitled?node-id=1-42&t=343u3m3KGvj7PCnJ-1

Figma Board
https://www.figma.com/board/jzC45tqIO9dFuR4YuV5jkJ/Untitled?node-id=0-1&p=f&t=JVQUrFIHCOjLQT6a-0

API für gesetztestexte
https://de.openlegaldata.io/


