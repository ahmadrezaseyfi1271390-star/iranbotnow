import os
import json
import hashlib
import base64
import requests

from rubka import Robot, Message


# ============================================================
# تنظیمات
# ============================================================

RUBIKA_TOKEN = "CDIBFG0LOWKACQPCLOMUZYMXHATMXOPJXNOZEJVDBLAGQYTOWBOQRTZWGHZPQTLS"

GITHUB_OWNER = "ahmadrezaseyfi1271390-star"
GITHUB_REPO = "iranbotnow"
GITHUB_BRANCH = "main"

STORAGE_TOKEN = os.getenv("STORAGE_TOKEN")

ADMIN_USER_ID = "b0FXnfh0BDAM07e25d345fec6dc6ca42"

DATA_PATH = "bots/registration_bot/data.json"

GITHUB_API = (
    f"https://api.github.com/repos/"
    f"{GITHUB_OWNER}/{GITHUB_REPO}/contents/{DATA_PATH}"
)

HEADERS = {
    "Authorization": f"Bearer {STORAGE_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


# ============================================================
# 🔐 رمزنگاری رمز عبور
# ============================================================

def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# ============================================================
# ☁️ دریافت data.json از GitHub
# ============================================================

def load_data():

    try:

        r = requests.get(
            GITHUB_API,
            headers=HEADERS,
            params={"ref": GITHUB_BRANCH},
            timeout=30
        )

        if r.status_code == 404:
            return {
                "users": []
            }, None

        r.raise_for_status()

        result = r.json()

        content = base64.b64decode(
            result["content"]
        ).decode("utf-8")

        data = json.loads(content)

        if "users" not in data:
            data["users"] = []

        return data, result["sha"]

    except Exception as e:

        print("خطا در دریافت اطلاعات:", e)

        return {
            "users": []
        }, None


# ============================================================
# 💾 ذخیره data.json در GitHub
# ============================================================

def save_data(data, sha=None):

    try:

        text = json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )

        encoded = base64.b64encode(
            text.encode("utf-8")
        ).decode("utf-8")

        payload = {
            "message": "Update registration data",
            "content": encoded,
            "branch": GITHUB_BRANCH,
        }

        if sha:
            payload["sha"] = sha

        r = requests.put(
            GITHUB_API,
            headers=HEADERS,
            json=payload,
            timeout=30
        )

        if r.status_code in (200, 201):

            print("✅ اطلاعات در GitHub ذخیره شد.")

            return True

        print(
            "❌ خطا در ذخیره اطلاعات:",
            r.status_code,
            r.text
        )

        return False

    except Exception as e:

        print(
            "❌ خطا در ذخیره:",
            e
        )

        return False


# ============================================================
# 🤖 ساخت ربات
# ============================================================

bot = Robot(
    token=RUBIKA_TOKEN
)


# ============================================================
# وضعیت موقت ثبت نام کاربران
# ============================================================

sessions = {}


# ============================================================
# /start
# ============================================================

@bot.on_message(commands=["start"])
async def start(bot, message: Message):

    user_id = str(message.sender_id)

    data, _ = load_data()

    users = data.get("users", [])

    existing_user = None

    for user in users:

        if str(user.get("id")) == user_id:

            existing_user = user
            break

    if existing_user:

        sessions[user_id] = {
            "step": "name",
            "existing": True
        }

    else:

        sessions[user_id] = {
            "step": "name",
            "existing": False
        }

    await message.reply(
        "لطفا اسم خود را وارد کنید."
    )


# ============================================================
# تمام پیام‌های متنی
# ============================================================

@bot.on_message()
async def handle_message(bot, message: Message):

    user_id = str(message.sender_id)

    text = str(
        getattr(message, "text", "")
        or ""
    ).strip()

    if not text:
        return

    # ----------------------------------------
    # آیدی
    # ----------------------------------------

    if text == "آیدی":

        await message.reply(
            f"آیدی عددی شما:\n\n`{user_id}`",
            parse_mode="markdown"
        )

        return

    # ----------------------------------------
    # آمار ادمین
    # ----------------------------------------

    if text == "امار":

        if user_id != str(ADMIN_USER_ID):

            await message.reply(
                "❌ شما دسترسی ادمین ندارید."
            )

            return

        data, _ = load_data()

        users = data.get(
            "users",
            []
        )

        result = (
            "📊 آمار ثبت‌نام\n\n"
            f"👥 تعداد کاربران: {len(users)}\n\n"
        )

        for index, user in enumerate(
            users,
            start=1
        ):

            name = user.get(
                "name",
                "نامشخص"
            )

            username = user.get(
                "username",
                "ندارد"
            )

            uid = user.get(
                "id",
                "نامشخص"
            )

            result += (
                f"{index}. "
                f"{name}\n"
                f"👤 @{username}\n"
                f"🆔 `{uid}`\n\n"
            )

        await message.reply(
            result,
            parse_mode="markdown"
        )

        return

    # ----------------------------------------
    # بررسی جلسه ثبت‌نام
    # ----------------------------------------

    if user_id not in sessions:

        return

    session = sessions[user_id]

    step = session.get("step")

    # ----------------------------------------
    # مرحله نام
    # ----------------------------------------

    if step == "name":

        session["name"] = text
        session["step"] = "username"

        await message.reply(
            "اسم ثبت شد لطفا نام کاربری دارای @ رو ارسال کنید."
        )

        return

    # ----------------------------------------
    # مرحله نام کاربری
    # ----------------------------------------

    if step == "username":

        username = text.strip()

        if not username.startswith("@"):

            await message.reply(
                "⚠️ لطفا نام کاربری را همراه با @ ارسال کنید."
            )

            return

        username = username[1:].strip()

        if not username:

            await message.reply(
                "⚠️ نام کاربری معتبر نیست."
            )

            return

        session["username"] = username
        session["step"] = "password"

        await message.reply(
            "لطفا رمز عبوری ارسال کنید."
        )

        return

    # ----------------------------------------
    # مرحله رمز
    # ----------------------------------------

    if step == "password":

        password = text

        if len(password) < 4:

            await message.reply(
                "⚠️ رمز عبور باید حداقل ۴ کاراکتر باشد."
            )

            return

        data, sha = load_data()

        users = data.setdefault(
            "users",
            []
        )

        existing = None

        for user in users:

            if str(user.get("id")) == user_id:

                existing = user
                break

        if existing:

            # کاربر قبلاً ثبت شده
            existing["name"] = session["name"]
            existing["username"] = session["username"]
            existing["password_hash"] = hash_password(
                password
            )

            message_text = (
                "شما قبلا ثبت نام شده بودید"
            )

        else:

            # کاربر جدید
            new_user = {
                "id": user_id,
                "name": session["name"],
                "username": session["username"],
                "password_hash": hash_password(
                    password
                )
            }

            users.append(
                new_user
            )

            message_text = (
                "شما تازه ثبت نام شدید"
            )

        if save_data(data, sha):

            await message.reply(
                message_text
            )

            await message.reply(
                "🆔 آیدی عددی شما:\n\n"
                f"`{user_id}`\n\n"
                "این آیدی را می‌توانید کپی کنید.",
                parse_mode="markdown"
            )

        else:

            await message.reply(
                "❌ ذخیره اطلاعات انجام نشد. "
                "لطفا دوباره تلاش کنید."
            )

        sessions.pop(
            user_id,
            None
        )

        return


# ============================================================
# اجرای ربات
# ============================================================

print("================================")
print("🤖 Registration Bot")
print("================================")
print("ربات در حال اجراست...")

bot.run()
