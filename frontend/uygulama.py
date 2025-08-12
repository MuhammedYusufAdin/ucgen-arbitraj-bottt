import os
import uuid
import datetime
import base64
import requests
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.metrics import dp

# Tam ekran ayarı
Window.clearcolor = (0.65, 0.78, 0.91, 1)
Window.fullscreen = 'auto'

# Dosya yolları
dosya_yolu = os.path.join(os.path.dirname(__file__), "durum.txt")
tarih_dosya_yolu = os.path.join(os.path.dirname(__file__), "tarih.txt")
aktiflik_dosya_yolu = os.path.join(os.path.dirname(__file__), "aktiflik.txt")
eski_sifre_dosya_yolu = os.path.join(os.path.dirname(__file__), "eski_sifre.txt")

class GirisEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint=(1, 1))

        self.label = Label(
            text='Şifreni Gir:', font_size=dp(32), color=(1, 1, 1, 1), size_hint=(1, 0.2)
        )
        self.text_input = TextInput(
            password=True, hint_text="Şifre", multiline=False, size_hint=(1, 0.2),
            foreground_color=(1, 1, 1, 1), background_color=(0.29, 0.56, 0.89, 1),
            hint_text_color=(0.9, 0.9, 0.9, 1)
        )
        button = Button(
            text="Giriş Yap", size_hint=(1, 0.2),
            background_color=(0.29, 0.56, 0.89, 1), color=(1, 1, 1, 1)
        )
        button.bind(on_press=self.sifre_kontrol)
        self.sonuc = Label(
            text="", font_size=dp(24), color=(1, 1, 1, 1), size_hint=(1, 0.2)
        )

        layout.add_widget(self.label)
        layout.add_widget(self.text_input)
        layout.add_widget(button)
        layout.add_widget(self.sonuc)
        self.add_widget(layout)

    def sifre_kontrol(self, instance):
        sayilar = [
            47596758,1434234,2342342342,234234234
        ]
        girilen_sifre = self.text_input.text.strip()

        try:
            girilen_sifre_int = int(girilen_sifre)
        except ValueError:
            self.sonuc.text = "Şifre sadece rakamlardan oluşmalı!"
            self.sonuc.color = (1, 0, 0, 1)
            return

        if os.path.exists(eski_sifre_dosya_yolu):
            with open(eski_sifre_dosya_yolu, 'r', encoding='utf-8') as f:
                eski_sifreler = f.read().splitlines()
                if girilen_sifre in eski_sifreler:
                    self.sonuc.text = "Bu şifre daha önce kullanılmış!"
                    self.sonuc.color = (1, 0, 0, 1)
                    return

        if girilen_sifre_int in sayilar:
            self.sonuc.text = "Giriş Başarılı"
            self.sonuc.color = (0, 1, 0, 1)
            with open(dosya_yolu, 'w', encoding='utf-8') as dosya:
                dosya.write("doğrulandı")
            with open(tarih_dosya_yolu, 'w', encoding='utf-8') as tarih_dosya:
                tarih_dosya.write(datetime.datetime.now().isoformat())
            with open(eski_sifre_dosya_yolu, 'a', encoding='utf-8') as f:
                f.write(girilen_sifre + '\n')
            self.manager.current = 'welcome'
        else:
            self.sonuc.text = "Hatalı Şifre"
            self.sonuc.color = (1, 0, 0, 1)

class Welcome(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint=(1, 1))

        self.label = Label(
            text="🚀 Welcome to Arbix! Üçgen arbitraj fırsatlarını anında yakala, "
                 "kazanç senin kontrol senin. Piyasayı sen yönet! -Bu Bir BotStore Ürünüdür-",
            color=(1, 1, 1, 1), font_size=dp(18), halign='center', valign='middle', size_hint=(1, 0.6)
        )
        self.label.bind(size=self.label.setter('text_size'))
        button = Button(
            text="Devam Et", size_hint=(1, 0.2),
            background_color=(0.29, 0.56, 0.89, 1), color=(1, 1, 1, 1)
        )
        button.bind(on_press=self.devam_et)

        layout.add_widget(self.label)
        layout.add_widget(button)
        self.add_widget(layout)

    def devam_et(self, instance):
        self.manager.current = 'cryptoapp'

