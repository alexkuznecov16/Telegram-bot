from yt_dlp import YoutubeDL
from dotenv import load_dotenv
import os
import re
import asyncio
from aiogram import F
from aiogram import Bot, Dispatcher
from aiogram.types import Message, FSInputFile, ChatPermissions
from aiogram.filters import CommandStart, Command
import requests
import random
import datetime

# Load API tokens
load_dotenv()
TOKEN = os.getenv('API') # telegram token
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY') # weather token

# Utilities
def escape_markdown(text):
  # markdown syntax for messages
  return re.sub(r'([_*[\]()~`>#+\-=|{}.!])', r'\\\1', text)

def parse_duration(duration_str):
  #  set mute duration
  duration_str = duration_str.lower().strip()
  match = re.match(r'^(\d+)([yms])$', duration_str) # check number and unit
  if not match:
    # incorrect number or unit
    return None
  
  value, unit = int(match.group(1)), match.group(2) # get number and unit
  
  now = datetime.datetime.utcnow() # current time
  if unit == 's':
    # seconds
    until_date = now + datetime.timedelta(seconds=value)
  elif unit == 'm':
    # minutes
    until_date = now + datetime.timedelta(minutes=value)
  elif unit == 'y':
    # years
    until_date = now + datetime.timedelta(days=365 * value)
  else:
    return None
  
  return until_date

activity_data = {} # contains chats top users

# Initialization
bot = Bot(token=TOKEN) # initialize telegram bot by token
dp = Dispatcher() # handle commands

# Localization
group_languages = {} # contains chats language data

@dp.message(Command('setlang')) # set language in specific chat
async def set_language(message: Message):
  args = message.text.replace('/setlang', '').strip().lower()
  if args not in ['en', 'ru']:
    # incorrect language
    await message.reply(tr(message.chat.id, 'unknown_language'))
    return
  
  group_languages[message.chat.id] = args # set chat language by chat id
  await message.reply(tr(message.chat.id, 'language_set'))
  
