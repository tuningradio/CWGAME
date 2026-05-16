import tkinter as tk
import time
import numpy as np
import pyaudio
from pynput import mouse
import logging

# ロギング設定
logging.basicConfig(filename='morse_tester.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

logging.debug("プログラム開始")

# グローバル変数
MORSE_CHECK_TIMEOUT = 800
SAMPLE_RATE = 44100
FREQUENCY = 800
SHORT_THRESHOLD = 0.35
LONG_THRESHOLD = 0.55
BUFFER_SIZE = 128 # バッファサイズを若干大きく
PRE_BUFFER_SIZE = 4096

class MorseTester:
    def __init__(self, root):
        self.root = root
        self.click_start_time = 0
        self.last_click_time = 0
        self.current_morse = ""
        self.timer_id = None
        self.playing = False
        self.stream = None
        self.current_phase = 0
        self.pre_buffer = (np.sin(2 * np.pi * np.arange(PRE_BUFFER_SIZE) * FREQUENCY / SAMPLE_RATE)).astype(np.float32)
        self.pre_buffer_index = 0

        try:
            self.p = pyaudio.PyAudio()
            logging.debug("pyaudio初期化成功")
        except Exception as e:
            logging.error(f"pyaudioの初期化エラー: {e}")
            print(f"pyaudioの初期化エラー: {e}")
            root.destroy()
            return

        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.daemon = True
        self.listener.start()
        logging.debug("マウスリスナースタート")
        print("テスト開始。マウスをクリックしてください。")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def start_tone(self):
        if self.stream is None:
            self.current_phase = 0
            self.pre_buffer_index = 0
            self.stream = self.p.open(format=pyaudio.paFloat32,
                                     channels=1,
                                     rate=SAMPLE_RATE,
                                     output=True,
                                     frames_per_buffer=BUFFER_SIZE,
                                     stream_callback=self.play_callback,
                                     start=False)
            self.stream.start_stream()
            self.playing = True
            logging.debug("ストリーム開始")

    def stop_tone(self):
        if self.stream is not None:
            self.playing = False
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            self.pre_buffer_index = 0
            logging.debug("ストリーム停止")

    def play_callback(self, in_data, frame_count, time_info, status):
        output = np.zeros(frame_count, dtype=np.float32)
        if self.playing:
            remaining_prebuffer = PRE_BUFFER_SIZE - self.pre_buffer_index
            samples_to_take = min(frame_count, remaining_prebuffer)
            output[:samples_to_take] = self.pre_buffer[self.pre_buffer_index:self.pre_buffer_index + samples_to_take]
            self.pre_buffer_index += samples_to_take

            remaining_samples = frame_count - samples_to_take

            if remaining_samples > 0:
                # 位相の連続性を厳密に確保
                samples = (np.sin(2 * np.pi * (np.arange(self.current_phase, self.current_phase + remaining_samples)) * FREQUENCY / SAMPLE_RATE)).astype(np.float32)
                output[samples_to_take:] = samples
                self.current_phase += remaining_samples
            return (output, pyaudio.paContinue)
        else:
            return (output, pyaudio.paComplete)

    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.left:
            if pressed:
                self.click_start_time = time.time()
                self.start_tone()
            else:
                self.stop_tone()
                elapsed_time = time.time() - self.click_start_time

                if elapsed_time < SHORT_THRESHOLD:
                    self.current_morse += "・"
                    print(f"入力された符号: {self.current_morse}")
                elif elapsed_time > LONG_THRESHOLD:
                    self.current_morse += "－"
                    print(f"入力された符号: {self.current_morse}")
                else:
                    print(f"中間の長さ ({elapsed_time:.2f}秒)。短点または長点として認識できませんでした。閾値を調整してください。")

                self.last_click_time = time.time()
                if self.timer_id is not None:
                    self.root.after_cancel(self.timer_id)
                self.timer_id = self.root.after(MORSE_CHECK_TIMEOUT, self.process_morse_code)

    def process_morse_code(self):
        if self.current_morse:
            print(f"確定した符号: {self.current_morse}")
            self.current_morse = ""
            self.timer_id = None

    def on_closing(self):
        self.terminate()
        self.root.destroy()

    def terminate(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        if self.p is not None:
            self.p.terminate()
        if self.listener is not None:
            self.listener.stop()
        print("テスト終了。")
        logging.debug("プログラム終了")

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Morse Tester")
    try:
        tester = MorseTester(root)
        if hasattr(tester, 'root'):
            root.mainloop()
    except Exception as e:
        logging.error(f"予期せぬエラー: {e}")
        print(f"予期せぬエラー: {e}")
    finally:
        try:
            tester.terminate()
        except AttributeError:
            pass