class CryptoApp(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint=(1, 1))

        self.label = Label(
            text="Lütfen Aşağıda İstenilen Bilgileri Giriniz", color=(1, 1, 1, 1), size_hint=(1, 0.2)
        )
        self.api_key_input = TextInput(
            hint_text="API Key", multiline=False, size_hint=(1, 0.2),
            foreground_color=(1, 1, 1, 1), background_color=(0.29, 0.56, 0.89, 1),
            hint_text_color=(0.9, 0.9, 0.9, 1)
        )
        self.api_secret_input = TextInput(
            password=True, hint_text="API Secret", multiline=False, size_hint=(1, 0.2),
            foreground_color=(1, 1, 1, 1), background_color=(0.29, 0.56, 0.89, 1),
            hint_text_color=(0.9, 0.9, 0.9, 1)
        )
        self.error_label = Label(
            text="", color=(1, 0, 0, 1), size_hint=(1, 0.2)
        )
        button = Button(
            text="Devam Et", size_hint=(1, 0.2),
            background_color=(0.29, 0.56, 0.89, 1), color=(1, 1, 1, 1)
        )
        button.bind(on_press=self.api_kontrol)

        layout.add_widget(self.label)
        layout.add_widget(self.api_key_input)
        layout.add_widget(self.api_secret_input)
        layout.add_widget(self.error_label)
        layout.add_widget(button)
        self.add_widget(layout)

    def api_kontrol(self, instance):
        api_key = self.api_key_input.text.strip()
        api_secret = self.api_secret_input.text.strip()

        if not api_key or not api_secret:
            self.error_label.text = "API Key ve Secret boş bırakılamaz!"
            return
        if len(api_key) < 30 or len(api_secret) < 30:
            self.error_label.text = "API Key veya Secret çok kısa!"
            return
        if any(ord(char) > 127 for char in api_key) or any(ord(char) > 127 for char in api_secret):
            self.error_label.text = "API Key ve Secret yalnızca ASCII karakterler içermelidir!"
            return

        is_testnet = True
        base_url = "https://testnet.binance.vision/api/v3/ping" if is_testnet else "https://api.binance.com/api/v3/ping"

        try:
            response = requests.get(base_url, auth=(api_key, api_secret), timeout=5)
            if response.status_code == 200:
                self.error_label.text = ""
                self.manager.current = 'cointype'
            elif response.status_code == 401:
                self.error_label.text = "Hatalı API bilgileri girişi!"
            else:
                self.error_label.text = f"API bağlantı hatası: {response.status_code}"
        except requests.exceptions.RequestException as e:
            self.error_label.text = f"API bağlantı hatası: {str(e)}"