def tr(chat_id, key):
  # return value by chat language
  lang = group_languages.get(chat_id, 'en') # defaults
  translation = {
    'greet': {
      'en': 'Hello! My contact: @kznws111',
      'ru': 'Привет! Мой контакт: @kznws111'
    },
    'choose_language': {
      'en': 'Please choose your language: \n\n🇷🇺 Russian\n🇬🇧 English',
      'ru': 'Пожалуйста, выберите язык: \n\n🇷🇺 Русский\n🇬🇧 Английский'
    },
    'language_set': {
      'en': 'Language set: English',
      'ru': 'Язык установлен: Русский'
    },
    'unknown_language': {
      'en': 'Use: /setlang ru (🇷🇺) or /setlang en (🇬🇧)',
      'ru': 'Используйте: /setlang ru (🇷🇺) или /setlang en (🇬🇧)'
    },
    'music_downloading': {
      'en': 'The music is downloading...',
      'ru': 'Музыка загружается...'
    },
    'song_missing': {
      'en': 'You forgot to provide a link or title!',
      'ru': 'Вы забыли указать ссылку или название!'
    },
    'mute_reply_required': {
      'en': 'Reply to a user you want to mute.',
      'ru': 'Ответьте на сообщение пользователя, которого хотите замутить.'
    },
    'mute_args_required': {
      'en': 'Specify mute time, for example: /mute 5m',
      'ru': 'Укажите время мута, например: /mute 5m'
    },
    'mute_success': {
      'en': 'The user is muted for',
      'ru': 'Пользователь замучен на'
    },
    'mute_failed': {
      'en': 'Failed to mute the user:',
      'ru': 'Не удалось замутить пользователя:'
    },
    'incorrect_duration': {
      'en': 'Incorrect time format. Use a number and a unit (y, m, s), e.g. 10m',
      'ru': 'Неверный формат времени. Используйте число и единицу измерения (y, m, s), например 10m'
    },
    'unmute_reply_required': {
      'en': 'Reply to a user you want to unmute.',
      'ru': 'Ответьте на сообщение пользователя, которого хотите размутить.'
    },
    'unmute_success': {
      'en': 'The user is unmuted',
      'ru': 'Пользователь размучен'
    },
    'unmute_failed': {
      'en': 'Failed to unmute the user:',
      'ru': 'Не удалось размутить пользователя:'
    },
    'kick_reply_required': {
      'en': 'Please reply to the message of the user you want to kick.',
      'ru': 'Пожалуйста, ответьте на сообщение пользователя, которого хотите кикнуть.'
    },
    'kick_success': {
      'en': 'The user has been kicked.',
      'ru': 'Пользователь был кикнут.'
    },
    'kick_failed': {
      'en': 'Kick error:',
      'ru': 'Ошибка при кике:'
    },
    'ban_reply_required': {
      'en': 'Please reply to the message of the user you want to ban.',
      'ru': 'Пожалуйста, ответьте на сообщение пользователя, которого хотите забанить.'
    },
    'ban_success': {
      'en': 'The user has been banned.',
      'ru': 'Пользователь был забанен.'
    },
    'ban_failed': {
      'en': 'Ban error:',
      'ru': 'Ошибка при бане:'
    },
    'weather_error': {
      'en': 'Error retrieving weather:',
      'ru': 'Ошибка при получении погоды:'
    },
    'temp': {
      'en': 'Temperature:',
      'ru': 'Температура:'
    },
    'conditions': {
      'en': 'Conditions:',
      'ru': 'Погодные условия:'
    },
    'wind': {
      'en': 'Wind speed:',
      'ru': 'Скорость ветра:'
    },
    'video_downloading': {
      'en': 'The video is downloading...',
      'ru': 'Видео загружается...'
    },
    'no_title': {
      'en': 'No Title',
      'ru': 'Без названия'
    },
    'no_author': {
      'en': 'Unknown Author',
      'ru': 'Неизвестный автор'
    },
    'video_not_found': {
      'en': 'Video not found',
      'ru': 'Видео не найдено'
    },
    'video_error': {
      'en': 'Error downloading video:',
      'ru': 'Ошибка при загрузке видео:'
    },
    'no_permissions': {
      'en': 'You do not have permissions',
      'ru': 'У вас нет прав'
    },
    'r': {
      'en': ["Do 5 push-ups",
    "Do 10 squats",
    "Do 3 push-ups",
    "Do 15 squats",
    "Do 2 push-ups with a pause at the bottom",
    "Do 12 squats",
    "Do 4 slow push-ups",
    "Do 18 squats",
    "Do 1 push-up with a hold",
    "Do 7 squats with arms up",
    "Do 2 close-grip push-ups",
    "Do 20 squats",
    "Do 3 wide-arm push-ups",
    "Do 6 squats with a pause",
    "Do 4 push-ups without stopping",
    "Do 14 squats",
    "Do 2 slow push-ups",
    "Do 11 squats with closed eyes",
    "Do 5 push-ups while counting out loud",
    "Do 9 squats while smiling",
    "Name a capital city of any country starting with 'C'",
    "Give yourself a compliment",
    "Imagine you're a movie hero. What genre is the movie?",
    "What's your favorite smell?",
    "If you were a color, what color would you be?",
    "Describe yourself in three words",
    "What word do you think is beautiful?",
    "What would you like to be able to do right now?",
    "If you had a dragon, what would you name it?",
    "Say a phrase that would start your novel",
    "What song lifts your mood?",
    "What animal would you have if there were no limits?",
    "Make a surprised face (and believe it)",
    "What was your favorite cartoon as a child?",
    "If you were invisible for a day, what would you do?",
    "Describe your perfect day off",
    "Name 3 things that make you happy",
    "How many tabs do you have open right now?",
    "If you could teleport, where would you go?",
    "Name your favorite book",
    "If you won a million, what would you buy first?",
    "What did you want to be as a child?",
    "If your day were a dish, what would it be?",
    "What’s a habit of yours that few people know about?",
    "Name any word that starts with the last letter of your name",
    "If you were a superhero, what would your power be?",
    "Say 'Hello' in three languages",
    "How many times did you drink water today?",
    "Describe your day in one word",
    "If you had one wish, what would it be?",
    "What’s your favorite holiday?",
    "If you opened a café, what would it be called?",
    "Name three things you see around you",
    "What’s your strangest hobby?",
    "What would you tell yourself 5 years ago?",
    "Which movie character do you relate to most?",
    "What skill would you improve right now?",
    "Name a country you’d like to visit",
    "If you were a song, which one would you be?",
    "What was your funniest moment in life?",
    "Imagine you’re a TV host — what’s your show about?",
    "How long could you go without your phone?",
    "Name your favorite dish",
    "Which language would you like to learn?",
    "What do you value most in friends?",
    "Imagine there's no school/work tomorrow — what do you do?",
    "If you could change your name, what would it be?",
    "What’s your favorite weather?",
    "You’re in a desert. What will you take with you?",
    "If you could have any pet — which one?",
    "What funny thing happened to you recently?",
    "What’s your favorite quote?",
    "Name 3 fruits",
    "What song is stuck in your head right now?",
    "What would you draw if you were an artist?",
    "Name any city you've never been to but want to visit",
    "How many times do you smile a day?",
    "If you were a sport, what would you be?",
    "What’s your favorite game?",
    "What would you never try?",
    "Name any historical fact",
    "You’re in a forest. What’s the first thing you do?",
    "How many hours of sleep do you need to be happy?",
    "If you were a blogger, what would your blog be about?",
    "What movie can you watch over and over?",
    "What’s your favorite quote or meme?",
    "What do you like most about yourself?",
    "What was your first phone?",
    "Would you rather time travel or read minds?",
    "If you could choose one super subject in school, what would it be?",
    "What’s the last dream you remember?",
    "If you were a tree — what kind would you be?",
    "Where do you see yourself in 5 years?",
    "What would you like to change in the world?",
    "If you had your own life rule, what would it be?",
    "What inspires you to get out of bed in the morning?",
    "Name three qualities of an ideal friend",
    "What can you do that most people can't?",
    "If you were a scent, what would you smell like?",
    "What can you say about yourself in 10 seconds?",
    "What’s your warmest memory?",
    "Name 3 things you can make from potatoes",
    "Write the names of 50 countries",
    "What’s your native language?",
    "The biggest country in the world?",
    "Take a photo of what’s outside your window",
    "For 10 minutes, add swearing to every sentence (voice/text)",
    "For 10 minutes, write and speak only in English",
    "Hide in a closet!!!",
    "Go to the gym with friends in June",
    "Write 8 Russian curse words",
    "If you became president (of any country), what would you do on day one?",
    "How much do you weigh?",
    "How old are you? If you were born 10 years ago — how old would you be now?"],
      'ru': ["Сделай 5 отжиманий",
    "Сделай 10 приседаний",
    "Сделай 3 отжимания",
    "Сделай 15 приседаний",
    "Сделай 2 отжимания с паузой внизу",
    "Сделай 12 приседаний",
    "Сделай 4 отжимания медленно",
    "Сделай 18 приседаний",
    "Сделай 1 отжимание с задержкой",
    "Сделай 7 приседаний с руками вверх",
    "Сделай 2 отжимания с узким хватом",
    "Сделай 20 приседаний",
    "Сделай 3 отжимания с широкой постановкой рук",
    "Сделай 6 приседаний с паузой",
    "Сделай 4 отжимания без остановки",
    "Сделай 14 приседаний",
    "Сделай 2 медленных отжимания",
    "Сделай 11 приседаний с закрытыми глазами",
    "Сделай 5 отжиманий, считая вслух",
    "Сделай 9 приседаний, улыбаясь",
    "Назови столицу любой страны на букву С",
    "Скажи комплимент себе",
    "Представь, что ты герой фильма. Какой жанр фильма?",
    "Какой у тебя любимый запах?",
    "Если бы ты был цветом, то каким?",
    "Опиши себя тремя словами",
    "Какое слово ты считаешь красивым?",
    "Что бы ты хотел уметь прямо сейчас?",
    "Если бы у тебя был дракон, как бы ты его назвал?",
    "Скажи фразу, которой бы начался твой роман",
    "Какая песня тебе поднимает настроение?",
    "Какое животное ты бы завёл, если бы не было ограничений?",
    "Сделай мимику, будто ты удивлён (и поверь в это)",
    "Какой у тебя был любимый мультфильм в детстве?",
    "Если бы ты стал невидимкой на день, что бы ты сделал?",
    "Опиши свой идеальный выходной",
    "Скажи 3 вещи, которые тебя радуют",
    "Сколько у тебя сейчас вкладок открыто?",
    "Если бы ты мог телепортироваться, куда бы ты отправился?",
    "Назови свою любимую книгу",
    "Если бы ты выиграл миллион, на что бы ты потратил первым делом?",
    "Кем ты хотел быть в детстве?",
    "Если бы твой день был блюдом, что бы это было?",
    "Какая у тебя привычка, которую мало кто знает?",
    "Назови любое слово, начинающееся на последнюю букву твоего имени",
    "Если бы ты был супергероем, в чём была бы твоя сила?",
    "Скажи «Привет» на трёх языках",
    "Сколько раз ты сегодня пил воду?",
    "Опиши свой сегодняшний день одним словом",
    "Если бы у тебя было одно желание — чего бы ты пожелал?",
    "Какой твой любимый праздник?",
    "Если бы ты открыл кафе, как бы оно называлось?",
    "Назови три вещи, которые ты видишь вокруг себя",
    "Какое твоё самое странное хобби?",
    "Что бы ты сказал себе 5 лет назад?",
    "Какой персонаж из фильма тебе ближе всего?",
    "Какой навык ты бы прокачал прямо сейчас?",
    "Назови страну, в которой ты хотел бы побывать",
    "Если бы ты был песней, какая бы ты была?",
    "Какой был твой самый смешной момент в жизни?",
    "Представь, что ты ведущий ТВ-шоу — о чём оно?",
    "Сколько времени ты бы выдержал без телефона?",
    "Назови своё любимое блюдо",
    "Какой язык ты бы хотел выучить?",
    "Что ты больше всего ценишь в друзьях?",
    "Представь, что завтра нет школы/работы — что сделаешь?",
    "Если бы ты мог сменить имя, как бы ты теперь звался?",
    "Какая у тебя любимая погода?",
    "Ты в пустыне. Что возьмешь с собой?",
    "Если бы ты мог завести любое домашнее животное — кого выбрал бы?",
    "Что смешного произошло с тобой недавно?",
    "Какая у тебя любимая цитата?",
    "Назови 3 фрукта",
    "Какая песня сейчас у тебя в голове?",
    "Что бы ты нарисовал, если бы был художником?",
    "Назови любой город, в котором ты не был, но хочешь побывать",
    "Сколько раз в день ты улыбаешься?",
    "Если бы ты был видом спорта, каким бы был?",
    "Какая у тебя любимая игра?",
    "Что бы ты никогда не попробовал?",
    "Назови любой исторический факт",
    "Ты в лесу. Что будешь делать первым делом?",
    "Сколько часов сна тебе нужно для счастья?",
    "Если бы ты стал блогером, о чём был бы твой блог?",
    "Какой фильм ты можешь пересматривать снова и снова?",
    "Какая у тебя любимая фраза или мем?",
    "Что тебе нравится в себе больше всего?",
    "Какой у тебя был первый телефон?",
    "Ты бы предпочёл путешествовать во времени или читать мысли?",
    "Если бы ты мог выбрать один суперпредмет в школе, что бы это было?",
    "Какой последний сон ты запомнил?",
    "Если бы ты был деревом — каким?",
    "Кем ты себя видишь через 5 лет?",
    "Что ты хотел бы изменить в мире?",
    "Если бы у тебя было своё правило жизни, как бы оно звучало?",
    "Что тебя вдохновляет утром встать с кровати?",
    "Назови три качества идеального друга",
    "Что ты умеешь, чего не умеют большинство?",
    "Если бы ты был запахом, чем бы ты пах?",
    "Что ты можешь рассказать о себе за 10 секунд?",
    "Какое твоё самое тёплое воспоминание?",
    "Назови 3 вещи, которые можно сделать из картошки",
    "Напиши названия 50 стран",
    "Какой твой родной язык?",
    "Самая большая страна в мире?",
    "Сфоткай то что в окне",
    "В течении 10 минут добавляй в каждое предложение по мату(голосовые и текст)",
    "В течении 10 минут пиши и разговаривай на английском языке",
    "Спрячься в шкафу!!!",
    "Сходи в июне в спортзал с друзьями",
    "Напиши 8 матов на русском языке",
    "Если бы ты стал президентом (на выбор страна), то что бы ты сделал в первый день?",
    "Сколько ты весишь?"
    "Сколько тебе лет? Если бы ты родился 10 лет назад - то сколько было бы сейчас?"]
    },
    'help': {
      'en': """Hello! Here are the commands you can use:\n
/start - Greet the bot and get contact info
/setlang [ru 🇷🇺 or en 🇬🇧] - Set language
/song [name or link] - Download music from YouTube
/tiktok - Download TikTok videos or just send a TikTok link to download automatically
/weather [location] - Get current weather by location
/r - Get a random task
/mute [reply] - Mute a user in the group (admin only)
/unmute [reply] - Unmute a user in the group (admin only)
/kick [reply] - Remove a user from the group (admin only)
/ban [reply] - Ban a user from the group (admin only)
/unban [reply] - Unban a user in the group (admin only)
    """,
      'ru': """Здравствуйте! Вот команды, которые вы можете использовать:\n
/start - Поприветствовать бота и получить контактную информацию
/setlang [ru 🇷🇺 или en 🇬🇧] - Установить язык чата
/song [название или ссылка] - Загрузить музыку с YouTube
/tiktok - Скачать видео с TikTok или же просто отправить ссылку на TikTok, чтобы скачать автоматически
/weather - Получить текущую погоду по местоположению
/r - Получить случайное задание
/mute [reply] - Замьютить пользователя в группе (только для администратора)
/unmute [reply] - Размьютить пользователя в группе (только для администраторов)
/kick [reply] - Удалить пользователя из группы (только для администраторов)
/ban [reply] - Забанить пользователя в группе (только для администраторов)
/unban [reply] - Разбанить пользователя в группе (только для администраторов)
      """
    }
  }
  
  return translation.get(key, {}).get(lang, key)

