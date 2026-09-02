import os
import glob
import re
from config import Config

class PersonaManager:
    def __init__(self, dir_path="personas"):
        self.dir_path = dir_path
        self.personas = {}
        self.load_personas()

    def load_personas(self):
        """Loads personas from the .txt files in the personas directory.
        Dynamically prepends normal.txt to all variant personas."""
        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path)
            # Create a default normal.txt if folder was just created
            with open(os.path.join(self.dir_path, "normal.txt"), "w", encoding="utf-8") as f:
                f.write("تو خودت «{owner_first_name} {owner_last_name}» هستی...")

        self.personas.clear()
        
        # 1. Load the master 'normal' persona first
        normal_path = os.path.join(self.dir_path, "normal.txt")
        normal_content = ""
        if os.path.exists(normal_path):
            try:
                with open(normal_path, "r", encoding="utf-8") as f:
                    normal_content = f.read().strip()
            except Exception as e:
                print(f"⚠️ Error loading master persona normal.txt: {e}")
        
        self.personas["normal"] = normal_content or "تو خودت «{owner_first_name} {owner_last_name}» هستی..."
        
        # 2. Load all other personas and prepend the normal content if they are variants
        for file_path in glob.glob(os.path.join(self.dir_path, "*.txt")):
            filename = os.path.basename(file_path)
            persona_name = os.path.splitext(filename)[0].lower()
            
            if persona_name == "normal":
                continue
                
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                
                is_standalone = persona_name == "assistant" or "[STANDALONE]" in content.upper()
                
                # Prepend master rules to variants
                if not is_standalone:
                    content = self.personas["normal"] + "\n\n" + content
                else:
                    # Remove the standalone tag if present so it doesn't leak into the prompt
                    content = re.sub(r'(?i)\[STANDALONE\]\s*', '', content).strip()
                    
                self.personas[persona_name] = content
            except Exception as e:
                print(f"⚠️ Error loading persona {filename}: {e}")

    def get_prompt(self, command_name: str) -> str:
        """Returns the prompt for a given persona command name, falling back to 'normal' with dynamic identity variables."""
        self.load_personas() # Dynamically reload to instantly catch new or edited persona files
        command_name = str(command_name).lower().strip()
        raw_prompt = self.personas.get(command_name, self.personas.get("normal", "تو خودت «{owner_name}» هستی..."))
        
        # Inject all identity configurations from .env
        prompt = (
            raw_prompt
            .replace("{owner_first_name}", Config.OWNER_FIRST_NAME)
            .replace("{owner_last_name}", Config.OWNER_LAST_NAME)
            .replace("{owner_bio}", Config.OWNER_BIO)
            .replace("{owner_website}", Config.OWNER_WEBSITE)
            .replace("{owner_services}", Config.OWNER_SERVICES)
            .replace("{owner_interests}", Config.OWNER_INTERESTS)
        )
        return prompt

    def get_all_persona_names(self):
        """Returns a list of all registered persona commands."""
        self.load_personas() # Ensure list is up to date
        return list(self.personas.keys())

# Singleton instance
persona_manager = PersonaManager(os.path.join(Config.PROFILE_DIR, "personas"))
