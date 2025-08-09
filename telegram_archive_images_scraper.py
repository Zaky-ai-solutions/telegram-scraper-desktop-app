import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import asyncio
import json
import os
import re
from telethon import TelegramClient, errors
from pathlib import Path
import time
import logging

# Set up logging to help with debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TelegramDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Telegram Media Downloader")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Configuration file path
        self.config_file = "config.json"
        
        # Variables for form fields
        self.api_id = tk.StringVar()
        self.api_hash = tk.StringVar()
        self.phone_number = tk.StringVar()
        self.session_path = tk.StringVar()
        self.search_query = tk.StringVar()
        self.images_path = tk.StringVar()
        self.archives_path = tk.StringVar()
        
        # Performance settings
        self.max_concurrent_downloads = tk.IntVar(value=3)
        self.chunk_size = tk.IntVar(value=1024*1024)  # 1MB chunks
        
        # Initialize client as None
        self.client = None
        self.is_running = False
        
        # Statistics
        self.downloaded_images = 0
        self.downloaded_archives = 0
        self.failed_downloads = 0
        
        self.create_widgets()
        self.load_config()
        
    def create_widgets(self):
        # Main frame with scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configuration Section
        config_frame = ttk.LabelFrame(main_frame, text="Telegram Configuration", padding=10)
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # API ID
        ttk.Label(config_frame, text="API ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.api_id, width=50).grid(row=0, column=1, columnspan=2, sticky=tk.EW, padx=(10, 0), pady=5)
        
        # API Hash
        ttk.Label(config_frame, text="API Hash:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.api_hash, width=50, show="*").grid(row=1, column=1, columnspan=2, sticky=tk.EW, padx=(10, 0), pady=5)
        
        # Phone Number
        ttk.Label(config_frame, text="Phone Number:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.phone_number, width=50).grid(row=2, column=1, columnspan=2, sticky=tk.EW, padx=(10, 0), pady=5)
        
        # Session Path
        ttk.Label(config_frame, text="Session File:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(config_frame, textvariable=self.session_path, width=40).grid(row=3, column=1, sticky=tk.EW, padx=(10, 5), pady=5)
        ttk.Button(config_frame, text="Browse", command=self.browse_session_file).grid(row=3, column=2, pady=5)
        
        # Configure column weights
        config_frame.columnconfigure(1, weight=1)
        
        # Performance Section
        perf_frame = ttk.LabelFrame(main_frame, text="Performance Settings", padding=10)
        perf_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(perf_frame, text="Max Concurrent Downloads:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Spinbox(perf_frame, from_=1, to=10, textvariable=self.max_concurrent_downloads, width=10).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(perf_frame, text="Chunk Size (MB):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.chunk_mb = tk.IntVar(value=self.chunk_size.get() // (1024*1024))
        chunk_spin = ttk.Spinbox(perf_frame, from_=1, to=10, textvariable=self.chunk_mb, width=10)
        chunk_spin.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        chunk_spin.bind('<Return>', lambda e: self.chunk_size.set(self.chunk_mb.get() * 1024 * 1024))
        
        # Paths Section
        paths_frame = ttk.LabelFrame(main_frame, text="Download Paths", padding=10)
        paths_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Images Path
        ttk.Label(paths_frame, text="Images Folder:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(paths_frame, textvariable=self.images_path, width=40).grid(row=0, column=1, sticky=tk.EW, padx=(10, 5), pady=5)
        ttk.Button(paths_frame, text="Browse", command=self.browse_images_folder).grid(row=0, column=2, pady=5)
        
        # Archives Path
        ttk.Label(paths_frame, text="Archives Folder:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(paths_frame, textvariable=self.archives_path, width=40).grid(row=1, column=1, sticky=tk.EW, padx=(10, 5), pady=5)
        ttk.Button(paths_frame, text="Browse", command=self.browse_archives_folder).grid(row=1, column=2, pady=5)
        
        # Configure column weights
        paths_frame.columnconfigure(1, weight=1)
        
        # Search Section
        search_frame = ttk.LabelFrame(main_frame, text="Search Configuration", padding=10)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Search Query:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(search_frame, textvariable=self.search_query, width=50).grid(row=0, column=1, sticky=tk.EW, padx=(10, 0), pady=5)
        
        search_frame.columnconfigure(1, weight=1)
        
        # Control Buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(control_frame, text="Save Config", command=self.save_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Load Config", command=self.load_config).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Setup Session", command=self.setup_session).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Test Connection", command=self.test_connection).pack(side=tk.LEFT, padx=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="Start Download", command=self.start_download)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_button = ttk.Button(control_frame, text="Stop", command=self.stop_download, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding=10)
        progress_frame.pack(fill=tk.BOTH, expand=True)
        
        # Statistics
        stats_frame = ttk.Frame(progress_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.stats_var = tk.StringVar(value="Images: 0 | Archives: 0 | Failed: 0")
        ttk.Label(stats_frame, textvariable=self.stats_var).pack(side=tk.LEFT)
        
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.progress_var).pack(anchor=tk.W, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Log Text Area
        self.log_text = scrolledtext.ScrolledText(progress_frame, height=15, width=80)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def update_stats(self):
        """Update statistics display"""
        self.stats_var.set(f"Images: {self.downloaded_images} | Archives: {self.downloaded_archives} | Failed: {self.failed_downloads}")
        
    def browse_session_file(self):
        filename = filedialog.asksaveasfilename(
            title="Select Session File Location",
            defaultextension=".session",
            filetypes=[("Session files", "*.session"), ("All files", "*.*")]
        )
        if filename:
            # Remove .session extension if present since Telethon adds it automatically
            if filename.endswith('.session'):
                filename = filename[:-8]
            self.session_path.set(filename)
    
    def browse_images_folder(self):
        folder = filedialog.askdirectory(title="Select Images Download Folder")
        if folder:
            self.images_path.set(folder)
    
    def browse_archives_folder(self):
        folder = filedialog.askdirectory(title="Select Archives Download Folder")
        if folder:
            self.archives_path.set(folder)
    
    def save_config(self):
        config = {
            "api_id": self.api_id.get(),
            "api_hash": self.api_hash.get(),
            "phone_number": self.phone_number.get(),
            "session_path": self.session_path.get(),
            "search_query": self.search_query.get(),
            "images_path": self.images_path.get(),
            "archives_path": self.archives_path.get(),
            "max_concurrent_downloads": self.max_concurrent_downloads.get(),
            "chunk_size": self.chunk_size.get()
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
            self.log("✅ Configuration saved successfully")
            messagebox.showinfo("Success", "Configuration saved successfully!")
        except Exception as e:
            self.log(f"❌ Error saving configuration: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def load_config(self):
        if not os.path.exists(self.config_file):
            return
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            self.api_id.set(config.get("api_id", ""))
            self.api_hash.set(config.get("api_hash", ""))
            self.phone_number.set(config.get("phone_number", ""))
            self.session_path.set(config.get("session_path", ""))
            self.search_query.set(config.get("search_query", ""))
            self.images_path.set(config.get("images_path", ""))
            self.archives_path.set(config.get("archives_path", ""))
            self.max_concurrent_downloads.set(config.get("max_concurrent_downloads", 3))
            self.chunk_size.set(config.get("chunk_size", 1024*1024))
            
            self.log("✅ Configuration loaded successfully")
        except Exception as e:
            self.log(f"❌ Error loading configuration: {e}")
            messagebox.showerror("Error", f"Failed to load configuration: {e}")
    
    def log(self, message):
        """Add message to log text area"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def validate_config(self):
        """Validate configuration before starting"""
        if not self.api_id.get() or not self.api_hash.get():
            messagebox.showerror("Error", "API ID and API Hash are required")
            return False
        
        if not self.phone_number.get():
            messagebox.showerror("Error", "Phone number is required")
            return False
        
        if not self.session_path.get():
            messagebox.showerror("Error", "Session file path is required")
            return False
        
        if not self.search_query.get():
            messagebox.showerror("Error", "Search query is required")
            return False
        
        if not self.images_path.get() or not self.archives_path.get():
            messagebox.showerror("Error", "Both images and archives paths are required")
            return False
        
        # Create directories if they don't exist
        try:
            os.makedirs(self.images_path.get(), exist_ok=True)
            os.makedirs(self.archives_path.get(), exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create directories: {e}")
            return False
        
        return True
    
    def setup_session(self):
        """Setup/Create a new Telegram session"""
        if not self.api_id.get() or not self.api_hash.get() or not self.phone_number.get():
            messagebox.showerror("Error", "Please fill in API ID, API Hash, and Phone Number first")
            return
        
        if not self.session_path.get():
            messagebox.showerror("Error", "Please select a session file path first")
            return
        
        # Check if session already exists
        session_file = self.session_path.get() + ".session"
        if os.path.exists(session_file):
            result = messagebox.askyesno(
                "Session Exists", 
                f"A session file already exists at {session_file}.\n\nDo you want to create a new session? This will overwrite the existing one.",
                icon='warning'
            )
            if not result:
                return
            else:
                # Delete existing session
                try:
                    os.remove(session_file)
                    self.log("🗑️ Removed existing session file")
                except Exception as e:
                    self.log(f"⚠️ Could not remove existing session: {e}")
        
        def setup_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                client = TelegramClient(
                    self.session_path.get(),
                    int(self.api_id.get()),
                    self.api_hash.get()
                )
                loop.run_until_complete(self._setup_session_async(client))
            except Exception as e:
                self.log(f"❌ Session setup failed: {e}")
                messagebox.showerror("Setup Error", f"Failed to setup session: {e}")
            finally:
                loop.close()
        
        self.log("🔧 Starting session setup...")
        threading.Thread(target=setup_async, daemon=True).start()
    
    async def _setup_session_async(self, client):
        try:
            self.log("📱 Connecting to Telegram...")
            await client.start(
                phone=lambda: self.phone_number.get(),
                code_callback=self._get_code,
                password=self._get_password
            )
            
            # Get user info to confirm login
            me = await client.get_me()
            self.log(f"✅ Successfully logged in as: {me.first_name} {me.last_name or ''}")
            self.log(f"📞 Phone: {me.phone}")
            self.log(f"🆔 User ID: {me.id}")
            
            await client.disconnect()
            
            messagebox.showinfo(
                "Success", 
                f"Session created successfully!\n\nLogged in as: {me.first_name} {me.last_name or ''}\nPhone: {me.phone}"
            )
            
        except errors.SessionPasswordNeededError:
            self.log("🔒 Two-factor authentication required")
            raise Exception("Two-factor authentication is required. Please ensure you enter the correct password.")
        except errors.PhoneCodeInvalidError:
            raise Exception("Invalid verification code. Please try again.")
        except errors.PhoneNumberInvalidError:
            raise Exception("Invalid phone number format. Please check your phone number.")
        except errors.FloodWaitError as e:
            raise Exception(f"Too many attempts. Please wait {e.seconds} seconds and try again.")
        except Exception as e:
            raise e
    
    def test_connection(self):
        """Test Telegram connection with proper authentication"""
        if not self.api_id.get() or not self.api_hash.get():
            messagebox.showerror("Error", "API ID and API Hash are required")
            return
        
        if not self.phone_number.get():
            messagebox.showerror("Error", "Phone number is required")
            return
        
        if not self.session_path.get():
            messagebox.showerror("Error", "Session file path is required")
            return
        
        # Check if session file exists
        session_file = self.session_path.get() + ".session"
        if not os.path.exists(session_file):
            messagebox.showerror("Error", f"Session file not found at {session_file}. Please setup session first.")
            return
        
        def test_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                client = TelegramClient(
                    self.session_path.get(),
                    int(self.api_id.get()),
                    self.api_hash.get()
                )
                loop.run_until_complete(self._test_connection_async(client))
            except Exception as e:
                self.log(f"❌ Connection test failed: {e}")
                messagebox.showerror("Connection Error", f"Failed to connect: {e}")
            finally:
                loop.close()
        
        threading.Thread(target=test_async, daemon=True).start()
    
    async def _test_connection_async(self, client):
        try:
            await client.connect()
            if not await client.is_user_authorized():
                raise Exception("Session is not authorized. Please setup session again.")
            
            me = await client.get_me()
            self.log(f"✅ Connection test successful! Logged in as: {me.first_name}")
            messagebox.showinfo("Success", f"Connection successful!\nLogged in as: {me.first_name} {me.last_name or ''}")
            await client.disconnect()
        except Exception as e:
            raise e
    
    def start_download(self):
        """Start the download process"""
        if not self.validate_config():
            return
        
        # Check if session file exists
        session_file = self.session_path.get() + ".session"
        if not os.path.exists(session_file):
            messagebox.showerror("Error", f"Session file not found at {session_file}. Please setup session first.")
            return
        
        if self.is_running:
            messagebox.showwarning("Warning", "Download is already running")
            return
        
        # Reset statistics
        self.downloaded_images = 0
        self.downloaded_archives = 0
        self.failed_downloads = 0
        self.update_stats()
        
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_bar.start()
        self.progress_var.set("Starting download...")
        
        def download_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                self.client = TelegramClient(
                    self.session_path.get(),
                    int(self.api_id.get()),
                    self.api_hash.get(),
                    connection_retries=5,
                    retry_delay=1
                )
                loop.run_until_complete(self._download_process())
            except Exception as e:
                self.log(f"❌ Download failed: {e}")
                messagebox.showerror("Download Error", f"Download failed: {e}")
            finally:
                self._reset_ui()
                loop.close()
        
        threading.Thread(target=download_async, daemon=True).start()
    
    def stop_download(self):
        """Stop the download process"""
        self.is_running = False
        self.progress_var.set("Stopping...")
        self.log("🛑 Stop requested...")
    
    def _reset_ui(self):
        """Reset UI after download completion or stop"""
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.progress_var.set("Ready")
    
    async def _download_process(self):
        """Main download process"""
        try:
            await self.client.connect()
            if not await self.client.is_user_authorized():
                raise Exception("Session is not authorized. Please setup session again.")
            
            self.log("✅ Connected to Telegram")
            
            # Create a semaphore to limit concurrent downloads
            semaphore = asyncio.Semaphore(self.max_concurrent_downloads.get())
            
            self.progress_var.set("Searching and downloading...")
            await self.search_and_download_pairs(semaphore)
            
            self.log("✅ Download process completed!")
            self.progress_var.set("Completed")
            
        except Exception as e:
            self.log(f"❌ Error in download process: {e}")
            raise e
        finally:
            if self.client:
                await self.client.disconnect()
    
    async def download_with_progress(self, message, file_path, semaphore, file_type="file"):
        """Download a single file with progress tracking and error handling"""
        async with semaphore:
            try:
                # Skip if file already exists
                if os.path.exists(file_path):
                    self.log(f"⏭️ Skipping existing {file_type}: {os.path.basename(file_path)}")
                    return True
                
                # Download the file
                await self.client.download_media(
                    message.media, 
                    file=file_path
                )
                
                if file_type == "image":
                    self.downloaded_images += 1
                else:
                    self.downloaded_archives += 1
                    
                self.update_stats()
                self.log(f"📥 Downloaded {file_type}: {os.path.basename(file_path)}")
                return True
                
            except Exception as e:
                self.failed_downloads += 1
                self.update_stats()
                self.log(f"❌ Failed to download {file_type} {os.path.basename(file_path)}: {e}")
                return False
    
    async def search_and_download_pairs(self, semaphore):
        """Search for images and immediately download corresponding archives"""
        search_name = self.search_query.get()
        processed_codes = set()
        
        async for dialog in self.client.iter_dialogs():
            if not self.is_running:
                break
                
            try:
                # Search for images in this dialog
                async for message in self.client.iter_messages(dialog.entity, search=search_name):
                    if not self.is_running:
                        break
                        
                    # Skip non-photo messages
                    if not message.media or not message.photo:
                        continue
                    
                    # Get filename and extract code
                    if hasattr(message, 'file') and message.file and hasattr(message.file, 'name') and message.file.name:
                        file_name = message.file.name
                    else:
                        if message.text:
                            file_name = message.text.strip().replace("\n", " ")
                        else:
                            file_name = f"{message.id}.jpg"
                    
                    code, clean_name = self.extract_code_and_description(file_name)
                    if not code or len(code) < 3 or "*" in code or code in processed_codes:
                        continue
                    
                    processed_codes.add(code)
                    
                    # Prepare image download
                    file_ext = ".jpg"
                    if hasattr(message, 'file') and message.file and hasattr(message.file, 'ext'):
                        file_ext = message.file.ext or ".jpg"
                    
                    image_path = os.path.join(self.images_path.get(), clean_name + file_ext)
                    
                    self.log(f"🔍 Found image with code: {code}")
                    
                    # Download image immediately
                    image_success = await self.download_with_progress(message, image_path, semaphore, "image")
                    
                    if image_success and self.is_running:
                        # Now search for corresponding archive
                        archive_found = await self.search_and_download_archive_for_code(code, clean_name, semaphore)
                        if not archive_found:
                            self.log(f"⚠️ No archive found for code: {code}")
                    
                    # Add small delay to prevent overwhelming the server
                    await asyncio.sleep(0.1)
                        
            except errors.FloodWaitError as e:
                self.log(f"⏳ Rate limited, waiting {e.seconds} seconds...")
                await asyncio.sleep(e.seconds)
            except errors.RPCError as e:
                self.log(f"⚠️ RPC Error in {dialog.name}: {e}")
            except Exception as e:
                self.log(f"🚨 Unexpected error in {dialog.name}: {e}")
    
    async def search_and_download_archive_for_code(self, code, file_name, semaphore):
        """Search and download archive for a specific code"""
        async for dialog in self.client.iter_dialogs():
            if not self.is_running:
                return False
                
            try:
                async for message in self.client.iter_messages(dialog.entity, search=code):
                    if not self.is_running:
                        return False
                        
                    if not message.media or not message.document:
                        continue
                    
                    complete_file_name = ""
                    if hasattr(message, 'file') and message.file and hasattr(message.file, 'name'):
                        complete_file_name = message.file.name or ''
                    
                    if not self.is_archive(complete_file_name):
                        continue
                    
                    # Found matching archive
                    ext = os.path.splitext(complete_file_name)[1] or ".rar"
                    archive_path = os.path.join(self.archives_path.get(), file_name + ext)
                    
                    success = await self.download_with_progress(message, archive_path, semaphore, "archive")
                    if success:
                        return True
                        
            except errors.FloodWaitError as e:
                self.log(f"⏳ Rate limited, waiting {e.seconds} seconds...")
                await asyncio.sleep(e.seconds)
            except errors.RPCError as e:
                self.log(f"⚠️ RPC Error searching for {code}: {e}")
            except Exception as e:
                self.log(f"🚨 Unexpected error searching for {code}: {e}")
        
        return False
    
    def extract_code_and_description(self, file_name: str):
        """Extract code and description from filename"""
        file_name = file_name.strip()
        
        match = re.match(r'^([^\s]+)\s+([\s\S]+)$', file_name)
        if not match:
            return None, self.sanitize_filename(file_name)
        
        code = match.group(1)
        description_part = match.group(2).strip()
        
        description_clean = re.sub(r'#.*', '', description_part, flags=re.DOTALL).strip()
        description_clean = re.sub(r'\s+', ' ', description_clean)
        description_clean = self.sanitize_filename(description_clean)
        
        return code, description_clean
    
    def sanitize_filename(self, name: str):
        """Sanitize filename for filesystem compatibility"""
        name = re.sub(r'[.-]', ' ', name)
        name = re.sub(r'[<>:"/\\|?*\n\r]', '', name)
        return name.strip()
    
    def is_archive(self, file_name):
        """Check if file is an archive"""
        if not file_name:
            return False
        return file_name.lower().endswith(('.rar', '.zip', '.7z', '.tar', '.gz', '.bz2'))
    
    def _get_code(self):
        """Get verification code from user with improved dialog"""
        dialog = AuthDialog(self.root, "Verification Code Required", 
                          "A verification code has been sent to your phone.\nPlease enter the code below:",
                          show_password=False)
        if dialog.result:
            self.log(f"📱 Verification code entered")
            return dialog.result
        else:
            raise ValueError("Verification code is required")
    
    def _get_password(self):
        """Get 2FA password from user with improved dialog"""
        dialog = AuthDialog(self.root, "Two-Factor Authentication", 
                          "This account has 2FA enabled.\nPlease enter your cloud password:",
                          show_password=True)
        if dialog.result:
            self.log(f"🔒 2FA password entered")
            return dialog.result
        else:
            raise ValueError("2FA password is required")


class AuthDialog:
    def __init__(self, parent, title, message, show_password=False):
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Message label
        ttk.Label(main_frame, text=message, wraplength=350).pack(pady=(0, 20))
        
        # Input frame
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.entry_var = tk.StringVar()
        entry = ttk.Entry(input_frame, textvariable=self.entry_var, font=('Arial', 12), width=30)
        if show_password:
            entry.config(show="*")
        entry.pack(fill=tk.X)
        entry.focus()
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.RIGHT)
        
        # Bind Enter key
        entry.bind('<Return>', lambda e: self.ok())
        self.dialog.bind('<Escape>', lambda e: self.cancel())
        
        # Wait for dialog to close
        self.dialog.wait_window()
    
    def ok(self):
        self.result = self.entry_var.get().strip()
        if self.result:
            self.dialog.destroy()
        else:
            messagebox.showwarning("Input Required", "Please enter a value", parent=self.dialog)
    
    def cancel(self):
        self.result = None
        self.dialog.destroy()


def main():
    root = tk.Tk()
    app = TelegramDownloaderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()