# General commands
async def main():
  # get updates
  await dp.start_polling(bot)
  
@dp.message(CommandStart()) # greetings and contact
async def cmd_start(message: Message):
  if message.chat.id not in group_languages:
    await message.reply(tr(message.chat.id, 'choose_language'))
  else:
    await message.reply(tr(message.chat.id, 'greet'))
  
@dp.message(Command('help')) # all commands
async def cmd_help(message: Message):
  help_text = tr(message.chat.id, 'help')
  await message.reply(help_text)

# User management commands
@dp.message(Command('mute')) # mute user for a certain time
async def mute_user(message: Message):
  # get IDs
  user_id = message.reply_to_message.from_user.id
  chat_id = message.chat.id
  
  chat_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)

  # No permissions
  if chat_member.status not in ['creator', 'administrator'] \
   or (chat_member.status == 'administrator' and not getattr(chat_member, "can_restrict_members", False)):
    await message.reply(tr(message.chat.id, 'no_permissions'))
    return
  
  if not message.reply_to_message:
    # if haven't tagged the user
    await message.reply(tr(message.chat.id, 'mute_reply_required'))
    return
  
  target_member = await message.bot.get_chat_member(chat_id, user_id)
  if target_member.status in ('creator', 'administrator'):
      await message.reply(tr(chat_id, 'no_permissions'))
      return
  
  _, _, tail = (message.text or '').partition(' ') # get everything after the first space (if there is no space => no args)
  args = tail.strip()
  
  until_date = None
  if args:
    parsed = parse_duration(args)
    if parsed:
      until_date = parsed
    else:
      until_date = None
  
  default_permissions = ChatPermissions(
    can_send_messages=False,
    can_send_media_messages=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
    can_change_info=False,
    can_invite_users=False,
    can_pin_messages=False,
  )
  
  try:
    await message.bot.restrict_chat_member(
      chat_id=chat_id,
      user_id=user_id,
      permissions=default_permissions,
      until_date=int(until_date.timestamp()) if until_date else None
    )
    
    await message.reply(f'{tr(chat_id, 'mute_success')}')
  except Exception as e:
    await message.reply(f'{tr(chat_id, 'mute_failed')} {e}')

