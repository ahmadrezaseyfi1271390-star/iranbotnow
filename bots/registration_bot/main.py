import os
import json
import base64
import hashlib
import requests

from rubka import Robot, Message


# =========================================================
# تنظیمات ربات
# =========================================================

RUBIKA_TOKEN = 'CDIBFG0LOWKACQPCLOMUZYMXHATMXOPJXNOZEJVDBLAGQYTOWBOQRTZWGHZPQTLS'

ADMIN_ID = 'b0FXnfh0BDAM07e25d345fec6dc6ca42'

GITHUB_OWNER = 'ahmadrezaseyfi1271390-star'
GITHUB_REPO = 'iranbotnow'
GITHUB_BRANCH = 'main'

DATA_PATH = 'bots/registration_bot/data.json'


# =========================================================
# GitHub Storage Token
# =========================================================

STORAGE_TOKEN = os.getenv("STORAGE_TOKEN")


if not STORAGE_TOKEN:

    raise RuntimeError(
        "STORAGE_TOKEN در GitHub Actions تنظیم نشده است."
    )


GITHUB_API = (
    "https://api.github.com/repos/"
    + GITHUB_OWNER
    + "/"
    + GITHUB_REPO
)


HEADERS = {

    "Authorization":
        "Bearer " + STORAGE_TOKEN,

    "Accept":
        "application/vnd.github+json",

    "X-GitHub-Api-Version":
        "2022-11-28"
}


# =========================================================
# ساخت ربات
# =========================================================

bot = Robot(
    token=RUBIKA_TOKEN
)


# =========================================================
# Session کاربران
# =========================================================

sessions = {}


# =========================================================
# دریافت اطلاعات از GitHub
# =========================================================

def load_data():

    url = (
        GITHUB_API
        + "/contents/"
        + DATA_PATH
    )


    try:

        response = requests.get(

            url,

            headers=HEADERS,

            params={
                "ref": GITHUB_BRANCH
            },

            timeout=30
        )


        if response.status_code == 404:

            return {
                "users": []
            }, None


        response.raise_for_status()


        result = response.json()


        sha = result.get("sha")


        content = result.get(
            "content",
            ""
        )


        if not content:

            return {
                "users": []
            }, sha


        decoded = base64.b64decode(

            content.replace(
                "\n",
                ""
            )

        ).decode("utf-8")


        data = json.loads(
            decoded
        )


        if not isinstance(
            data,
            dict
        ):

            data = {
                "users": []
            }


        if "users" not in data:

            data["users"] = []


        return data, sha


    except Exception as e:

        print(
            "خطا در خواندن اطلاعات:",
            e
        )


        return {
            "users": []
        }, None


# =========================================================
# ذخیره اطلاعات در GitHub
# =========================================================

def save_data(
    data,
    sha=None
):

    url = (
        GITHUB_API
        + "/contents/"
        + DATA_PATH
    )


    try:

        content = json.dumps(

            data,

            ensure_ascii=False,

            indent=2
        )


        encoded = base64.b64encode(

            content.encode(
                "utf-8"
            )

        ).decode("utf-8")


        body = {

            "message":
                "Update registration data",

            "content":
                encoded,

            "branch":
                GITHUB_BRANCH
        }


        if sha:

            body["sha"] = sha


        response = requests.put(

            url,

            headers=HEADERS,

            json=body,

            timeout=30
        )


        if response.status_code in (
            200,
            201
        ):

            print(
                "اطلاعات در GitHub ذخیره شد."
            )

            return True


        print(
            "خطا در ذخیره اطلاعات:"
        )

        print(
            response.status_code
        )

        print(
            response.text
        )


        return False


    except Exception as e:

        print(
            "Save error:",
            e
        )

        return False


# =========================================================
# رمزگذاری رمز عبور
# =========================================================

def hash_password(
    password
):

    return hashlib.sha256(

        password.encode(
            "utf-8"
        )

    ).hexdigest()


# =========================================================
# /start
# =========================================================

