import os
import time
import csv
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL_NAME = os.getenv("CURRENT_MODEL")  # Берем модель, указанную в .env

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def ask_model(prompt: str, model_name: str) -> tuple[str, float]:
    started = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "Отвечай точно и по существу."},
                {"role": "user", "content": prompt},
            ],
        )
        elapsed = time.perf_counter() - started
        return response.choices[0].message.content, elapsed
    except Exception as e:
        return f"Ошибка API: {e}", 0.0


if __name__ == "__main__":
    print(f"--- Начинаем тестирование модели: {MODEL_NAME} ---")

    # Наш тестовый запрос (пока один, для проверки работоспособности)
    prompt = "Объясни разницу между хешированием и шифрованием. Не более 50 слов."

    answer, latency = ask_model(prompt, MODEL_NAME)

    print(answer)
    print(f"\nВремя ответа: {latency:.2f} с")

    # Сохраняем результат в общий файл
    file_exists = os.path.isfile('results.csv')

    with open('results.csv', mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Если файла не было, пишем заголовки
        if not file_exists:
            writer.writerow(["model", "prompt", "latency", "answer"])

        # Записываем данные
        writer.writerow([MODEL_NAME, prompt, round(latency, 3), answer])

    print("\nРезультат добавлен в файл results.csv")