@dp.message(Command('unmute')) # unmute user for a certain time
async def unmute_user(message: Message):
  # get IDs
  user_id = message.reply_to_message.from_user.id
  chat_id = message.chat.id
  
  chat_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
  
  # No permissions
  if chat_member.status not in ['creator', 'administrator'] \
  or (chat_member.status == 'administrator' and not getattr(chat_member, "can_restrict_members", False)):
    await message.reply(tr(message.chat.id, 'no_permissions'))
    return
  
  if not message.reply_to_message:
    # if haven't tagged the user
    await message.reply(tr(message.chat.id, 'unmute_reply_required'))
    return
  
  
  try:
    default_permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_change_info=True,
        can_invite_users=True,
        can_pin_messages=True,
    )

    await bot.restrict_chat_member(
        chat_id=chat_id,
        user_id=user_id,
        permissions=default_permissions
    )
    await message.reply(f'{tr(chat_id, 'unmute_success')}')
  except Exception as e:
    await message.reply(f'{tr(chat_id, 'unmute_failed')} {e}')

@dp.message(Command('kick')) # kick user
async def kick_user(message: Message):
  # get IDs
  user_id = message.reply_to_message.from_user.id
  chat_id = message.chat.id
  
  chat_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
  
  # No permissions
  if chat_member.status not in ['creator', 'administrator'] \
   or (chat_member.status == 'administrator' and not getattr(chat_member, "can_restrict_members", False)):
    await message.reply(tr(message.chat.id, 'no_permissions'))
    return
  
  if not message.reply_to_message:
    # if haven't tagged the user
    await message.reply(tr(message.chat.id, 'kick_reply_required'))
    return
  
  target_member = await message.bot.get_chat_member(chat_id, user_id)
  if target_member.status in ('creator', 'administrator'):
    await message.reply(tr(chat_id, 'no_permissions'))
    return
  
  try:
    await bot.ban_chat_member(chat_id, user_id, until_date=0) # ban
    await bot.unban_chat_member(chat_id, user_id) # unban
    
    await message.reply(tr(chat_id, 'kick_success'))
  except Exception as e:
    await message.reply(f'{tr(chat_id), 'kick_failed'} {e}')

