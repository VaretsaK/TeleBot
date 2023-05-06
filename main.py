import logging
import pickle

from telegram import Update
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler
from telegram.error import BadRequest
from datetime import datetime, timedelta


TOKEN_BOT = "YOUR TOKEN HERE"
filename = "person_data.pkl"
expense_categories = {
    "food": [],
    "restaurants": [],
    "accommodation": [],
    "education": [],
    "vacation": []
}
money_flow = {"expenses": expense_categories, "income": []}
user_info = dict()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
    )


class Money:
    def __init__(self, amount: int, category: str):
        self.amount = amount
        self.time = datetime.now()
        self.category = category

    def __str__(self):
        return f"{self.amount} in {self.category}"


def read_file():
    global user_info
    try:
        with open(filename, 'rb') as file:
            user_info = pickle.load(file)
    except EOFError:
        logging.info("Initiation...")


def write_file():
    with open(filename, 'wb') as file:
        pickle.dump(user_info, file)


async def add_expense(update: Update, context: CallbackContext) -> None:
    """
    Format of adding expenses: /spent <category> <sum>
    """
    user_id = update.message.from_user.id

    if len(context.args) == 2:
        try:
            amount = int(context.args[1].strip())
            category = context.args[0].strip()
        except ValueError:
            logging.error("Invalid amount format")
            await update.message.reply_text("Your input is invalid, please, use only digits in 'sum' part")
            return

    else:
        logging.error("Invalid input")
        await update.message.reply_text("Your should input in a format <category> <sum>")
        return

    if not user_info.get(user_id):
        user_info[user_id] = money_flow

    money = Money(amount, category)
    try:
        user_info[user_id]["expenses"][category].append(money)
    except KeyError:
        logging.error("Invalid category")
        await update.message.reply_text("You've entered wrong category.")
        return

    await update.message.reply_text(f"Expense: {amount}$ in a {category} category was successfully added!")
    write_file()


async def list_categories(update: Update, context: CallbackContext) -> None:
    result = "\n".join(expense_categories.keys())
    await update.message.reply_text(result)


