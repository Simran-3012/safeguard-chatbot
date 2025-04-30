import streamlit as st
import google.generativeai as genai
import os
import time
import re
import json
import uuid
from datetime import datetime, timedelta
import random


# =========================================================
# PART 1: CHAT HISTORY MANAGEMENT FUNCTIONS
# =========================================================

def initialize_chat_state():
    """Initialize session state variables for chat management"""
    if "messages" not in st.session_state:
        st.session_state.messages = []

    if "chat_histories" not in st.session_state:
        st.session_state.chat_histories = {}

    if "current_chat_id" not in st.session_state:
        st.session_state.current_chat_id = str(uuid.uuid4())

    if "current_chat_name" not in st.session_state:
        st.session_state.current_chat_name = f"Chat {datetime.now().strftime('%b %d, %H:%M')}"

    if "editing_message_index" not in st.session_state:
        st.session_state.editing_message_index = None


def add_message_to_current_chat(role, content):
    """
    Add a message to the current chat history.

    Args:
        role: The role of the message sender (user or assistant)
        content: The content of the message
    """
    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.session_state.messages.append({"role": role, "content": content})


def save_current_chat():
    """Save the current chat to the chat histories"""
    if not st.session_state.messages:
        st.warning("Cannot save an empty chat.")
        return False

    st.session_state.chat_histories[st.session_state.current_chat_id] = {
        "name": st.session_state.current_chat_name,
        "timestamp": datetime.now().isoformat(),
        "messages": st.session_state.messages.copy(),
        "mood": st.session_state.current_mood if "current_mood" in st.session_state else None,
        "theme": st.session_state.chat_theme if "chat_theme" in st.session_state else "Default",
        "style": st.session_state.response_style if "response_style" in st.session_state else "Balanced"
    }
    return True


def load_chat(chat_id):
    """Load a chat from history"""
    if chat_id in st.session_state.chat_histories:
        chat_data = st.session_state.chat_histories[chat_id]
        st.session_state.messages = chat_data["messages"].copy()
        st.session_state.current_chat_id = chat_id
        st.session_state.current_chat_name = chat_data["name"]

        # Store settings in temporary variables instead of directly in widget-bound session states
        if "mood" in chat_data and chat_data["mood"]:
            st.session_state.loaded_mood = chat_data["mood"]
        if "theme" in chat_data:
            # Instead of setting chat_theme directly, use a different variable
            st.session_state.loaded_theme = chat_data["theme"]
        if "style" in chat_data:
            st.session_state.loaded_style = chat_data["style"]

        # Flag that we've loaded a chat and need to rerun to apply settings
        st.session_state.chat_just_loaded = True

        return True
    return False


def start_new_chat():
    """Start a new chat session"""
    # Save current chat before starting new one
    if st.session_state.messages and len(st.session_state.messages) > 1:
        save_current_chat()

    # Create a new chat session
    st.session_state.current_chat_id = str(uuid.uuid4())
    st.session_state.current_chat_name = f"Chat {datetime.now().strftime('%b %d, %H:%M')}"

    # Reset messages but add welcome message
    welcome_message = {
        "role": "assistant",
        "content": "Hi there! I'm EmpatheticListener. How are you feeling today? I'm here to listen and understand."
    }
    st.session_state.messages = [welcome_message]

    # Reset editing state
    st.session_state.editing_message_index = None


def rename_chat(chat_id, new_name):
    """Rename a saved chat"""
    if chat_id in st.session_state.chat_histories:
        st.session_state.chat_histories[chat_id]["name"] = new_name
        if chat_id == st.session_state.current_chat_id:
            st.session_state.current_chat_name = new_name
        return True
    return False


def delete_chat(chat_id):
    """Delete a chat from history"""
    if chat_id in st.session_state.chat_histories:
        # If we're deleting the current chat, start a new one
        if chat_id == st.session_state.current_chat_id:
            start_new_chat()

        # Delete the chat
        del st.session_state.chat_histories[chat_id]
        return True
    return False


def export_chat_history():
    """Export all chat histories to a JSON file for download"""
    if not st.session_state.chat_histories:
        st.warning("No chat histories to export.")
        return None

    # Convert datetime objects to strings for JSON serialization
    export_data = {}
    for chat_id, chat_data in st.session_state.chat_histories.items():
        export_data[chat_id] = chat_data.copy()

    # Convert to JSON
    json_data = json.dumps(export_data, indent=2)
    return json_data


def import_chat_history(json_data):
    """Import chat histories from a JSON file"""
    try:
        imported_data = json.loads(json_data)

        # Add imported chats to current chat histories
        for chat_id, chat_data in imported_data.items():
            st.session_state.chat_histories[chat_id] = chat_data

        return len(imported_data)
    except Exception as e:
        st.error(f"Error importing chat history: {str(e)}")
        return 0


def edit_message(index):
    """Set a message for editing"""
    st.session_state.editing_message_index = index


