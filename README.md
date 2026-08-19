# ⚖️ Alpha Advocates LLP — Legal Information Assistant

A deployable Streamlit prototype for a **grounded, source-visible legal information assistant** for Alpha Advocates LLP in Addis Ababa, Ethiopia.

The app answers only from local, firm-controlled knowledge files. It runs in an extractive demo mode without an API key and uses Gemini for concise synthesis when a key is configured.

## What is improved from the original draft

- Uses Google's current `google-genai` SDK instead of the retired `google.generativeai` package.
- Makes the Gemini model configurable; the included default is `gemini-3.1-flash-lite`.
- Removes LangChain, Chroma, Torch, and downloaded embedding-model dependencies.
- Uses a lightweight local BM25 retriever, suitable for a small curated knowledge base and free hosting.
- Reads Markdown, text, and text-based PDF files.
- Shows the knowledge sources used for each answer.
- Rejects unsupported questions instead of asking the model to guess.
- Treats the knowledge base and user input as untrusted data to reduce prompt-injection risk.
- Appends the exact disclaimer and consultation referral in application code, so the model cannot omit them.
- Starts safely in demo mode when no API key is present.
- Includes privacy messaging, a user acknowledgement, and firm contact details.

## Project structure

```text
alpha-legal-assistant/
├── app.py
├── core/
│   ├── assistant.py
│   └── knowledge.py
├── knowledge_base/
│   ├── 01_firm_profile.md
│   ├── 02_practice_areas.md
│   ├── 03_contact_and_consultations.md
│   ├── 04_knowledge_scope.md
│   └── README.md
├── tests/
│   └── test_core.py
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
├── DEPLOYMENT.md
├── SYSTEM_PROMPT.md
├── requirements.txt
└── requirements-dev.txt
```

## Run locally

Requirements: Python 3.11 or newer.

```bash
cd alpha-legal-assistant
python -m venv .venv
source .venv/bin/activate             # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Add a Gemini API key to `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your-real-key"
GEMINI_MODEL = "gemini-3.1-flash-lite"
```

Then run:

```bash
streamlit run app.py
```

Without a key, the app still starts and displays the most relevant approved excerpts. This is useful for UI review and safe demonstrations.

## Add lawyer-approved knowledge

1. Add `.md`, `.txt`, or text-based `.pdf` files to `knowledge_base/`.
2. Give Markdown files a title, source link, and review date using the example in `knowledge_base/README.md`.
3. Restart or redeploy the app.
4. Test supported and unsupported questions before publishing.

Do not upload client files to the public app. Do not represent draft, repealed, unverified, or unreviewed material as current law.

## Test

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Free-tier note

The prototype can be hosted on Streamlit Community Cloud and can use a Gemini free tier where available. Free quotas, eligible models, hosting limits, and terms can change. “$0” is therefore a prototype target, not a permanent cost guarantee. Keep the model ID configurable and monitor usage and provider notices.

## Production boundaries

Before public launch, Alpha Advocates LLP should approve:

- every legal source and answer policy;
- privacy notice, retention policy, and vendor/data-location choices;
- whether chat logging is allowed (this code does not add a chat database);
- escalation and secure-intake procedures;
- scheduled legal-content review and withdrawal of superseded content;
- accessibility, Amharic-language quality, and adversarial safety testing.

See [DEPLOYMENT.md](DEPLOYMENT.md) for the deployment and website-integration steps.
