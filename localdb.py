import os
import pickle

class SimpleDB:
    def __init__(self, filename='data.bin'):
        self.filename = filename
        self._data = self._load()

    def _load(self):
        """Load data from the file, or initialize an empty dict if file doesn't exist."""
        if not os.path.exists(self.filename):
            # create a database with default values
            self._save({
                'browser': 'edge',
                'ca': '',
                'classname': '',
                'path': '',
                'video_resolution': '720p',
                'sl': 'English'
            })
        with open(self.filename, 'rb') as f:
            return pickle.load(f)

    def _save(self, data):
        """Save current data to file."""
        with open(self.filename, 'wb') as f:
            pickle.dump(data, f)

    def create(self, key, value):
        """Create a new key-value pair. Raises error if key exists."""
        if key in self._data:
            raise KeyError(f"Key '{key}' already exists.")
        self._data[key] = value
        self._save(self._data)

    def read(self, key):
        """Read the value for a given key. Returns None if not found."""
        return self._data.get(key, None)

    def update(self, key, value):
        """Update the value for an existing key."""
        if key not in self._data:
            raise KeyError(f"Key '{key}' not found.")
        self._data[key] = value
        self._save(self._data)

    def delete(self, key):
        """Delete a key-value pair."""
        if key in self._data:
            del self._data[key]
            self._save(self._data)
        else:
            raise KeyError(f"Key '{key}' not found.")

    def get_full_db(self):
        """Return the full dictionary."""
        return dict(self._data)
    
if __name__ == '__main__':
    db = SimpleDB()

    # db.create('username', 'alice')
    # print(db.read('username'))  # alice

    # db.update('username', 'bob')
    # print(db.read('username'))  # bob

    # db.delete('username')
    # print(db.read('username'))  # None

    print(db.get_full_db())        # {}
