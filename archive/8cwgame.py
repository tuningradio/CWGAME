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
FALLING_SPEED = 1  # 落下の速さ
MAX_MISTAKES = 5 # ゲームオーバーになる間違い回数
# TEXT_X_OFFSET = 5 # 中央表示の微調整用Xオフセット (現在はオフセットなし)

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
    def __init__(self, canvas, alphabet, morse_code):
        self.canvas = canvas
        self.alphabet = alphabet
        self.morse_code = morse_code
        self.speed = FALLING_SPEED

        # テキストオブジェクトを生成（位置は一旦(0,0)で生成）
        self.alphabet_text = canvas.create_text(0, 0, text=alphabet, font=("Helvetica", CHARACTER_FONT_SIZE), anchor='s')
        self.morse_code_text = canvas.create_text(0, 0, text=morse_code, font=("Helvetica", CHARACTER_FONT_SIZE), anchor='n',
                                                  justify='center')

        # 全体の幅を取得
        alphabet_bbox = canvas.bbox(self.alphabet_text)
        morse_code_bbox = canvas.bbox(self.morse_code_text)
        total_width = max(alphabet_bbox[2] - alphabet_bbox[0], morse_code_bbox[2] - morse_code_bbox[0])

        # 初期x座標をランダムに決定
        self.x = random.randint(0, 599)

        # x座標がはみ出していないかチェックし、必要に応じて調整
        if self.x + total_width / 2 > 600:  # 右端からはみ出す場合
            self.x = 600 - int(total_width / 2)
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

        if self.y > 670 and not self.passed_line:
            self.passed_line = True


