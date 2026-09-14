
import os
import json
import time
import hashlib
import base64
import requests

from rubka import Robot, Message


# =========================================================
# تنظیمات
# =========================================================

RUBIKA_BOT_TOKEN = "CDIBFG0LOWKACQPCLOMUZYMXHATMXOPJXNOZEJVDBLAGQYTOWBOQRTZWGHZPQTLS"
ADMIN_USER_ID = "b0FXnfh0BDAM07e25d345fec6dc6ca42"

GITHUB_OWNER = "ahmadrezaseyfi1271390-star"
GITHUB_REPO = "iranbotnow"
GITHUB_BRANCH = "main"

DATA_PATH = "bots/registration_bot/data.json"

# توکن GitHub از Secret گرفته می‌شود
GITHUB_STORAGE_TOKEN = os.getenv("GITHUB_STORAGE_TOKEN")


# =========================================================
# ربات
# =========================================================

bot = Robot(RUBIKA_BOT_TOKEN)


# =========================================================
# نشست‌های موقت ثبت‌نام
# =========================================================

sessions = {}


# =========================================================
# GitHub
# =========================================================

def github_headers():

    return {
        "Authorization": f"Bearer {GITHUB_STORAGE_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def github_url():

    return (
        f"https://api.github.com/repos/"
        f"{GITHUB_OWNER}/{GITHUB_REPO}/contents/"
        f"{DATA_PATH}"
    )


# =========================================================
# خواندن اطلاعات
# =========================================================

def load_data():

    if not GITHUB_STORAGE_TOKEN:

        print(
            "ERROR: GITHUB_STORAGE_TOKEN "
            "is not configured."
        )

        return {
            "users": {}
        }

    try:

        response = requests.get(
            github_url(),
            headers=github_headers(),
            params={
                "ref": GITHUB_BRANCH
            },
            timeout=30
        )

        if response.status_code == 404:

            return {
                "users": {}
            }

        if response.status_code != 200:

            print(
                "GitHub GET error:",
                response.status_code,
                response.text
            )

            return {
                "users": {}
            }

        result = response.json()

        content = result.get("content", "")

        content = content.replace("\n", "")

        decoded = base64.b64decode(
            content
        ).decode("utf-8")

        data = json.loads(decoded)

        if "users" not in data:

            data["users"] = {}

        return data

    except Exception as e:

        print(
            "load_data error:",
            e
        )

        return {
            "users": {}
        }


# =========================================================
# ذخیره اطلاعات
# =========================================================

def save_data(data):

    if not GITHUB_STORAGE_TOKEN:

        print(
            "ERROR: GITHUB_STORAGE_TOKEN "
            "is not configured."
        )

        return False

    try:

        # گرفتن SHA فایل
        response = requests.get(
            github_url(),
            headers=github_headers(),
            params={
                "ref": GITHUB_BRANCH
            },
            timeout=30
        )

        sha = None

        if response.status_code == 200:

            sha = response.json().get("sha")

        raw = json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )

        encoded = base64.b64encode(
            raw.encode("utf-8")
        ).decode("utf-8")

        payload = {
            "message": "Update registration data",
            "content": encoded,
            "branch": GITHUB_BRANCH
        }

        if sha:

            payload["sha"] = sha

        result = requests.put(
            github_url(),
            headers=github_headers(),
            json=payload,
            timeout=30
        )

        if result.status_code in (200, 201):

            print(
                "data.json updated successfully."
            )

            return True

        print(
            "GitHub PUT error:",
            result.status_code,
            result.text
        )

        return False

    except Exception as e:

        print(
            "save_data error:",
            e
        )

        return False


# =========================================================
# هش رمز
# =========================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# ارسال پیام
# =========================================================

def reply(message, text):

    try:

        message.reply(text)

    except Exception as e:

        print(
            "Reply error:",
            e
        )


# =========================================================
# دریافت ID
# =========================================================

def get_user_id(message):

    user_id = (
        getattr(message, "sender_id", None)
        or getattr(message, "author_id", None)
        or getattr(message, "chat_id", None)
    )

    if user_id is None:

        return ""

    return str(user_id)


# =========================================================
# پیام‌ها
# =========================================================