class CoinType(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint=(1, 1))

        self.label = Label(
            text="Lütfen Aralarında İşlem Yapmak İstediğiniz 3 Coini Giriniz",
            color=(1, 1, 1, 1), size_hint=(1, 0.1)
        )
        self.coin1_input = TextInput(
            hint_text="Coin 1", multiline=False, size_hint=(1, 0.15),
            foreground_color=(1, 1, 1, 1), background_color=(0.29, 0.56, 0.89, 1),
            hint_text_color=(0.9, 0.9, 0.9, 1)
        )
        self.coin2_input = TextInput(
            hint_text="Coin 2", multiline=False, size_hint=(1, 0.15),
            foreground_color=(1, 1, 1, 1), background_color=(0.29, 0.56, 0.89, 1),
            hint_text_color=(0.9, 0.9, 0.9, 1)
        )
        self.coin3_input = TextInput(
            hint_text="Coin 3", multiline=False, size_hint=(1, 0.15),
            foreground_color=(1, 1, 1, 1), background_color=(0.29, 0.56, 0.89, 1),
            hint_text_color=(0.9, 0.9, 0.9, 1)
        )
        self.amount_label = Label(
            text="Miktarını Giriniz(USD)", color=(1, 1, 1, 1), size_hint=(1, 0.1)
        )
        self.amount_input = TextInput(
            hint_text="Miktar (Sadece sayı)", multiline=False, size_hint=(1, 0.15),
            input_filter='int', foreground_color=(1, 1, 1, 1),
            background_color=(0.29, 0.56, 0.89, 1), hint_text_color=(0.9, 0.9, 0.9, 1)
        )
        button = Button(
            text="Onayla", size_hint=(1, 0.2),
            background_color=(0.29, 0.56, 0.89, 1), color=(1, 1, 1, 1)
        )
        button.bind(on_press=self.gonder_coins)

        layout.add_widget(self.label)
        layout.add_widget(self.coin1_input)
        layout.add_widget(self.coin2_input)
        layout.add_widget(self.coin3_input)
        layout.add_widget(self.amount_label)
        layout.add_widget(self.amount_input)
        layout.add_widget(button)
        self.add_widget(layout)

    def show_popup(self, mesaj):
        popup = Popup(
            title='Bilgi', content=Label(text=mesaj, halign='center'),
            size_hint=(0.8, 0.4)
        )
        popup.open()

    def gonder_coins(self, instance):
        if (not self.coin1_input.text.strip() or
                not self.coin2_input.text.strip() or
                not self.coin3_input.text.strip() or
                not self.amount_input.text.strip()):
            self.label.text = "Lütfen tüm bilgileri eksiksiz giriniz!"
            self.label.color = (1, 0, 0, 1)
            return

        miktar = self.amount_input.text.strip()
        api_key = self.manager.get_screen('cryptoapp').api_key_input.text.strip()
        api_secret = self.manager.get_screen('cryptoapp').api_secret_input.text.strip()
        coin1 = self.coin1_input.text.strip()
        coin2 = self.coin2_input.text.strip()
        coin3 = self.coin3_input.text.strip()

        if not api_key or not api_secret:
            self.show_popup("API Key ve Secret boş bırakılamaz!")
            return

        api_key_b64 = base64.b64encode(api_key.encode('utf-8')).decode('utf-8')
        api_secret_b64 = base64.b64encode(api_secret.encode('utf-8')).decode('utf-8')

        bot_id = str(uuid.uuid4())
        with open("id.txt", "w", encoding="utf-8") as f:
            f.write(bot_id)

        url = "http://185.255.95.86:5000/start_bot"
        data = {
            "bot_id": bot_id,
            "api_key": api_key_b64,
            "api_secret": api_secret_b64,
            "coin1": coin1,
            "coin2": coin2,
            "coin3": coin3,
            "amount": miktar
        }

        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                with open(aktiflik_dosya_yolu, 'w', encoding='utf-8') as f:
                    f.write("gönderildi")
                with open(tarih_dosya_yolu, 'w', encoding='utf-8') as tarih_dosya:
                    tarih_dosya.write(datetime.datetime.now().isoformat())
                self.show_popup("Veriler başarıyla gönderildi.")
                self.manager.current = 'aktifbot'
            else:
                self.show_popup(f"Sunucu hatası: {response.status_code}")
        except requests.ConnectionError:
            self.show_popup("Bağlantı hatası: İnternet bağlantınızı kontrol edin.")
        except requests.Timeout:
            self.show_popup("Bağlantı hatası: Sunucuya zaman aşımı nedeniyle ulaşılamadı.")
        except Exception as e:
            self.show_popup(f"Bağlantı hatası: {str(e)}")

class AktifBotEkrani(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10), size_hint=(1, 1))

        bot_label = Label(
            text="Arbix Bot", color=(1, 1, 1, 1), font_size=dp(18),
            size_hint=(1, 0.2), halign='center', valign='middle'
        )
        bot_label.bind(size=bot_label.setter('text_size'))
        durdur_button = Button(
            text="Durdur", size_hint=(1, 0.2),
            background_color=(0.1, 0.15, 0.3, 1), color=(1, 1, 1, 1), font_size=dp(16)
        )
        durdur_button.bind(on_press=self.durdur_botu)

        layout.add_widget(bot_label)
        layout.add_widget(durdur_button)
        self.add_widget(layout)

    def durdur_botu(self, instance):
        try:
            with open(aktiflik_dosya_yolu, "w", encoding="utf-8") as f:
                f.write("aktifdegil")
            with open("id.txt", "r", encoding="utf-8") as f:
                bot_id = f.read().strip()

            data = {"bot_id": bot_id, "durum": "dur"}
            response = requests.post("http://185.255.95.86:5000/stop_bot", json=data)

            if response.status_code == 200:
                mesaj = "Bot başarıyla durduruldu."
            elif response.status_code == 404:
                mesaj = "Bot durdurulamadı: Endpoint bulunamadı."
            else:
                mesaj = f"Hata oluştu: {response.status_code}"
        except Exception as e:
            mesaj = f"Bağlantı hatası: {str(e)}"

        box = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        label = Label(text=mesaj, halign='center')
        btn = Button(text='Kapat', size_hint=(1, 0.3))
        box.add_widget(label)
        box.add_widget(btn)

        popup = Popup(title='Durum', content=box, size_hint=(0.75, 0.4))
        btn.bind(on_press=popup.dismiss)
        popup.open()