async def show_expenses(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    if not user_info.get(user_id):
        await update.message.reply_text("You don't have any expanses.")
        return

    all_expenses = 0
    for i in user_info[user_id]["expenses"].values():
        for j in range(len(i)):
            all_expenses += i[j].amount
    await update.message.reply_text(f"All time expenses: {all_expenses}")


async def list_expenses(update: Update, context: CallbackContext) -> None:
    """
    Format of list all expenses: /expl [<%Y-%m>]
    """
    user_id = update.message.from_user.id

    if not user_info.get(user_id):
        await update.message.reply_text("You don't have any expanses.")
        return

    if len(context.args) == 0:
        list_exp = []
        for key, value in user_info[user_id]["expenses"].items():
            if len(value) > 0:
                for i in range(len(value)):
                    list_exp.append(f"{key}: {i + 1}. {value[i].amount}$ - {value[i].time.strftime('%Y-%m-%d')}")
        result = "\n".join(list_exp)
        await update.message.reply_text(f"{result}")

    if len(context.args) > 0:
        list_exp = []
        for key, value in user_info[user_id]["expenses"].items():
            if len(value) > 0:
                for i in range(len(value)):
                    if context.args[0].strip() == value[i].time.strftime('%Y-%m'):
                        list_exp.append(f"{key}: {i + 1}. {value[i].amount}$ - {value[i].time.strftime('%Y-%m-%d')}")
        result = "\n".join(list_exp)
        try:
            await update.message.reply_text(f"{result}")
        except BadRequest:
            await update.message.reply_text("There is no expenses in chosen period.")


async def add_income(update: Update, context: CallbackContext) -> None:
    """
    Format of adding income: /earned <category> <sum>
    """
    user_id = update.message.from_user.id

    if len(context.args) == 2:
        try:
            amount = int(context.args[1].strip())
            category = context.args[0].strip()
        except ValueError:
            logging.error("Invalid amount format")
            await update.message.reply_text("Your input is invalid, please, use only digits in 'sum' part")
            return

    else:
        logging.error("Invalid input")
        await update.message.reply_text("Your should input in a format <category> <sum>")
        return

    if not user_info.get(user_id):
        user_info[user_id] = money_flow

    money = Money(amount, category)
    user_info[user_id]["income"].append(money)
    await update.message.reply_text(f"Income: {amount}$ in a {category} category was successfully added!")
    write_file()


async def show_income(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    if not user_info.get(user_id):
        await update.message.reply_text("You don't have any income.")
        return

    all_income = 0
    for i in user_info[user_id]["income"]:
        all_income += i.amount
    await update.message.reply_text(f"All time income: {all_income}$")


async def remove_expense(update: Update, context: CallbackContext) -> None:
    """
        Format of removing expense: /remove <category> <expense number>
    """
    user_id = update.message.from_user.id

    if not user_info.get(user_id):
        await update.message.reply_text("You don't have any expenses.")
        return
    if len(context.args) == 2:
        try:
            category = context.args[0]
            removed_idx = int(context.args[1]) - 1
            exp = user_info[user_id]["expenses"][category].pop(removed_idx)
            await update.message.reply_text(f"{category}: {exp.amount}$ was successfully removed!")
            write_file()
        except (ValueError, IndexError):
            logging.error("Invalid index")
            await update.message.reply_text("You've entered invalid index.")
        except KeyError:
            logging.error("Invalid category")
            await update.message.reply_text("You've entered wrong category.")
    else:
        logging.error("Invalid input")
        await update.message.reply_text("Your should input in a format <category> <expense number>")


async def statistics(update: Update, context: CallbackContext, timedel: timedelta, period: str) -> None:
    user_id = update.message.from_user.id
    now = datetime.now()
    stat = list()
    all_income = 0

    if not user_info.get(user_id):
        await update.message.reply_text("You don't have any expenses/income.")
        return

    for key, value in user_info[user_id]["expenses"].items():
        if len(value) > 0:
            for i in range(len(value)):
                if value[i].time >= (now - timedel):
                    stat.append(f"{key}: {value[i].amount}$ - {value[i].time.strftime('%Y-%m-%d')}")

    for i in range(len(user_info[user_id]["income"])):
        if user_info[user_id]["income"][i].time >= (now - timedel):
            all_income += user_info[user_id]["income"][i].amount

    if stat or all_income:
        result = "\n".join(stat)
        await update.message.reply_text(f"Your expenses for the {period}:\n{result}\n\n"
                                        f"Your income for the {period}:\n{all_income}$")
        return

    await update.message.reply_text(f"You don't have any expenses/income within a {period}.")


async def stat_day(update: Update, context: CallbackContext) -> None:
    await statistics(update, context, timedelta(days=1), "day")


async def stat_week(update: Update, context: CallbackContext) -> None:
    await statistics(update, context, timedelta(weeks=1), "week")


async def stat_month(update: Update, context: CallbackContext) -> None:
    await statistics(update, context, timedelta(days=31), "month")


async def stat_year(update: Update, context: CallbackContext) -> None:
    await statistics(update, context, timedelta(days=365), "year")


async def start(update: Update, context: CallbackContext) -> None:
    logging.info("Command start was triggered")
    await update.message.reply_text(
        "Welcome to your Income & Expenses Bot!\n"
        "Commands:\n"
        "Adding expenses: /spent <category> <sum>\n"
        "Adding income: /earned <category> <sum>\n"
        "List categories: /categories\n"
        "Show all income: /income\n"
        "Show all expenses: /expenses\n"
        "List all expenses: /expl [<year-month>]\n"
        "Remove expenses: /remove <category> <expense number>\n"
        "Check statistics:  /day  /week  /month  /year"
    )


def run():
    read_file()
    app = ApplicationBuilder().token(TOKEN_BOT).build()
    logging.info("Application build successfully")

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("spent", add_expense))
    app.add_handler(CommandHandler("categories", list_categories))
    app.add_handler(CommandHandler("expenses", show_expenses))
    app.add_handler(CommandHandler("expl", list_expenses))
    app.add_handler(CommandHandler("earned", add_income))
    app.add_handler(CommandHandler("income", show_income))
    app.add_handler(CommandHandler("remove", remove_expense))
    app.add_handler(CommandHandler("day", stat_day))
    app.add_handler(CommandHandler("week", stat_week))
    app.add_handler(CommandHandler("month", stat_month))
    app.add_handler(CommandHandler("year", stat_year))

    app.run_polling()


if __name__ == "__main__":
    run()
