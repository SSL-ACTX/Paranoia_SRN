import tkinter as tk
from PIL import ImageTk
import asyncio
from character import HuTaoCharacter
from database import DatabaseManager
from utils import create_circular_image
from config import config

# --- Tkinter Setup ---
root = tk.Tk()
root.title("Director Hu Tao")

# --- Load config ---
WINDOW_WIDTH = config["tkinter"]["window_width"]
WINDOW_HEIGHT = config["tkinter"]["window_height"]
HUTAO_IMAGE_PATH = config["tkinter"]["hutao_image_path"]
HUTAO_IMAGE_SIZE = tuple(config["tkinter"]["hutao_image_size"])
VERSION_NUMBER = config["tkinter"]["version_number"]
HU_TAO_RED = config["hu_tao"]["color_scheme"]["red"]
HU_TAO_MESSAGE = config["hu_tao"]["color_scheme"]["message"]
HU_TAO_WHITE = config["hu_tao"]["color_scheme"]["white"]
HU_TAO_DARK = config["hu_tao"]["color_scheme"]["dark"]
DEFAULT_USER_NAME = config["characterai"]["default_user_name"]
IDLE_TIMEOUT = config["characterai"]["idle_timeout"]

# Center the window on the screen
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x = (screen_width - WINDOW_WIDTH) // 2
y = (screen_height - WINDOW_HEIGHT) // 2
root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}+{x}+{y}")
root.configure(bg=HU_TAO_DARK)

# --- Flags ---
running = True

# --- Initialize Character and Database ---
hu_tao = HuTaoCharacter()
db_manager = DatabaseManager()
initial_chat_created = False

# --- Frames ---
main_frame = tk.Frame(root, bg=HU_TAO_DARK)
main_frame.pack(fill=tk.BOTH, expand=True)

chat_frame = tk.Frame(main_frame, bg=HU_TAO_DARK)
chat_frame.pack(fill=tk.BOTH, expand=True)

chat_log = tk.Text(chat_frame, bg=HU_TAO_DARK, fg=HU_TAO_WHITE, wrap=tk.WORD, state=tk.DISABLED)
chat_log.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

input_frame = tk.Frame(root, bg=HU_TAO_DARK)
input_frame.pack(side=tk.BOTTOM, fill=tk.X)

message_entry = tk.Entry(input_frame, bg=HU_TAO_DARK, fg=HU_TAO_WHITE, font=("Courier New", 12),
                         insertbackground=HU_TAO_WHITE)
message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)

send_button = tk.Button(input_frame, text="Send", bg=HU_TAO_RED, fg=HU_TAO_WHITE, font=("Arial", 12), padx=10, pady=10)
send_button.pack(side=tk.RIGHT, padx=10, pady=10)

# --- Hu Tao Info ---
info_frame = tk.Frame(chat_frame, bg=HU_TAO_DARK)
info_frame.pack(side=tk.TOP, fill=tk.X)

circular_image = create_circular_image(HUTAO_IMAGE_PATH, HUTAO_IMAGE_SIZE)
if circular_image:
    photo = ImageTk.PhotoImage(circular_image)
    image_label = tk.Label(info_frame, image=photo, bg=HU_TAO_DARK)
    image_label.image = photo
    image_label.pack(side=tk.LEFT, padx=10, pady=10)

name_label_frame = tk.Frame(info_frame, bg=HU_TAO_DARK)
name_label_frame.pack(side=tk.LEFT, pady=10)

name_label = tk.Label(name_label_frame, text="Hu Tao", font=("Baskerville", 22), bg=HU_TAO_DARK, fg=HU_TAO_RED)
name_label.pack(side=tk.TOP)

version_label = tk.Label(name_label_frame, text=f"by Altair, Version {VERSION_NUMBER}", font=("Arial", 10),
                         bg=HU_TAO_DARK, fg=HU_TAO_WHITE)
version_label.pack(side=tk.TOP)

# --- Emotion and Affection Label Setup ---
emotion_affection_frame = tk.Frame(info_frame, bg=HU_TAO_DARK)
emotion_affection_frame.pack(side=tk.RIGHT, padx=10)

emotion_label = tk.Label(emotion_affection_frame, text=f"{hu_tao.current_emotion}", font=("Arial", 12), bg=HU_TAO_DARK,
                         fg=hu_tao.EMOTION_COLORS[hu_tao.current_emotion])
emotion_label.pack(side=tk.TOP)

affection_label = tk.Label(emotion_affection_frame, text=f"Affection: {hu_tao.user_affection}", font=("Arial", 10), bg=HU_TAO_DARK, fg=HU_TAO_WHITE)
affection_label.pack(side=tk.TOP)