class AktiflikOnaylama(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20), size_hint=(1, 1))

        self.header_label = Label(
            text="🔄 Bot Aktiflik Onaylama", font_size=dp(22), color=(1, 1, 1, 1), size_hint=(1, 0.2)
        )
        self.info_label = Label(
            text="Bot aktif mi, durduruldu mu kontrol ediliyor...",
            font_size=dp(18), color=(1, 1, 1, 1), halign='center', valign='middle', size_hint=(1, 0.2)
        )
        self.info_label.bind(size=self.info_label.setter('text_size'))
        self.status_label = Label(
            text="", font_size=dp(16), color=(1, 1, 1, 1), size_hint=(1, 0.2),
            halign='center', valign='middle'
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        self.yenile_button = Button(
            text="🔁 Durumu Yenile", size_hint=(1, 0.2),
            background_color=(0.3, 0.6, 1, 1), color=(1, 1, 1, 1), font_size=dp(18)
        )
        self.yenile_button.bind(on_press=self.durum_kontrol)

        layout.add_widget(self.header_label)
        layout.add_widget(self.info_label)
        layout.add_widget(self.status_label)
        layout.add_widget(self.yenile_button)
        self.add_widget(layout)

    def durum_kontrol(self, instance):
        if os.path.exists(aktiflik_dosya_yolu):
            with open(aktiflik_dosya_yolu, 'r', encoding='utf-8') as f:
                aktiflik = f.read().strip()
            if aktiflik == "gönderildi":
                self.status_label.text = "✅ Bot şu an AKTİF."
                self.status_label.color = (0, 1, 0, 1)
                self.manager.current = 'aktifbot'
            elif aktiflik == "aktifdegil":
                self.status_label.text = "❌ Bot durdurulmuş."
                self.status_label.color = (1, 0, 0, 1)
                self.manager.current = 'cryptoapp'
            else:
                self.status_label.text = f"⚠️ Bilinmeyen durum: {aktiflik}"
                self.status_label.color = (1, 0.5, 0, 1)
        else:
            self.status_label.text = "⚠️ Aktiflik kaydı bulunamadı."
            self.status_label.color = (1, 0.5, 0, 1)

class MainApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(GirisEkrani(name='giris'))
        sm.add_widget(Welcome(name='welcome'))
        sm.add_widget(CryptoApp(name='cryptoapp'))
        sm.add_widget(CoinType(name='cointype'))
        sm.add_widget(AktiflikOnaylama(name='onay'))
        sm.add_widget(AktifBotEkrani(name='aktifbot'))
        sm.current = 'giris'
        self.sm = sm
        return sm

    def on_start(self):
        try:
            with open(dosya_yolu, 'r', encoding='utf-8') as f:
                icerik = f.read().strip()
                if icerik == "doğrulandı":
                    with open(tarih_dosya_yolu, 'r', encoding='utf-8') as tarih_dosya:
                        tarih_str = tarih_dosya.read().strip()
                        tarih = datetime.datetime.fromisoformat(tarih_str)
                        if (datetime.datetime.now() - tarih).days < 30:
                            if os.path.exists(aktiflik_dosya_yolu):
                                with open(aktiflik_dosya_yolu, 'r', encoding='utf-8') as aktiflik_dosya:
                                    aktiflik = aktiflik_dosya.read().strip()
                                    if aktiflik == "gönderildi":
                                        self.sm.current = 'aktifbot'
                                    elif aktiflik == "aktifdegil":
                                        self.sm.current = 'cryptoapp'
                                    else:
                                        self.sm.current = 'cryptoapp'
                            else:
                                self.sm.current = 'cryptoapp'
                        else:
                            self.sm.current = 'giris'
        except FileNotFoundError:
            self.sm.current = 'giris'

if __name__ == "__main__":
    MainApp().run()