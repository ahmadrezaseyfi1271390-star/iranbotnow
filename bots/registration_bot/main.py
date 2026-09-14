import os
import json
import hashlib
import base64
import requests

from rubka import Robot, Message


# ============================================================
# تنظیمات
# ============================================================

RUBIKA_TOKEN = 'CDIBFG0LOWKACQPCLOMUZYMXHATMXOPJXNOZEJVDBLAGQYTOWBOQRTZWGHZPQTLS'

ADMIN_USER_ID = 'b0FXnfh0BDAM07e25d345fec6dc6ca42'

GITHUB_OWNER = 'ahmadrezaseyfi1271390-star'
GITHUB_REPO = 'iranbotnow'
GITHUB_BRANCH = 'main'

DATA_PATH = "bots/registration_bot/data.json"

STORAGE_TOKEN = os.getenv("STORAGE_TOKEN")


# ============================================================
# GitHub API
# ============================================================

GITHUB_API = (
    f"https://api.github.com/repos/"
    f"{GITHUB_OWNER}/{GITHUB_REPO}"
)

GITHUB_HEADERS = {
    "Authorization": f"Bearer {STORAGE_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


# ============================================================
# وضعیت موقت ثبت نام
# ============================================================

sessions = {}


# ============================================================
# بررسی تنظیمات
# ============================================================

if not STORAGE_TOKEN:
    raise RuntimeError(
        "STORAGE_TOKEN تنظیم نشده است. "
        "مطمئن شوید Secret با نام STORAGE_TOKEN "
        "در GitHub Actions ساخته شده است."
    )


# ============================================================
# دریافت data.json از GitHub
# ============================================================

def load_data():

    url = f"{GITHUB_API}/contents/{DATA_PATH}"

    response = requests.get(
        url,
        headers=GITHUB_HEADERS,
        params={"ref": GITHUB_BRANCH},
        timeout=30
    )

    if response.status_code == 404:
        return {"users": []}, None

    response.raise_for_status()

    result = response.json()

    encoded = result["content"].replace("\\n", "")

    decoded = base64.b64decode(encoded).decode(
        "utf-8"
    )

    try:
        data = json.loads(decoded)
    except Exception:
        data = {"users": []}

    return data, result.get("sha")


# ============================================================
# ذخیره data.json در GitHub
# ============================================================

def save_data(data, sha):

    url = f"{GITHUB_API}/contents/{DATA_PATH}"

    content = json.dumps(
        data,
        ensure_ascii=False,
        indent=2
    )

    encoded = base64.b64encode(
        content.encode("utf-8")
    ).decode("utf-8")

    payload = {
        "message": "Update registration data",
        "content": encoded,
        "branch": GITHUB_BRANCH,
    }

    if sha:
        payload["sha"] = sha

    response = requests.put(
        url,
        headers=GITHUB_HEADERS,
        json=payload,
        timeout=30
    )

    response.raise_for_status()


# ============================================================
# هش کردن رمز عبور
# ============================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# ============================================================
# استخراج آیدی کاربر
# ============================================================

def get_user_id(message):

    possible = [
        getattr(message, "sender_id", None),
        getattr(message, "author_id", None),
        getattr(message, "chat_id", None),
    ]

    for value in possible:
        if value is not None:
            return str(value)

    return "unknown"


# ============================================================
# پاسخ
# ============================================================

async def reply(message, text):

    await message.reply(text)


# ============================================================
# /start
# ============================================================

@bot.on_message(commands=["start"])
async def start(bot, message: Message):

    user_id = get_user_id(message)

    try:
        data, sha = load_data()

        users = data.get("users", [])

        exists = False

        for user in users:
            if str(user.get("id")) == str(user_id):
                exists = True
                break

        sessions[user_id] = {
            "step": "name",
            "name": None,
            "username": None,
        }

        await reply(
            message,
            "لطفا اسم خود را وارد کنید."
        )

    except Exception as e:

        print("START ERROR:", repr(e))

        await reply(
            message,
            "خطایی رخ داد. لطفا دوباره تلاش کنید."
        )


# ============================================================
# دریافت پیام‌ها
# ============================================================

@bot.on_message()
async def handle_message(bot, message: Message):

    user_id = get_user_id(message)

    text = getattr(message, "text", None)

    if text is None:
        return

    text = str(text).strip()

    # --------------------------------------------------------
    # آیدی
    # --------------------------------------------------------

    if text == "آیدی":

        await reply(
            message,
            f"`{user_id}`"
        )

        return


    # --------------------------------------------------------
    # آمار - فقط ادمین
    # --------------------------------------------------------

    if text == "امار":

        if str(user_id) != str(ADMIN_USER_ID):

            await reply(
                message,
                "شما دسترسی به این بخش را ندارید."
            )

            return

        try:

            data, sha = load_data()

            users = data.get("users", [])

            if not users:

                await reply(
                    message,
                    "هیچ کاربری ثبت نام نکرده است."
                )

                return

            result = [
                f"📊 تعداد ثبت نام: {len(users)}",
                "",
            ]

            for index, user in enumerate(users, 1):

                name = user.get("name", "-")
                username = user.get("username", "-")
                uid = user.get("id", "-")

                result.append(
                    f"{index}. "
                    f"{name} | "
                    f"{username} | "
                    f"{uid}"
                )

            await reply(
                message,
                "\n".join(result)
            )

        except Exception as e:

            print("STATS ERROR:", repr(e))

            await reply(
                message,
                "خطا در دریافت آمار."
            )

        return


    # --------------------------------------------------------
    # اگر جلسه‌ای وجود ندارد
    # --------------------------------------------------------

    if user_id not in sessions:

        return


    session = sessions[user_id]

    step = session.get("step")


    # ========================================================
    # مرحله اول: نام
    # ========================================================

    if step == "name":

        session["name"] = text
        session["step"] = "username"

        await reply(
            message,
            "اسم ثبت شد لطفا نام کاربری دارای @ رو ارسال کنید."
        )

        return


    # ========================================================
    # مرحله دوم: نام کاربری
    # ========================================================

    if step == "username":

        if not text.startswith("@"):

            await reply(
                message,
                "لطفا نام کاربری دارای @ رو ارسال کنید."
            )

            return

        session["username"] = text
        session["step"] = "password"

        await reply(
            message,
            "لطفا رمز عبوری ارسال کنید."
        )

        return


    # ========================================================
    # مرحله سوم: رمز عبور
    # ========================================================

    if step == "password":

        password_hash = hash_password(text)

        try:

            data, sha = load_data()

            users = data.setdefault(
                "users",
                []
            )

            existing_user = None

            for user in users:

                if str(user.get("id")) == str(user_id):

                    existing_user = user
                    break


            # ------------------------------------------------
            # کاربر قبلاً ثبت نام شده
            # ------------------------------------------------

            if existing_user:

                await reply(
                    message,
                    "شما قبلا ثبت نام شده بودید"
                )

            # ------------------------------------------------
            # کاربر جدید
            # ------------------------------------------------

            else:

                users.append({
                    "id": user_id,
                    "name": session["name"],
                    "username": session["username"],
                    "password_hash": password_hash,
                })

                save_data(data, sha)

                await reply(
                    message,
                    "شما تازه ثبت نام شدید"
                )

                await reply(
                    message,
                    f"`{user_id}`"
                )


            sessions.pop(
                user_id,
                None
            )

        except Exception as e:

            print(
                "REGISTER ERROR:",
                repr(e)
            )

            await reply(
                message,
                "خطایی هنگام ثبت اطلاعات رخ داد."
            )

        return


# ============================================================
# ساخت ربات
# ============================================================

bot = Robot(
    token=RUBIKA_TOKEN
)


# ============================================================
# اجرای ربات
# ============================================================

print("========================================")
print("Registration Bot Started")
print("========================================")

bot.run()