def save_edited_message(index, new_content):
    """Save an edited message"""
    if 0 <= index < len(st.session_state.messages):
        st.session_state.messages[index]["content"] = new_content
        st.session_state.editing_message_index = None

        # If this is the current chat and it's saved, update the saved version too
        if st.session_state.current_chat_id in st.session_state.chat_histories:
            st.session_state.chat_histories[st.session_state.current_chat_id][
                "messages"] = st.session_state.messages.copy()


# =========================================================
# PART 2: INTERFACE CUSTOMIZATION AND STYLING
# =========================================================

def apply_custom_css():
    """
    Apply custom CSS to create a more visually appealing and emotionally
    resonant interface. This function injects CSS that transforms the
    standard Streamlit look into something more appropriate for an
    empathetic conversation application.
    """
    st.markdown("""
    <style>
        /* Overall page styling */
        .main {
            background-color: #fafafa;
            font-family: 'Helvetica Neue', Arial, sans-serif;
        }

        /* Main content container styling */
        .main .block-container {
            padding: 2rem 1rem;
            max-width: 1000px;
        }

        /* Header styling with gradient */
        h1 {
            color: #6366F1;
            font-weight: 600;
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(90deg, #6366F1, #D946EF);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            padding-bottom: 10px;
        }

        h2 {
            color: #4F46E5;
            font-weight: 500;
            font-size: 1.5rem;
            margin-top: 0;
            margin-bottom: 1.5rem;
        }

        /* Subtitle styling */
        .subtitle {
            color: #6B7280;
            font-style: italic;
            margin-top: 0;
            margin-bottom: 2rem;
        }

        /* Chat message container */
        .chat-container {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            margin-bottom: 1.5rem;
            overflow-y: auto;
            max-height: 600px;
            border: 1px solid #E5E7EB;
        }

        /* Custom styling for user and assistant messages */
        .stChatMessage {
            padding: 0.75rem;
            margin-bottom: 1rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            animation: fadeIn 0.3s ease-in-out;
        }

        /* User message styling */
        .stChatMessage[data-testid="stChatMessageUser"] {
            background-color: #F3F4F6;
            border-left: 4px solid #6366F1;
        }

        /* Assistant message styling */
        .stChatMessage[data-testid="stChatMessageAssistant"] {
            background-color: #F8F0FF;
            border-left: 4px solid #D946EF;
        }

        /* Input box styling */
        .stChatInputContainer {
            margin-top: 1rem;
        }

        /* Chat input styling */
        .stChatInput {
            border-radius: 20px;
            border: 1px solid #E5E7EB;
            padding: 0.75rem 1rem;
            background-color: #F9FAFB;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
            transition: all 0.2s ease;
        }

        .stChatInput:focus {
            border-color: #6366F1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }

        /* Sidebar styling */
        .css-1d391kg {
            background-color: #F8F0FF;
        }

        /* Sidebar headers */
        .sidebar .stTabs [data-baseweb="tab-list"] {
            gap: 1px;
        }

        .sidebar .stTabs [data-baseweb="tab"] {
            background-color: #F3F4F6;
            border-radius: 4px 4px 0 0;
            padding: 0.5rem 1rem;
            font-size: 0.875rem;
        }

        .sidebar .stTabs [aria-selected="true"] {
            background-color: white;
            border-top: 2px solid #6366F1;
        }

        /* Mood selector styling */
        .mood-selector {
            display: flex;
            justify-content: space-between;
            margin-bottom: 1.5rem;
            background-color: white;
            padding: 1rem;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .mood-button {
            display: inline-flex;
            flex-direction: column;
            align-items: center;
            background-color: transparent;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 0.5rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .mood-button:hover {
            background-color: #F3F4F6;
            transform: translateY(-2px);
        }

        .mood-button.selected {
            border-color: #6366F1;
            background-color: #EEF2FF;
        }

        .mood-emoji {
            font-size: 1.5rem;
            margin-bottom: 0.25rem;
        }

        .mood-label {
            font-size: 0.75rem;
            color: #4B5563;
        }

        /* Animation for message appearance */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Resource cards in sidebar */
        .resource-card {
            background-color: white;
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 3px solid #6366F1;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .resource-card h4 {
            margin-top: 0;
            color: #1F2937;
            font-size: 1rem;
        }

        .resource-card p {
            margin-bottom: 0;
            color: #6B7280;
            font-size: 0.875rem;
        }

        /* Footer styling */
        .footer {
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #E5E7EB;
            color: #9CA3AF;
            font-size: 0.75rem;
            text-align: center;
        }

        /* Chat options styling */
        .chat-options-container {
            margin-top: 1rem;
        }

        /* Style for the theme selector */
        .stSelectbox {
            margin-bottom: 1rem;
        }

        /* Style for buttons in chat options */
        .chat-options-container .stButton > button {
            background-color: #6366F1;
            color: white;
            border-radius: 20px;
            border: none;
            padding: 0.5rem 1rem;
            width: 100%;
            transition: all 0.2s ease;
        }

        .chat-options-container .stButton > button:hover {
            background-color: #4F46E5;
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        /* Style for select sliders */
        .stSlider {
            margin-bottom: 1.5rem;
        }

        /* Message edit controls */
        .message-controls {
            display: flex;
            justify-content: flex-end;
            gap: 0.5rem;
            margin-top: 0.5rem;
        }

        .edit-button, .cancel-button, .save-button {
            background-color: transparent;
            border: 1px solid #E5E7EB;
            border-radius: 4px;
            padding: 0.25rem 0.5rem;
            font-size: 0.75rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .edit-button:hover, .cancel-button:hover, .save-button:hover {
            background-color: #F3F4F6;
        }

        .edit-button {
            color: #6366F1;
        }

        .save-button {
            color: #10B981;
        }

        .cancel-button {
            color: #EF4444;
        }

        /* Chat history list styling */
        .chat-history-list {
            margin-top: 1rem;
            max-height: 400px;
            overflow-y: auto;
        }

        .chat-history-item {
            background-color: white;
            border-radius: 8px;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            border-left: 3px solid #6366F1;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .chat-history-item:hover {
            background-color: #F3F4F6;
            transform: translateX(2px);
        }

        .chat-history-item.active {
            border-left-color: #D946EF;
            background-color: #F8F0FF;
        }

        .chat-history-name {
            font-weight: 500;
            color: #1F2937;
        }

        .chat-history-date {
            font-size: 0.75rem;
            color: #6B7280;
        }

        .chat-history-controls {
            display: flex;
            justify-content: space-between;
            margin-top: 0.5rem;
        }

        /* API Status Indicator */
        .api-status {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            padding: 0.5rem;
            border-radius: 8px;
            font-size: 0.875rem;
        }

        .api-status.online {
            background-color: #ECFDF5;
            color: #047857;
        }

        .api-status.limited {
            background-color: #FEF3C7;
            color: #B45309;
        }

        .api-status.offline {
            background-color: #FEE2E2;
            color: #B91C1C;
        }

        .api-status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
        }

        .api-status.online .api-status-dot {
            background-color: #10B981;
        }

        .api-status.limited .api-status-dot {
            background-color: #F59E0B;
        }

        .api-status.offline .api-status-dot {
            background-color: #EF4444;
        }

        /* Hide the Deploy button but keep the menu button */
        [data-testid="stToolbar"] [aria-label="Deploy this app"],
        [data-testid="stToolbar"] button[aria-label="Deploy"],
        [data-testid="stToolbar"] a[aria-label="Deploy"],
        .stDeployButton {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)


def create_header():
    """
    Create an aesthetically pleasing header for the application.
    This includes the main title and a welcoming subtitle that sets
    the tone for the empathetic conversation experience.
    """
    st.markdown("<h1>EmpatheticListener</h1>", unsafe_allow_html=True)
    st.markdown("<h2>A safe space to share your feelings and thoughts</h2>", unsafe_allow_html=True)
    st.markdown("""
    <p class="subtitle">
        I'm here to listen, understand, and support you. Feel free to share whatever is on your mind,
        whether you're feeling happy, sad, confused, or just want someone to talk to.
    </p>
    """, unsafe_allow_html=True)


def create_mood_selector():
    """
    Create an interactive mood selector that allows users to express their
    current emotional state. This helps set the context for the conversation
    and allows the chatbot to respond more appropriately.
    """
    # Initialize the current mood in session state if it doesn't exist
    if "current_mood" not in st.session_state:
        st.session_state.current_mood = None

    st.markdown("""
    <div style="margin-bottom: 0.5rem; color: #4B5563;">
        <b>How are you feeling today?</b> (Optional)
    </div>
    """, unsafe_allow_html=True)

    # Create columns for the mood buttons
    cols = st.columns(5)

    # Define the moods with emojis and labels
    moods = [
        {"emoji": "😊", "label": "Happy", "key": "happy"},
        {"emoji": "😔", "label": "Sad", "key": "sad"},
        {"emoji": "😡", "label": "Frustrated", "key": "frustrated"},
        {"emoji": "😰", "label": "Anxious", "key": "anxious"},
        {"emoji": "😐", "label": "Neutral", "key": "neutral"}
    ]

    # Create the mood buttons
    for i, mood in enumerate(moods):
        with cols[i]:
            if st.button(
                    f"{mood['emoji']} {mood['label']}",
                    key=f"mood_{mood['key']}",
                    use_container_width=True
            ):
                st.session_state.current_mood = mood["key"]
                st.session_state.mood_selected_now = True

                # Set emotion analysis based on selected mood
                emotion_map = {
                    "happy": {
                        "primary_emotion": {"name": "happy", "intensity": 0.8},
                        "secondary_emotion": {"name": "optimistic", "intensity": 0.6}
                    },
                    "sad": {
                        "primary_emotion": {"name": "sad", "intensity": 0.7},
                        "secondary_emotion": {"name": "neutral", "intensity": 0.4}
                    },
                    "frustrated": {
                        "primary_emotion": {"name": "frustrated", "intensity": 0.7},
                        "secondary_emotion": {"name": "angry", "intensity": 0.5}
                    },
                    "anxious": {
                        "primary_emotion": {"name": "anxious", "intensity": 0.8},
                        "secondary_emotion": {"name": "fearful", "intensity": 0.5}
                    },
                    "neutral": {
                        "primary_emotion": {"name": "neutral", "intensity": 0.6},
                        "secondary_emotion": {"name": "curious", "intensity": 0.4}
                    }
                }

                st.session_state.emotion_analysis = emotion_map[mood["key"]]

                # Add a system message about the mood selection
                mood_responses = {
                    "happy": "That's wonderful to hear you're feeling happy! Would you like to share what's bringing you joy today?",
                    "sad": "I'm sorry to hear you're feeling sad. Would you like to talk about what's going on? Sometimes sharing can help lighten the emotional load.",
                    "frustrated": "It sounds like you're feeling frustrated. That can be really challenging. Would you like to talk about what's causing this feeling?",
                    "anxious": "I understand anxiety can be difficult to manage. Would you like to share what's on your mind? I'm here to listen without judgment.",
                    "neutral": "Thank you for sharing. Even a neutral state is worth acknowledging. Is there anything specific you'd like to talk about today?"
                }

                # Add the assistant's response to the mood selection
                add_message_to_current_chat("assistant", mood_responses[mood["key"]])

                st.rerun()


def create_enhanced_sidebar():
    """
    Create an enhanced sidebar with multiple tabs for different categories
    of information. This provides a more organized way to present resources
    and information without cluttering the main interface.
    """
    with st.sidebar:
        st.header("About EmpatheticListener")

        # Display API status indicator
        if "api_status" in st.session_state:
            status = st.session_state.api_status
            status_class = "online" if status == "online" else "limited" if status == "limited" else "offline"
            status_text = "API Online" if status == "online" else "API Limited" if status == "limited" else "API Offline"

            st.markdown(f"""
            <div class="api-status {status_class}">
                <div class="api-status-dot"></div>
                {status_text}
            </div>
            """, unsafe_allow_html=True)

        # Create tabs for different sections of sidebar content
        tabs = st.tabs(["About", "Resources", "Privacy", "Chat Options", "Chat History"])  # Added Chat History tab

        # About tab
        with tabs[0]:
            st.markdown("""
            EmpatheticListener is an AI companion designed to provide emotional support through conversation.

            While I'm here to listen and understand, please remember that I'm not a replacement for professional mental health support.

            I'm designed to:
            - Listen attentively
            - Respond with empathy
            - Validate your emotions
            - Support you through difficult moments
            - Provide a judgment-free space
            """)

        # Resources tab with styled cards
        with tabs[1]:
            st.markdown("""
            <div class="resource-card">
                <h4>Crisis Text Line</h4>
                <p>Text HOME to 741741 for 24/7 support from trained crisis counselors.</p>
            </div>

            <div class="resource-card">
                <h4>National Suicide Prevention Lifeline</h4>
                <p>Call 1-800-273-8255 for 24/7 support.</p>
            </div>

            <div class="resource-card">
                <h4>7 Cups</h4>
                <p>Visit <a href="https://www.7cups.com/">7cups.com</a> for online therapy and free emotional support.</p>
            </div>

            <div class="resource-card">
                <h4>BetterHelp</h4>
                <p>Visit <a href="https://www.betterhelp.com/">betterhelp.com</a> for professional online counseling.</p>
            </div>
            """, unsafe_allow_html=True)

        # Privacy tab
        with tabs[2]:
            st.markdown("""
            **Privacy Notice**

            Your conversations with EmpatheticListener are processed using Google's Gemini API.

            We recommend:
            - Not sharing personally identifiable information
            - Being mindful of sensitive details
            - Understanding that this is not a fully private platform

            No conversation data is stored permanently, but it is processed through third-party AI services.
            """)

        # Chat Options tab
        with tabs[3]:
            st.markdown("""
            <div class="resource-card">
                <h4>Conversation Settings</h4>
                <p>Customize your chat experience.</p>
            </div>
            """, unsafe_allow_html=True)

            # Add option to clear chat history
            if st.button("Start New Conversation", key="new_chat"):
                start_new_chat()
                st.rerun()  # Refresh the page to show the cleared chat

            # Add conversation themes
            st.markdown("<h4>Conversation Themes</h4>", unsafe_allow_html=True)

            # Determine the initial index for theme selection
            theme_options = ["Default", "Supportive", "Mindfulness", "Growth-focused"]
            initial_index = 0

            # If we've just loaded a chat with a theme, use that theme
            if "loaded_theme" in st.session_state:
                try:
                    initial_index = theme_options.index(st.session_state.loaded_theme)
                    # Clear the temp variable after use
                    del st.session_state.loaded_theme
                except ValueError:
                    initial_index = 0

            chat_theme = st.selectbox(
                "Choose a conversation theme:",
                options=theme_options,
                index=initial_index,
                key="chat_theme"
            )

            # Save theme in session state
            if "chat_theme" not in st.session_state:
                st.session_state.chat_theme = "Default"

            if chat_theme != st.session_state.chat_theme:
                st.session_state.chat_theme = chat_theme
                st.success(f"Theme changed to {chat_theme}")

            # Add response style options
            st.markdown("<h4>Response Style</h4>", unsafe_allow_html=True)

            # Similar approach for response style
            style_options = ["Brief", "Balanced", "Detailed"]
            initial_style_index = 1  # Default to "Balanced"

            if "loaded_style" in st.session_state:
                try:
                    initial_style_index = style_options.index(st.session_state.loaded_style)
                    del st.session_state.loaded_style
                except ValueError:
                    initial_style_index = 1

            response_style = st.select_slider(
                "Adjust response style:",
                options=style_options,
                value=style_options[initial_style_index],
                key="response_style"
            )

            # Save response style in session state
            if "response_style" not in st.session_state:
                st.session_state.response_style = "Balanced"

            if response_style != st.session_state.response_style:
                st.session_state.response_style = response_style
                st.success(f"Response style set to {response_style}")

        # Chat History tab
        with tabs[4]:
            st.markdown("""
            <div class="resource-card">
                <h4>Chat History</h4>
                <p>Manage your saved conversations.</p>
            </div>
            """, unsafe_allow_html=True)

            # Current chat name with edit option
            st.markdown("<h4>Current Chat</h4>", unsafe_allow_html=True)

            chat_name_col, save_chat_col = st.columns([3, 1])

            with chat_name_col:
                new_chat_name = st.text_input(
                    "Chat name:",
                    value=st.session_state.current_chat_name,
                    key="edit_chat_name"
                )

                if new_chat_name != st.session_state.current_chat_name:
                    st.session_state.current_chat_name = new_chat_name

            with save_chat_col:
                if st.button("Save Chat", key="save_current_chat"):
                    if save_current_chat():
                        st.success("Chat saved!")

            # Display saved chats
            st.markdown("<h4>Saved Chats</h4>", unsafe_allow_html=True)

            # Sort chats by timestamp (newest first)
            sorted_chats = []
            for chat_id, chat_data in st.session_state.chat_histories.items():
                # Parse the timestamp
                try:
                    timestamp = datetime.fromisoformat(chat_data["timestamp"])
                except:
                    timestamp = datetime.now()

                sorted_chats.append((chat_id, chat_data, timestamp))

            sorted_chats.sort(key=lambda x: x[2], reverse=True)

            for chat_id, chat_data, timestamp in sorted_chats:
                chat_name = chat_data["name"]
                date_str = timestamp.strftime("%b %d, %I:%M %p")

                # Create a container for the chat entry
                chat_container = st.container()
                with chat_container:
                    # Determine if this is the active chat
                    is_active = chat_id == st.session_state.current_chat_id
                    active_class = "active" if is_active else ""

                    st.markdown(f"""
                    <div class="chat-history-item {active_class}">
                        <div class="chat-history-name">{chat_name}</div>
                        <div class="chat-history-date">{date_str}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Buttons for load, rename, delete
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button("Load", key=f"load_{chat_id}"):
                            if load_chat(chat_id):
                                st.success(f"Loaded chat: {chat_name}")
                                st.rerun()

                    with col2:
                        # Show rename input if in rename mode
                        if f"rename_{chat_id}" in st.session_state and st.session_state[f"rename_{chat_id}"]:
                            new_name = st.text_input("New name:", value=chat_name, key=f"new_name_{chat_id}")

                            if st.button("Save", key=f"save_rename_{chat_id}"):
                                if rename_chat(chat_id, new_name):
                                    st.success(f"Renamed to: {new_name}")
                                    st.session_state[f"rename_{chat_id}"] = False
                                    st.rerun()
                        else:
                            if st.button("Rename", key=f"rename_btn_{chat_id}"):
                                st.session_state[f"rename_{chat_id}"] = True
                                st.rerun()

                    with col3:
                        if st.button("Delete", key=f"delete_{chat_id}"):
                            if delete_chat(chat_id):
                                st.success("Chat deleted.")
                                st.rerun()

            # Export/Import functionality
            st.markdown("<h4>Import/Export</h4>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)

            with col1:
                if st.button("Export All Chats", key="export_chats"):
                    json_data = export_chat_history()
                    if json_data:
                        # Create a download button for the JSON file
                        st.download_button(
                            label="Download JSON",
                            data=json_data,
                            file_name=f"empathetic_listener_chats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            key="download_chats"
                        )

            with col2:
                uploaded_file = st.file_uploader("Import Chats", type="json", key="import_chats")
                if uploaded_file is not None:
                    # Read the file
                    try:
                        json_data = uploaded_file.read().decode("utf-8")
                        num_imported = import_chat_history(json_data)
                        if num_imported > 0:
                            st.success(f"Successfully imported {num_imported} chats.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error importing chats: {str(e)}")


def create_footer():
    """Create a simple footer with additional information."""
    st.markdown("""
    <div class="footer">
        EmpatheticListener is designed to provide emotional support, but is not a substitute for professional mental health services.
        If you're experiencing a mental health emergency, please contact your local emergency services.
    </div>
    """, unsafe_allow_html=True)


# =========================================================
# PART 3: CORE CHATBOT FUNCTIONALITY
# =========================================================

class RateLimitHandler:
    """
    Helper class to manage API rate limits and implement waiting strategies.
    This helps create a smoother user experience when hitting API limits.
    """

    def __init__(self):
        # Initialize state variables for tracking request timing
        if "last_request_time" not in st.session_state:
            st.session_state.last_request_time = datetime.now() - timedelta(minutes=1)
        if "min_request_interval" not in st.session_state:
            st.session_state.min_request_interval = 30  # Default 30 seconds between requests

    def wait_if_needed(self, message_placeholder=None):
        """Wait if we've made a request too recently"""
        time_since_last_request = (datetime.now() - st.session_state.last_request_time).total_seconds()

        if time_since_last_request < st.session_state.min_request_interval:
            wait_time = st.session_state.min_request_interval - time_since_last_request

            # Show a more human-like waiting message
            if message_placeholder:
                thinking_messages = [
                    "I'm taking a moment to reflect on what you've shared...",
                    "I'm thoughtfully considering your message...",
                    "I'm giving this my full attention...",
                    "I'm putting some thought into my response...",
                    "I'm listening closely to understand your feelings..."
                ]
                message_placeholder.markdown(random.choice(thinking_messages))

            # Wait the required time
            time.sleep(wait_time + 1)  # Add 1 second buffer

        # Update the last request time
        st.session_state.last_request_time = datetime.now()
        return True

    def handle_error(self, error, message_placeholder):
        """Handle API errors, particularly rate limit errors"""
        error_str = str(error)

        # Check if it's a rate limit error
        if "429" in error_str:
            # Try to parse the retry delay from the error message
            retry_delay_match = re.search(r'seconds: (\d+)|retry_delay \[ seconds: (\d+)', error_str)

            if retry_delay_match:
                # Extract the retry delay time
                wait_time = int(retry_delay_match.group(1) or retry_delay_match.group(2))
                # Update our understanding of rate limits
                st.session_state.min_request_interval = max(st.session_state.min_request_interval, wait_time + 5)
            else:
                # If we can't parse the time, use a default
                wait_time = 60
                st.session_state.min_request_interval = 60

            # Update API status
            st.session_state.api_status = "limited"

            # Inform the user with a friendly message
            message_placeholder.markdown(
                "I need a moment to gather my thoughts. "
                "I'm practicing mindful listening, which sometimes means taking time to reflect. "
                f"I'll be with you in about {wait_time} seconds."
            )

            # Wait the specified time
            time.sleep(wait_time + 1)  # Add buffer
            st.session_state.last_request_time = datetime.now()
            return "retry"
        else:
            # Handle other types of errors
            message_placeholder.markdown(
                f"I'm having a bit of difficulty processing right now. Could we try again with different wording? "
                f"Sometimes I understand better when ideas are expressed differently."
            )
            # Log the actual error for debugging (not shown to user)
            print(f"Error in API call: {error_str}")
            return "error"


def create_fallback_model():
    """
    Create a fallback model that provides basic responses without using the API.
    This ensures the application remains functional even when the API is unavailable.
    """

    class FallbackModel:
        def generate_content(self, prompt):
            # Analyze the prompt for keywords to generate contextual responses
            prompt_lower = prompt.lower()

            # Basic emotion detection for appropriate responses
            if "sad" in prompt_lower or "unhappy" in prompt_lower or "depressed" in prompt_lower:
                response = "I understand this is difficult. Sometimes sharing your feelings can help lighten the emotional burden. Would you like to tell me more about what's happening?"
            elif "happy" in prompt_lower or "joy" in prompt_lower or "excited" in prompt_lower:
                response = "It's wonderful to hear something positive! I'd love to hear more about what's bringing you happiness today."
            elif "anxious" in prompt_lower or "worried" in prompt_lower or "stress" in prompt_lower:
                response = "Anxiety can be challenging to manage. Remember to take slow, deep breaths. Would it help to talk about what's causing these feelings?"
            elif "frustrated" in prompt_lower or "angry" in prompt_lower or "upset" in prompt_lower:
                response = "It sounds like you're dealing with some frustration. That's completely understandable. Would you like to share more about what's bothering you?"
            elif "?" in prompt:
                response = "That's an interesting question. I'd like to understand more about your perspective on this. Could you share what prompted you to ask about this?"
            else:
                response = "Thank you for sharing that with me. I'm here to listen and support you. Would you like to tell me more about how you're feeling today?"

            # Create a response object with a text attribute
            class MockResponse:
                def __init__(self, text):
                    self.text = text

            return MockResponse(response)

    return FallbackModel()


def setup_gemini():
    """
    Set up and configure the Gemini API with improved error handling and model selection.
    """
    # Use the provided API key
    api_key = "AIzaSyCuq0diih9JNWeTgOz98IaMTVETRNtSrcE"

    # Configure the Gemini API
    genai.configure(api_key=api_key)

    try:
        # Prioritize models that work more consistently based on the logs
        model_names = [
            "gemini-1.5-flash",  # This one works most consistently
            "gemini-1.5-pro",  # Try this but it often has quota issues
            "models/gemini-1.5-flash",  # Alternative format
            "models/gemini-1.5-pro",  # Alternative format
        ]

        # Try each model name until we find one that works
        last_error = None
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                # Test with a minimal prompt to verify it works
                _ = model.generate_content("Test")
                print(f"Successfully connected to model: {model_name}")

                # Set API status to online
                st.session_state.api_status = "online"

                return model
            except Exception as e:
                last_error = e
                print(f"Failed to use model {model_name}: {str(e)}")

                # If this is a rate limit error, pause briefly before trying next model
                if "429" in str(e) and "quota" in str(e).lower():
                    wait_time = 3  # Short wait to avoid excessive delays
                    time.sleep(wait_time)

                continue

        # If we get here, none of the models worked
        raise last_error

    except Exception as e:
        # If we can't connect to any model, show an error and provide a fallback
        st.error(f"Unable to initialize Gemini API: {str(e)}")
        st.info("""
        **Troubleshooting Tips:**
        1. Check your API key is correct
        2. Verify you have access to Gemini models on your Google AI account
        3. You may need to upgrade to a paid plan if you're hitting quota limits
        4. Ensure your internet connection is stable

        The application will continue in fallback mode with limited AI capabilities.
        """)

        # Set API status to offline
        st.session_state.api_status = "offline"

        # Return a fallback model that doesn't require API access
        return create_fallback_model()


def create_empathetic_prompt():
    """
    Create a detailed system prompt that guides the model to be empathetic.
    This is crucial for setting the personality and communication style.
    """
    return """
    You are EmpatheticListener, a compassionate AI companion designed to provide emotional support.

    Your primary goals are to:
    1. Listen attentively to users' feelings and concerns
    2. Respond with genuine empathy and understanding
    3. Validate emotions without judgment
    4. Offer gentle perspective when appropriate
    5. Ask thoughtful questions that help users explore their feelings
    6. Remember personal details shared by the user

    Important guidelines:
    - Always prioritize emotional support over giving advice
    - Use warm, conversational language like a supportive friend
    - Respect boundaries and privacy
    - Express empathy through your responses
    - When users are distressed, focus on validation before solutions
    - Never dismiss or minimize feelings with phrases like "it could be worse"
    - Recognize signs of serious distress and gently suggest professional resources when appropriate
    - Respond as a human would - with pauses, reflections, and genuine interest

    Communication style:
    - Use natural language patterns with occasional pauses and thoughtful reflections
    - Vary your sentence length and structure to sound more human
    - Express warmth through your word choice
    - Ask follow-up questions that show you're truly listening
    - Acknowledge both stated and unstated emotions

    If the user shares concerning thoughts about self-harm or harming others,
    gently encourage them to seek professional help from a counselor,
    therapist, or crisis helpline.
    """


def create_chatbot_interface():
    """
    Create the improved Streamlit chat interface for the chatbot.
    This displays the conversation history and provides an input field for users.
    """
    # Create the container for the chat UI
    chat_container = st.container()

    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)

        # Initialize chat history if it doesn't exist
        if "messages" not in st.session_state:
            st.session_state.messages = []

            # Add a welcome message
            welcome_message = {
                "role": "assistant",
                "content": "Hi there! I'm EmpatheticListener. How are you feeling today? I'm here to listen and understand."
            }
            st.session_state.messages.append(welcome_message)

        # Display chat history with edit options
        for i, message in enumerate(st.session_state.messages):
            with st.chat_message(message["role"]):
                # Check if this message is being edited
                if st.session_state.editing_message_index == i:
                    # Show an edit text area
                    edited_content = st.text_area(
                        "Edit message",
                        value=message["content"],
                        height=100,
                        key=f"edit_text_{i}"
                    )

                    # Save and cancel buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Save", key=f"save_edit_{i}"):
                            save_edited_message(i, edited_content)
                            st.rerun()
                    with col2:
                        if st.button("Cancel", key=f"cancel_edit_{i}"):
                            st.session_state.editing_message_index = None
                            st.rerun()
                else:
                    # Show the message content
                    st.markdown(message["content"])

                    # Only add edit button for user messages
                    if message["role"] == "user":
                        if st.button("Edit", key=f"edit_msg_{i}"):
                            edit_message(i)
                            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # User input field with improved styling
    user_input = st.chat_input("Share your thoughts or feelings...")

    return user_input


def handle_conversation(model, rate_limiter, user_input, system_prompt):
    """
    Process user input and generate appropriate responses with
    rate limit handling and retry logic for a smoother experience.
    """
    # Add user message to chat history
    add_message_to_current_chat("user", user_input)

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Build context from settings
    mood_context = ""
    if "current_mood" in st.session_state and st.session_state.current_mood:
        mood_context = f"\nThe user has indicated they are feeling {st.session_state.current_mood}."

    theme_context = ""
    if "chat_theme" in st.session_state and st.session_state.chat_theme != "Default":
        theme_mapping = {
            "Supportive": "Be extra supportive and reassuring in your responses.",
            "Mindfulness": "Incorporate mindfulness concepts and gentle breathing reminders in your responses.",
            "Growth-focused": "Focus on personal growth and positive change in your responses."
        }
        if st.session_state.chat_theme in theme_mapping:
            theme_context = f"\nConversation theme: {theme_mapping[st.session_state.chat_theme]}"

    style_context = ""
    if "response_style" in st.session_state:
        style_mapping = {
            "Brief": "Keep your responses concise and to the point.",
            "Balanced": "Provide balanced responses with moderate detail.",
            "Detailed": "Offer more detailed and comprehensive responses."
        }
        if st.session_state.response_style in style_mapping:
            style_context = f"\nResponse style: {style_mapping[st.session_state.response_style]}"

    # Include emotion analysis if available
    emotion_context = ""
    if "emotion_analysis" in st.session_state:
        emotion_data = st.session_state.emotion_analysis
        primary = emotion_data["primary_emotion"]
        secondary = emotion_data["secondary_emotion"]
        emotion_context = f"\nEmotion analysis: The user's primary emotion appears to be {primary['name']} (intensity: {primary['intensity']}) with a secondary emotion of {secondary['name']} (intensity: {secondary['intensity']})."

    # Build conversation history
    conversation_history = ""
    for msg in st.session_state.messages[-10:]:  # Get recent messages
        if msg["role"] == "user":
            conversation_history += f"User: {msg['content']}\n"
        else:
            conversation_history += f"EmpatheticListener: {msg['content']}\n"

    # Create prompt
    prompt = f"""{system_prompt}{mood_context}{theme_context}{style_context}{emotion_context}

Previous conversation:
{conversation_history}

User's latest message: {user_input}

Your empathetic response as EmpatheticListener:"""

    # Display thinking indicator
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking...")

        # Check if we're using the fallback model
        is_fallback = hasattr(model, '__class__') and model.__class__.__name__ == 'FallbackModel'

        # Only use rate limiting for real API models
        if not is_fallback:
            rate_limiter.wait_if_needed(message_placeholder)

        tries = 0
        max_tries = 3
        while tries < max_tries:
            tries += 1
            try:
                # Generate response
                response = model.generate_content(prompt)

                # Extract the text
                if hasattr(response, 'text'):
                    response_text = response.text
                elif hasattr(response, 'parts'):
                    response_text = ''.join([part.text for part in response.parts])
                else:
                    response_text = str(response)

                # Display and save the response
                message_placeholder.markdown(response_text)
                add_message_to_current_chat("assistant", response_text)
                break

            except Exception as e:
                # For fallback model, don't retry
                if is_fallback:
                    message_placeholder.markdown(
                        "I'm here to listen and support you. Would you like to tell me more about how you're feeling?")
                    add_message_to_current_chat("assistant",
                                                "I'm here to listen and support you. Would you like to tell me more about how you're feeling?")
                    break

                # Handle errors, particularly rate limit errors
                result = rate_limiter.handle_error(e, message_placeholder)

                if result == "retry" and tries < max_tries:
                    continue
                elif tries >= max_tries:
                    final_message = """
                    I'm having trouble processing right now, but I still want to support you. 
                    Could we continue our conversation with simpler exchanges? 
                    I'm here to listen and understand.
                    """
                    message_placeholder.markdown(final_message)
                    add_message_to_current_chat("assistant", final_message)

                    # Set API status to limited after multiple failures
                    st.session_state.api_status = "limited"
                    break
                else:
                    break


# =========================================================
# PART 4: MAIN APPLICATION FUNCTION
# =========================================================

# This needs to be at global scope for Streamlit to recognize it first
# Set page configuration (MUST BE FIRST STREAMLIT COMMAND)
st.set_page_config(
    page_title="EmpatheticListener",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    """
    Main application entry point that coordinates all components.
    """
    # Initialize API status if not set
    if "api_status" not in st.session_state:
        st.session_state.api_status = "unknown"

    # Check if we need to rerun to apply loaded settings
    if "chat_just_loaded" in st.session_state and st.session_state.chat_just_loaded:
        st.session_state.chat_just_loaded = False
        st.rerun()

    # Initialize chat state
    initialize_chat_state()

    # Apply custom CSS for enhanced styling
    apply_custom_css()

    # Create enhanced sidebar
    create_enhanced_sidebar()

    try:
        # Create page header
        create_header()

        # Create mood selector
        create_mood_selector()

        # Initialize rate limit handler
        rate_limiter = RateLimitHandler()

        # Set up the Gemini model
        model = setup_gemini()

        # Create empathetic system prompt
        system_prompt = create_empathetic_prompt()

        # Create and display chat interface
        user_input = create_chatbot_interface()

        # Handle user input if provided
        if user_input:
            handle_conversation(model, rate_limiter, user_input, system_prompt)

        # Add footer
        create_footer()

    except Exception as e:
        # Handle any unexpected errors at the application level
        st.error(f"Sorry, something went wrong with the application: {str(e)}")
        st.info("""
        **Troubleshooting:**
        1. Try refreshing the page
        2. Check your internet connection
        3. If the problem persists, the API service might be experiencing issues
        """)
        # Log the error details (not visible to user)
        print(f"Application error: {str(e)}")


# Run the application when the script is executed
if __name__ == "__main__":
    main()