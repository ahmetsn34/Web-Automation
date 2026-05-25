import imaplib
import email
import re
import time
import os
import sys
import json
import threading
import queue
import logging
import winsound
import socket
import random
import shutil
from datetime import datetime
from typing import Optional, Dict, List, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import pandas as pd

# Akıllı PDF Okuma Kütüphanesi
import pdfplumber

import undetected_chromedriver as uc 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException, UnexpectedAlertPresentException

# =====================================================================
# --- MONKEY PATCH: WinError 6 Kirliliğini Kökten Yok Etme Zırhı ---
# =====================================================================
try:
    original_del = uc.Chrome.__del__
    def safe_del(self):
        try:
            original_del(self)
        except Exception:
            pass
    uc.Chrome.__del__ = safe_del
except Exception:
    pass
# =====================================================================

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import config
    from logger_config import setup_logger
    logger = setup_logger()
except ImportError:
    class MockLogger:
        def info(self, msg): print(f"[INFO] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}")
    logger = MockLogger()
    class MockConfig:
        DISABLE_IMAGES = False
        LOGIN_URL = "https://wellcome.azurewebsites.net/pnlwell/"
    config = MockConfig()

os.environ['WDM_LOG'] = '0'

# =====================================================================
# --- 🐋 SEA FORT SERVICE KURUMSAL SAAS RENK PALETİ CONFIGURATION 🐋 ---
# =====================================================================
ctk.set_appearance_mode("Dark")
# Ana Tema: #0d1b2a (Deep Space), Kartlar: #162a3d, Vurgu: #62b6cb, Başarı: #2ecc71
# =====================================================================

# =====================================================================
# --- ÇOKLU DİL DESTEĞİ VE SÖZLÜK ---
# =====================================================================
LANG_PACK = {
    "TR": {
        "title": "UNIVERSAL | AUTOMATION SUITE",
        "subtitle": "Kurumsal RPA Veri Ekranı v2.0",
        "select_folder": "Dizin Bağla",
        "placeholder": "Personel klasörlerinin ana dizinini seçin...",
        "headless": "Tarayıcıyı Gizle (Headless)",
        "start": "OTOMASYONU BAŞLAT",
        "running": "İŞLEMLER SÜRÜYOR...",
        "pause": "DURAKLAT",
        "resume": "DEVAM ET",
        "kpi_success": "BAŞARILI KAYIT",
        "kpi_failed": "HATALI / KALAN",
        "kpi_eta": "TAHMİNİ BİTİŞ (ETA)",
        "no_folder": "Lütfen önce personel klasörlerinin bulunduğu ana dizini seçin!",
        "pre_flight_start": "[SİSTEM] Başlangıç sağlık kontrolleri yapılıyor...",
        "internet_ok": "  🌐 İnternet bağlantısı aktif.",
        "internet_err": "❌ KRİTİK HATA: İnternet bağlantısı yok!",
        "chrome_ok": "  🚗 Chrome görünmezlik altyapısı hazır.",
        "eta_calculating": "Hesaplanıyor...",
        "all_done": "Seçilen dizindeki tüm personel klasörleri başarıyla işlendi!",
        "login_wait": "🔐 Gömülü bilgilerle giriş yapılıyor, OTP kodu bekleniyor...",
        "process_folder": "📂 Klasör Analiz Ediliyor: {}",
        "read_success": "   📋 Okunan -> Ad Soyad: {}, TC: {}, Tel: {}",
        "img1_click": "   -> 'Çalışan Tanımla' sekmesine geçiliyor...",
        "img2_click": "   -> '+ Yeni Çalışan' form ekranı açılıyor...",
        "img3_fill": "   -> Form alanları ve kimlik bilgileri yazılıyor...",
        "gen_password": "   🔑 'Üret' butonuna basılarak rastgele şifre oluşturuluyor...",
        "submit_form": "   -> Bilgiler doğrulanıyor, 'Bilgileri Kontrol Et' butonuna basıldı.",
        "success_log": "✅ [BAŞARILI] {} sisteme başarıyla kaydedildi.",
        "error_log": "❌ [HATA] {} işlenirken sorun çıktı: {}",
        "checkpoint_title": "Kaldığı Yerden Devam",
        "checkpoint_msg": "Önceki oturumdan kalan {} adet işlenmiş klasör bulundu.\nKaldığınız yerden devam etmek ister misiniz?\n\nEvet: Sadece kalanları işler.\nHayır: Her şeye sıfırdan başlar.",
        "checkpoint_clean": "[SİSTEM] Eski hafıza temizlendi, sıfırdan başlanıyor...",
        "report_gen": "📊 Operasyon raporu harici dizine kaydedildi: {}",
        "sw_retry": "Hata Anında 3 Kez Yeniden Dene",
        "sw_alert": "Alert Pop-upları Otomatik Geç",
        "lbl_comp": "Şirket Kodu",
        "lbl_user": "Kullanıcı Adı",
        "lbl_pass": "Şifre",
        "otp_title": "🔐 OTP Güvenlik Kodu",
        "otp_prompt": "Telefonunuza veya e-postanıza gelen 6 haneli OTP kodunu giriniz:"
    },
    "EN": {
        "title": "UNIVERSAL | AUTOMATION SUITE",
        "subtitle": "Enterprise RPA Dashboard v2.0",
        "select_folder": "Link Directory",
        "placeholder": "Select the main directory containing personnel folders...",
        "headless": "Hide Browser (Headless)",
        "start": "START AUTOMATION",
        "running": "PROCESSING...",
        "pause": "PAUSE",
        "resume": "RESUME",
        "kpi_success": "SUCCESSFUL LOGS",
        "kpi_failed": "FAILED / REMAINING",
        "kpi_eta": "ESTIMATED TIME (ETA)",
        "no_folder": "Please select the main personnel directory first!",
        "pre_flight_start": "[SYSTEM] Running pre-flight health checks...",
        "internet_ok": "  🌐 Internet connection is active.",
        "internet_err": "❌ CRITICAL ERROR: No internet connection!",
        "chrome_ok": "  🚗 Chrome stealth infrastructure is ready.",
        "eta_calculating": "Calculating...",
        "all_done": "All personnel folders in the selected directory have been processed!",
        "demo_alert": "🤖 SIMULATION MODE ACTIVE: Browser will not open, actions are simulated...",
        "login_wait": "🔐 Logging in with embedded credentials, waiting for OTP...",
        "process_folder": "📂 Analyzing Folder: {}",
        "read_success": "   📋 Extracted -> Name: {}, ID: {}, Tel: {}",
        "img1_click": "   -> Navigating to 'Personnel Definitions'...",
        "img2_click": "   -> Opening '+ New Employee' form...",
        "img3_fill": "   -> Filling out form fields and identity data...",
        "gen_password": "   🔑 Clicking 'Generate' to create a random password...",
        "submit_form": "   -> Verifying details, clicking 'Check Information' button.",
        "success_log": "✅ [SUCCESS] {} registered successfully.",
        "error_log": "❌ [ERROR] Failed to process {}: {}",
        "checkpoint_title": "Resume Session",
        "checkpoint_msg": "Found {} processed folders from previous session.\nDo you want to resume where you left off?\n\nYes: Process remaining only.\nNo: Start from scratch.",
        "checkpoint_clean": "[SYSTEM] Old memory cleared, starting from scratch...",
        "report_gen": "📊 Operation report saved to external directory: {}",
        "sw_retry": "Retry 3 Times on Error", 
        "sw_alert": "Automatically Dismiss Browser Alerts",
        "lbl_comp": "Company Code",
        "lbl_user": "Username",
        "lbl_pass": "Password",
        "otp_title": "🔐 OTP Security Code",
        "otp_prompt": "Enter the 6-digit OTP code sent to your phone/email:"
    }
}


class WellcomeRPAApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.settings_file = "settings.json"
        self.checkpoint_file = "checkpoint.json"
        self.geometry("740x800")

        # İç Durum Değişkenleri
        self.base_folder_path = tk.StringVar()
        self.company_code_var = tk.StringVar() 
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.is_running = False
        
        # Zırh Switch Değişkenleri
        self.headless_var = tk.BooleanVar(value=False)
        self.retry_enabled = tk.BooleanVar(value=True)
        self.alert_dismiss_enabled = tk.BooleanVar(value=True)
        self.current_lang = "TR"
        
        self.pause_event = threading.Event()
        self.pause_event.set()  
        self.checkpoint_lock = threading.Lock()
        
        self.start_time = None
        self.processed_count_for_eta = 0
        self.current_report_path = None

        self._load_settings() 
        self._build_ui()  
        self._update_ui_texts()
        logger.info("Application initialized with armored SaaS RPA Dashboard architecture.")

    def _log(self, message: str, tag: str = "normal") -> None:
        def update_gui():
            self.log_text.configure(state="normal")
            self.log_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n", tag)
            self.log_text.see(tk.END)
            self.log_text.configure(state="disabled")
        self.after(0, update_gui)

    def _on_lang_change(self, choice: str) -> None:
        self.current_lang = choice
        self._update_ui_texts()
        self._save_settings()

    def _toggle_pause(self) -> None:
        lg = LANG_PACK[self.current_lang]
        if self.pause_event.is_set():
            self.pause_event.clear()  
            self.pause_button.configure(text=lg["resume"], fg_color="#2ecc71", hover_color="#27ae60")
            self._log(f"[SYSTEM] {lg['pause']} - Otomasyon duraklatıldı. Kontrol yapabilirsiniz.", "warning")
        else:
            self.pause_event.set()  
            self.pause_button.configure(text=lg["pause"], fg_color="#e67e22", hover_color="#d35400")
            self._log(f"[SYSTEM] {lg['resume']} - Otomasyon kaldığı yerden devam ediyor...", "system")

    def _select_folder(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.base_folder_path.set(path)
            self._log(f"[SİSTEM] Ana dizin bağlandı: {path}", "system")
            self._save_settings()

    def _load_settings(self) -> None:
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r") as f:
                    settings = json.load(f)
                    self.current_lang = settings.get("lang", "TR")
                    self.base_folder_path.set(settings.get("base_folder_path", ""))
                    self.company_code_var.set(settings.get("company_code", "")) 
                    self.username_var.set(settings.get("username", ""))
                    self.password_var.set(settings.get("password", ""))
                    self.headless_var.set(settings.get("headless", False))
                    self.retry_enabled.set(settings.get("retry_enabled", True))
                    self.alert_dismiss_enabled.set(settings.get("alert_dismiss_enabled", True))
            except Exception: pass

    def _save_settings(self) -> None:
        settings = {
            "lang": self.current_lang,
            "base_folder_path": self.base_folder_path.get(),
            "company_code": self.company_code_var.get(), 
            "username": self.username_var.get(),
            "password": self.password_var.get(),
            "headless": self.headless_var.get(),
            "retry_enabled": self.retry_enabled.get(),
            "alert_dismiss_enabled": self.alert_dismiss_enabled.get()
        }
        try:
            with open(self.settings_file, "w") as f: json.dump(settings, f)
        except Exception: pass

    def _clean_phone_number(self, phone_str: str) -> str:
        if not phone_str: return ""
        digits = re.sub(r'\D', '', phone_str)
        if digits.startswith("90") and len(digits) > 10: digits = digits[2:]
        elif digits.startswith("0") and len(digits) == 11: digits = digits[1:]
        return digits

    def _mask_sensitive_data(self, value: str, is_tc: bool = True) -> str:
        if not value or value == "00000000000": return "---"
        if is_tc and len(value) == 11:
            return f"{value[:3]}******{value[-2:]}"
        elif not is_tc and len(value) >= 7:
            return f"{value[:3]}***{value[-2:]}"
        return value

    def _validate_tc_kn(self, tc_str: str) -> bool:
        if not tc_str or len(tc_str) != 11 or not tc_str.isdigit(): return False
        if tc_str[0] == '0': return False
        
        digits = [int(d) for d in tc_str]
        if digits[10] % 2 != 0: return False
        
        tekler = sum(digits[0:9:2])
        ciftler = sum(digits[1:8:2])
        if ((tekler * 7) - ciftler) % 10 != digits[9]: return False
        if sum(digits[0:10]) % 10 != digits[10]: return False
        
        return True

    def _request_otp_from_user(self) -> str:
        lg = LANG_PACK[self.current_lang]
        otp_box = ctk.CTkInputDialog(text=lg["otp_prompt"], title=lg["otp_title"])
        otp_code = otp_box.get_input()
        return otp_code if otp_code else ""

    def _generate_corporate_email(self, full_name: str) -> str:
        if not full_name: return f"personel.{random.randint(1000,9999)}@seafortservice.com"
        
        char_map = {
            'ç': 'c', 'Ç': 'c', 'ğ': 'g', 'Ğ': 'g', 'ı': 'i', 'I': 'i', 'İ': 'i',
            'ö': 'o', 'Ö': 'o', 'ş': 's', 'Ş': 's', 'ü': 'u', 'Ü': 'u'
        }
        
        cleaned_name = full_name.lower().strip()
        for tr_char, eng_char in char_map.items():
            cleaned_name = cleaned_name.replace(tr_char, eng_char)
            
        cleaned_name = re.sub(r'[^a-z\s\.]', '', cleaned_name)
        parts = [p for p in cleaned_name.split() if p]
        
        if len(parts) >= 2:
            email_username = f"{parts[0]}.{parts[-1]}"
        elif len(parts) == 1:
            email_username = parts[0]
        else:
            email_username = f"personel.{random.randint(1000,9999)}"
            
        return f"{email_username}@seafortservice.com"

    def _check_folder_health(self, folder_path: str) -> Tuple[bool, str]:
        if not os.path.exists(folder_path):
            return False, "Klasör bulunamadı"
            
        pdf_dosyalari = [f for f in os.listdir(folder_path) if f.upper().endswith('.PDF')]
        if not pdf_dosyalari:
            return False, "Klasörün içi boş veya PDF dosyası mevcut değil"
            
        target_pdf = os.path.join(folder_path, pdf_dosyalari[0])
        if os.path.getsize(target_pdf) == 0:
            return False, "PDF dosyası bozuk veya 0 KB (OneDrive Senkronizasyon Hatası)"
            
        return True, "Sağlıklı"

    def _read_personel_txt(self, folder_path: str) -> Dict[str, str]:
        klasor_adi = os.path.basename(folder_path.strip().rstrip('\\/'))
        veriler = {
            "tc": "00000000000", 
            "isim_soyisim": klasor_adi.replace("_", " "), 
            "gorev": "Personel",
            "telefon": "",
            "eposta": "",
            "valid_record": True
        }
        
        is_healthy, health_msg = self._check_folder_health(folder_path)
        if not is_healthy:
            self._log(f"❌ [EVRAK HATASI] {klasor_adi} -> {health_msg}", "error")
            veriler["valid_record"] = False
            return veriler
        
        try:
            pdf_dosyalari = [f for f in os.listdir(folder_path) if f.upper().endswith('.PDF')]
            pdf_path = os.path.join(folder_path, pdf_dosyalari[0])
            with pdfplumber.open(pdf_path) as pdf:
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text: full_text += text
            
            tc_match = re.search(r'\b\d{11}\b', full_text)
            if tc_match:
                aday_tc = tc_match.group(0)
                if self._validate_tc_kn(aday_tc):
                    veriler["tc"] = aday_tc
                    masked_tc = self._mask_sensitive_data(aday_tc, is_tc=True)
                    self._log(f"🤖 [AI-OCR] PDF içinden T.C. çekildi ve Doğrulandı: {masked_tc}", "success")
                else:
                    self._log(f"❌ [ALGORİTMA HATASI] PDF'deki T.C. gerçek bir T.C. formatına uymuyor!", "error")
                    veriler["valid_record"] = False
            else:
                self._log(f"⚠️ {klasor_adi} belgesinde T.C. numarası bulunamadı!", "warning")
                veriler["valid_record"] = False

            clean_text_for_phone = re.sub(r'[\s\-\(\)]', '', full_text)
            phone_match = re.search(r'(?:90|0)?(5\d{9})\b', clean_text_for_phone)
            
            if phone_match:
                veriler["telefon"] = self._clean_phone_number(phone_match.group(1))
                masked_tel = self._mask_sensitive_data(veriler["telefon"], is_tc=False)
                self._log(f"🤖 [AI-OCR] PDF içinden Telefon başarıyla çekildi: {masked_tel}", "success")
            else:
                alt_phone = re.search(r'(?:\+?90|\b0)?\s*(5\d{2})\s*(\d{3})\s*(\d{2})\s*(\d{2})', full_text)
                if alt_phone:
                    raw_phone = "".join(alt_phone.groups())
                    veriler["telefon"] = self._clean_phone_number(raw_phone)
                    masked_tel = self._mask_sensitive_data(veriler["telefon"], is_tc=False)
                    self._log(f"🤖 [AI-OCR] PDF içinden Telefon (Yedek Kalıp) çekildi: {masked_tel}", "success")
                else:
                    self._log(f"⚠️ {klasor_adi} belgesinde Telefon numarası bulunamadı!", "warning")
                    
            email_match = re.search(r'\b[A-Za-0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', full_text)
            if email_match:
                veriler["eposta"] = email_match.group(0).lower()
                self._log(f"🤖 [AI-OCR] PDF içinden E-Posta çekildi: {veriler['eposta']}", "success")
            else:
                veriler["eposta"] = self._generate_corporate_email(veriler["isim_soyisim"])
                self._log(f"🔑 [OTO-MAIL] PDF'de mail bulunamadı, kurumsal mail üretildi: {veriler['eposta']}", "success")
                    
        except Exception as pdf_err:
            self._log(f"⚠️ Evrak okuma motoru hatası: {str(pdf_err)[:40]}", "warning")
            veriler["valid_record"] = False
                    
        return veriler

    def _create_driver(self) -> Optional[uc.Chrome]:
        os.system("taskkill /f /im chromedriver.exe >nul 2>&1")
        os.system("taskkill /f /im chrome.exe >nul 2>&1")
        time.sleep(1)

        chrome_options = uc.ChromeOptions()
        chrome_options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": config.DISABLE_IMAGES,
            "profile.default_content_setting_values.notifications": 2
        })
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--window-size=1280,720")
        
        try:
            return uc.Chrome(options=chrome_options, headless=self.headless_var.get(), use_subprocess=True)
        except Exception as e:
            self._log(f"⚠️ Dinamik sürücü hatası: {str(e)[:40]}. Zorunlu v148 modu deneniyor...", "warning")
            os.system("taskkill /f /im chromedriver.exe >nul 2>&1")
            
        try:
            backup_options = uc.ChromeOptions()
            backup_options.add_experimental_option("prefs", {
                "profile.managed_default_content_settings.images": config.DISABLE_IMAGES,
                "profile.default_content_setting_values.notifications": 2
            })
            backup_options.add_argument("--no-sandbox")
            backup_options.add_argument("--disable-dev-shm-usage")
            backup_options.add_argument("--disable-gpu")
            backup_options.add_argument("--ignore-certificate-errors")
            backup_options.add_argument("--window-size=1280,720")
            
            return uc.Chrome(options=backup_options, headless=self.headless_var.get(), version_main=148, use_subprocess=False)
        except Exception as e_backup:
            self._log(f"❌ [KRİTİK] Sürücü ayağa kalkamadı. Sürüm uyumsuzluğu mevcut: {str(e_backup)[:40]}", "error")
            os.system("taskkill /f /im chromedriver.exe >nul 2>&1")
            raise e_backup

    def _handle_embedded_login(self, driver: uc.Chrome, bekleme: WebDriverWait) -> bool:
        lg = LANG_PACK[self.current_lang]
        try:
            self._log("🔐 Giriş alanları dolduruluyor...", "system")
            time.sleep(1.5) 

            if self.company_code_var.get():
                comp_input = bekleme.until(EC.presence_of_element_located((By.ID, "FirmCode")))
                comp_input.clear()
                comp_input.send_keys(self.company_code_var.get())
                
                self._log("⚡ Şirket kodu gönderildi, AJAX Postback tetikleniyor...", "system")
                comp_input.send_keys(Keys.ENTER)
                
                self._log("⏳ Sayfa Postback oluyor, alanların canlanması bekleniyor...", "warning")
                time.sleep(4.5) 
                bekleme = WebDriverWait(driver, 20)

            self._log("👁️ Alanlar taranıyor, Username kutusu bekleniyor...", "system")
            user_box = bekleme.until(EC.element_to_be_clickable((By.ID, "Username")))
            pass_box = driver.find_element(By.ID, "Password")
            
            driver.execute_script("arguments[0].value = arguments[1];", user_box, self.username_var.get())
            driver.execute_script("arguments[0].value = arguments[1];", pass_box, self.password_var.get())
            time.sleep(0.5)

            login_btn = bekleme.until(EC.element_to_be_clickable((By.ID, "loginButton")))
            driver.execute_script("arguments[0].click();", login_btn) 
            
            self._log(lg["login_wait"], "warning")
            time.sleep(3.5) 
            
            otp_done_event = threading.Event()
            otp_code_container = [""]

            def ask_gui():
                otp_code_container[0] = self._request_otp_from_user()
                otp_done_event.set()

            self.after(0, ask_gui)
            otp_done_event.wait() 

            user_otp = otp_code_container[0]
            if user_otp:
                self._log("🔐 OTP kodu siteye enjekte ediliyor...", "system")
                otp_input = bekleme.until(EC.presence_of_element_located((By.ID, "VerificationCode")))
                driver.execute_script("arguments[0].value = arguments[1];", otp_input, user_otp)
                time.sleep(0.5)
                
                self._log("🚀 'Doğrula ve Giriş Yap' butonuna basılıyor...", "success")
                otp_submit_btn = bekleme.until(EC.element_to_be_clickable((
                    By.XPATH, "//a[contains(@class, 'btn-sms-verification') or text()='Doğrula ve Giriş Yap']"
                )))
                driver.execute_script("arguments[0].click();", otp_submit_btn) 
                time.sleep(3.0)
            return True
        except Exception as e:
            self._log(f"❌ KRİTİK GİRİŞ HATASI: Giriş elemanları doldurulamadı! Detay: {str(e)[:50]}", "error")
            try: winsound.MessageBeep(winsound.MB_ICONHAND)
            except: pass
            return False

    def _process_single_folder(self, driver: Optional[uc.Chrome], folder_name: str, base_path: str) -> Tuple[str, Dict[str, str]]:
        lg = LANG_PACK[self.current_lang]
        folder_path = os.path.join(base_path, folder_name) if base_path else folder_name
        
        self.pause_event.wait()
        personel_bilgisi = self._read_personel_txt(folder_path)
        
        if not personel_bilgisi["valid_record"]:
            return "Mükerrer veya Hatalı Veri", personel_bilgisi

        self._log(lg["process_folder"].format(folder_name), "system")
        masked_tc = self._mask_sensitive_data(personel_bilgisi['tc'], is_tc=True)
        masked_tel = self._mask_sensitive_data(personel_bilgisi['telefon'], is_tc=False)
        self._log(lg["read_success"].format(personel_bilgisi['isim_soyisim'], masked_tc, masked_tel), "normal")

        deneme_siniri = 3 if self.retry_enabled.get() else 1
        for deneme in range(1, deneme_siniri + 1):
            try:
                bekleme = WebDriverWait(driver, 20)

                if self.alert_dismiss_enabled.get():
                    try:
                        alert = driver.switch_to.alert
                        self._log(f"⚠️ Sinsi Alert yakalandı ve temizlendi: {alert.text}", "warning")
                        alert.accept()
                    except Exception: pass

                # SÜREÇ 1: Çalışan Tanımla Sekmesi
                self._log(lg["img1_click"], "normal")
                calisan_tanimla_btn = bekleme.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/files/workgroup/')]")))
                driver.execute_script("arguments[0].click();", calisan_tanimla_btn)

                time.sleep(random.uniform(3.5, 5.8))

                # SÜREÇ 2: + Yeni Çalışan Butonu
                self._log(lg["img2_click"], "normal")
                yeni_calisan_btn = bekleme.until(EC.presence_of_element_located((By.ID, "ContentPlaceHolder1_btnNewUserPanel")))
                driver.execute_script("arguments[0].click();", yeni_calisan_btn)

                time.sleep(random.uniform(2.5, 4.2))

                # SÜREÇ 3: Kayıt Alanları Formu
                self._log(lg["img3_fill"], "normal")
                isim_input = bekleme.until(EC.presence_of_element_located((By.ID, "NameSurname")))
                isim_input.clear()
                isim_input.send_keys(personel_bilgisi["isim_soyisim"])

                tc_input = driver.find_element(By.ID, "kimlikno")
                tc_input.clear()
                tc_input.send_keys(personel_bilgisi["tc"])

                gorev_input = driver.find_element(By.ID, "yetkinlik")
                gorev_input.clear()
                gorev_input.send_keys(personel_bilgisi["gorev"])

                self._log(lg["gen_password"], "normal")
                uret_btn = driver.find_element(By.XPATH, "//a[contains(@onclick, 'rndPassword') or @title='Random Şifre Türet ']")
                driver.execute_script("arguments[0].click();", uret_btn)
                time.sleep(0.5)

                if personel_bilgisi["telefon"]:
                    tel_input = driver.find_element(By.ID, "telefon")
                    tel_input.clear()
                    tel_input.send_keys(personel_bilgisi["telefon"])

                if presidential_data := personel_bilgisi["eposta"]:
                    mail_input = driver.find_element(By.ID, "eposta")
                    mail_input.clear()
                    mail_input.send_keys(personel_bilgisi["eposta"])

                time.sleep(1.5)
                self._log(lg["submit_form"], "normal")
                
                kaydet_btn = driver.find_element(By.XPATH, "//a[contains(@onclick, 'CheckInfo') or contains(@class, 'checkUser')]")
                driver.execute_script("arguments[0].click();", kaydet_btn)
                
                if self.alert_dismiss_enabled.get():
                    time.sleep(1.5)
                    try:
                        alert = driver.switch_to.alert
                        alert_msg = alert.text
                        self._log(f"❌ Site Kayıt Başarısız Pop-up Uyarısı: {alert_msg}", "error")
                        alert.accept()
                        return f"Site Engeli: {alert_msg}", personel_bilgisi
                    except Exception: pass

                insansi_bekleme = random.uniform(4.5, 7.2)  
                time.sleep(insansi_bekleme)
                
                self._log(lg["success_log"].format(folder_name), "success")
                with self.checkpoint_lock: self._save_to_checkpoint(folder_name)
                return "Success", personel_bilgisi

            except (TimeoutException, UnexpectedAlertPresentException, OSError):
                self._log(f"⚠️ Deneme {deneme}/{deneme_siniri} başarısız oldu (Ağ/Timeout). Yeniden yönlendiriliyor...", "warning")
                time.sleep(6.0)
                try: driver.get("https://wellcome.azurewebsites.net/pnlwell/")
                except Exception: pass
                if deneme == deneme_siniri: return f"Error: Network Timeout after {deneme_siniri} retries.", personel_bilgisi
            except Exception as e:
                error_msg = str(e)[:40]
                self._log(lg["error_log"].format(folder_name, error_msg), "error")
                return f"Error: {error_msg}", personel_bilgisi
        return "Failed", personel_bilgisi

    def _run_automation_loop(self, folders: list, base_path: str) -> None:
        lg = LANG_PACK[self.current_lang]
        driver = None
        results_report: List[Dict[str, str]] = []
        
        upper_directory = os.path.dirname(os.path.abspath(base_path))
        center_directory = os.path.join(upper_directory, "Sea_Fort_RPA_Operasyon_Merkezi")
        
        try:
            if not os.path.exists(center_directory):
                os.makedirs(center_directory)
        except Exception:
            center_directory = os.path.join(base_path, "Sea_Fort_RPA_Operasyon_Merkezi")
            if not os.path.exists(center_directory): os.makedirs(center_directory)

        try:
            total_folders = len(folders)
            success_count = 0
            error_count = 0
            
            self.after(0, lambda: (
                self.progress_bar.set(0),
                self.val_success.configure(text="0"),
                self.val_pending.configure(text=f"0 / {total_folders}"),
                self.val_eta.configure(text="--:--")
            ))

            driver = self._create_driver()
            driver.get(config.LOGIN_URL)
            bekleme = WebDriverWait(driver, 15)
            
            if self.username_var.get() and self.password_var.get():
                login_success = self._handle_embedded_login(driver, bekleme)
                if not login_success:
                    self._log("⚠️ [KRİTİK DURDURMA] Giriş başarısız olduğu için işlem tamamen iptal edildi. Klasörler ellenmedi.", "error")
                    if driver:
                        try: driver.quit()
                        except Exception: pass
                    return 
            else:
                messagebox.showinfo("Giriş Onayı", "Giriş bilgileri boş! Lütfen tarayıcıdan giriş yapıp OK basın.")

            for index, folder in enumerate(folders):
                if not self.is_running: break
                
                status_res, personel_data = self._process_single_folder(driver, folder, base_path)
                
                if status_res == "Mükerrer veya Hatalı Veri":
                    error_count += 1
                    try:
                        bozuk_dizini = os.path.join(center_directory, "[BOZUK_EVRAK]")
                        if not os.path.exists(bozuk_dizini): os.makedirs(bozuk_dizini)
                        shutil.move(os.path.join(base_path, folder), os.path.join(bozuk_dizini, folder))
                        self._log(f"🗂️ {folder} -> Bozuk/Eksik PDF dışarıdaki [BOZUK_EVRAK] merkezine karantinaya alındı.", "warning")
                    except Exception as m_err:
                        self._log(f"⚠️ Taşıma hatası ({folder}): {str(m_err)[:40]}", "warning")
                    
                    results_report.append({
                        "Klasör Adı": folder,
                        "Personel Ad Soyad": personel_data["isim_soyisim"],
                        "TC Kimlik No": self._mask_sensitive_data(personel_data["tc"], is_tc=True),
                        "İşlem Durumu": "Bozuk / Eksik Evrak",
                        "Detay": "PDF dosyası bulunamadı, boş veya 0 KB boyutta.",
                        "Zaman": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    self._generate_report(results_report, center_directory)
                    continue

                results_report.append({
                    "Klasör Adı": folder,
                    "Personel Ad Soyad": personel_data["isim_soyisim"],
                    "TC Kimlik No": self._mask_sensitive_data(personel_data["tc"], is_tc=True),
                    "İşlem Durumu": "Başarılı" if status_res == "Success" else "Hata/Engel",
                    "Detay": "" if status_res == "Success" else status_res,
                    "Zaman": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                self._generate_report(results_report, center_directory)

                if status_res == "Success":
                    success_count += 1
                    try:
                        arsiv_dizini = os.path.join(center_directory, "[BASARILI_ARSIV]")
                        if not os.path.exists(arsiv_dizini): os.makedirs(arsiv_dizini)
                        shutil.move(os.path.join(base_path, folder), os.path.join(arsiv_dizini, folder))
                        self._log(f"🗂️ {folder} başarıyla dışarıdaki [BASARILI_ARSIV] dizinine arşivlendi.", "system")
                    except Exception as archive_err:
                        self._log(f"⚠️ Arşivleme hatası ({folder}): {str(archive_err)[:40]}", "warning")
                else: 
                    error_count += 1
                
                self.processed_count_for_eta += 1
                kalan = total_folders - (index + 1)
                
                eta_text = self._calculate_eta(kalan) if kalan > 0 else "00:00"
                progress_val = (index + 1) / total_folders
                pending_text = f"{error_count} / {kalan}"
                
                self.after(0, lambda p=progress_val, s=str(success_count), d=pending_text, e=eta_text: (
                    self.progress_bar.set(p),
                    self.val_success.configure(text=s),
                    self.val_pending.configure(text=d),
                    self.val_eta.configure(text=e)
                ))

                time.sleep(2.0)

            if results_report and self.is_running:
                with open(self.checkpoint_file, "w") as f: json.dump([], f)
                if self.current_report_path:
                    self._log(LANG_PACK[self.current_lang]["report_gen"].format(self.current_report_path), "success")

        except Exception as main_err: 
            self._log(f"[CRITICAL] Ana döngü hatası: {main_err}", "error")
        finally:
            if driver:
                try: driver.quit()
                except Exception: pass
                
            os.system("taskkill /f /im chromedriver.exe >nul 2>&1")
            
            self.after(0, lambda: (
                setattr(self, 'is_running', False), 
                self.start_button.configure(state="normal", text=LANG_PACK[self.current_lang]["start"], fg_color="#2ecc71"), 
                self.pause_button.configure(state="disabled")
            ))

    def _start_automation(self) -> None:
        lg = LANG_PACK[self.current_lang]
        if not self.base_folder_path.get():
            messagebox.showwarning("Warning", lg["no_folder"])
            return
        if self.is_running: return

        self._log(lg["pre_flight_start"], "system")
        try: socket.create_connection(("8.8.8.8", 53), timeout=3)
        except OSError:
            self._log(lg["internet_err"], "error")
            return

        base_path = self.base_folder_path.get()
        if not os.path.exists(base_path):
            messagebox.showwarning("Warning", lg["no_folder"])
            return
        personel_folders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]

        processed_folders = []
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, "r") as f: processed_folders = json.load(f)
            except Exception: pass

        if processed_folders:
            resume = messagebox.askyesno(lg["checkpoint_title"], lg["checkpoint_msg"].format(len(processed_folders)))
            if resume: 
                personel_folders = [f for f in personel_folders if f not in processed_folders]
            else:
                with open(self.checkpoint_file, "w") as f: json.dump([], f)

        # [DÜZELTME] Walrus operatörlü hatalı if ataması düzeltildi
        if not personel_folders:
            messagebox.showinfo("Bilgi", "İşlenecek yeni personel klasörü bulunamadı.")
            return

        self.is_running = True
        self.start_button.configure(state="disabled", text=lg["running"], fg_color="gray")
        self.pause_button.configure(state="normal")
        self.pause_event.set()  
        self.start_time = time.time()
        self.processed_count_for_eta = 0
        self.current_report_path = None 
        self._save_settings()

        threading.Thread(target=self._run_automation_loop, args=(personel_folders, base_path), daemon=True).start()

    # =====================================================================
    # --- UI ÇİZİM METODU (EN ALTTA GÜVENLİ BÖLGEDE) ---
    # =====================================================================
    def _build_ui(self) -> None:
        self.configure(fg_color="#0d1b2a")

        # --- TOP BAR (HEADER) ---
        top_bar = ctk.CTkFrame(self, fg_color="#162a3d", corner_radius=12, height=70)
        top_bar.pack(side="top", fill="x", padx=20, pady=(15, 10))
        top_bar.pack_propagate(False)

        title_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_frame.pack(side="left", padx=20, pady=10)

        self.title_label = ctk.CTkLabel(title_frame, text="", font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"), text_color="#f8f9fa")
        self.title_label.pack(anchor="w")
        
        self.subtitle_label = ctk.CTkLabel(title_frame, text="", font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#62b6cb")
        self.subtitle_label.pack(anchor="w")

        self.lang_dropdown = ctk.CTkOptionMenu(
            top_bar, 
            values=["TR", "EN"], 
            command=self._on_lang_change, 
            width=75, 
            height=30,
            fg_color="#102233", 
            button_color="#62b6cb", 
            button_hover_color="#52a6bb", 
            text_color="#f8f9fa", 
            font=ctk.CTkFont(weight="bold"),
            corner_radius=8
        )
        self.lang_dropdown.pack(side="right", padx=20, pady=20)

        # Ana Gövde Çerçevesi
        main_container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_container.pack(side="top", fill="both", expand=True, padx=20, pady=5)

        # --- GİRİŞ KİMLİK BİLGİLERİ PANELİ ---
        login_card = ctk.CTkFrame(main_container, fg_color="#162a3d", corner_radius=12)
        login_card.pack(pady=8, fill="x", padx=5)
        
        login_card.grid_columnconfigure(0, weight=1)
        login_card.grid_columnconfigure(1, weight=1)
        login_card.grid_columnconfigure(2, weight=1)

        comp_frame = ctk.CTkFrame(login_card, fg_color="transparent")
        comp_frame.grid(row=0, column=0, padx=15, pady=12, sticky="ew")
        self.lbl_comp_txt = ctk.CTkLabel(comp_frame, text="", font=ctk.CTkFont(size=11, weight="bold"), text_color="#62b6cb")
        self.lbl_comp_txt.pack(anchor="w", padx=2, pady=2)
        self.company_entry = ctk.CTkEntry(comp_frame, textvariable=self.company_code_var, placeholder_text="şirket kodu", height=35, fg_color="#0d1b2a", border_color="#2b3e50", text_color="#f8f9fa", border_width=1)
        self.company_entry.pack(fill="x")

        user_frame = ctk.CTkFrame(login_card, fg_color="transparent")
        user_frame.grid(row=0, column=1, padx=15, pady=12, sticky="ew")
        self.lbl_user_txt = ctk.CTkLabel(user_frame, text="", font=ctk.CTkFont(size=11, weight="bold"), text_color="#62b6cb")
        self.lbl_user_txt.pack(anchor="w", padx=2, pady=2)
        self.username_entry = ctk.CTkEntry(user_frame, textvariable=self.username_var, placeholder_text="username", height=35, fg_color="#0d1b2a", border_color="#2b3e50", text_color="#f8f9fa", border_width=1)
        self.username_entry.pack(fill="x")

        pass_frame = ctk.CTkFrame(login_card, fg_color="transparent")
        pass_frame.grid(row=0, column=2, padx=15, pady=12, sticky="ew")
        self.lbl_pass_txt = ctk.CTkLabel(pass_frame, text="", font=ctk.CTkFont(size=11, weight="bold"), text_color="#62b6cb")
        self.lbl_pass_txt.pack(anchor="w", padx=2, pady=2)
        self.password_entry = ctk.CTkEntry(pass_frame, textvariable=self.password_var, placeholder_text="••••••••", show="*", height=35, fg_color="#0d1b2a", border_color="#2b3e50", text_color="#f8f9fa", border_width=1)
        self.password_entry.pack(fill="x")

        # --- KLASÖR BAĞLANTI PANELİ ---
        folder_card = ctk.CTkFrame(main_container, fg_color="#162a3d", corner_radius=12)
        folder_card.pack(pady=8, fill="x", padx=5)

        self.folder_entry = ctk.CTkEntry(folder_card, textvariable=self.base_folder_path, placeholder_text="", height=38, fg_color="#0d1b2a", border_color="#2b3e50", text_color="#f8f9fa", border_width=1)
        self.folder_entry.pack(side="left", padx=15, pady=15, expand=True, fill="x")

        self.folder_button = ctk.CTkButton(folder_card, text="", command=self._select_folder, width=120, height=38, fg_color="#62b6cb", hover_color="#52a6bb", text_color="#0d1b2a", font=ctk.CTkFont(weight="bold"), corner_radius=8)
        self.folder_button.pack(side="right", padx=15, pady=15)

        # --- GELİŞMİŞ AYARLAR PANELİ ---
        config_card = ctk.CTkFrame(main_container, fg_color="#162a3d", corner_radius=12)
        config_card.pack(pady=8, fill="x", padx=5)

        config_card.grid_columnconfigure(0, weight=1)
        config_card.grid_columnconfigure(1, weight=1)

        self.cb_headless = ctk.CTkCheckBox(config_card, text="", variable=self.headless_var, text_color="#f8f9fa", fg_color="#62b6cb", border_color="#62b6cb", font=ctk.CTkFont(size=12))
        self.cb_headless.grid(row=0, column=0, padx=20, pady=12, sticky="w")

        self.sw_retry_cb = ctk.CTkSwitch(config_card, text="", variable=self.retry_enabled, progress_color="#62b6cb", text_color="#f8f9fa", font=ctk.CTkFont(size=12))
        self.sw_retry_cb.grid(row=1, column=0, padx=20, pady=12, sticky="w")

        self.sw_alert_cb = ctk.CTkSwitch(config_card, text="", variable=self.alert_dismiss_enabled, progress_color="#62b6cb", text_color="#f8f9fa", font=ctk.CTkFont(size=12))
        self.sw_alert_cb.grid(row=1, column=1, padx=20, pady=12, sticky="w")

        # --- YAN YANA MODERN KPI METRİK SİSTEMİ ---
        kpi_container = ctk.CTkFrame(main_container, fg_color="transparent")
        kpi_container.pack(pady=10, fill="x", padx=5)
        kpi_container.grid_columnconfigure(0, weight=1)
        kpi_container.grid_columnconfigure(1, weight=1)
        kpi_container.grid_columnconfigure(2, weight=1)

        card_success = ctk.CTkFrame(kpi_container, fg_color="#162a3d", border_color="#2ecc71", border_width=1, corner_radius=12, height=85)
        card_success.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        card_success.pack_propagate(False)
        self.kpi_lbl_succ = ctk.CTkLabel(card_success, text="", font=ctk.CTkFont(size=10, weight="bold"), text_color="#94a3b8")
        self.kpi_lbl_succ.pack(pady=(12, 0), padx=15, anchor="w")
        self.val_success = ctk.CTkLabel(card_success, text="0", font=ctk.CTkFont(size=24, weight="bold"), text_color="#2ecc71")
        self.val_success.pack(pady=(2, 10), padx=15, anchor="w")

        card_pending = ctk.CTkFrame(kpi_container, fg_color="#162a3d", border_color="#3b82f6", border_width=1, corner_radius=12, height=85)
        card_pending.grid(row=0, column=1, padx=5, sticky="ew")
        card_pending.pack_propagate(False)
        self.kpi_lbl_fail = ctk.CTkLabel(card_pending, text="", font=ctk.CTkFont(size=10, weight="bold"), text_color="#94a3b8")
        self.kpi_lbl_fail.pack(pady=(12, 0), padx=15, anchor="w")
        self.val_pending = ctk.CTkLabel(card_pending, text="0 / 0", font=ctk.CTkFont(size=22, weight="bold"), text_color="#3b82f6")
        self.val_pending.pack(pady=(4, 10), padx=15, anchor="w")

        card_eta = ctk.CTkFrame(kpi_container, fg_color="#162a3d", border_color="#eab308", border_width=1, corner_radius=12, height=85)
        card_eta.grid(row=0, column=2, padx=(10, 0), sticky="ew")
        card_eta.pack_propagate(False)
        self.kpi_lbl_eta = ctk.CTkLabel(card_eta, text="", font=ctk.CTkFont(size=10, weight="bold"), text_color="#94a3b8")
        self.kpi_lbl_eta.pack(pady=(12, 0), padx=15, anchor="w")
        self.val_eta = ctk.CTkLabel(card_eta, text="--:--", font=ctk.CTkFont(size=22, weight="bold"), text_color="#eab308")
        self.val_eta.pack(pady=(4, 10), padx=15, anchor="w")

        self.progress_bar = ctk.CTkProgressBar(main_container, height=10, progress_color="#62b6cb", fg_color="#162a3d", corner_radius=5)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=5, pady=(10, 15))

        # --- OPERASYON KONTROL MERKEZİ ---
        button_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        button_frame.pack(pady=5, fill="x", padx=5)

        button_frame.grid_columnconfigure(0, weight=3)
        button_frame.grid_columnconfigure(1, weight=1)

        self.start_button = ctk.CTkButton(
            button_frame, 
            text="", 
            fg_color="#2ecc71", 
            hover_color="#27ae60", 
            command=self._start_automation, 
            height=45, 
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold"), 
            text_color="#f8f9fa"
        )
        self.start_button.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.pause_button = ctk.CTkButton(
            button_frame, 
            text="", 
            fg_color="#e67e22", 
            hover_color="#d35400", 
            command=self._toggle_pause, 
            height=45, 
            corner_radius=10,
            state="disabled", 
            font=ctk.CTkFont(size=13, weight="bold"), 
            text_color="#f8f9fa"
        )
        self.pause_button.grid(row=0, column=1, sticky="ew")

        # --- SİBER KONSOL TERMİNAL KUTUSU ---
        log_card = ctk.CTkFrame(main_container, fg_color="#162a3d", corner_radius=12)
        log_card.pack(pady=15, fill="both", expand=True, padx=5)

        self.log_textInput = tk.Text(log_card, bg="#0a111a", fg="#f8f9fa", font=("Consolas", 10), wrap="word", bd=0, highlightthickness=0)
        self.log_textInput.pack(fill="both", expand=True, padx=12, pady=12)
        self.log_text = self.log_textInput 

        self.log_text.tag_config("normal", foreground="#f8f9fa")
        self.log_text.tag_config("system", foreground="#62b6cb")
        self.log_text.tag_config("success", foreground="#2ecc71", font=("Consolas", 10, "bold"))
        self.log_text.tag_config("error", foreground="#e74c3c", font=("Consolas", 10, "bold"))
        self.log_text.tag_config("warning", foreground="#f1c40f")
        self.log_text.configure(state="disabled")

    def _update_ui_texts(self) -> None:
        lg = LANG_PACK[self.current_lang]
        self.title(lg["title"])
        self.title_label.configure(text=lg["title"])
        self.subtitle_label.configure(text=lg["subtitle"])
        
        self.folder_button.configure(text=lg["select_folder"])
        self.folder_entry.configure(placeholder_text=lg["placeholder"])
        self.cb_headless.configure(text=lg["headless"])
        self.sw_retry_cb.configure(text=lg["sw_retry"])
        self.sw_alert_cb.configure(text=lg["sw_alert"])
        self.lbl_comp_txt.configure(text=lg["lbl_comp"]) 
        self.lbl_user_txt.configure(text=lg["lbl_user"])
        self.lbl_pass_txt.configure(text=lg["lbl_pass"])
        
        self.kpi_lbl_succ.configure(text=lg["kpi_success"])
        self.kpi_lbl_fail.configure(text=lg["kpi_failed"])
        self.kpi_lbl_eta.configure(text=lg["kpi_eta"])
        
        self.pause_button.configure(text=lg["pause"] if self.pause_event.is_set() else lg["resume"])
        
        if not self.is_running:
            self.start_button.configure(text=lg["start"])
        else:
            self.start_button.configure(text=lg["running"])
        self.lang_dropdown.set(self.current_lang)


if __name__ == "__main__":
    try:
        app = WellcomeRPAApp()
        app.mainloop()
    except KeyboardInterrupt: os._exit(0)