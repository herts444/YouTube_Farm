import os
from typing import Any, Dict, List, Optional, Union

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import OperationFailure

# === Конфиг ===
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB  = os.getenv("MONGO_DB",  "youtube_farm")

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


def db() -> AsyncIOMotorDatabase:
    """Синглтон к базе."""
    global _client, _db
    if _db is None:
        _client = AsyncIOMotorClient(MONGO_URI)
        _db = _client[MONGO_DB]
    return _db


# ----------------------------- УТИЛИТЫ -----------------------------

def is_object_id(val: Union[str, ObjectId]) -> bool:
    if isinstance(val, ObjectId):
        return True
    if not isinstance(val, str):
        return False
    try:
        ObjectId(val)
        return True
    except InvalidId:
        return False


def oid(id_str: str) -> ObjectId:
    """Оставлен для обратной совместимости."""
    return ObjectId(id_str)


def channel_selector(id_or_name: Union[str, ObjectId]) -> Dict[str, Any]:
    """
    Универсальный селектор канала:
      - если передан ObjectId / его hex -> {"_id": ...}
      - иначе -> {"name": <строка>}
    """
    if isinstance(id_or_name, ObjectId):
        return {"_id": id_or_name}
    if isinstance(id_or_name, str) and is_object_id(id_or_name):
        return {"_id": ObjectId(id_or_name)}
    return {"name": str(id_or_name)}


async def _ensure_index_safe(coll, keys: List[tuple], unique: bool = False) -> None:
    """
    Идемпотентное создание индекса:
      - если индекс с теми же keys уже есть — ничего не делаем (даже если unique отличается)
      - если нет — создаём с указанными параметрами
    keys: список пар, например [("name", 1)]
    """
    existing = await coll.list_indexes().to_list(length=None)
    # ключи в индексе — OrderedDict в 'key'
    for idx in existing:
        idx_keys = list(idx.get("key", {}).items())
        if idx_keys == keys:
            # Индекс по этим полям уже есть — не трогаем (во избежание IndexOptionsConflict)
            return
    try:
        await coll.create_index(keys, unique=unique)
    except OperationFailure:
        # если параллельно кто-то создал, или иная гонка — тихо игнорируем
        pass


# ----------------------------- ИНИЦИАЛИЗАЦИЯ -----------------------------

async def init_db() -> AsyncIOMotorDatabase:
    """
    Инициализирует соединение и индексы без конфликтов.
    """
    _ = db()  # прогреваем синглтон

    # Каналы: хотим индекс по name (можно уникальный, но не ломаем существующие)
    await _ensure_index_safe(db().channels, [("name", 1)], unique=True)

    # Тематики: индекс по name
    await _ensure_index_safe(db().themes, [("name", 1)], unique=True)

    # Промпты: уникальная комбинация (scope, preset, lang)
    await _ensure_index_safe(db().prompts, [("scope", 1), ("preset", 1), ("lang", 1)], unique=True)

    # Библиотека фонов: уникальная комбинация (scope, file)
    await _ensure_index_safe(db().backgrounds, [("scope", 1), ("file", 1)], unique=True)

    return db()


# ----------------------------- ТЕМАТИКИ -----------------------------

async def list_themes() -> List[Dict[str, Any]]:
    cur = db().themes.find({})
    return [doc async for doc in cur]


# ----------------------------- КАНАЛЫ -----------------------------

async def list_channels() -> List[Dict[str, Any]]:
    cur = db().channels.find({})
    return [doc async for doc in cur]


async def create_channel(name: str, **extra) -> Dict[str, Any]:
    """
    Создаёт канал (уникален по name).
    """
    defaults = {
        "name": name,
        "tts_engine": "edge",    # gtts/edge/elevenlabs/silero
        "tts_lang": "en",
        "tts_voice": None,
        "theme": None,           # строка-название тематики
        "subtitles": None,
        # --- Новое: конфиг для режима «Нарезки»
        # Если cuts is not None -> канал работает в режиме cuts
        "cuts": None,            # {"kind": "cartoons"|"films", "collection": "spongebob", "min_sec":180, "max_sec":240}
        # --- Пресет промпта:
        "prompt_preset": "default",
        # --- Тип фона для Reddit (видео или анимация):
        "background_type": "video",  # "video" или "animation"
    }
    defaults.update(extra or {})
    await db().channels.update_one(
        {"name": name},
        {"$setOnInsert": defaults},
        upsert=True,
    )
    return await db().channels.find_one({"name": name})

