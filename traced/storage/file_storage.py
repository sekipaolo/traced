import os
import json
import threading

class FileStorage:
    """
    A thread-safe file-based storage system for key-value data.

    Supports basic CRUD operations with file-based persistence.
    """

    def __init__(self, base_path='./data', namespace='default'):
        """
        Initialize the file storage with a base path and namespace.

        Args:
            base_path (str): Base directory for storing files
            namespace (str): Namespace to segregate different storage contexts
        """
        self.base_path = os.path.abspath(base_path)
        self.namespace = namespace
        self._lock = threading.Lock()

        # Ensure base directory exists
        os.makedirs(os.path.join(self.base_path, self.namespace), exist_ok=True)

    def _get_file_path(self, key):
        """
        Generate the full file path for a given key.

        Args:
            key (str): Storage key

        Returns:
            str: Full file path for the key
        """
        safe_key = ''.join(c for c in key if c.isalnum() or c in '_-')
        return os.path.join(self.base_path, self.namespace, f"{safe_key}.json")

    def set(self, key, value):
        """
        Store a value for a given key.

        Args:
            key (str): Storage key
            value (Any): Value to store
        """
        file_path = self._get_file_path(key)
        with self._lock:
            with open(file_path, 'w') as f:
                json.dump(value, f)

    def get(self, key, default=None):
        """
        Retrieve a value for a given key.

        Args:
            key (str): Storage key
            default (Any, optional): Default value if key not found

        Returns:
            Any: Stored value or default
        """
        file_path = self._get_file_path(key)
        with self._lock:
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                return default

    def delete(self, key):
        """
        Delete a key from storage.

        Args:
            key (str): Storage key to delete
        """
        file_path = self._get_file_path(key)
        with self._lock:
            try:
                os.remove(file_path)
            except FileNotFoundError:
                pass

    def list_keys(self):
        """
        List all keys in the current namespace.

        Returns:
            list: Available keys
        """
        namespace_path = os.path.join(self.base_path, self.namespace)
        with self._lock:
            return [
                os.path.splitext(f)[0]
                for f in os.listdir(namespace_path)
                if f.endswith('.json')
            ]

    def clear(self):
        """
        Clear all data in the current namespace.
        """
        namespace_path = os.path.join(self.base_path, self.namespace)
        with self._lock:
            for filename in os.listdir(namespace_path):
                file_path = os.path.join(namespace_path, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