class Game:
    def __init__(self, root):
        self.root = root
        
        # Configure the root window to use grid layout
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        # self.root.columnconfigure(1, weight=0)  # 終了ボタンをキャンバス内に移動するため、この行は不要になる
        

        self.canvas = tk.Canvas(root, width=600, height=700)
        self.canvas.grid(row=0, column=0, sticky="nsew")  # Make canvas expand with window
        
        # スコア表示を中央に配置（ターコイズ色に変更）
        self.score = 0
        self.score_text = self.canvas.create_text(300, SCORE_FONT_SIZE, text=f"Score: {self.score:03d}",
                                                  font=("MS Gothic", SCORE_FONT_SIZE), anchor=tk.CENTER, fill="turquoise")
        
        # 間違い回数カウンターと表示を中央に配置し、Y座標を調整（表示を「しっぱい」に、色をうすピンク色に変更）
        self.mistakes = 0
        self.mistakes_text = self.canvas.create_text(300, 650, # Y座標を650に調整
                                                     text=f"しっぱい： {self.mistakes}/{MAX_MISTAKES}",
                                                     font=("MS Gothic", SCORE_FONT_SIZE), fill="LightPink",
                                                     anchor=tk.CENTER)

        self.characters = []
        self.current_morse = ""
        self.last_click_time = 0
        self.next_char_spawn_time = 0
        self.click_start_time = 0  # 追加
        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.start()
        
        # 入力中のモールス信号表示を中央に配置
        self.current_morse_display = self.canvas.create_text(300, 600, text="", font=("Helvetica", 30),
                                                             anchor=tk.CENTER)
        self.x_mark = None
        self.game_active = True # ゲームがアクティブかどうかを示すフラグ
        self.game_over_text = None # ゲームオーバー表示用

        self.root.after(100, self.game_loop)
        
        # キャンバスにリスタートボタンを作成
        self.restart_button = tk.Button(self.canvas, text="ﾘｽﾀｰﾄ", command=self.restart,
                                         font=("MS Gothic", 20), padx=20, pady=10) # フォントサイズとパディングを調整
        # キャンバスの左上(0,0)に配置
        self.restart_button_window = self.canvas.create_window(0, 0, anchor=tk.NW, window=self.restart_button)


        # 終了ボタンをキャンバス内に配置
        self.exit_button = tk.Button(self.canvas, text="終了", command=root.quit,
                                     font=("MS Gothic", 20), padx=20, pady=10) # フォントサイズとパディングを調整
        # キャンバスの右上(width, 0)に配置。anchor=tk.NE でボタンの右上が指定座標になる
        self.exit_button_window = self.canvas.create_window(600, 0, anchor=tk.NE, window=self.exit_button)


    def generate_character(self):
        if not self.game_active: # ゲームがアクティブでない場合は生成しない
            return

        alphabet = random.choice(list(morse_code_dict.keys()))
        morse_code = morse_code_dict[alphabet]
        char = Character(self.canvas, alphabet, morse_code)
        self.characters.append(char)

        interval = random.randint(CHARACTER_SPAWN_INTERVAL_MIN, CHARACTER_SPAWN_INTERVAL_MAX)
        self.next_char_spawn_time = time.time() * 1000 + interval

    def game_loop(self):
        if not self.game_active: # ゲームがアクティブでない場合はループを停止
            return

        if time.time() * 1000 >= self.next_char_spawn_time or not self.characters:
            self.generate_character()
        self.update()
        self.root.after(30, self.game_loop)

    def update(self):
        # self.charactersリストのコピーをループすることで、元のリストをループ中に変更しても安全にする
        # ただし、game_over()が呼ばれた際に元のリストがクリアされることを考慮する必要がある
        chars_to_remove = []
        for char in list(self.characters): # リストのコピーに対してイテレーション
            if not self.game_active: # game_overが呼ばれたら直ちにループを抜ける
                break
            
            char.move()

            if char.y > 700: # キャラクターが画面下端を通過した
                # 間違いとしてカウント
                self.mistakes += 1
                self.canvas.itemconfig(self.mistakes_text, text=f"しっぱい： {self.mistakes}/{MAX_MISTAKES}") # 表示を更新
                
                # ゲームオーバー判定
                if self.mistakes >= MAX_MISTAKES:
                    self.game_over() # game_over()内でself.charactersがクリアされる
                    # game_overが呼び出されたら、これ以上キャラクターを処理する必要はない
                    if not self.game_active: # game_over()がself.game_activeをFalseにしたことを確認
                        break # updateループを抜ける

                chars_to_remove.append(char) # 削除対象のキャラクターをマーク

        # ループが終了した後、マークされたキャラクターを削除
        for char in chars_to_remove:
            if char in self.characters: # game_over()で既にクリアされていないか確認
                self.canvas.delete(char.text_group[0])
                self.canvas.delete(char.text_group[1])
                self.characters.remove(char)

    def check_timeout(self):
        if not self.game_active:
            return

        if time.time() - self.last_click_time > MORSE_CHECK_TIMEOUT / 1000:
            self.process_morse_code()

    def on_click(self, x, y, button, pressed):
        if not self.game_active: # ゲームがアクティブでない場合はクリックを無視
            return

        if button == mouse.Button.left:  # 左ボタンのみ反応
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
                self.root.after(2000, self.check_timeout)

    def process_morse_code(self):
        if not self.game_active: # ゲームがアクティブでない場合は処理しない
            return

        if self.current_morse:
            matched = False
            for char in list(self.characters):
                if char.morse_code == self.current_morse and not char.passed_line:
                    self.canvas.delete(char.text_group[0])
                    self.canvas.delete(char.text_group[1])
                    self.characters.remove(char)
                    self.score += 1
                    self.canvas.itemconfig(self.score_text, text=f"Score: {self.score:03d}")
                    matched = True
                    break
            
            if not matched: # 間違い入力の場合もカウント
                self.show_x_mark()
                self.mistakes += 1
                self.canvas.itemconfig(self.mistakes_text, text=f"しっぱい： {self.mistakes}/{MAX_MISTAKES}") # 表示を更新
                if self.mistakes >= MAX_MISTAKES:
                    self.game_over()

            self.current_morse = ""
            self.canvas.itemconfig(self.current_morse_display, text="")

    def show_x_mark(self):
        if self.x_mark:
            self.canvas.delete(self.x_mark)
        # Xマーク表示を中央に配置
        self.x_mark = self.canvas.create_text(300, 350, text="×", font=("MS Gothic", 70), fill="red", anchor=tk.CENTER)
        self.root.after(1000, self.hide_x_mark)

    def hide_x_mark(self):
        if self.x_mark:
            self.canvas.delete(self.x_mark)
            self.x_mark = None  # ここまで

    def game_over(self):
        self.game_active = False
        # 落下中の文字を全て削除
        for char in list(self.characters): # ここもlist(self.characters)でコピーをループ
            self.canvas.delete(char.text_group[0])
            self.canvas.delete(char.text_group[1])
        self.characters.clear() # ここでリストがクリアされる

        # ゲームオーバーメッセージを中央に配置
        if self.game_over_text:
            self.canvas.delete(self.game_over_text)
        self.game_over_text = self.canvas.create_text(300, 350, text="GAME OVER", 
                                                      font=("MS Gothic", 60), fill="black", anchor=tk.CENTER)

        
    # リスタート関数
    def restart(self):
        # スコアと間違い回数をリセット
        self.score = 0
        self.canvas.itemconfig(self.score_text, text=f"Score: {self.score:03d}")
        self.mistakes = 0
        self.canvas.itemconfig(self.mistakes_text, text=f"しっぱい： {self.mistakes}/{MAX_MISTAKES}") # 表示を更新


        # 落下中の文字を全て削除
        for char in list(self.characters):
            self.canvas.delete(char.text_group[0])
            self.canvas.delete(char.text_group[1])
        self.characters.clear()

        # モールス信号とペケ印をリセット
        self.current_morse = ""
        self.canvas.itemconfig(self.current_morse_display, text="")
        if self.x_mark:
            self.canvas.delete(self.x_mark)
            self.x_mark = None
        
        # ゲームオーバーメッセージを削除
        if self.game_over_text:
            self.canvas.delete(self.game_over_text)
            self.game_over_text = None

        # 文字の落下を再開
        self.game_active = True
        self.next_char_spawn_time = time.time() * 1000 + random.randint(CHARACTER_SPAWN_INTERVAL_MIN,
                                                                       CHARACTER_SPAWN_INTERVAL_MAX)
        self.game_loop() # ゲームループを再開


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Morse Game")
    game = Game(root)
    root.mainloop()
