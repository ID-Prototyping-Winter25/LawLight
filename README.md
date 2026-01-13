# LawLight – Dein Chatbot zum deutschen Straf- und Ordnungsrecht

<div align="center">
  <img width="150" src="https://github.com/user-attachments/assets/93a2bd7f-404d-4a00-9986-a0399912606d" />
</div> 

**LawLight** ist ein Semesterprojekt von drei Studierenden des Studiengangs *Informatik und Design* an der Hochschule München.  
Unser Ziel: Ein Chatbot, der mithilfe von OpenAI-Technologie Fragen rund um das **deutsche Recht** beantwortet – verständlich für alle, ohne juristisches Fachwissen vorauszusetzen.

⚠️ **Wichtiger Hinweis:**  
LawLight bietet **keine Rechtsberatung** und ersetzt nicht den Rat einer qualifizierten Rechtsanwältin oder eines Rechtsanwalts. Die Antworten dienen ausschließlich zu Informationszwecken oder der ersten Orientierung bevor sie eine rechtsberatende Person konsultieren.

***

## Probiere LawLight aus
https://neele2-lawlight.hf.space

***

## Installation & lokale Nutzung

### Voraussetzungen

*   **Python 3.10+**
*   **pip** (Python-Paketmanager)
*   Ein **OpenAI API Key** (erforderlich für die lokale Nutzung des Chatbots)

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
Detailierte Einblicke in unseren Entwicklungsprozess findest du in unserem Projekt-Wiki:
https://github.com/ID-Prototyping-Winter25/LawLight/wiki

Figma Präsentation
https://www.figma.com/slides/UwW9SFU3DMqpcK2UF4aECe/Untitled?node-id=1-42&t=343u3m3KGvj7PCnJ-1

API für gesetztestexte
https://de.openlegaldata.io/

Figma Arbeitsboards mit Hintergrundinfos und Überlegungen
Accessability Check: https://www.figma.com/board/hqgdds3ckVgT2xl39lsts3/Accessibility-Check-LawLight?t=cn7j26W5EhJjmU3E-6

Usability Testing: https://www.figma.com/board/84MICquGFk7uriuhJUOtNo/Usability-Testing?t=cn7j26W5EhJjmU3E-6

Branding: https://www.figma.com/board/lZvkaVWlACTSOBtYDe1nUp/Projektmodul-Prototyping---Branding--Copy-?t=cn7j26W5EhJjmU3E-6

LawLight Logos: https://www.figma.com/board/O4m2xkVQkSnWNabN39nvD0/LawLight-Logos?t=cn7j26W5EhJjmU3E-6

Style Tile: https://www.figma.com/board/jhdC2U0DcSalIfDsfHlrw9/Style-Tile-LawLight?t=cn7j26W5EhJjmU3E-6

Präsentation LawLight: https://www.figma.com/slides/UwW9SFU3DMqpcK2UF4aECe/Law-Light-ChatBot?t=cn7j26W5EhJjmU3E-6


