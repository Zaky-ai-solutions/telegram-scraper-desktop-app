# 📥 Telegram Media Downloader (GUI)
A Python desktop application with a Tkinter-based GUI to search, download, and organize images and archives from Telegram chats, channels, or groups using the Telethon library.
Supports config saving/loading, session authentication, search queries, and concurrent downloads with progress tracking.
![Telegram Media Downloader Screenshot](telegram%20bot.PNG)
### ✨ Features
- Easy-to-use GUI built with Tkinter.

- Secure Telegram login with session file storage.

- Save & load configuration for quick reuse.

- Search and download media from multiple chats/channels.

- Concurrent downloads with adjustable limits.

- Customizable chunk size for large files.

- Separate save locations for images and archives.

- Real-time progress updates with logs and statistics.

- Error handling for Telegram API limits and connection issues.

### 📦 Requirements
- Python 3.8+

- Pip packages:

``` bash
pip install telethon
```

For GUI components, tkinter comes pre-installed with most Python distributions.

### ⚙️ Installation
Clone or download this repository:

```bash
git clone https://github.com/yourusername/telegram-media-downloader.git
cd telegram-media-downloader
```
Install dependencies:

```bash
pip install telethon
```
Run the app:

```bash
python telegram_downloader.py
```
### 🖥 Usage Guide
**1️⃣ Setup API Credentials**

- Get your API ID and API Hash from my.telegram.org.

- Enter them in the "Telegram Configuration" section.

**2️⃣ Session File**

- Choose a .session file path where Telegram login details will be saved.

**3️⃣ Login**

- Click "Setup Session".

- Enter the verification code sent to your Telegram.

- If your account has two-step verification enabled, you’ll also need to enter your password.

**4️⃣ Performance Settings**

- Set Max Concurrent Downloads (default: 3).

- Set Chunk Size in MB for file downloads.

**5️⃣ Download Paths**

- Choose folders for Images and Archives.

**6️⃣ Search Configuration**

- Enter the search keyword or code to find matching media.

**7️⃣ Start Download**

- Click "Start Download" to begin.

The app will search for images matching your query, download them, and attempt to find corresponding archive files.

### 📊 Statistics

During downloads, the app displays:

- Images downloaded

- Archives downloaded

- Failed downloads

### 🔧 Configuration File
The app saves settings to config.json:

```json
{
    "api_id": "123456",
    "api_hash": "your_api_hash",
    "phone_number": "+1234567890",
    "session_path": "path/to/session",
    "search_query": "example",
    "images_path": "downloads/images",
    "archives_path": "downloads/archives",
    "max_concurrent_downloads": 3,
    "chunk_size": 1048576
}
```
### 🛡 Error Handling
- Session expired → Re-run "Setup Session".

- FloodWaitError → App waits automatically for Telegram rate limit cooldown.

- File already exists → Skips downloading to save time.

- Invalid credentials → Recheck API ID, API Hash, and phone number.

### 📜 License
This project is licensed under the MIT License — feel free to modify and share.