async def set_channel_cuts(id_or_name, kind: str, collection: str) -> None:
    await db().channels.update_one(
        channel_selector(id_or_name),
        {"$set": {"cuts": {"kind": kind, "collection": collection, "min_sec": 180, "max_sec": 240}}}
    )

async def set_channel_cuts_duration(id_or_name, min_sec: int, max_sec: int) -> None:
    ch = await db().channels.find_one(channel_selector(id_or_name))
    cuts = (ch or {}).get("cuts") or {}
    cuts.update({"min_sec": int(min_sec), "max_sec": int(max_sec)})
    await db().channels.update_one(channel_selector(id_or_name), {"$set": {"cuts": cuts}})

async def get_channel(id_or_name: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
    return await db().channels.find_one(channel_selector(id_or_name))


async def set_channel_theme(id_or_name: Union[str, ObjectId], theme_name: Optional[str]) -> None:
    await db().channels.update_one(channel_selector(id_or_name), {"$set": {"theme": theme_name}})


async def set_channel_tts(id_or_name: Union[str, ObjectId], engine: str) -> None:
    await db().channels.update_one(channel_selector(id_or_name), {"$set": {"tts_engine": engine}})


async def set_channel_tts_lang(id_or_name: Union[str, ObjectId], lang: str) -> None:
    await db().channels.update_one(channel_selector(id_or_name), {"$set": {"tts_lang": lang}})


async def set_channel_tts_voice(id_or_name: Union[str, ObjectId], voice: Optional[str]) -> None:
    await db().channels.update_one(channel_selector(id_or_name), {"$set": {"tts_voice": voice}})


async def set_channel_tts_speed(id_or_name: Union[str, ObjectId], speed: float) -> None:
    await db().channels.update_one(channel_selector(id_or_name), {"$set": {"tts_speed": speed}})


async def set_channel_prompt_preset(id_or_name: Union[str, ObjectId], preset: str) -> None:
    await db().channels.update_one(channel_selector(id_or_name), {"$set": {"prompt_preset": preset}})


async def set_channel_background_type(id_or_name: Union[str, ObjectId], bg_type: str) -> None:
    """Set background type for Reddit channel: 'video' or 'animation'"""
    await db().channels.update_one(channel_selector(id_or_name), {"$set": {"background_type": bg_type}})


async def delete_channel(id_or_name: Union[str, ObjectId]) -> None:
    await db().channels.delete_one(channel_selector(id_or_name))


# ----------------------------- PROMPTS (Reddit) -----------------------------
# Схема: { _id, scope: "reddit", preset: "default", lang: "ru|en", name?: str, text: str, created_at, updated_at, updated_by? }

from datetime import datetime

async def prompts_list(scope: str = "reddit", lang: Optional[str] = None) -> List[Dict[str, Any]]:
    q: Dict[str, Any] = {"scope": scope}
    if lang:
        q["lang"] = lang
    cur = db().prompts.find(q).sort([("preset", 1), ("lang", 1)])
    return [doc async for doc in cur]

async def prompts_get_by_id(pid: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
    _id = ObjectId(pid) if not isinstance(pid, ObjectId) else pid
    return await db().prompts.find_one({"_id": _id})

async def prompts_get(scope: str, preset: str, lang: str) -> Optional[Dict[str, Any]]:
    return await db().prompts.find_one({"scope": scope, "preset": preset, "lang": lang})

async def prompts_upsert(
    scope: str,
    preset: str,
    lang: str,
    text: str,
    name: Optional[str] = None,
    updated_by: Optional[int] = None,
) -> str:
    now = datetime.utcnow()
    doc = await db().prompts.find_one({"scope": scope, "preset": preset, "lang": lang})
    if doc:
        await db().prompts.update_one(
            {"_id": doc["_id"]},
            {"$set": {
                "text": text,
                "name": name or doc.get("name") or preset,
                "updated_at": now,
                "updated_by": updated_by
            }}
        )
        return str(doc["_id"])
    res = await db().prompts.insert_one({
        "scope": scope, "preset": preset, "lang": lang,
        "name": name or preset, "text": text,
        "created_at": now, "updated_at": now, "updated_by": updated_by
    })
    return str(res.inserted_id)

async def prompts_delete_by_id(pid: Union[str, ObjectId]) -> int:
    _id = ObjectId(pid) if not isinstance(pid, ObjectId) else pid
    r = await db().prompts.delete_one({"_id": _id})
    return r.deleted_count


# ----------------------------- BACKGROUNDS (библиотека фонов) -----------------------------
# Схема: { _id, scope: "reddit", file: "bg1.mp4", path: "assets/bg/reddit/bg1.mp4", uploaded_at, uploaded_by }

async def backgrounds_list(scope: str = "reddit") -> List[Dict[str, Any]]:
    cur = db().backgrounds.find({"scope": scope}).sort("file", 1)
    return [doc async for doc in cur]

async def backgrounds_add(scope: str, file: str, path: str, uploaded_by: Optional[int] = None) -> str:
    now = datetime.utcnow()
    doc = await db().backgrounds.find_one({"scope": scope, "file": file})
    if doc:
        await db().backgrounds.update_one(
            {"_id": doc["_id"]},
            {"$set": {"path": path, "uploaded_at": now, "uploaded_by": uploaded_by}}
        )
        return str(doc["_id"])
    res = await db().backgrounds.insert_one({
        "scope": scope, "file": file, "path": path,
        "uploaded_at": now, "uploaded_by": uploaded_by
    })
    return str(res.inserted_id)

async def backgrounds_delete(scope: str, file: str) -> int:
    r = await db().backgrounds.delete_one({"scope": scope, "file": file})
    return r.deleted_count

async def banners_list(scope: str = "cuts") -> List[Dict[str, Any]]:
    """Список баннеров"""
    cur = db().banners.find({"scope": scope}).sort("file", 1)
    return [doc async for doc in cur]

async def banners_add(scope: str, file: str, path: str, uploaded_by: Optional[int] = None) -> str:
    """Добавляет баннер в БД"""
    now = datetime.utcnow()
    doc = await db().banners.find_one({"scope": scope, "file": file})
    if doc:
        await db().banners.update_one(
            {"_id": doc["_id"]},
            {"$set": {"path": path, "uploaded_at": now, "uploaded_by": uploaded_by}}
        )
        return str(doc["_id"])
    res = await db().banners.insert_one({
        "scope": scope, "file": file, "path": path,
        "uploaded_at": now, "uploaded_by": uploaded_by
    })
    return str(res.inserted_id)

async def banners_delete(scope: str, file: str) -> int:
    """Удаляет баннер из БД"""
    r = await db().banners.delete_one({"scope": scope, "file": file})
    return r.deleted_count

async def banners_get_by_file(scope: str, file: str) -> Optional[Dict[str, Any]]:
    """Получает баннер по имени файла"""
    return await db().banners.find_one({"scope": scope, "file": file})

# Функции для привязки баннера к каналу
async def set_channel_banner(id_or_name: Union[str, ObjectId], banner_file: Optional[str], position: str = "center") -> None:
    """Устанавливает баннер для канала с позицией (top/center/bottom)"""
    banner_config = None
    if banner_file:
        banner_config = {
            "file": banner_file,
            "position": position  # top, center, bottom
        }
    await db().channels.update_one(
        channel_selector(id_or_name),
        {"$set": {"banner": banner_config}}
    )

async def get_channel_banner(id_or_name: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
    """Получает конфигурацию баннера канала"""
    ch = await get_channel(id_or_name)
    if ch:
        return ch.get("banner")
    return None


# ----------------------------- КЛОНИРОВАННЫЕ ГОЛОСА (XTTS) -----------------------------
# Схема: { _id, name: str, sample_path: str, language: str, created_at, created_by }

async def cloned_voices_list() -> List[Dict[str, Any]]:
    """Список всех клонированных голосов"""
    cur = db().cloned_voices.find({}).sort("name", 1)
    return [doc async for doc in cur]


async def cloned_voice_add(
    name: str,
    sample_path: str,
    language: str = "ru",
    created_by: Optional[int] = None
) -> str:
    """Добавляет клонированный голос в БД"""
    now = datetime.utcnow()
    # Проверяем уникальность имени
    doc = await db().cloned_voices.find_one({"name": name})
    if doc:
        # Обновляем существующий
        await db().cloned_voices.update_one(
            {"_id": doc["_id"]},
            {"$set": {
                "sample_path": sample_path,
                "language": language,
                "updated_at": now,
                "created_by": created_by
            }}
        )
        return str(doc["_id"])
    # Создаем новый
    res = await db().cloned_voices.insert_one({
        "name": name,
        "sample_path": sample_path,
        "language": language,
        "created_at": now,
        "created_by": created_by
    })
    return str(res.inserted_id)


async def cloned_voice_get(name: str) -> Optional[Dict[str, Any]]:
    """Получает клонированный голос по имени"""
    return await db().cloned_voices.find_one({"name": name})


async def cloned_voice_get_by_id(vid: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
    """Получает клонированный голос по ID"""
    _id = ObjectId(vid) if not isinstance(vid, ObjectId) else vid
    return await db().cloned_voices.find_one({"_id": _id})


async def cloned_voice_delete(name: str) -> int:
    """Удаляет клонированный голос по имени"""
    r = await db().cloned_voices.delete_one({"name": name})
    return r.deleted_count


async def cloned_voice_delete_by_id(vid: Union[str, ObjectId]) -> int:
    """Удаляет клонированный голос по ID"""
    _id = ObjectId(vid) if not isinstance(vid, ObjectId) else vid
    r = await db().cloned_voices.delete_one({"_id": _id})
    return r.deleted_count


# ----------------------------- PRESET VOICES (GenAI голоса для Reddit) -----------------------------
# Схема: { _id, name: str, voice_id: str, lang: str, gender: str, description: str, created_at, created_by }

async def preset_voices_list(lang: Optional[str] = None) -> List[Dict[str, Any]]:
    """Список предустановленных голосов для Reddit Stories"""
    query: Dict[str, Any] = {}
    if lang:
        query["lang"] = lang
    cur = db().preset_voices.find(query).sort("name", 1)
    return [doc async for doc in cur]


async def preset_voices_add(
    name: str,
    voice_id: str,
    lang: Optional[str] = None,
    gender: Optional[str] = None,
    description: Optional[str] = None,
    created_by: Optional[int] = None
) -> str:
    """Добавляет предустановленный голос"""
    now = datetime.utcnow()

    # Проверяем, не существует ли уже голос с таким voice_id
    existing = await db().preset_voices.find_one({"voice_id": voice_id})
    if existing:
        # Обновляем существующий
        update_data = {
            "name": name,
            "gender": gender,
            "description": description,
            "updated_at": now,
            "created_by": created_by
        }
        # Добавляем lang только если он указан
        if lang:
            update_data["lang"] = lang

        await db().preset_voices.update_one(
            {"_id": existing["_id"]},
            {"$set": update_data}
        )
        return str(existing["_id"])

    # Создаем новый
    new_voice = {
        "name": name,
        "voice_id": voice_id,
        "gender": gender,
        "description": description,
        "created_at": now,
        "created_by": created_by
    }
    # Добавляем lang только если он указан
    if lang:
        new_voice["lang"] = lang

    res = await db().preset_voices.insert_one(new_voice)
    return str(res.inserted_id)


async def preset_voices_get_by_id(vid: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
    """Получает предустановленный голос по _id"""
    _id = ObjectId(vid) if not isinstance(vid, ObjectId) else vid
    return await db().preset_voices.find_one({"_id": _id})


async def preset_voices_get_by_voice_id(voice_id: str) -> Optional[Dict[str, Any]]:
    """Получает предустановленный голос по voice_id"""
    return await db().preset_voices.find_one({"voice_id": voice_id})


async def preset_voices_delete(voice_id: str) -> int:
    """Удаляет предустановленный голос по voice_id"""
    r = await db().preset_voices.delete_one({"voice_id": voice_id})
    return r.deleted_count


async def preset_voices_delete_by_id(vid: Union[str, ObjectId]) -> int:
    """Удаляет предустановленный голос по _id"""
    _id = ObjectId(vid) if not isinstance(vid, ObjectId) else vid
    r = await db().preset_voices.delete_one({"_id": _id})
    return r.deleted_count