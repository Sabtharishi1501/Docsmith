# ⚒️ Docsmith

> **Smart DevTool for API Integration**

Docsmith is an AI-powered developer assistant that simplifies API integration by analyzing API documentation, extracting key information, generating SDK wrapper classes, and answering documentation-related questions through an intelligent chat interface.

---

## ✨ Features

- 📄 Analyze API documentation from any URL
- 🔍 Automatically extract:
  - API endpoints
  - Authentication methods
  - Base URLs
  - SDK information
- 🤖 AI-powered documentation chat
- 💡 API Advisor for best practices and API recommendations
- ⚙️ Generate wrapper classes in:
  - Python
  - JavaScript
  - TypeScript
  - Java
- 📥 Download generated client code
- ⚡ Semantic search using vector indexing

---

## 🏗️ How It Works

1. Enter an API documentation URL.
2. Docsmith scrapes and processes the documentation.
3. Documentation is chunked and indexed for semantic retrieval.
4. AI extracts endpoints, authentication methods, and SDK information.
5. A wrapper class is generated automatically.
6. Chat with the documentation to get contextual answers and integration guidance.

---

## 🛠️ Tech Stack

- Python
- Streamlit
- Groq API (Llama 3.3 70B)
- FAISS
- Sentence Transformers
- BeautifulSoup
- Requests
- python-dotenv

---

## 🚀 Installation

Clone the repository

```bash
git clone https://github.com/yourusername/Docsmith.git
cd Docsmith
```

Create a virtual environment

```bash
python -m venv venv
```

Activate it

**Windows**

```bash
venv\Scripts\activate
```

**Linux/macOS**

```bash
source venv/bin/activate
```

Install the dependencies

```bash
pip install -r requirements.txt
```

Create a `.env` file

```env
GROQ_API_KEY=your_groq_api_key
```

Run the application

```bash
streamlit run app.py
```

---

## 🔮 Roadmap

- Multi-document support
- Postman collection export
- OpenAPI/Swagger generation
- API testing sandbox
- Deployment support
- Improved retrieval with hybrid search

---

## 👨‍💻 Author

**Rishi**

Passionate about building AI-powered developer tools that simplify software development.

---

## ⭐ Support

If you found this project useful, consider giving it a **Star ⭐** on GitHub.