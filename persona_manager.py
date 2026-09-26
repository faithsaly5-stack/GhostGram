import os
import glob
import re
import time
from config import Config

STANDALONE_TAG_REGEX = re.compile(r'\[\s*STANDALONE\s*\]', re.IGNORECASE)

class PersonaManager:
    def __init__(self, dir_path="personas"):
        self.dir_path = dir_path
        self.personas = {}
        self.standalone_personas = set()
        self._last_load_time = 0
        self.load_personas()

    def load_personas(self, force: bool = False):
        """Loads personas from the .txt files in the personas directory.
        Dynamically prepends normal.txt to all variant personas."""
        now = time.time()
        if not force and (now - getattr(self, "_last_load_time", 0) < 2.0):
            return
        self._last_load_time = now

        if not os.path.exists(self.dir_path):
            os.makedirs(self.dir_path, exist_ok=True)

        # Synchronize persona templates from root 'personas/' into profile directory if separate
        if os.path.exists("personas") and os.path.abspath(self.dir_path) != os.path.abspath("personas"):
            import shutil
            for p in glob.glob(os.path.join("personas", "*.txt")):
                filename = os.path.basename(p)
                dest = os.path.join(self.dir_path, filename)
                if not os.path.exists(dest):
                    try:
                        shutil.copy2(p, dest)
                    except Exception as e:
                        print(f"⚠️ Error copying template persona {filename}: {e}")

        existing_files = glob.glob(os.path.join(self.dir_path, "*.txt"))
        if not existing_files:
            # Create a default normal.txt if folder was just created and no templates exist
            with open(os.path.join(self.dir_path, "normal.txt"), "w", encoding="utf-8") as f:
                f.write("تو خودت «{owner_first_name} {owner_last_name}» هستی...")

        self.personas.clear()
        self.standalone_personas.clear()
        
        # 1. Load the master 'normal' persona first
        normal_path = os.path.join(self.dir_path, "normal.txt")
        normal_content = ""
        if os.path.exists(normal_path):
            try:
                with open(normal_path, "r", encoding="utf-8-sig") as f:
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
                with open(file_path, "r", encoding="utf-8-sig") as f:
                    content = f.read().strip()
                
                is_standalone = persona_name == "assistant" or bool(STANDALONE_TAG_REGEX.search(content))
                
                # Prepend master rules to variants
                if not is_standalone:
                    content = self.personas["normal"] + "\n\n" + content
                else:
                    # Remove the standalone tag if present so it doesn't leak into the prompt
                    content = STANDALONE_TAG_REGEX.sub('', content).strip()
                    self.standalone_personas.add(persona_name)
                    
                self.personas[persona_name] = content
            except Exception as e:
                print(f"⚠️ Error loading persona {filename}: {e}")

    def is_standalone(self, command_name: str) -> bool:
        """Returns True if the persona is marked with [STANDALONE] or is the built-in assistant."""
        self.load_personas()
        command_name = str(command_name).lower().strip()
        return command_name in self.standalone_personas or command_name == "assistant"

    def get_prompt(self, command_name: str) -> str:
        """Returns the prompt for a given persona command name, falling back to 'normal' with dynamic identity variables."""
        self.load_personas() # Dynamically reload to instantly catch new or edited persona files
        command_name = str(command_name).lower().strip()
        raw_prompt = self.personas.get(command_name, self.personas.get("normal", "تو خودت «{owner_name}» هستی..."))
        
        # Inject all identity configurations from .env
        owner_full_name = f"{Config.OWNER_FIRST_NAME} {Config.OWNER_LAST_NAME}".strip() or Config.OWNER_FIRST_NAME
        prompt = (
            raw_prompt
            .replace("{owner_name}", owner_full_name)
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
