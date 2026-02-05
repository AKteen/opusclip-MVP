import tempfile
import os
import shutil
import atexit
from pathlib import Path

class TempFileManager:
    def __init__(self):
        self.temp_dirs = []
        self.temp_files = []
        atexit.register(self.cleanup_all)
    
    def create_temp_dir(self, prefix="opus_"):
        """Create temporary directory with auto-cleanup"""
        temp_dir = tempfile.mkdtemp(prefix=prefix)
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def add_temp_file(self, file_path):
        """Track temp file for cleanup"""
        self.temp_files.append(file_path)
    
    def cleanup_file(self, file_path):
        """Clean up specific file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            if file_path in self.temp_files:
                self.temp_files.remove(file_path)
        except:
            pass
    
    def cleanup_all(self):
        """Clean up all temp files and directories"""
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass
        
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except:
                pass
        
        self.temp_files.clear()
        self.temp_dirs.clear()
    
    def cleanup_old_files(self, directory, max_age_hours=24):
        """Clean up old files on startup"""
        try:
            current_time = os.path.getmtime('.')
            for file_path in Path(directory).glob('*'):
                if file_path.is_file():
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_hours * 3600:
                        os.remove(file_path)
        except:
            pass

# Global temp file manager
temp_manager = TempFileManager()