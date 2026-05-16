import tkinter as tk
import random
import time
from pynput import mouse

# グローバル変数
CHARACTER_FONT_SIZE = 35
CHARACTER_SPAWN_INTERVAL_MIN = 3000
CHARACTER_SPAWN_INTERVAL_MAX = 5000
MORSE_CHECK_TIMEOUT = 800  # マウス無入力タイマー（ms）
SCORE_FONT_SIZE = 40  # スコアフォントサイズ
FALLING_SPEED = 1  # 落下の速さ（デフォルト値。難易度選択で変更される）
MAX_MISTAKES = 5 # ゲームオーバーになる間違い回数

# モールスコード辞書
morse_code_dict = {
    'A': '・－', 'B': '－・・・', 'C': '－・－・', 'D': '－・・', 'E': '・', 'F': '・・－・',
    'G': '－－・', 'H': '・・・・', 'I': '・・', 'J': '・－－－', 'K': '－・－', 'L': '・－・・',
    'M': '－－', 'N': '－・', 'O': '－－－', 'P': '・－－・', 'Q': '－－・－', 'R': '・－・',
    'S': '・・・', 'T': '－', 'U': '・・－', 'V': '・・・－', 'W': '・－－', 'X': '－・・－',
    'Y': '－・－－', 'Z': '－－・・',
    '1': '・－－－－', '2': '・・－－－', '3': '・・・－－', '4': '・・・・－', '5': '・・・・・',
    '6': '－・・・・', '7': '－－・・・', '8': '－－－・・', '9': '－－－－・', '0': '－－－－－',
}

class Character:
    def __init__(self, canvas, alphabet, morse_code, speed): # speed引数を追加
        self.canvas = canvas
        self.alphabet = alphabet
        self.morse_code = morse_code
        self.speed = speed # speedをインスタンス変数として設定

        # テキストオブジェクトを生成（位置は一旦(0,0)で生成）
        self.alphabet_text = canvas.create_text(0, 0, text=alphabet, font=("Helvetica", CHARACTER_FONT_SIZE), anchor='s')
        self.morse_code_text = canvas.create_text(0, 0, text=morse_code, font=("Helvetica", CHARACTER_FONT_SIZE), anchor='n',
                                                 justify='center')

        # 全体の幅を取得
        alphabet_bbox = canvas.bbox(self.alphabet_text)
        morse_code_bbox = canvas.bbox(self.morse_code_text)
        total_width = max(alphabet_bbox[2] - alphabet_bbox[0], morse_code_bbox[2] - morse_code_bbox[0])

        # 初期x座標をランダムに決定 (キャンバスの幅に基づいて調整)
        canvas_width = canvas.winfo_width() if canvas.winfo_width() > 1 else 600
        self.x = random.randint(0, canvas_width - 1)

        # x座標がはみ出していないかチェックし、必要に応じて調整
        if self.x + total_width / 2 > canvas_width:  # 右端からはみ出す場合
            self.x = canvas_width - int(total_width / 2)
        elif self.x - total_width / 2 < 0:  # 左端からはみ出す場合
            self.x = int(total_width / 2)

        # 最終的な位置にテキストオブジェクトを移動
        self.canvas.move(self.alphabet_text, self.x - (alphabet_bbox[0] + alphabet_bbox[2]) / 2,
                         0)  # 初期位置からのオフセットを考慮
        self.canvas.move(self.morse_code_text, self.x - (morse_code_bbox[0] + morse_code_bbox[2]) / 2,
                         0)  # 初期位置からのオフセットを考慮

        # テキストオブジェクトをグループ化
        self.text_group = [self.alphabet_text, self.morse_code_text]
        self.y = 0
        self.passed_line = False

    def move(self):
        self.y += self.speed
        for text_id in self.text_group:
            self.canvas.move(text_id, 0, self.speed)

        # キャンバスの高さに基づいてpassed_lineをチェック
        canvas_height = self.canvas.winfo_height() if self.canvas.winfo_height() > 1 else 700
        if self.y > canvas_height - 30 and not self.passed_line: # 間違い表示ラインの少し上
            self.passed_line = True