@dp.message(Command('ban')) # ban user
async def ban_user(message: Message):
  # get IDs
  user_id = message.reply_to_message.from_user.id
  chat_id = message.chat.id
  
  chat_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
  
  # No permissions
  if chat_member.status not in ['creator', 'administrator'] \
   or (chat_member.status == 'administrator' and not getattr(chat_member, "can_restrict_members", False)):
    await message.reply(tr(message.chat.id, 'no_permissions'))
    return
  
  if not message.reply_to_message:
    # if haven't tagged the user
    await message.reply(tr(message.chat.id, 'ban_reply_required'))
    return
  
  target_member = await message.bot.get_chat_member(chat_id, user_id)
  if target_member.status in ('creator', 'administrator'):
    await message.reply(tr(chat_id, 'no_permissions'))
    return
  
  try:
    await bot.ban_chat_member(chat_id, user_id) # ban
    
    await message.reply(tr(chat_id, 'ban_success'))
  except Exception as e:
    await message.reply(f'{tr(chat_id), 'ban_failed'} {e}')

@dp.message(Command('unban')) # unban user
async def unban_user(message: Message):
  # get IDs
  user_id = message.reply_to_message.from_user.id
  chat_id = message.chat.id
  
  chat_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
  
  # No permissions
  if chat_member.status not in ['creator', 'administrator'] \
   or (chat_member.status == 'administrator' and not getattr(chat_member, "can_restrict_members", False)):
    await message.reply(tr(message.chat.id, 'no_permissions'))
    return
  
  if not message.reply_to_message:
    # if haven't tagged the user
    await message.reply(tr(message.chat.id, 'ban_reply_required'))
    return
  
  try:
    await bot.unban_chat_member(chat_id, user_id) # unban
    await message.reply(tr(chat_id, 'ban_success'))
  except Exception as e:
    await message.reply(f'{tr(chat_id), 'ban_failed'} {e}')

