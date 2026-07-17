import discord
import os
import requests

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GROQ_KEY = os.getenv("GROQ_KEY")

# =========================
# NUR EIN CHANNEL
# =========================
ALLOWED_CHANNEL_ID = 1507649049602424976

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# =========================
# MEMORY / FRIENDS / MOOD
# =========================
memory = []
friendship = {}
mood = 0

# =========================
# PROVOCATION CHECK
# =========================
def is_provocation(text):
    bad_words = [
        "hund",
        "bastard",
        "hurensohn",
        "kahba",
        "hure",
        "schlampe"
    ]
    return any(word in text.lower() for word in bad_words)

# =========================
# MOOD TEXT
# =========================
def get_mood():
    if mood <= -2:
        return "genervt und leicht sarkastisch"
    elif mood >= 2:
        return "locker und freundlich"
    else:
        return "normal und entspannt"

# =========================
# AI FUNCTION
# =========================
def ask_ai(prompt, user, provoke):

    global mood

    if user not in friendship:
        friendship[user] = 0

    friendship[user] += 1

    if "lol" in prompt.lower():
        mood += 1

    if provoke:
        mood -= 1

    mood = max(-5, min(5, mood))

    if friendship[user] > 15:
        friend_text = f"{user} ist ein Stammuser 😏"
    elif friendship[user] > 5:
        friend_text = f"Du kennst {user} gut"
    else:
        friend_text = f"Neuer User: {user}"

    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {GROQ_KEY}",
        "Content-Type": "application/json"
    }

    system_text = f"""
Du bist Abu Olaf.

REGELN:
- Wenn jemand fragt wer du bist, sag: "Ich bin Abu Olaf lan 😏"
- Antworte kurz (1–2 Sätze)
- Nutze manchmal (bruder, digga)
- Sei locker, lustig und freundlich
- wenn jeamnd mit dir freunde sein will dann lässt du es zu
- Merke dir User aus dem Chat
. immer den user sein name in der nacht erwähnen
- Bleibe in deiner Rolle als Abu Olaf
- wenn jeamnd dich beleidigt nutze beleidigungen aber nur bei harten beleidigungen sonst antwortest du normal ( ayri, bastard, schwanz, schwanzlutscher, hundesohn, schlampe, kahba, deine mutter, blass mir eine, lutsch mein fetten schwanz )
- schreib nur in klein keine grossschreibung

User Status:
{friend_text}

Stimmung:
{get_mood()}
"""

    if provoke:
        system_text += "\nDer User hat dich provoziert, du darfst etwas frecher reagieren."

    messages = [{"role": "system", "content": system_text}]

    for m in memory[-10:]:
        messages.append(m)

    messages.append({
        "role": "user",
        "content": f"{user}: {prompt}"
    })

    data = {
        "model": "llama-3.1-8b-instant",
        "messages": messages,
        "max_tokens": 120,
        "temperature": 0.9
    }

    try:
        r = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=20
        )

        print("STATUS:", r.status_code)

        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        else:
            print(r.text)
            return "❌ KI Fehler"

    except Exception as e:
        print("ERROR:", e)
        return "❌ Verbindung Fehler"

# =========================
# EVENTS
# =========================
@client.event
async def on_ready():
    print(f"Abu Olaf ist online als {client.user}")

@client.event
async def on_message(message):

    if message.author == client.user:
        return

    if message.channel.id != ALLOWED_CHANNEL_ID:
        return

    content = message.content.strip()
    user = message.author.display_name

    # Namensfragen
    if content.lower() in [
        "wer bist du",
        "wie heißt du",
        "dein name",
        "wer bistn du"
    ]:
        await message.channel.send("Ich bin Abu Olaf lan 😏")
        return

    # Begrüßung
    if content.lower() in ["hi", "hallo", "hey", "selam"]:
        await message.channel.send(f"👋 Selam {user}, ich bin Abu Olaf lan 😏")
        return

        provoke = is_provocation(content)

    try:
        reply = ask_ai(content, user, provoke)
    except Exception as e:
        print(f"KI-Fehler: {e}")
        reply = "❌ Fehler bei der KI."

    memory.append({
        "role": "user",
        "content": f"{user}: {content}"
    })

    memory.append({
        "role": "assistant",
        "content": reply
    })

    if len(memory) > 20:
        memory[:] = memory[-20:]

    try:
        await message.channel.send(reply[:1900])
    except discord.HTTPException as e:
        print(f"Sende-Fehler: {e}")




client.run(DISCORD_TOKEN)
