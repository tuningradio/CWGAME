import tkinter as tk

class TestProgram:
    def __init__(self, root):
        self.root = root
        self.root.title("Test Program")

        # キャンバスの幅と高さを定義
        canvas_width = 600
        canvas_height = 700

        # キャンバスを作成
        self.canvas = tk.Canvas(root, width=canvas_width, height=canvas_height, bg="white")
        self.canvas.pack()

        # キャンバスの中心点を計算
        center_x = canvas_width / 2
        center_y = canvas_height / 2

        # 中心に「・」を表示
        # フォントサイズは適当に設定していますが、必要に応じて調整してください
        self.canvas.create_text(center_x, center_y, text="・", font=("MS Gothic", 50), anchor=tk.CENTER, fill="black")

if __name__ == "__main__":
    root = tk.Tk()
    app = TestProgram(root)
    root.mainloop()