# Interacting commands
@dp.message(Command('r')) # random task
async def cmd_r(message: Message):
  await message.reply(random.choice(tr(message.chat.id, 'r')))
  
@dp.message(Command('song')) # send audio
async def cmd_song(message: Message):
  query = message.text.replace('/song', '').strip()
  
  if not query:
    # incorrect song
    await message.reply(tr(message.chat.id, 'song_missing'))
    return
    
  if not query.startswith('http'):
    query = f'ytsearch:{query}'
    
  loading_msg = await message.reply(tr(message.chat.id, 'music_downloading'))
  
  try:
    ydl_opts = {
      'format': 'bestaudio/best',
      'outtmpl': 'song.%(ext)s',
      'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
      }],
      'quiet': True,
    }
    
    with YoutubeDL(ydl_opts) as ydl:
      ydl.download([query])
      
    audio = FSInputFile('song.mp3') # audio name
    await message.reply_audio(audio)
    
    os.remove('song.mp3') # remove audio
    
  except Exception as e:
    print(f'Ошибка: {e}')
    
  try:
    await loading_msg.delete()
  except:
    pass

@dp.message(Command('weather')) # current weather in region
async def get_weather(message: Message):
  location = message.text.replace('/weather', '').strip()
  
  if location == '':
    await message.reply('')
    return
  
  try:
    base_url = f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{location}/today'
    params = {
      'unitGroup': 'metric',
      'include': 'current',
      'key': WEATHER_API_KEY,
      'contentType': 'json'
    }
    
    response = requests.get(base_url, params=params)
    data = response.json()
    
    if 'currentConditions' in data:
      place = data['resolvedAddress']
      current = data['currentConditions']
      temp = current['temp']
      conditions = current['conditions']
      wind_speed = current['windspeed']
      result = (
        f'📍 {place}\n\n'
        f'🌡 {tr(message.chat.id, 'temp')} {temp}°C\n'
        f'☁️ {tr(message.chat.id, 'conditions')} {conditions}\n'
        f'💨 {tr(message.chat.id, 'wind')} {wind_speed} km/h'
      )
      await message.reply(result)
      
  except Exception as e:
    await message.reply(f'{tr(message.chat.id, 'weather_error')} {e}')