# --- Typing Indicator ---
typing_indicator = tk.Label(info_frame, text="Hu Tao is typing...", font=("Arial", 10), bg=HU_TAO_DARK, fg=HU_TAO_WHITE)
typing_indicator.pack(side=tk.BOTTOM, padx=10)
typing_indicator.pack_forget()  # Hide initially

# --- Function Bindings ---
def update_emotion_label(emotion):
    emotion_label.config(text=f"{emotion}", fg=hu_tao.EMOTION_COLORS.get(emotion, "#FFFFFF"))

def update_affection_label():
    affection_label.config(text=f"Affection: {int(hu_tao.user_affection)}")

def update_chat_log(message, sender="user"):
    chat_log.config(state=tk.NORMAL)
    if sender == "hutao":
        chat_log.insert(tk.END, message + "\n", "hutao")
    else:
        chat_log.insert(tk.END, message + "\n")
    chat_log.tag_config("hutao", foreground=HU_TAO_MESSAGE)
    chat_log.see(tk.END)
    chat_log.config(state=tk.DISABLED)

def send_message():
    user_message = message_entry.get().strip()
    if user_message:
        update_chat_log(f"{DEFAULT_USER_NAME}: {user_message}")
        message_entry.delete(0, tk.END)
        user_id = 1
        typing_indicator.pack(side=tk.BOTTOM, padx=10)
        asyncio.create_task(process_and_respond(user_message, user_id))
        hu_tao.last_interaction_time = asyncio.get_event_loop().time()

async def display_conversation():
    user_id = 1
    chat_id, conversation_history = await db_manager.get_chat_session(user_id)

    chat_log.config(state=tk.NORMAL)
    chat_log.delete("1.0", tk.END)

    for line in conversation_history:
        if line.startswith("Hu Tao:"):
            update_chat_log(line, sender="hutao")
        else:
            update_chat_log(line)
    chat_log.config(state=tk.DISABLED)
    chat_log.see(tk.END)

async def shutdown():
    print("Shutting down...")
    await hu_tao.close_characterai()
    print("Shutdown complete.")

def on_closing():
    global running
    running = False
    print("Closing application...")

    async def _close():
        await shutdown()
        root.destroy()

    asyncio.create_task(_close())

async def process_and_respond(user_message, user_id):
    """Processes the user's message and updates the GUI."""
    print("User message in process_and_respond:", user_message) #ADD IT HERE.
    await hu_tao.process_response(user_message, user_id, update_chat_log, display_conversation, update_affection_label)
    update_emotion_label(hu_tao.current_emotion)
    typing_indicator.pack_forget()
    update_affection_label()

# --- Event Bindings ---
send_button.config(command=send_message)
message_entry.bind("<Return>", lambda event: send_message())
root.protocol("WM_DELETE_WINDOW", on_closing)

# --- Main Event Loop ---
async def main():
    global initial_chat_created

    db_manager.initialize_db()
    await hu_tao.initialize_characterai(config["characterai"]["api_key"])
    user_id = 1
    chat_id, conversation_history = await db_manager.get_chat_session(user_id)
    await display_conversation()
    hu_tao.choose_activity()
    update_affection_label()

    while running:
        chat_id, conversation_history = await db_manager.get_chat_session(user_id) #Refresh

        if not chat_id and not initial_chat_created:
            initial_message = hu_tao.INITIAL_MESSAGE
            update_chat_log(f"Hu Tao: {initial_message}", sender="hutao")
            initial_chat_created = True
            new_chat = await hu_tao.client.connect()
            new_chat, _ = await new_chat.new_chat(hu_tao.CHAR_ID, (await hu_tao.client.get_me()).id)
            chat_id = new_chat.chat_id
            conversation_history = [f"Hu Tao: {initial_message}"]
            await db_manager.save_chat_session(user_id, chat_id, conversation_history)
        try:
            current_time = asyncio.get_event_loop().time()
            if current_time - hu_tao.last_interaction_time > IDLE_TIMEOUT:
                hu_tao.last_interaction_time = current_time
                idle_message = await hu_tao.generate_idle_response(user_id)
                update_chat_log(f"Hu Tao: {idle_message}", sender="hutao")
                await display_conversation()
                update_emotion_label(hu_tao.current_emotion)
                update_affection_label()
            root.update()
            await asyncio.sleep(0.01)
        except tk.TclError as e:
            if "application has been destroyed" not in str(e):
                print(f"Tkinter error: {e}")
            break
    print("Main loop terminated.")

if __name__ == "__main__":
    asyncio.run(main())