@bot.on_message(
    commands=["start"]
)
async def start(
    bot: Robot,
    message: Message
):

    user_id = str(
        message.sender_id
    )


    data, sha = load_data()


    exists = False


    for user in data.get(
        "users",
        []
    ):

        if str(
            user.get("id")
        ) == user_id:

            exists = True

            break


    sessions[user_id] = {

        "step":
            "name",

        "exists":
            exists
    }


    await message.reply(
        "لطفا اسم خود را وارد کنید."
    )


# =========================================================
# پیام‌های کاربران
# =========================================================

@bot.on_message()
async def messages(
    bot: Robot,
    message: Message
):

    user_id = str(
        message.sender_id
    )


    text = message.text


    if not text:

        return


    text = text.strip()


    # =====================================================
    # آیدی
    # =====================================================

    if text == "آیدی":

        await message.reply(

            "`"
            + user_id
            + "`"

        )

        return


    # =====================================================
    # آمار
    # =====================================================

    if text == "امار":

        if user_id != str(
            ADMIN_ID
        ):

            await message.reply(
                "شما دسترسی به این بخش را ندارید."
            )

            return


        data, sha = load_data()


        users = data.get(
            "users",
            []
        )


        if not users:

            await message.reply(
                "هنوز کاربری ثبت نشده است."
            )

            return


        result = []

        result.append(

            "تعداد کاربران: "
            + str(len(users))

        )

        result.append("")


        for index, user in enumerate(
            users,
            1
        ):

            name = str(
                user.get(
                    "name",
                    ""
                )
            )


            username = str(
                user.get(
                    "username",
                    ""
                )
            )


            uid = str(
                user.get(
                    "id",
                    ""
                )
            )


            result.append(

                str(index)
                + ". "
                + name
                + " | "
                + username
                + " | "
                + uid

            )


        await message.reply(
            "\n".join(result)
        )

        return


    # =====================================================
    # بررسی Session
    # =====================================================

    session = sessions.get(
        user_id
    )


    if not session:

        await message.reply(

            "برای شروع ثبت نام "
            "/start "
            "را ارسال کنید."

        )

        return


    step = session.get(
        "step"
    )


    # =====================================================
    # مرحله اسم
    # =====================================================

    if step == "name":

        sessions[user_id][
            "name"
        ] = text


        sessions[user_id][
            "step"
        ] = "username"


        await message.reply(

            "اسم ثبت شد لطفا نام کاربری "
            "دارای @ رو ارسال کنید."

        )

        return


    # =====================================================
    # مرحله نام کاربری
    # =====================================================

    if step == "username":

        if not text.startswith("@"):

            await message.reply(

                "نام کاربری باید "
                "با @ شروع شود."

            )

            return


        sessions[user_id][
            "username"
        ] = text


        sessions[user_id][
            "step"
        ] = "password"


        await message.reply(
            "لطفا رمز عبوری ارسال کنید."
        )

        return


    # =====================================================
    # مرحله رمز عبور
    # =====================================================

    if step == "password":

        password_hash = hash_password(
            text
        )


        data, sha = load_data()


        users = data.get(
            "users",
            []
        )


        already_exists = False


        for user in users:

            if str(
                user.get("id")
            ) == user_id:

                already_exists = True

                break


        # -------------------------------------------------
        # کاربر قبلاً ثبت شده
        # -------------------------------------------------

        if already_exists:

            await message.reply(
                "شما قبلا ثبت نام شده بودید"
            )


        # -------------------------------------------------
        # کاربر جدید
        # -------------------------------------------------

        else:

            new_user = {

                "id":
                    user_id,

                "name":
                    sessions[user_id].get(
                        "name",
                        ""
                    ),

                "username":
                    sessions[user_id].get(
                        "username",
                        ""
                    ),

                "password_hash":
                    password_hash
            }


            users.append(
                new_user
            )


            data["users"] = users


            success = save_data(
                data,
                sha
            )


            if success:

                await message.reply(
                    "شما تازه ثبت نام شدید"
                )

            else:

                await message.reply(

                    "خطا در ذخیره اطلاعات. "
                    "دوباره تلاش کنید."

                )

                return


        await message.reply(

            "`"
            + user_id
            + "`"

        )


        sessions.pop(
            user_id,
            None
        )


# =========================================================
# اجرای ربات
# =========================================================

print(
    "Registration bot is starting..."
)


bot.run()
