import os
from ..config.logger import logger

class FileUtils:
    @staticmethod
    def ensure_directory(directory_path):
        """
        Ensure a directory exists, create if it doesn't
        
        Args:
            directory_path (str): Path to the directory
            
        Returns:
            bool: True if directory exists or was created successfully
        """
        try:
            if not os.path.exists(directory_path):
                os.makedirs(directory_path)
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {directory_path}: {str(e)}")
            return False

    @staticmethod
    def save_file(file_path, content, mode='w', encoding=None):
        """
        Save content to a file with proper error handling
        
        Args:
            file_path (str): Path to save the file
            content: Content to write to file
            mode (str): File open mode ('w' for text, 'wb' for binary)
            encoding (str): File encoding (for text files)
            
        Returns:
            bool: True if file was saved successfully
        """
        try:
            # Ensure the directory exists
            directory = os.path.dirname(file_path)
            FileUtils.ensure_directory(directory)
            
            # Write the file
            with open(file_path, mode=mode, encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Failed to save file {file_path}: {str(e)}")
            return False 