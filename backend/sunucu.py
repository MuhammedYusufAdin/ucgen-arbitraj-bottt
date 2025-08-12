from flask import Flask, request, jsonify
import threading
import time
import base64
import ccxt
import logging
from threading import Lock
import uuid

# Log yapılandırması
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
running_bots = {}
bot_lock = Lock()

def decode_base64(s):
    """Base64 kodlu string'i çözer."""
    return base64.b64decode(s).decode()

def check_liquidity(exchange, pair, amount, side='buy'):
    """Sipariş defterinde yeterli likidite olup olmadığını kontrol eder."""
    try:
        order_book = exchange.fetch_order_book(pair, limit=10)
        if side == 'buy':
            available_volume = sum([bid[1] for bid in order_book['bids']])
            return available_volume >= amount
        else:  # sell
            available_volume = sum([ask[1] for ask in order_book['asks']])
            return available_volume >= amount
    except Exception as e:
        logger.error(f"Likidite kontrol hatası: {e}")
        return False

def bot_worker(bot_id):
    bot_data = running_bots.get(bot_id)
    if not bot_data:
        return
    stop_event = bot_data['stop_event']
    params = bot_data['params']

    # API anahtarlarını çöz
    try:
        api_key = decode_base64(params['api_key'])
        api_secret = decode_base64(params['api_secret'])
        use_testnet = params.get('testnet', False)
    except Exception as e:
        logger.error(f"[{bot_id}] API anahtarı çözümlenemedi: {e}")
        return

    # Binance bağlantısı
    exchange = ccxt.binance({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'testnet': True,
        'options': {'defaultType': 'spot'},
    })

    if use_testnet:
        exchange.set_sandbox_mode(True)

    # Parametreleri al
    try:
        miktar_try = float(params['miktar'])
        coin1 = params['coin1'].upper()
        coin2 = params['coin2'].upper()
        coin3 = params['coin3'].upper()

        if miktar_try <= 0:
            logger.error(f"[{bot_id}] Miktar pozitif olmalı.")
            return

        pair1 = f"{coin1}/TRY"
        pair2 = f"{coin2}/TRY"
        pair3 = f"{coin3}/TRY"
    except Exception as e:
        logger.error(f"[{bot_id}] Parametre hatası: {e}")
        return

    fee_rate = 0.001
    markets = exchange.load_markets()

    # Market kontrolü
    if not all(pair in markets for pair in [pair1, pair2, pair3]):
        logger.warning(f"[{bot_id}] Bir veya daha fazla market bulunamadı: {pair1}, {pair2}, {pair3}")
        return

    while not stop_event.is_set():
        try:
            # Fiyatları al
            price1 = exchange.fetch_ticker(pair1)['last']
            price2 = exchange.fetch_ticker(pair2)['last']
            price3 = exchange.fetch_ticker(pair3)['last']

            # Arbitraj hesaplaması
            amount_coin1 = miktar_try / price1
            amount_coin2 = (amount_coin1 * (1 - fee_rate)) * (price1 / price2)
            amount_coin3 = (amount_coin2 * (1 - fee_rate)) * (price2 / price3)
            final_try = (amount_coin3 * (1 - fee_rate)) * price3

            logger.info(f"[{bot_id}] Simülasyon sonucu: Başlangıç TRY = {miktar_try:.2f}, Tahmini Son TRY = {final_try:.2f}")

            if final_try > miktar_try * 1.001:  # %0.1 kazanç şartı
                logger.info(f"[{bot_id}] ✅ Arbitraj fırsatı bulundu! İşlemler başlatılıyor.")

                # 1. İşlem: coin1/TRY alımı (örn. BTC/TRY)
                if not check_liquidity(exchange, pair1, amount_coin1, 'buy'):
                    logger.warning(f"[{bot_id}] Yetersiz likidite: {pair1}")
                    time.sleep(10)
                    continue

                # Bakiye kontrolü
                balance = exchange.fetch_balance()
                try_balance = balance['TRY']['free']
                if try_balance < miktar_try:
                    logger.error(f"[{bot_id}] Yetersiz TRY bakiyesi: {try_balance} < {miktar_try}")
                    time.sleep(10)
                    continue

                order1 = exchange.create_market_buy_order(pair1, amount_coin1)
                time.sleep(exchange.rateLimit / 1000)

                # Emir durumunu kontrol et
                order_status = exchange.fetch_order(order1['id'], pair1)
                while order_status['status'] != 'closed':
                    if order_status['status'] in ['canceled', 'failed']:
                        logger.error(f"[{bot_id}] İlk emir başarısız: {order_status['status']}")
                        time.sleep(10)
                        break
                    time.sleep(1)
                    order_status = exchange.fetch_order(order1['id'], pair1)
                else:
                    amount_coin1_filled = order_status['filled']
                    logger.info(f"[{bot_id}] {pair1} alımı tamamlandı: {amount_coin1_filled} {coin1}")

                # 2. İşlem: coin2/TRY satışı (örn. ETH/TRY)
                amount_coin2 = (amount_coin1_filled * (1 - fee_rate)) * (price1 / price2)
                if not check_liquidity(exchange, pair2, amount_coin2, 'sell'):
                    logger.warning(f"[{bot_id}] Yetersiz likidite: {pair2}")
                    time.sleep(10)
                    continue

                # Bakiye kontrolü
                balance = exchange.fetch_balance()
                coin1_balance = balance[coin1]['free']
                if coin1_balance < amount_coin1_filled:
                    logger.error(f"[{bot_id}] Yetersiz {coin1} bakiyesi: {coin1_balance} < {amount_coin1_filled}")
                    time.sleep(10)
                    continue

                order2 = exchange.create_market_sell_order(pair2, amount_coin2)
                time.sleep(exchange.rateLimit / 1000)

                # Emir durumunu kontrol et
                order_status = exchange.fetch_order(order2['id'], pair2)
                while order_status['status'] != 'closed':
                    if order_status['status'] in ['canceled', 'failed']:
                        logger.error(f"[{bot_id}] İkinci emir başarısız: {order_status['status']}")
                        time.sleep(10)
                        break
                    time.sleep(1)
                    order_status = exchange.fetch_order(order2['id'], pair2)
                else:
                    amount_coin2_filled = order_status['filled']
                    logger.info(f"[{bot_id}] {pair2} satışı tamamlandı: {amount_coin2_filled} {coin2}")

                # 3. İşlem: coin3/TRY satışı (örn. LTC/TRY)
                amount_coin3 = (amount_coin2_filled * (1 - fee_rate)) * (price2 / price3)
                if not check_liquidity(exchange, pair3, amount_coin3, 'sell'):
                    logger.warning(f"[{bot_id}] Yetersiz likidite: {pair3}")
                    time.sleep(10)
                    continue

                # Bakiye kontrolü
                balance = exchange.fetch_balance()
                coin2_balance = balance[coin2]['free']
                if coin2_balance < amount_coin2_filled:
                    logger.error(f"[{bot_id}] Yetersiz {coin2} bakiyesi: {coin2_balance} < {amount_coin2_filled}")
                    time.sleep(10)
                    continue

                order3 = exchange.create_market_sell_order(pair3, amount_coin3)
                time.sleep(exchange.rateLimit / 1000)

                # Emir durumunu kontrol et
                order_status = exchange.fetch_order(order3['id'], pair3)
                while order_status['status'] != 'closed':
                    if order_status['status'] in ['canceled', 'failed']:
                        logger.error(f"[{bot_id}] Üçüncü emir başarısız: {order_status['status']}")
                        time.sleep(10)
                        break
                    time.sleep(1)
                    order_status = exchange.fetch_order(order3['id'], pair3)
                else:
                    amount_coin3_filled = order_status['filled']
                    final_try_actual = (amount_coin3_filled * (1 - fee_rate)) * price3
                    logger.info(f"[{bot_id}] ✅ Arbitraj tamamlandı. Kazanç: {final_try_actual - miktar_try:.2f} TRY")

            else:
                logger.info(f"[{bot_id}] ❌ Kârlı arbitraj fırsatı yok. Bekleniyor...")
                time.sleep(10)

        except ccxt.InsufficientFunds as e:
            logger.error(f"[{bot_id}] Yetersiz bakiye: {e}")
            time.sleep(10)
        except ccxt.NetworkError as e:
            logger.error(f"[{bot_id}] Ağ hatası: {e}")
            time.sleep(60)
        except ccxt.ExchangeError as e:
            logger.error(f"[{bot_id}] Borsa hatası: {e}")
            time.sleep(10)
        except Exception as e:
            logger.error(f"[{bot_id}] Beklenmedik hata: {e}")
            time.sleep(10)

