import telebot
import config
import json
import logging

# logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

bot = telebot.TeleBot(config.TOKEN)

user_data = {}

# read json data
def read_json():
    with open('ClubDB.json', 'r', encoding='utf-8') as file:
        json_data = file.read()
        parsed_data = json.loads(json_data)
        return parsed_data

# write json data
def write_json(data):
    with open('ClubDB.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

# react to /start
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.send_message(message.chat.id, "Бот для информации о клубах используй /clubs\nДля поиска по названию используй /search\nДля создания новой записи используй /add\nДля получения справки используй /help")
    logger.info("Пользователь " + str(message.chat.id) + " запросил /start")

# react to /help
@bot.message_handler(commands=['help'])
def welcome(message):
    str_message = {
        'Бот для получения информации о клубах\n\n/start - Начальное сообщание\n/clubs - Для получения информации о клубе\n/search - Поиск клуба по названию\n'+
        '/add - Добавить новый клуб\nДля редактирования существующей записи, выбери запись, после чего нажми edit\n/help - Текущая справка\n\n'+
        'Пример форматов и вложенности\n'+
        '{\n'+'    "name": "город Москва, улица Новопеределкинская, дом 9А",\n'+'    "town": "Москва",\n'+'    "FortiGate": {\n'+
        '       "hostname": "msk-novoperedelkinskaya-9a",\n'+'      "wan1": "194.135.65.86",\n'+'       "wan2": "Dynamic",\n'+
        '       "lo0": "10.200.200.14:8443"\n'+'    },\n'+'    "Switches": {\n'+'       "sw1": "10.64.53.130"\n'+'  }\n'+
        '},\n'+
        '\n\nВладелец - @Norldress\nНаписал - @foxolave\nОбновил - @razuwaikin'
    }
    bot.send_message(message.chat.id, str_message)
    logger.info("Пользователь " + str(message.chat.id) + " запросил /help")

# react to /clubs
@bot.message_handler(commands=['clubs'])
def clubs(message):
    cid = message.chat.id
    data = read_json()
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for club in data["clubs"]:
        button_text = club["name"]
        markup.add(telebot.types.KeyboardButton(button_text))
    bot.send_message(cid, "Выберите клуб", reply_markup=markup)
    logger.info("Пользователь " + str(cid) + " запросил /clubs")

# react ro /add
@bot.message_handler(commands=['add'])
def add_club(message):
    cid = message.chat.id
    bot.send_message(cid, "Введите название клуба:")
    logger.info(f"Пользователь {cid} запросил /add")
    bot.register_next_step_handler(message, get_club_name)

def get_club_name(message):
    cid = message.chat.id
    club_name = message.text
    if not club_name:
        bot.send_message(cid, "Название клуба не может быть пустым. Попробуйте снова.")
        return
    user_data[cid] = {'club_name': club_name}
    bot.send_message(cid, f"Введите город для клуба {club_name}:")
    bot.register_next_step_handler(message, get_club_town)

def get_club_town(message):
    cid = message.chat.id
    club_town = message.text
    if not club_town:
        bot.send_message(cid, "Город не может быть пустым. Попробуйте снова.")
        return
    club_name = user_data[cid]['club_name']
    user_data[cid]['club_town'] = club_town
    bot.send_message(cid, f"Введите данные для Switch для клуба {club_name}:")
    bot.register_next_step_handler(message, get_swithces_data)

def get_swithces_data(message):
    cid = message.chat.id
    switch_value = message.text
    if not switch_value:
        bot.send_message(cid, "Swithc не может быть пустым. Попробуйте снова.")
        return
    club_name = user_data[cid]['club_name']
    user_data[cid]['switch_value'] = switch_value
    bot.send_message(cid, f"Введите данные для FortiGate для клуба {club_name} в формате JSON:")
    bot.register_next_step_handler(message, get_fortigate_data)

def get_fortigate_data(message):
    cid = message.chat.id
    fortigate_data = message.text
    club_name = user_data[cid]['club_name']
    club_town = user_data[cid]['club_town']
    switch_value = user_data[cid]['switch_value']

    try:
        fortigate_json = json.loads(fortigate_data)  # Пытаемся преобразовать в JSON
    except json.JSONDecodeError:
        bot.send_message(cid, "Некорректный формат JSON. Попробуйте снова.")
        return

    new_club = {
        "name": club_name,
        "town": club_town,
        "FortiGate": fortigate_json,
        "Switches":{
            "sw1":switch_value,
        }
    }

    data = read_json()
    data["clubs"].append(new_club)
    write_json(data)
    bot.send_message(cid, f"Новый клуб {club_name} успешно добавлен.")
    logger.info(f"Пользователь {cid} добавил новый клуб: {club_name}")

# react to /search
@bot.message_handler(commands=['search'])
def search_club(message):
    cid = message.chat.id
    bot.send_message(cid, "Введите название клуба или часть названия для поиска:")
    logger.info("Пользователь " + str(cid) + " запросил /search")
    bot.register_next_step_handler(message, process_search_query)

def process_search_query(message):
    cid = message.chat.id
    search_query = message.text.lower()
    data = read_json()
    found_clubs = []

    for club in data["clubs"]:
        if search_query in club["name"].lower():
            found_clubs.append(club)

    if found_clubs:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for club in found_clubs:
            markup.add(telebot.types.KeyboardButton(club["name"]))
        bot.send_message(cid, "Найденные клубы:", reply_markup=markup)
        logger.info("Пользователь " + str(cid) + " нашел клубы по запросу: " + search_query)
        bot.register_next_step_handler(message, get_club_data)
    else:
        bot.send_message(cid, "Клубы по вашему запросу не найдены.")
        logger.info("Пользователь " + str(cid) + " не нашел клубы по запросу: " + search_query)

@bot.message_handler(func=lambda message: True)
def get_club_data(message):
    cid = message.chat.id
    data = read_json()
    selected_club_name = message.text

    user_data[cid] = {'selected_club_name': selected_club_name}

    attribute_buttons = ["all", "edit"]  # Добавлена кнопка "edit"
    for club in data["clubs"]:
        if club["name"] == selected_club_name:
            for key in club.keys():
                if key != "name":
                    attribute_buttons.append(telebot.types.KeyboardButton(key))

            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            markup.add(*attribute_buttons)

            bot.send_message(cid, f"Выберите атрибут клуба:\n\n{selected_club_name}\n\n", reply_markup=markup)
            logger.info(f"Пользователь {cid} запросил данные для {selected_club_name}")
            bot.register_next_step_handler(message, process_attribute_selection)
            return

def process_attribute_selection(message):
    cid = message.chat.id
    data = read_json()
    attribute_selected = message.text

    # Получаем выбранный клуб из user_data
    selected_club_name = user_data.get(cid, {}).get('selected_club_name')

    if not selected_club_name:
        bot.send_message(cid, "Ошибка: клуб не выбран.")
        return

    # Ищем клуб в данных
    selected_club = next((club for club in data["clubs"] if club["name"] == selected_club_name), None)
    if not selected_club:
        bot.send_message(cid, "Клуб не найден.")
        return

    # Обработка кнопки "edit"
    if attribute_selected == "edit":
        bot.send_message(cid, "Введите название атрибута для редактирования (например: town, FortiGate.hostname):")
        bot.register_next_step_handler(message, process_edit_attribute)
        return

    if attribute_selected == "all":
        # Отправка всех атрибутов клуба
        response = f"Все атрибуты клуба {selected_club_name}:\n\n"
        for key, value in selected_club.items():
            if key != "name":  # Пропускаем название клуба
                formatted_value = json.dumps(value, indent=4, ensure_ascii=False)
                response += f"{key}: {formatted_value}\n"
        bot.send_message(cid, response)
        return

    elif attribute_selected in selected_club:
        # Обработка выбранного атрибута
        attribute_value = selected_club[attribute_selected]

        # Если атрибут является вложенным словарем
        if isinstance(attribute_value, dict):
            markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            for sub_attr in attribute_value.keys():
                markup.add(telebot.types.KeyboardButton(f"{attribute_selected}.{sub_attr}"))
            bot.send_message(cid, f"Выберите под-атрибут для {attribute_selected}:", reply_markup=markup)
            bot.register_next_step_handler(message, process_sub_attribute_selection)
            return
        else:
            # Если атрибут простой (строка, число и т.д.)
            formatted_value = json.dumps(attribute_value, indent=4, ensure_ascii=False)
            bot.send_message(cid, f"Значение атрибута {attribute_selected} для клуба {selected_club_name}:\n\n{formatted_value}")
            return

    else:
        # Если атрибут не найден
        bot.send_message(cid, f"Клуб {selected_club_name} не имеет атрибута {attribute_selected}.")
        return

def process_sub_attribute_selection(message):
    cid = message.chat.id
    sub_attribute_selected = message.text  # Пример: "FortiGate.hostname"
    data = read_json()

    # Извлекаем выбранный клуб из user_data
    selected_club_name = user_data.get(cid, {}).get('selected_club_name')
    if not selected_club_name:
        bot.send_message(cid, "Ошибка: клуб не выбран. Начните заново.")
        return

    # Разделяем атрибут на родительский и под-атрибут
    if "." not in sub_attribute_selected:
        bot.send_message(cid, "Некорректный формат под-атрибута!")
        return

    main_attr, sub_attr = sub_attribute_selected.split(".", 1)

    # Ищем клуб и проверяем вложенную структуру
    for club in data["clubs"]:
        if club["name"] == selected_club_name:
            if main_attr in club and isinstance(club[main_attr], dict):
                if sub_attr in club[main_attr]:
                    # Сохраняем выбранные атрибуты для возможного редактирования
                    user_data[cid] = {
                        "selected_club_name": selected_club_name,
                        "main_attr": main_attr,
                        "sub_attr": sub_attr
                    }

                    # Формируем ответ
                    value = club[main_attr][sub_attr]
                    response = (
                        f"Клуб: {selected_club_name}\n"
                        f"Атрибут: {main_attr}.{sub_attr}\n"
                        f"Значение:\n{json.dumps(value, indent=2, ensure_ascii=False)}"
                    )

                    # Создаем клавиатуру с действиями
                    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.add("Редактировать", "Назад")
                    
                    bot.send_message(cid, response, reply_markup=markup)
                    bot.register_next_step_handler(message, handle_sub_attribute_action)
                    return
                else:
                    bot.send_message(cid, f"Под-атрибут {sub_attr} не найден в {main_attr}!")
                    return
            else:
                bot.send_message(cid, f"Атрибут {main_attr} не существует или не является словарем!")
                return

    bot.send_message(cid, "Клуб не найден в базе данных!")
    
def handle_sub_attribute_action(message):
    cid = message.chat.id
    action = message.text
    
    if action == "Редактировать":
        bot.send_message(cid, "Введите новое значение:")
        bot.register_next_step_handler(message, process_sub_attribute_edit)
    elif action == "Назад":
        # Возвращаемся к выбору атрибутов клуба
        clubs(message)
    else:
        bot.send_message(cid, "Неизвестное действие!")
        clubs(message)

def process_sub_attribute_edit(message):
    cid = message.chat.id
    new_value = message.text
    data = read_json()

    # Получаем контекст из user_data
    context = user_data.get(cid, {})
    club_name = context.get("selected_club_name")
    main_attr = context.get("main_attr")
    sub_attr = context.get("sub_attr")

    if not all([club_name, main_attr, sub_attr]):
        bot.send_message(cid, "Ошибка контекста! Начните заново.")
        return

    # Обновляем значение
    for club in data["clubs"]:
        if club["name"] == club_name:
            if main_attr in club and isinstance(club[main_attr], dict):
                club[main_attr][sub_attr] = new_value
                write_json(data)
                bot.send_message(cid, "✅ Значение успешно обновлено!")
                logger.info(f"User {cid} updated {club_name}.{main_attr}.{sub_attr}")
                return

    bot.send_message(cid, "❌ Ошибка при обновлении!")

def process_edit_attribute(message):
    cid = message.chat.id
    selected_club_name = user_data.get(cid, {}).get('selected_club_name')
    attribute_to_edit = message.text
    user_data[cid]['attribute_selected'] = attribute_to_edit

    # Проверяем, является ли атрибут вложенным (например, FortiGate.hostname)
    if '.' in attribute_to_edit:
        main_attr, sub_attr = attribute_to_edit.split('.', 1)
        user_data[cid]['main_attr'] = main_attr
        user_data[cid]['sub_attr'] = sub_attr
    else:
        user_data[cid]['main_attr'] = attribute_to_edit
        user_data[cid]['sub_attr'] = None

    bot.send_message(cid, f"Введите новое значение для атрибута {attribute_to_edit}:")
    bot.register_next_step_handler(message, process_edit_club)

def process_edit_club(message):
    cid = message.chat.id
    selected_club_name = user_data.get(cid, {}).get('selected_club_name')
    main_attr = user_data.get(cid, {}).get('main_attr')
    sub_attr = user_data.get(cid, {}).get('sub_attr')
    new_value = message.text

    if not selected_club_name or not main_attr:
        bot.send_message(cid, "Ошибка: данные контекста утеряны.")
        return

    data = read_json()
    for club in data["clubs"]:
        if club["name"] == selected_club_name:
            # Редактирование корневого атрибута (например, town)
            if not sub_attr:
                if main_attr in club:
                    club[main_attr] = new_value
                    write_json(data)
                    bot.send_message(cid, f"✅ Атрибут {main_attr} обновлен!")
                    logger.info(f"User {cid} edited {selected_club_name}.{main_attr}")
                    return
                else:
                    bot.send_message(cid, f"❌ Атрибут {main_attr} не найден!")
                    return

            # Редактирование вложенного атрибута (например, FortiGate.hostname)
            else:
                if main_attr in club and isinstance(club[main_attr], dict):
                    club[main_attr][sub_attr] = new_value
                    write_json(data)
                    bot.send_message(cid, f"✅ Атрибут {main_attr}.{sub_attr} обновлен!")
                    logger.info(f"User {cid} edited {selected_club_name}.{main_attr}.{sub_attr}")
                    return
                else:
                    bot.send_message(cid, f"❌ Атрибут {main_attr}.{sub_attr} не найден!")
                    return

    bot.send_message(cid, "❌ Клуб не найден!")

# RUN
bot.infinity_polling()
