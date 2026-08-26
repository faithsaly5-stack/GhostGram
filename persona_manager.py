import os
import glob
from config import Config

class PersonaManager:
    def __init__(self, dir_path="personas"):
        self.dir_path = dir_path
        self.personas = {}
        self.load_personas()

    def load_personas(self):
        """Loads personas from the .txt files in the personas directory."""
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)
            # Create a default normal.txt if folder was just created
            with open(os.path.join(self.dir_path, "normal.txt"), "w", encoding="utf-8") as f:
                f.write("تو خودت «{owner_name}» هستی...")

        for file_path in glob.glob(os.path.join(self.dir_path, "*.txt")):
            filename = os.path.basename(file_path)
            persona_name = os.path.splitext(filename)[0].lower()
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.personas[persona_name] = f.read().strip()
            except Exception as e:
                print(f"⚠️ Error loading persona {filename}: {e}")

        # Ensure fallback exists
        if "normal" not in self.personas:
            self.personas["normal"] = "تو خودت «{owner_name}» هستی..."

    def get_prompt(self, command_name: str) -> str:
        """Returns the prompt for a given persona command name, falling back to 'normal' with dynamic identity variables."""
        command_name = str(command_name).lower().strip()
        raw_prompt = self.personas.get(command_name, self.personas.get("normal", "تو خودت «{owner_name}» هستی..."))
        
        # Inject all identity configurations from .env
        prompt = (
            raw_prompt
            .replace("{owner_name}", Config.OWNER_NAME)
            .replace("{owner_bio}", Config.OWNER_BIO)
            .replace("{owner_website}", Config.OWNER_WEBSITE)
            .replace("{owner_services}", Config.OWNER_SERVICES)
            .replace("{owner_interests}", Config.OWNER_INTERESTS)
        )
        return prompt

    def get_all_persona_names(self):
        """Returns a list of all registered persona commands."""
        return list(self.personas.keys())

# Singleton instance
persona_manager = PersonaManager(os.path.join(Config.PROFILE_DIR, "personas"))
