# Refactored by: Seuriin
# Creator: Altair
import random
import asyncio
import datetime

# <-- Self-made imports (Classes) -->

# Core for logical char interactions
from characterai import aiocai
from database import DatabaseManager
from config import config # For fetching JSON config :P

# Emotion and affection detector using Gemini AI (Flash 2.0)
from gemini_sentiment import GeminiSentimentAnalyzer

# long ahh code ahead ;/
class HuTaoCharacter:
    def __init__(self):
        self.CHAR_ID = config["characterai"]["character_id"]
        self.USER_NAME = config["characterai"]["user_name"]
        self.DEFAULT_USER_NAME = config["characterai"]["default_user_name"]
        self.IDLE_TIMEOUT = config["characterai"]["idle_timeout"]
        self.HU_TAO_TOPICS = config["hu_tao"]["topics"]
        self.HU_TAO_ACTIVITIES = config["hu_tao"]["activities"]
        self.ACTIVITY_DURATION = config["hu_tao"]["activity_duration"]
        self.EMOTIONS = config["emotion"]["list"]
        self.EMOTION_COLORS = config["emotion"]["colors"]
        self.DEFAULT_AFFECTION = config["affection"]["default"]
        self.MAX_AFFECTION = config["affection"]["max"]
        self.MIN_AFFECTION = config["affection"]["min"]
        self.AFFECTION_CHANGE_AMOUNT = config["affection"]["change_amount"]
        self.PERSONALITY_TRAITS = config["personality"]["traits"]
        self.TRAIT_ADJUSTMENT_RATE = config["personality"]["trait_adjustment_rate"]
        self.POSITIVE_TRAITS = config["personality"]["positive_traits"]
        self.NEGATIVE_TRAITS = config["personality"]["negative_traits"]
        self.NEUTRAL_TRAITS = config["personality"]["neutral_traits"]
        self.INFLUENCE_FACTOR = config["personality"]["influence_factor"]
        self.INITIAL_MESSAGE = config["characterai_prompts"]["initial_message"]
        self.BASE_PROMPT = config["characterai_prompts"]["base_prompt"]
        self.IDLE_PROMPT_ACTIVITY_TOPIC = config["characterai_prompts"]["idle_prompt_activity_topic"]
        self.IDLE_PROMPT_ACTIVITY = config["characterai_prompts"]["idle_prompt_activity"]
        self.INTERRUPTION_CHANCE = config["conversation"]["interruption_chance"]

        self.current_activity = None
        self.activity_start_time = None
        self.current_emotion = "Neutral"
        self.user_affection = self.DEFAULT_AFFECTION
        self.client = None
        self.last_interaction_time = asyncio.get_event_loop().time()
        self.db_manager = DatabaseManager()
        self.gemini_analyzer = GeminiSentimentAnalyzer()
        self.gemini_analyzer.api_key = config["gemini"]["api_key"]

    async def initialize_characterai(self, api_key):
        """Initializes the CharacterAI client."""
        self.client = aiocai.Client(api_key)

    async def close_characterai(self):
        """Closes the CharacterAI client."""
        if self.client and hasattr(self.client, 'close') and callable(self.client.close):
             await self.client.close()

    def choose_activity(self):
        """Selects a new activity for Hu Tao."""
        activities = self.HU_TAO_ACTIVITIES.get(self.current_emotion, self.HU_TAO_ACTIVITIES["Neutral"])
        self.current_activity = random.choice(activities)
        self.activity_start_time = asyncio.get_event_loop().time()

    def suggest_topic(self):
        """Randomly selects a new conversation topic."""
        return random.choice(self.HU_TAO_TOPICS)

    def get_activity_status(self):
        """Checks if the current activity is ongoing."""
        if self.current_activity is None:
            self.choose_activity()
            return f"I was about to begin {self.current_activity}!"

        elapsed_time = asyncio.get_event_loop().time() - self.activity_start_time
        if elapsed_time >= self.ACTIVITY_DURATION:
            self.choose_activity()
            return f"Oh, I've just finished {self.current_activity}."
        else:
            remaining_time = self.ACTIVITY_DURATION - elapsed_time
            return f"Currently, I'm engaged in {self.current_activity}.  It'll take about {int(remaining_time)} more seconds."

    def analyze_emotion(self, text):
        """Robust emotion analysis."""
        text_lower = text.lower()

        if any(word in text_lower for word in ["happy", "joyful", "delighted", "excited"]):
            return "Happy"
        elif any(word in text_lower for word in ["sad", "depressed", "unhappy", "grief", "mourning"]):
            return "Sad"
        elif any(word in text_lower for word in ["angry", "furious", "irate", "annoyed"]):
            return "Angry"
        elif any(word in text_lower for word in ["fearful", "scared", "afraid", "terrified"]):
            return "Fearful"
        elif any(word in text_lower for word in ["surprised", "amazed", "astonished", "shocked"]):
            return "Surprised"
        elif any(word in text_lower for word in ["disgusted", "repulsed", "sickened", "nauseated"]):
            return "Disgusted"
        elif any(word in text_lower for word in ["worried", "anxious", "concerned", "apprehensive"]):
            return "Worried"
        elif any(word in text_lower for word in ["loving", "affectionate", "caring", "romantic"]):
            return "Loving"
        elif any(word in text_lower for word in ["obsessed", "fixated", "infatuated", "stalking"]):
            return "Obsessed"
        elif any(word in text_lower for word in ["darling", "sweetheart", "dearest", "honey"]):
            return "Endearing"
        else:
            return "Neutral"

    async def adjust_affection(self, user_text, response_text):
        """Forces affection increase for debugging."""  # Modified docstring
        prompt = f"Analyze the sentiment of both messages. The user said: '{user_text}'. Hu Tao responded with: '{response_text}'. Given this exchange, does the user likely have increased affection, decreased affection, or neutral affection towards Hu Tao? Respond with 'positive', 'negative', or 'neutral'."
        sentiment = await self.gemini_analyzer.analyze_sentiment(prompt)

        print("Prompt send to Gemini:", prompt)
        print(f"Gemini Sentiment: {sentiment}")

        print(f"Affection before adjustment: {self.user_affection}") # ADDED: Log affection before

        if sentiment == "positive":
            self.user_affection += 0.5 # Forced increase by 0.5 for testing <----- FORCED INCREASE
        elif sentiment == "negative":
            self.user_affection -= self.AFFECTION_CHANGE_AMOUNT
        # If neutral, no change

        self.user_affection = max(self.MIN_AFFECTION, min(self.MAX_AFFECTION, self.user_affection))
        print(f"Affection after adjustment: {self.user_affection}") # ADDED: Log affection after :/

    def analyze_conversation_traits(self, conversation_history):
        """Analyzes conversation history for personality traits."""
        analysis = {trait: 0.0 for trait in self.PERSONALITY_TRAITS}
        recent_history = " ".join(conversation_history[-5:]).lower()

        if any(word in recent_history for word in ["hope", "bright", "positive", "wonderful", "amazing", "believe", "confident"]):
            analysis["optimism"] += 0.1
        if any(word in recent_history for word in ["pointless", "meaningless", "waste", "doomed", "inevitable", "pathetic", "useless"]):
            analysis["cynicism"] += 0.1
        if any(word in recent_history for word in ["joke", "funny", "tease", "prank", "silly", "laugh", "amuse"]):
            analysis["playfulness"] += 0.1
        if any(word in recent_history for word in ["important", "matter", "consider", "reflection", "thoughtful", "grave", "solemn"]):
            analysis["seriousness"] += 0.1
        if any(word in recent_history for word in ["trick", "sneak", "surprise", "rascal", "impish", "naughty", "scheme"]):
            analysis["mischievousness"] += 0.1
        if any(word in recent_history for word in ["honor", "respect", "courtesy", "polite", "deference", "esteem", "revere"]):
            analysis["respectfulness"] += 0.1
        analysis["worldliness"] += 0.02
        if any(word in recent_history for word in ["hurry", "rush", "wait", "delay", "bother", "late", "annoying"]):
            analysis["impatience"] += 0.1
        if any(word in recent_history for word in ["sympathy", "care", "comfort", "console", "kind", "gentle", "empathy"]):
            analysis["compassion"] += 0.1

        return analysis

    def adjust_personality_traits(self, analysis_results):
        """Adjusts personality traits."""

        for trait, value in analysis_results.items():
            self.PERSONALITY_TRAITS[trait] += value * self.TRAIT_ADJUSTMENT_RATE
            self.PERSONALITY_TRAITS[trait] = max(0.0, min(1.0, self.PERSONALITY_TRAITS[trait]))

        for positive_trait in self.POSITIVE_TRAITS:
            for negative_trait in self.NEGATIVE_TRAITS:
                influence = (self.PERSONALITY_TRAITS[negative_trait] - 0.5) * self.INFLUENCE_FACTOR
                self.PERSONALITY_TRAITS[positive_trait] -= influence
                influence = (self.PERSONALITY_TRAITS[positive_trait] - 0.5) * self.INFLUENCE_FACTOR
                self.PERSONALITY_TRAITS[negative_trait] -= influence

            for neutral_trait in self.NEUTRAL_TRAITS:
                influence = (self.PERSONALITY_TRAITS[positive_trait] - 0.5) * self.INFLUENCE_FACTOR
                self.PERSONALITY_TRAITS[neutral_trait] += influence
                influence = (self.PERSONALITY_TRAITS[negative_trait] - 0.5) * self.INFLUENCE_FACTOR
                self.PERSONALITY_TRAITS[neutral_trait] += influence

    async def handle_characterai_command(self, user_id, message):
        """Handles interaction with CharacterAI, including prompts and responses."""
        try:
            chat_id, conversation_history = await self.db_manager.get_chat_session(user_id)
            chat = await self.client.connect()

            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M")
            current_date = now.strftime("%Y-%m-%d")
            context = f"The current time is {current_time} on {current_date}. "

            if not chat_id:
                initial_message = self.INITIAL_MESSAGE
                new_chat, _ = await chat.new_chat(self.CHAR_ID, (await self.client.get_me()).id)
                chat_id = new_chat.chat_id
                conversation_history = [f"Hu Tao: {initial_message}"]
                await self.db_manager.save_chat_session(user_id, chat_id, conversation_history)

            trait_analysis = self.analyze_conversation_traits(conversation_history)
            self.adjust_personality_traits(trait_analysis)

            if self.user_affection > 75:
                tone = "Warm, playful, and slightly flirtatious"
            elif self.user_affection < 25:
                tone = "Slightly distant, teasing, and subtly morbid"
            else:
                tone = "Playful, mischievous, and generally cheerful"

            prompt = self.BASE_PROMPT.format(
                user_name=self.USER_NAME,
                tone=tone,
                affection_level=self.user_affection,
                conversation_history=conversation_history,
                message=message
            )

            full_message = context + prompt
            response = await chat.send_message(self.CHAR_ID, chat_id, full_message)
            response_text = response.text

            self.current_emotion = self.analyze_emotion(response_text)

            conversation_history.extend([f"{self.USER_NAME}: {message}", f"Hu Tao: {response_text}"])
            await self.db_manager.save_chat_session(user_id, chat_id, conversation_history)

            return response_text

        except Exception as e:
            print(f"Error generating content: {e}")
            return f"Error: {e}"

    async def generate_idle_response(self, user_id):
        """Generates an idle response from Hu Tao."""
        try:
            chat_id, conversation_history = await self.db_manager.get_chat_session(user_id)
            chat = await self.client.connect()

            now = datetime.datetime.now()
            current_time = now.strftime("%H:%M")
            current_date = now.strftime("%Y-%m-%d")
            context = f"The current time is {current_time} on {current_date}. "

            if not chat_id:
                new_chat, _ = await chat.new_chat(self.CHAR_ID, (await self.client.get_me()).id)
                chat_id = new_chat.chat_id
                conversation_history = []
                await self.db_manager.save_chat_session(user_id, chat_id, conversation_history)

            activity_status = self.get_activity_status()
            if random.random() < 0.6:
                topic = random.choice(self.HU_TAO_TOPICS)
                prompt = self.IDLE_PROMPT_ACTIVITY_TOPIC.format(
                    activity_status=activity_status,
                    topic=topic,
                    user_name=self.USER_NAME,
                    affection_level=self.user_affection
                )
            else:
                prompt = self.IDLE_PROMPT_ACTIVITY.format(
                    activity_status=activity_status,
                    user_name=self.USER_NAME,
                    affection_level=self.user_affection
                )
            full_message = context + prompt
            response = await chat.send_message(self.CHAR_ID, chat_id, full_message)
            response_text = response.text

            if "I am an AI" in response_text or len(response_text) < 5:
                print("Filtered nonsensical response.")
                response_text = "Hehe... Are you still there?"

            self.current_emotion = self.analyze_emotion(response_text)

            conversation_history.append(f"Hu Tao: {response_text}")
            await self.db_manager.save_chat_session(user_id, chat_id, conversation_history)

            return response_text

        except Exception as e:
            print(f"Error generating idle response: {e}")
            return "Boo! Did I scare you?"

    async def process_response(self, message, user_id, update_chat_log_func, display_conversation_func, update_affection_label_func):
        """Processes the user's message and gets a response."""

        if random.random() < self.INTERRUPTION_CHANCE:
            interruption_message = f"Oh, excuse me! I was in the middle of {self.current_activity}."
            update_chat_log_func(f"Hu Tao: {interruption_message}", sender="hutao")
            display_conversation_func()
            await asyncio.sleep(1)

        response = await self.handle_characterai_command(user_id, message) #Get the response from hutao first.

        await self.adjust_affection(message, response)  # Pass both messages to adjust_affection

        update_chat_log_func(f"Hu Tao: {response}", sender="hutao")
        display_conversation_func()
        update_affection_label_func()
