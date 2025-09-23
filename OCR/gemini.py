import google.generativeai as genai


genai.configure(api_key="AIzaSyC7EjsWlNLMVJfLyaBkAkYkud6bo9ElQ9U")
model = genai.GenerativeModel("gemini-2.0-flash")


resp = model.generate_content("Hello, test whether this model is accessible.")
print(resp.text)
