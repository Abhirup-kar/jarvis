import unittest
import tempfile
from pathlib import Path
from core.memory import ConversationMemory

class TestConversationMemory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_chat.db"
        
        # Monkeypatch memory path
        self.memory = ConversationMemory()
        self.memory.db_path = self.db_path
        self.memory._init_db()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_add_and_retrieve_messages(self):
        self.memory.add_message("user", "Hello JARVIS")
        self.memory.add_message("assistant", "Greetings, Sir. How may I assist you?")

        history = self.memory.get_recent_history(limit=5)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[0]["content"], "Hello JARVIS")
        self.assertEqual(history[1]["role"], "assistant")
        self.assertEqual(history[1]["content"], "Greetings, Sir. How may I assist you?")

    def test_history_limit(self):
        for i in range(10):
            self.memory.add_message("user", f"Message {i}")

        history = self.memory.get_recent_history(limit=3)
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]["content"], "Message 7")
        self.assertEqual(history[1]["content"], "Message 8")
        self.assertEqual(history[2]["content"], "Message 9")

if __name__ == "__main__":
    unittest.main()

