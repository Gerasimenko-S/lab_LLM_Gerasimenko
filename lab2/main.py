import os
import time
import json
from dotenv import load_dotenv
from openai import OpenAI

# Загружаем настройки из .env
load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)
MODEL = os.getenv("LLM_MODEL")

# Глобальный список для сбора результатов
all_results = []


def ask_model(experiment_name, prompt: str, system_id: str, system: str = "Ты полезный ассистент.", temperature=None,
              max_tokens=None, repeat=1):
    """
    Функция для отправки запроса и сохранения результата.
    """
    kwargs = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }

    # Добавляем параметры, только если они переданы
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    try:
        started = time.perf_counter()
        response = client.chat.completions.create(**kwargs)
        latency = time.perf_counter() - started
        answer = response.choices[0].message.content

        # Формируем запись по стандарту из раздела 8.6 методички
        result_entry = {
            "model": MODEL,
            "experiment": experiment_name,
            "temperature": temperature if temperature is not None else "default",
            "max_tokens": max_tokens if max_tokens is not None else "default",
            "system_id": system_id,
            "repeat": repeat,
            "latency_s": round(latency, 2),
            "answer": answer,
            "error": None
        }
        all_results.append(result_entry)
        print(
            f"  [Успех] {experiment_name} | {system_id} | T={temperature} | Повтор {repeat} | {round(latency, 2)} сек.")
        return answer

    except Exception as e:
        print(f"  [Ошибка] {e}")
        # Фиксируем ошибку API (например, если параметр не поддерживается)
        all_results.append({
            "model": MODEL,
            "experiment": experiment_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "system_id": system_id,
            "repeat": repeat,
            "latency_s": None,
            "answer": None,
            "error": str(e)
        })
        return None


def save_results():
    """Сохраняет все результаты в JSON."""
    filename = "results.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Все результаты ({len(all_results)} шт.) сохранены в файл {filename}")


# ==========================================
# ЭТАП 1: Базовая конфигурация
# ==========================================
def stage_1_baseline():
    print("\n--- ЭТАП 1: Базовая конфигурация (значения по умолчанию) ---")
    prompts = [
        "Привет! В двух словах, что такое информационная безопасность?",
        "Назови три основных принципа ИБ (триада).",
        "Что такое фишинг?"
    ]
    for i, p in enumerate(prompts):
        ask_model("stage_1_baseline", p, system_id="sys_default", repeat=1)


# ==========================================
# ЭТАП 2: Влияние system prompt
# ==========================================
def stage_2_system_prompt():
    print("\n--- ЭТАП 2: Влияние system prompt ---")
    user_prompt = "Событие: в 03:17 зафиксировано 25 неудачных попыток входа в учётную запись admin с одного IP, после чего произошёл успешный вход. Проанализируй ситуацию."

    systems = [
        ("sys_01", "Отвечай на запрос пользователя."),
        ("sys_02",
         "Ты ассистент аналитика ИБ. Отвечай не более чем в 5 пунктах. Для каждого пункта укажи риск и рекомендуемое действие."),
        ("sys_03",
         "Ты ассистент аналитика ИБ. Не выдумывай недостающие данные. Явно отделяй факты от предположений. Ответ верни в формате: Факты / Гипотезы / Действия.")
    ]

    for sys_id, sys_prompt in systems:
        ask_model("stage_2_system", user_prompt, system_id=sys_id, system=sys_prompt, repeat=1)



# ЭТАП 3: Влияние temperature
# ==========================================
def stage_3_temperature():
    print("\n--- ЭТАП 3: Влияние temperature (5 повторов) ---")
    user_prompt = "Предложи пять названий сервиса для автоматического анализа журналов событий информационной безопасности. Для каждого названия дай пояснение в одном предложении."

    # Значения строго по методичке: 0, 0.3, 0.7, 1.0
    # (Если LM Studio будет ругаться на 0.0, замените на 0.01)
    temperatures = [0.1, 0.3, 0.7, 1.0]

    for temp in temperatures:
        # Выполняем ровно 5 повторов для каждой конфигурации
        for rep in range(1, 6):
            ask_model("stage_3_temperature", user_prompt, system_id="sys_default", temperature=temp, repeat=rep)

# ==========================================
# ЭТАП 4: Ограничение длины (max_tokens)
# ==========================================
def stage_4_max_tokens():
    print("\n--- ЭТАП 4: Ограничение длины ---")
    user_prompt = "Объясни студенту 4 курса архитектуру RAG-системы: ingestion, chunking, embeddings, vector database, retrieval, prompt construction и generation. Для каждого этапа укажи его назначение и одну типичную ошибку."

    # Малый, средний и большой лимит (в токенах)
    limits = [50, 200, 500]

    for limit in limits:
        ask_model("stage_4_max_tokens", user_prompt, system_id="sys_default", max_tokens=limit, repeat=1)


if __name__ == "__main__":
    print(f"Запуск лабораторной работы на модели: {MODEL}")

    # Запускаем этапы по очереди
    stage_1_baseline()
    stage_2_system_prompt()
    stage_3_temperature()
    stage_4_max_tokens()

    # Сохраняем всё в файл
    save_results()
    print("\nРабота завершена! Откройте файл results.json для анализа.")