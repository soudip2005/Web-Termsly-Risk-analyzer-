Web-Termsly is an AI-powered privacy policy analyzer designed to protect users by scanning long, complex "Terms of Service" agreements for potential risks. By using Natural Language Processing (NLP), the system extracts specific clauses, classifies them into risk categories, and generates multi-lingual summaries for better accessibility.


Key Features
Intelligent Web Scraping: Automatically searches for policy links on a domain and uses Selenium to extract text from dynamic JavaScript-heavy pages.

Machine Learning Classification: Uses a trained Logistic Regression model to identify "High," "Medium," and "Safe" risk factors within policy text.

Executive Summarization: Leverages the Hugging Face T5-small model to create concise, easy-to-read English summaries.

Multi-Lingual Support: Translates summaries into Bengali, Hindi, Tamil, French, and Russian to ensure non-native English speakers understand their rights.

Interactive Dashboard: A professional Streamlit UI featuring a risk distribution pie chart and detailed findings expanders.

Exportable Reports: Generates a professional PDF report containing the full analysis and translated summaries.




📊 Risk Levels Explained
🔴 High Risk: Includes data selling to third parties, waiving legal rights, or perpetual licenses to user content.

🟠 Medium Risk: Includes the use of cookies for analytics, sharing with service providers, or data retention policies.

🟢 Safe: Includes data deletion rights, encryption standards, and "Privacy by Design" principles.



⚖️ Disclaimer
Web-Termsly is an AI tool designed for educational and informational purposes. It does not provide legal advice. Always consult with a legal professional for binding agreements.