@bot.on_message()
def handle_message(message):

    try:

        text = getattr(
            message,
            "text",
            ""
        )

        if text is None:

            text = ""

        text = str(text).strip()

        user_id = get_user_id(message)

        if not user_id:

            return


        # =====================================================
        # آیدی
        # =====================================================

        if text == "آیدی":

            reply(
                message,
                f"آیدی عددی شما:\n`{user_id}`"
            )

            return


        # =====================================================
        # آمار
        # =====================================================

        if text == "امار":

            if user_id != str(
                ADMIN_USER_ID
            ):

                reply(
                    message,
                    "⛔ شما دسترسی به این دستور را ندارید."
                )

                return

            data = load_data()

            users = data.get(
                "users",
                {}
            )

            lines = [
                "📊 آمار ثبت‌نام",
                "",
                f"👥 تعداد کاربران: {len(users)}",
                ""
            ]

            for uid, info in users.items():

                name = info.get(
                    "name",
                    "نامشخص"
                )

                username = info.get(
                    "username",
                    "نامشخص"
                )

                lines.append(
                    f"👤 {name}"
                )

                lines.append(
                    f"🆔 {uid}"
                )

                lines.append(
                    f"🔗 @{username}"
                )

                lines.append("")

            reply(
                message,
                "\n".join(lines)
            )

            return


        # =====================================================
        # شروع
        # =====================================================

        if text == "/start":

            data = load_data()

            users = data.get(
                "users",
                {}
            )

            if user_id in users:

                reply(
                    message,
                    "شما قبلا ثبت نام شده بودید"
                )

                return

            sessions[user_id] = {
                "step": "name"
            }

            reply(
                message,
                "لطفا اسم خود را وارد کنید."
            )

            return


        # =====================================================
        # اگر در روند ثبت‌نام نیست
        # =====================================================

        if user_id not in sessions:

            return


        session = sessions[user_id]

        step = session.get(
            "step"
        )


        # =====================================================
        # نام
        # =====================================================

        if step == "name":

            if not text:

                reply(
                    message,
                    "لطفا یک اسم معتبر وارد کنید."
                )

                return

            session["name"] = text

            session["step"] = "username"

            reply(
                message,
                "اسم ثبت شد لطفا نام کاربری دارای @ رو ارسال کنید."
            )

            return


        # =====================================================
        # نام کاربری
        # =====================================================

        if step == "username":

            username = text

            if not username.startswith("@"):

                reply(
                    message,
                    "نام کاربری باید با @ شروع شود."
                )

                return

            username = username[1:].strip()

            if not username:

                reply(
                    message,
                    "نام کاربری معتبر نیست."
                )

                return

            session["username"] = username

            session["step"] = "password"

            reply(
                message,
                "لطفا رمز عبوری ارسال کنید."
            )

            return


        # =====================================================
        # رمز
        # =====================================================

        if step == "password":

            password = text

            if len(password) < 4:

                reply(
                    message,
                    "رمز عبور باید حداقل ۴ کاراکتر باشد."
                )

                return

            data = load_data()

            if "users" not in data:

                data["users"] = {}

            users = data["users"]


            # -------------------------------------------------
            # بررسی قبلی بودن ID
            # -------------------------------------------------

            already_registered = (
                user_id in users
            )


            # -------------------------------------------------
            # بررسی username
            # -------------------------------------------------

            username_exists = False

            for uid, info in users.items():

                old_username = str(
                    info.get(
                        "username",
                        ""
                    )
                ).lower()

                if old_username == session[
                    "username"
                ].lower():

                    username_exists = True

                    break


            if username_exists:

                reply(
                    message,
                    "این نام کاربری قبلا ثبت شده است."
                )

                sessions.pop(
                    user_id,
                    None
                )

                return


            # -------------------------------------------------
            # ذخیره
            # -------------------------------------------------

            users[user_id] = {

                "name": session[
                    "name"
                ],

                "username": session[
                    "username"
                ],

                "password": hash_password(
                    password
                ),

                "registered_at": int(
                    time.time()
                )
            }


            # -------------------------------------------------
            # GitHub
            # -------------------------------------------------

            if not save_data(data):

                reply(
                    message,
                    "❌ ذخیره اطلاعات انجام نشد. دوباره تلاش کنید."
                )

                return


            # -------------------------------------------------
            # پایان session
            # -------------------------------------------------

            sessions.pop(
                user_id,
                None
            )


            # -------------------------------------------------
            # پیام نهایی
            # -------------------------------------------------

            if already_registered:

                reply(
                    message,
                    "شما قبلا ثبت نام شده بودید"
                )

            else:

                reply(
                    message,
                    "شما تازه ثبت نام شدید"
                )


            # -------------------------------------------------
            # ID قابل کپی
            # -------------------------------------------------

            reply(
                message,
                f"آیدی عددی شما:\n`{user_id}`"
            )

            return


    except Exception as e:

        print(
            "Message handler error:",
            e
        )


# =========================================================
# شروع
# =========================================================

print(
    "===================================="
)

print(
    "      IranBot Registration Bot"
)

print(
    "===================================="
)

print(
    "Bot is starting..."
)


if not GITHUB_STORAGE_TOKEN:

    print(
        "WARNING:"
        " GITHUB_STORAGE_TOKEN is missing."
    )


bot.run()
