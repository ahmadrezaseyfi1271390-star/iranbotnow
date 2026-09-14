import os
import json
import base64
import hashlib
import requests

from rubka import Robot, Message


RUBIKA_TOKEN = "'CDIBFG0LOWKACQPCLOMUZYMXHATMXOPJXNOZEJVDBLAGQYTOWBOQRTZWGHZPQTLS'"

ADMIN_ID = "'b0FXnfh0BDAM07e25d345fec6dc6ca42'"

GITHUB_OWNER = "'ahmadrezaseyfi1271390-star'"
GITHUB_REPO = "'iranbotnow'"
GITHUB_BRANCH = "'main'"

DATA_PATH = "'bots/registration_bot/data.json'"

STORAGE_TOKEN = os.getenv("STORAGE_TOKEN")


if not STORAGE_TOKEN:
    raise RuntimeError(
        "STORAGE_TOKEN environment variable is not configured"
    )


GITHUB_API = (
    "https://api.github.com/repos/"
    + GITHUB_OWNER
    + "/"
    + GITHUB_REPO
)


HEADERS = {
    "Authorization": "Bearer " + STORAGE_TOKEN,
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}


bot = Robot(token=RUBIKA_TOKEN)


sessions = {}


# =========================================================
# DATA
# =========================================================

def load_data():

    try:
        url = GITHUB_API + "/contents/" + DATA_PATH

        response = requests.get(
            url,
            headers=HEADERS,
            params={"ref": GITHUB_BRANCH},
            timeout=30
        )

        if response.status_code == 404:
            return {"users": []}, None

        response.raise_for_status()

        result = response.json()

        content = result.get("content", "")
        sha = result.get("sha")

        if not content:
            return {"users": []}, sha

        decoded = base64.b64decode(
            content.replace("\n", "")
        ).decode("utf-8")

        data = json.loads(decoded)

        if not isinstance(data, dict):
            data = {"users": []}

        if "users" not in data:
            data["users"] = []

        return data, sha

    except Exception as e:
        print("load_data error:", e)
        return {"users": []}, None


def save_data(data, sha=None):

    try:
        url = GITHUB_API + "/contents/" + DATA_PATH

        content = json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        )

        encoded = base64.b64encode(
            content.encode("utf-8")
        ).decode("utf-8")

        body = {
            "message": "Update registration data",
            "content": encoded,
            "branch": GITHUB_BRANCH
        }

        if sha:
            body["sha"] = sha

        response = requests.put(
            url,
            headers=HEADERS,
            json=body,
            timeout=30
        )

        if response.status_code in (200, 201):
            print("Data saved to GitHub")
            return True

        print("save_data error:")
        print(response.status_code)
        print(response.text)

        return False

    except Exception as e:
        print("save_data exception:", e)
        return False


# =========================================================
# HELPERS
# =========================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def get_user_id(message):

    possible_fields = [
        "sender_id",
        "author_id",
        "user_id"
    ]

    for field in possible_fields:

        try:
            value = getattr(message, field, None)

            if value is not None:
                return str(value)

        except Exception:
            pass

    return "unknown"


def get_text(message):

    try:
        text = getattr(message, "text", None)

        if text is not None:
            return str(text).strip()

    except Exception:
        pass

    return ""


def send_text(message, text):

    try:
        message.reply(text)
        return

    except Exception:
        pass

    try:
        bot.send_message(
            message.chat_id,
            text
        )
    except Exception as e:
        print("send error:", e)


# =========================================================
# START
# =========================================================

@bot.on_message(commands=["start"])
def start(message):

    user_id = get_user_id(message)

    data, sha = load_data()

    exists = False

    for user in data.get("users", []):

        if str(user.get("id")) == str(user_id):
            exists = True
            break

    sessions[user_id] = {
        "step": "name",
        "existing": exists
    }

    send_text(
        message,
        "لطفا اسم خود را وارد کنید."
    )


# =========================================================
# MESSAGE
# =========================================================

@bot.on_message()
def message_handler(message):

    user_id = get_user_id(message)
    text = get_text(message)

    if not text:
        return


    # =====================================================
    # ID
    # =====================================================

    if text == "آیدی":

        send_text(
            message,
            "`" + str(user_id) + "`"
        )

        return


    # =====================================================
    # ADMIN STATS
    # =====================================================

    if text == "امار":

        if str(user_id) != str(ADMIN_ID):

            send_text(
                message,
                "شما دسترسی به این بخش را ندارید."
            )

            return


        data, sha = load_data()

        users = data.get("users", [])

        if not users:

            send_text(
                message,
                "هنوز کاربری ثبت نشده است."
            )

            return


        lines = []

        lines.append(
            "تعداد کاربران: "
            + str(len(users))
        )

        lines.append("")

        for index, user in enumerate(users, 1):

            uid = str(user.get("id", ""))
            name = str(user.get("name", ""))
            username = str(user.get("username", ""))

            lines.append(
                str(index)
                + ". "
                + name
                + " | "
                + username
                + " | "
                + uid
            )


        send_text(
            message,
            "\n".join(lines)
        )

        return


    # =====================================================
    # REGISTRATION
    # =====================================================

    session = sessions.get(user_id)

    if not session:

        send_text(
            message,
            "برای شروع ثبت نام /start را ارسال کنید."
        )

        return


    step = session.get("step")


    # =====================================================
    # NAME
    # =====================================================

    if step == "name":

        sessions[user_id]["name"] = text
        sessions[user_id]["step"] = "username"

        send_text(
            message,
            "اسم ثبت شد لطفا نام کاربری دارای @ رو ارسال کنید."
        )

        return


    # =====================================================
    # USERNAME
    # =====================================================

    if step == "username":

        if not text.startswith("@"):

            send_text(
                message,
                "نام کاربری باید با @ شروع شود."
            )

            return


        sessions[user_id]["username"] = text
        sessions[user_id]["step"] = "password"

        send_text(
            message,
            "لطفا رمز عبوری ارسال کنید."
        )

        return


    # =====================================================
    # PASSWORD
    # =====================================================

    if step == "password":

        password_hash = hash_password(text)

        data, sha = load_data()

        users = data.get("users", [])


        already_exists = False

        for user in users:

            if str(user.get("id")) == str(user_id):

                already_exists = True
                break


        if already_exists:

            send_text(
                message,
                "شما قبلا ثبت نام شده بودید"
            )

        else:

            new_user = {
                "id": str(user_id),
                "name": sessions[user_id].get("name", ""),
                "username": sessions[user_id].get("username", ""),
                "password_hash": password_hash
            }

            users.append(new_user)

            data["users"] = users

            saved = save_data(data, sha)

            if saved:

                send_text(
                    message,
                    "شما تازه ثبت نام شدید"
                )

            else:

                send_text(
                    message,
                    "خطا در ذخیره اطلاعات. دوباره تلاش کنید."
                )

                return


        send_text(
            message,
            "`" + str(user_id) + "`"
        )

        sessions.pop(user_id, None)

        return


# =========================================================
# RUN
# =========================================================

print("Registration bot is starting...")

bot.run()
