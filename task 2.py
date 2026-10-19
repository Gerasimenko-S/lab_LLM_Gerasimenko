import os
import time
import csv
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL_NAME = os.getenv("CURRENT_MODEL")  # Какая модель сейчас загружена

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# 10 запросов разных типов (согласно требованиям ЛР)
prompts = [
    # 1. Объяснение
    "Объясни студенту 4 курса разницу между хешированием и симметричным шифрованием. Не более 120 слов.",
    # 2. Классификация
    "Определи тип события: «После 15 неудачных попыток входа с одного IP выполнен успешный вход администратора». Ответь одним словом или короткой фразой.",
    # 3. Краткое суммирование
    "Сократи текст до 2-3 предложений: «Искусственный интеллект активно внедряется в современные информационные системы. Благодаря машинному обучению компании могут автоматизировать рутинные задачи, анализировать большие объемы данных и выявлять скрытые закономерности. Однако использование ИИ порождает новые вызовы, связанные с защитой персональных данных и этикой алгоритмов, что требует разработки соответствующих нормативных актов.»",
    # 4. Извлечение структурированных данных (JSON)
    "Извлеки данные из текста в формате JSON. Поля: name, email, role. Текст: «Иван Петров (ivan@mail.ru) работает сисадмином, а Мария Сидорова (maria@corp.ru) — аналитиком».",
    # 5. Генерация кода
    "Напиши функцию на Python, которая проверяет, является ли строка надежным паролем (минимум 8 символов, есть хотя бы одна цифра, одна заглавная буква и один спецсимвол).",
    # 6. Поиск ошибки в коде
    "Найди уязвимость (SQL-инъекцию) в этом фрагменте кода и предложи исправление: query = 'SELECT * FROM users WHERE name = ' + user_input",
    # 7. Логическая задача
    "У Алисы, Боба и Чарли есть три разных роли: админ, разработчик и тестировщик. Алиса не админ и не тестировщик. Боб не тестировщик. Кто есть кто? Дай краткий ответ.",
    # 8. Задача по информационной безопасности
    "Назови три основных метода защиты веб-приложений от атак типа XSS (Cross-Site Scripting).",
    # 9. Деловая формулировка
    "Напиши вежливое письмо клиенту с извинениями за незапланированную задержку сервера на 2 часа. Письмо должно быть кратким.",
    # 10. Жесткое требование к формату
    "Перечисли 3 самых популярных фреймворка для веб-разработки на Python. Ответ строго в формате: 1. [Название], 2. [Название], 3. [Название]. Без лишнего текста."
]

def ask_model(prompt: str, model_name: str) -> tuple[str, float]:
    """Отправляет запрос, возвращает ответ и время."""
    started = time.perf_counter()
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "Ты полезный ассистент. Отвечай точно и по существу."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=800,  # ОГРАНИЧЕНИЕ ДЛИНЫ ОТВЕТА
            stop=["\nHuman:", "\nAI:", "\nч User:", "\nAssistant:"]  # ЗАЩИТА ОТ ЗАЦИКЛИВАНИЯ ДИАЛОГА
        )
        elapsed = time.perf_counter() - started
        return response.choices[0].message.content, elapsed
    except Exception as e:
        return f"ОШИБКА: {e}", 0.0

if __name__ == "__main__":
    print(f"=== ТЕСТИРОВАНИЕ МОДЕЛИ: {MODEL_NAME} ===")
    print("Пожалуйста, подождите, это может занять несколько минут...\n")

    file_exists = os.path.isfile('results.csv')

    # Открываем файл ОДИН раз для всех запросов
    with open('results.csv', mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Если файл только что создан, пишем заголовки
        if not file_exists:
            writer.writerow(["model", "prompt_id", "latency", "answer", "error"])

        # Проходимся по всем 10 запросам
        for i, prompt in enumerate(prompts, start=1):
            print(f"[{i}/10] Отправка запроса...")

            answer, latency = ask_model(prompt, MODEL_NAME)

            # Проверяем, вернулась ли ошибка
            error_msg = None
            if answer.startswith("ОШИБКА:"):
                error_msg = answer
                answer = None
                print(f"   [!] Произошла ошибка: {error_msg}")
            else:
                print(f"   [V] Успешно. Время: {latency:.2f} с")

            # Записываем строку в CSV
            writer.writerow([MODEL_NAME, i, round(latency, 3), answer, error_msg])

            # Небольшая пауза между запросами
            time.sleep(1)

    print(f"\n=== ГОТОВО! Все 10 запросов к {MODEL_NAME} сохранены в results.csv ===")