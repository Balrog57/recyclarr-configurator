import sys
import logging
import json
from pathlib import Path
from PySide6.QtCore import QThread, Signal

# Add parent directory to sys.path to allow importing scripts from root
sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    from utils import templates_extractor
    from utils import trash_cf_extractor
except ImportError as e:
    logging.error(f"Failed to import extractor scripts: {e}")

logger = logging.getLogger(__name__)

class SyncWorker(QThread):
    """
    Worker thread to handle background data synchronization.
    Wraps templates_extractor.py and trash_cf_extractor.py.
    """
    progress = Signal(str)      # Emits status messages
    finished = Signal()         # Emits when all tasks are done
    data_ready = Signal(dict, dict) # Emits (templates_data, custom_formats_data)
    error = Signal(str)         # Emits error messages

    def run(self):
        """Executes the extraction process."""
        try:
            self.progress.emit("Initializing extraction...")
            
            # --- Extract Templates ---
            self.progress.emit("Extracting Recyclarr templates...")
            
            # Initialize Client and Extractor from templates_extractor
            try:
                # instantiate classes designed in the scripts
                client_tmpl = templates_extractor.GitHubClient()
                extractor_tmpl = templates_extractor.ConfigTemplatesExtractor(client_tmpl)
                
                # Perform extraction
                templates_data = extractor_tmpl.extract_all()
                self._save_json(templates_data, "templates.json")
                self.progress.emit("Templates extracted successfully.")
                
            except Exception as e:
                logger.exception("Error extracting templates")
                self.error.emit(f"Error extracting templates: {str(e)}")
                return # Stop processing on heavy error? Or continue? Let's stop to be safe.

            # --- Extract Custom Formats ---
            self.progress.emit("Extracting TRaSH Custom Formats...")
            
            try:
                # Instantiate classes from trash_cf_extractor
                # Note: GitHubClient logic is duplicated in both scripts, better to use separate instances
                client_cf = trash_cf_extractor.GitHubClient() 
                description_extractor = trash_cf_extractor.DescriptionExtractor(client_cf)
                extractor_cf = trash_cf_extractor.CustomFormatExtractor(client_cf, description_extractor)
                
                # Perform extraction
                formats_raw = extractor_cf.extract_all()
                
                # Convert to dict format expected by generating function
                cf_data = trash_cf_extractor.generate_output(formats_raw)
                self._save_json(cf_data, "custom_formats.json")
                self.progress.emit("Custom Formats extracted successfully.")
                
            except Exception as e:
                logger.exception("Error extracting custom formats")
                self.error.emit(f"Error extracting Custom Formats: {str(e)}")
                return

            # --- Finalize ---
            self.progress.emit("Synchronization complete.")
            self.data_ready.emit(templates_data, cf_data)
            self.finished.emit()

        except Exception as e:
            logger.exception("Critical worker error")
            self.error.emit(f"Critical error: {str(e)}")

    def _save_json(self, data, filename):
        """Helper to save JSON data to disk."""
        try:
            # Resolve to 'data' directory relative to project root
            root_path = Path(__file__).resolve().parent.parent
            data_dir = root_path / "data"
            data_dir.mkdir(exist_ok=True) # Ensure data dir exists
            file_path = data_dir / filename
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {filename} to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save {filename}: {e}")
            # We don't necessarily want to fail the whole process if save fails but data is in memory
            # but usually persistence is desired.