@app.route('/start_bot', methods=['POST'])
def start_bot():
    data = request.get_json()
    if not data or not data.get('bot_id'):
        return jsonify({'status': 'error', 'message': 'Geçersiz veri'}), 400

    try:
        params = {
            'miktar': float(data.get('amount', 0)),
            'coin1': data.get('coin1'),
            'coin2': data.get('coin2'),
            'coin3': data.get('coin3'),
            'api_key': data.get('api_key'),
            'api_secret': data.get('api_secret'),
            'testnet': data.get('testnet', False),
        }
        if not all([params['coin1'], params['coin2'], params['coin3']]) or params['miktar'] <= 0:
            return jsonify({'status': 'error', 'message': 'Geçersiz parametreler'}), 400
    except ValueError as e:
        return jsonify({'status': 'error', 'message': f'Parametre hatası: {e}'}), 400

    bot_id = data['bot_id']
    with bot_lock:
        if bot_id in running_bots:
            running_bots[bot_id]['stop_event'].set()
            running_bots[bot_id]['thread'].join()
        stop_event = threading.Event()
        thread = threading.Thread(target=bot_worker, args=(bot_id,), daemon=True)
        running_bots[bot_id] = {'stop_event': stop_event, 'params': params, 'thread': thread}
        thread.start()
    logger.info(f"[{bot_id}] Bot başlatıldı.")
    return jsonify({'status': 'started', 'bot_id': bot_id})

@app.route('/stop_bot', methods=['POST'])
def stop_bot():
    data = request.get_json()
    if not data or not data.get('bot_id'):
        return jsonify({'status': 'error', 'message': 'Geçersiz veri'}), 400

    bot_id = data.get('bot_id')
    with bot_lock:
        if bot_id not in running_bots:
            return jsonify({'status': 'error', 'message': 'bot_id bulunamadı'}), 404
        running_bots[bot_id]['stop_event'].set()
        running_bots[bot_id]['thread'].join()
        del running_bots[bot_id]
    logger.info(f"[{bot_id}] Bot durduruldu.")
    return jsonify({'status': 'stopped', 'bot_id': bot_id})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)