class Game:
    def __init__(self, root):
        self.root = root
        self.root.title("Morse Game")
        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.start()

        # 設定変数 (初期化時にこれらを先に定義する)
        self.game_width = 600
        self.game_height = 660 # デフォルトは横向き
        self.goal_score = tk.StringVar(value="5") # デフォルトは5点
        self.falling_speed = FALLING_SPEED # デフォルトの落下速度
        self.selected_size = tk.StringVar() # StringVarを初期化
        self.selected_speed = tk.StringVar() # StringVarを初期化

        self.game_active = False # ゲームがアクティブかどうかを示すフラグ
        self.game_clear = False # ゲームクリア状態を示すフラグ

        # ゲームオブジェクト
        self.canvas = None
        self.score_text = None
        self.mistakes_text = None
        self.characters = []
        self.current_morse = ""
        self.last_click_time = 0
        self.next_char_spawn_time = 0
        self.click_start_time = 0
        self.current_morse_display = None
        self.x_mark = None
        self.game_over_text = None
        self.clear_text = None
        self.restart_button = None
        self.exit_button = None
        self.timeout_id = None # timeout_idを追加
        self.start_game_button = None # start_game_buttonもinitで初期化（None）

        self.setup_start_screen()

    def setup_start_screen(self):
        # 既存のウィジェットがあればクリア
        for widget in self.root.winfo_children():
            widget.destroy()

        self.start_frame = tk.Frame(self.root, padx=20, pady=20)
        self.start_frame.pack(expand=True, fill='both')

        # 1. 表示サイズ選択
        tk.Label(self.start_frame, text="モニターの向きを選択してください", font=("MS Gothic", 16)).pack(pady=10)
        size_frame = tk.Frame(self.start_frame)
        size_frame.pack(pady=5)
        tk.Radiobutton(size_frame, text="横 (W:600, H:660)", variable=self.selected_size, value="横",
                       command=lambda: self.set_display_size(600, 660)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(size_frame, text="縦 (W:700, H:920)", variable=self.selected_size, value="縦",
                       command=lambda: self.set_display_size(700, 920)).pack(side=tk.LEFT, padx=10)
        self.selected_size.set("横") # デフォルト選択
        self.set_display_size(600, 660) # デフォルトサイズを適用

        # 2. ゴール点数入力
        tk.Label(self.start_frame, text="ゴール点数を入力してください (デフォルト: 5)", font=("MS Gothic", 16)).pack(pady=10)
        self.goal_score_entry = tk.Entry(self.start_frame, textvariable=self.goal_score, font=("MS Gothic", 14), width=10)
        self.goal_score_entry.pack(pady=5)
        self.goal_score_entry.bind("<KeyRelease>", self.check_start_button_state)


        # 3. 難易度選択
        tk.Label(self.start_frame, text="落下速度を選択してください", font=("MS Gothic", 16)).pack(pady=10)
        speed_frame = tk.Frame(self.start_frame)
        speed_frame.pack(pady=5)
        tk.Radiobutton(speed_frame, text="やさしい (現在の速度)", variable=self.selected_speed, value="やさしい",
                       command=lambda: self.set_falling_speed(FALLING_SPEED)).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(speed_frame, text="むずかしい (1.2倍速)", variable=self.selected_speed, value="むずかしい",
                       command=lambda: self.set_falling_speed(FALLING_SPEED * 1.2)).pack(side=tk.LEFT, padx=10)
        self.selected_speed.set("やさしい") # デフォルト選択
        self.set_falling_speed(FALLING_SPEED) # デフォルト速度を適用

        # GAME START ボタン
        self.start_game_button = tk.Button(self.start_frame, text="GAME START", command=self.start_game_setup,
                                            font=("MS Gothic", 24), state=tk.DISABLED, padx=30, pady=15)
        self.start_game_button.pack(pady=30)
        self.check_start_button_state() # 初期状態でボタンの状態をチェック

    def set_display_size(self, w, h):
        self.game_width = w
        self.game_height = h
        self.check_start_button_state() # サイズ選択時もボタンの状態をチェック

    def set_falling_speed(self, speed):
        self.falling_speed = speed
        self.check_start_button_state() # 速度選択時もボタンの状態をチェック

    def check_start_button_state(self, event=None):
        # self.start_game_buttonがまだ存在しない可能性があるのでチェック
        if not hasattr(self, 'start_game_button') or self.start_game_button is None:
            return

        try:
            goal = int(self.goal_score.get())
            if goal > 0 and self.selected_size.get() and self.selected_speed.get():
                self.start_game_button.config(state=tk.NORMAL)
            else:
                self.start_game_button.config(state=tk.DISABLED)
        except ValueError:
            self.start_game_button.config(state=tk.DISABLED)

    def start_game_setup(self):
        # スタート画面をクリア
        self.start_frame.destroy()

        # キャンバスとゲームUIの設定
        self.root.geometry(f"{self.game_width}x{self.game_height}") # ウィンドウサイズを設定
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.root, width=self.game_width, height=self.game_height)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # スコア表示を中央に配置（ターコイズ色に変更）
        self.score = 0
        self.score_text = self.canvas.create_text(self.game_width / 2, SCORE_FONT_SIZE, text=f"Score: {self.score:03d}",
                                                 font=("MS Gothic", SCORE_FONT_SIZE), anchor=tk.CENTER, fill="turquoise")

        # 間違い回数カウンターと表示を中央に配置し、Y座標を調整（表示を「しっぱい」に、色をうすピンク色に変更）
        self.mistakes = 0
        self.mistakes_text = self.canvas.create_text(self.game_width / 2, self.game_height - SCORE_FONT_SIZE, # Y座標を調整
                                                 text=f"しっぱい： {self.mistakes}/{MAX_MISTAKES}",
                                                 font=("MS Gothic", SCORE_FONT_SIZE), fill="LightPink",
                                                 anchor=tk.CENTER)

        # 入力中のモールス信号表示を中央に配置
        self.current_morse_display = self.canvas.create_text(self.game_width / 2, self.game_height - SCORE_FONT_SIZE * 3, text="", font=("Helvetica", 30),
                                                              anchor=tk.CENTER)

        # キャンバスにリスタートボタンを作成
        self.restart_button = tk.Button(self.canvas, text="ﾘｽﾀｰﾄ", command=self.restart,
                                         font=("MS Gothic", 20), padx=20, pady=10)
        self.restart_button_window = self.canvas.create_window(0, 0, anchor=tk.NW, window=self.restart_button)

        # 終了ボタンをキャンバス内に配置
        self.exit_button = tk.Button(self.canvas, text="終了", command=self.root.quit,
                                       font=("MS Gothic", 20), padx=20, pady=10)
        self.exit_button_window = self.canvas.create_window(self.game_width, 0, anchor=tk.NE, window=self.exit_button)

        # ゲーム開始
        self.game_active = True
        self.game_clear = False
        self.next_char_spawn_time = time.time() * 1000 + random.randint(CHARACTER_SPAWN_INTERVAL_MIN, CHARACTER_SPAWN_INTERVAL_MAX)
        self.game_loop()

    def generate_character(self):
        if not self.game_active:
            return

        alphabet = random.choice(list(morse_code_dict.keys()))
        morse_code = morse_code_dict[alphabet]
        char = Character(self.canvas, alphabet, morse_code, self.falling_speed) # speedを渡す
        self.characters.append(char)

        interval = random.randint(CHARACTER_SPAWN_INTERVAL_MIN, CHARACTER_SPAWN_INTERVAL_MAX)
        self.next_char_spawn_time = time.time() * 1000 + interval

    def game_loop(self):
        if not self.game_active:
            return

        if time.time() * 1000 >= self.next_char_spawn_time or not self.characters:
            self.generate_character()
        self.update()
        self.root.after(30, self.game_loop)

    def update(self):
        chars_to_remove = []
        for char in list(self.characters):
            if not self.game_active:
                break

            char.move()

            # 文字が画面下端を通過したか、または間違い表示ラインを通過したかをチェック
            if char.y > self.game_height - SCORE_FONT_SIZE * 2: # 間違い表示ライン（スコア表示より少し上）
                if not char.passed_line: # 既にカウントされていない場合のみ
                    self.mistakes += 1
                    self.canvas.itemconfig(self.mistakes_text, text=f"しっぱい： {self.mistakes}/{MAX_MISTAKES}")

                    if self.mistakes >= MAX_MISTAKES:
                        self.game_over()
                        if not self.game_active:
                            break # game_over()がself.game_activeをFalseにしたことを確認

                chars_to_remove.append(char)

        for char in chars_to_remove:
            if char in self.characters:
                self.canvas.delete(char.text_group[0])
                self.canvas.delete(char.text_group[1])
                self.characters.remove(char)

        # スコアがゴール点数に達したかチェック
        try:
            goal_score_int = int(self.goal_score.get())
        except ValueError:
            goal_score_int = 0 # 無効な入力の場合は0として扱う

        if self.game_active and not self.game_clear and self.score >= goal_score_int and goal_score_int > 0:
            self.clear_game()

    def check_timeout(self):
        if not self.game_active:
            return

        # 既存のタイムアウトをキャンセル
        if self.timeout_id:
            self.root.after_cancel(self.timeout_id)
            self.timeout_id = None

        if time.time() - self.last_click_time > MORSE_CHECK_TIMEOUT / 1000:
            self.process_morse_code()

    def on_click(self, x, y, button, pressed):
        if not self.game_active:
            return

        if button == mouse.Button.left:
            if pressed:
                self.click_start_time = time.time()
            else:
                elapsed_time = time.time() - self.click_start_time
                if elapsed_time < 0.3:
                    self.current_morse += "・"
                else:
                    self.current_morse += "－"
                self.canvas.itemconfig(self.current_morse_display, text=self.current_morse)
                self.last_click_time = time.time()

                # 新しいタイムアウトをスケジュールし、IDを保存
                if self.timeout_id:
                    self.root.after_cancel(self.timeout_id)
                self.timeout_id = self.root.after(MORSE_CHECK_TIMEOUT, self.check_timeout)

    def process_morse_code(self):
        if not self.game_active:
            return

        # タイムアウトが呼ばれたらIDをリセット
        if self.timeout_id:
            self.timeout_id = None

        if self.current_morse:
            matched = False
            for char in list(self.characters):
                # 画面下端を通過していない文字のみを対象とする
                if char.morse_code == self.current_morse and not char.passed_line:
                    self.canvas.delete(char.text_group[0])
                    self.canvas.delete(char.text_group[1])
                    self.characters.remove(char)
                    self.score += 1
                    self.canvas.itemconfig(self.score_text, text=f"Score: {self.score:03d}")
                    matched = True
                    break

            if not matched:
                self.show_x_mark()
                self.mistakes += 1
                self.canvas.itemconfig(self.mistakes_text, text=f"しっぱい： {self.mistakes}/{MAX_MISTAKES}")
                if self.mistakes >= MAX_MISTAKES:
                    self.game_over()

            self.current_morse = ""
            self.canvas.itemconfig(self.current_morse_display, text="")

    def show_x_mark(self):
        if self.x_mark:
            self.canvas.delete(self.x_mark)
        self.x_mark = self.canvas.create_text(self.game_width / 2, self.game_height / 2, text="×", font=("MS Gothic", 70), fill="red", anchor=tk.CENTER)
        self.root.after(1000, self.hide_x_mark)

    def hide_x_mark(self):
        if self.x_mark:
            self.canvas.delete(self.x_mark)
            self.x_mark = None

    def game_over(self):
        self.game_active = False
        # 落下中の文字を全て削除
        for char in list(self.characters):
            self.canvas.delete(char.text_group[0])
            self.canvas.delete(char.text_group[1])
        self.characters.clear()

        # ゲームオーバーメッセージを中央に配置
        if self.game_over_text:
            self.canvas.delete(self.game_over_text)
        self.game_over_text = self.canvas.create_text(self.game_width / 2, self.game_height / 2, text="GAME OVER",
                                                      font=("MS Gothic", 60), fill="black", anchor=tk.CENTER)

    def clear_game(self):
        self.game_active = False
        self.game_clear = True
        # 落下中の文字を全て削除
        for char in list(self.characters):
            self.canvas.delete(char.text_group[0])
            self.canvas.delete(char.text_group[1])
        self.characters.clear()

        # クリアメッセージを中央に配置
        if self.clear_text:
            self.canvas.delete(self.clear_text)
        self.clear_text = self.canvas.create_text(self.game_width / 2, self.game_height / 2, text="ＣＬＥＡＲ！",
                                                  font=("MS Gothic", 60), fill="blue", anchor=tk.CENTER)

    def restart(self):
        # スコアと間違い回数をリセット
        self.score = 0
        self.mistakes = 0

        # タイマーがあればキャンセル
        if self.timeout_id:
            self.root.after_cancel(self.timeout_id)
            self.timeout_id = None

        # 全てのゲームオブジェクトを削除
        if self.canvas:
            for char in list(self.characters):
                self.canvas.delete(char.text_group[0])
                self.canvas.delete(char.text_group[1])
            self.characters.clear()
            self.canvas.destroy() # キャンバスを破棄

        # モールス信号とペケ印をリセット
        self.current_morse = ""
        # 画面中央のXマークを削除
        if self.x_mark:
            self.x_mark = None

        # ゲームオーバー/クリアメッセージを削除
        if self.game_over_text:
            self.game_over_text = None
        if self.clear_text:
            self.clear_text = None

        # start_game_buttonをNoneにリセットして、setup_start_screenで再作成されるようにする
        self.start_game_button = None

        # ゲーム設定画面に戻る
        self.game_active = False
        self.game_clear = False
        self.setup_start_screen()


if __name__ == "__main__":
    root = tk.Tk()
    game = Game(root)
    root.mainloop()
