import openai
import time

# Можеш зберігати ключ у змінних середовища або secrets.toml
openai.api_key = "YOUR_OPENAI_API_KEY"  # 🔐 заміни або імпортуй окремо

def call_gpt(prompt: str, model: str = "gpt-4", max_tokens: int = 300) -> str:
    """
    Викликає GPT з заданим промптом і повертає відповідь як текст.
    """
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "Ти помічник-аналітик, який відповідає чітко, структуровано і коротко."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"[GPT Error] {e}")
        return "GPT Error"