@dp.message(F.text) # handle each chat message
async def tiktok_handle_requests(message: Message):
  text = message.text.strip()

  if 'tiktok.com' in text:
    await tiktok_download(message)
    
  if message.chat.type == 'private':
    return
  
  # get IDs
  chat_id = message.chat.id
  user_id = message.from_user.id
  username = message.from_user.username or message.from_user.full_name
  
  if chat_id not in activity_data:
    activity_data[chat_id] = {}
    
  if user_id not in activity_data[chat_id]:
    activity_data[chat_id][user_id] = {'username': username, 'messages': 0}
    
  activity_data[chat_id][user_id]['messages'] += 1

@dp.message(Command('tiktok')) # download tiktok videos
async def tiktok_download(message: Message):
  query = message.text.replace('/tiktok', '').strip()
  loading_msg = await message.reply(tr(message.chat.id, 'video_downloading'))

  try:
    ydl_opts = {
      'outtmpl': 'tiktok.mp4',
      'format': 'mp4',
      'quiet': True,
      'writesubtitles': True,
      'writeinjson': True,
      'skip_download': False,
      'cookiefile': os.path.join(os.getcwd(), 'cookies.txt'),
    }

    with YoutubeDL(ydl_opts) as ydl:
      info = ydl.extract_info(query.strip(), download=True)
      
    # video info
    title = escape_markdown(info.get('title', tr(message.chat.id, 'no_title')))
    author = escape_markdown(info.get('uploader', tr(message.chat.id, 'no_author')))
    
    caption_text = f'*{title}* — {author}\n\n[Schmidt Talk Bot](https://t.me/schmidt_talk_bot)'

    filename = 'tiktok.mp4'
    
    if os.path.exists(filename):
      video = FSInputFile(filename)
      await message.reply_video(video, caption=caption_text, parse_mode='MarkdownV2')
      
      try:
        os.remove(filename)
      except Exception as e:
        print(f'File remove error: {e}')
    else:
      await message.reply(tr(message.chat.id, 'video_not_found'))

  except Exception as e:
    await message.reply(f'{tr(message.chat.id, 'video_error')} {e}')

  try:
    await loading_msg.delete()
  except:
    pass

# start the bot
if __name__ == '__main__':
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    # catches the stop
    print('The bot is off!')