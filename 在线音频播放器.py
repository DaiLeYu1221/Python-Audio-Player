import sounddevice as sd
import soundfile as sf
import requests
from io import BytesIO
import tkinter as tk
from tkinter import ttk, messagebox
import threading

class AudioPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("在线音频播放器")
        
        # 初始化所有变量
        self.playing = False
        self.play_thread = None
        self.error_message = ""  # 确保变量存在
        
        # 创建界面组件
        self.setup_ui()

    def setup_ui(self):
        # 输入框区域
        input_frame = ttk.Frame(self.root, padding=10)
        input_frame.pack(fill=tk.X)
        
        ttk.Label(input_frame, text="音频URL：").pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(input_frame, width=40)
        self.url_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        
        # 控制按钮区域
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(fill=tk.X)
        
        self.play_btn = ttk.Button(control_frame, text="播放", command=self.toggle_play)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        # 状态显示
        self.status_label = ttk.Label(self.root, text="已经准备好进行播放", padding=10)
        self.status_label.pack(fill=tk.X)

    def toggle_play(self):
        if self.playing:
            self.stop_playback()
        else:
            self.start_playback()

    def start_playback(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("警告", "请输入有效的音频URL！")
            return

        self.playing = True
        self.play_btn.config(text="停止")
        self.status_label.config(text="正在下载音频...")
        
        # 使用新线程处理网络请求和播放
        self.play_thread = threading.Thread(target=self.download_and_play, args=(url,))
        self.play_thread.start()

    def stop_playback(self):
        self.playing = False
        sd.stop()
        self.play_btn.config(text="播放")
        self.status_label.config(text="播放已停止")
        
    def download_and_play(self, url):
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()
            
            audio_data = BytesIO(response.content)
            data, samplerate = sf.read(audio_data)
            
            self.root.event_generate("<<UpdateStatus>>", when="tail")
            sd.play(data, samplerate)
            sd.wait()
            
            if self.playing:
                self.root.event_generate("<<PlayFinished>>", when="tail")

        except Exception as e:
            self.error_message = str(e)  # 正确赋值
            self.root.event_generate("<<PlayError>>", when="tail")
        finally:
            self.playing = False

    def on_status_update(self, event):
        self.status_label.config(text="开始播放")

    def on_play_finished(self, event):
        self.play_btn.config(text="播放")
        self.status_label.config(text="播放完毕！")

    def on_play_error(self, event):
        error_msg = self.error_message  # 现在可以安全访问
        messagebox.showerror("播放错误", f"发生错误：{error_msg}")
        self.play_btn.config(text="播放")
        self.status_label.config(text="准备就绪")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioPlayerApp(root)
    
    # 绑定自定义事件
    root.bind("<<UpdateStatus>>", app.on_status_update)
    root.bind("<<PlayFinished>>", app.on_play_finished)
    root.bind("<<PlayError>>", app.on_play_error)
    
    root.mainloop()
