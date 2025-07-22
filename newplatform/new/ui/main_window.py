import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import sys
import os

class FaceControlUI:
    def __init__(self, root, analyzer=None):
        self.root = root
        self.root.title("机器人面部控制器 - 集成音频分析")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # 使用传入的分析器或创建新的
        if analyzer:
            self.analyzer = analyzer
        else:
            # 动态导入避免循环导入
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from analysis_sound import AudioAnalyzer
            self.analyzer = AudioAnalyzer()
        
        # 设置回调函数
        self.analyzer.set_connection_callback(self.on_connection_change)
        self.analyzer.set_response_callback(self.on_response_received)
        
        # 存储滑块和标签
        self.sliders = {}
        self.value_labels = {}
        
        # 音频播放状态
        self.is_playing = False
        
        # 创建界面
        self.create_widgets()
        
        # 自动刷新串口列表
        self.refresh_ports()
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主要的Notebook控件
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建标签页
        self.create_connection_tab()
        self.create_control_tab()
        self.create_audio_tab()
        self.create_log_tab()
    
    def create_connection_tab(self):
        """创建连接标签页"""
        conn_frame = ttk.Frame(self.notebook)
        self.notebook.add(conn_frame, text="连接设置")
        
        # 连接区域
        conn_group = ttk.LabelFrame(conn_frame, text="串口连接", padding="10")
        conn_group.pack(fill=tk.X, padx=10, pady=10)
        
        # 串口选择行
        port_frame = ttk.Frame(conn_group)
        port_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(port_frame, text="串口:").pack(side=tk.LEFT, padx=(0, 5))
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(port_frame, textvariable=self.port_var, state="readonly", width=15)
        self.port_combo.pack(side=tk.LEFT, padx=(0, 5))
        
        self.refresh_btn = ttk.Button(port_frame, text="刷新", command=self.refresh_ports, width=8)
        self.refresh_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.connect_btn = ttk.Button(port_frame, text="连接", command=self.toggle_connection, width=8)
        self.connect_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.status_label = ttk.Label(port_frame, text="未连接", foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 控制按钮行
        ctrl_frame = ttk.Frame(conn_group)
        ctrl_frame.pack(fill=tk.X, pady=5)
        
        self.center_btn = ttk.Button(ctrl_frame, text="回中位", command=self.center_all, width=10, state="disabled")
        self.center_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.test_btn = ttk.Button(ctrl_frame, text="测试舵机", command=self.test_servos, width=10, state="disabled")
        self.test_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 参数设置区域
        param_group = ttk.LabelFrame(conn_frame, text="参数设置", padding="10")
        param_group.pack(fill=tk.X, padx=10, pady=10)
        
        # 音频参数
        audio_frame = ttk.Frame(param_group)
        audio_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(audio_frame, text="低振幅阈值:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.low_threshold_var = tk.DoubleVar(value=self.analyzer.threshold_low)
        ttk.Scale(audio_frame, from_=0.0, to=1.0, variable=self.low_threshold_var, 
                 orient=tk.HORIZONTAL, length=200).grid(row=0, column=1, padx=(0, 5))
        ttk.Label(audio_frame, textvariable=self.low_threshold_var).grid(row=0, column=2, padx=(5, 0))
        
        ttk.Label(audio_frame, text="高振幅阈值:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        self.high_threshold_var = tk.DoubleVar(value=self.analyzer.threshold_high)
        ttk.Scale(audio_frame, from_=0.0, to=1.0, variable=self.high_threshold_var, 
                 orient=tk.HORIZONTAL, length=200).grid(row=1, column=1, padx=(0, 5))
        ttk.Label(audio_frame, textvariable=self.high_threshold_var).grid(row=1, column=2, padx=(5, 0))
        
        # 眨眼参数
        ttk.Label(audio_frame, text="眨眼间隔(秒):").grid(row=2, column=0, sticky=tk.W, padx=(0, 5))
        self.blink_interval_var = tk.DoubleVar(value=self.analyzer.blink_interval)
        ttk.Scale(audio_frame, from_=1.0, to=10.0, variable=self.blink_interval_var, 
                 orient=tk.HORIZONTAL, length=200).grid(row=2, column=1, padx=(0, 5))
        ttk.Label(audio_frame, textvariable=self.blink_interval_var).grid(row=2, column=2, padx=(5, 0))
        
        # 应用按钮
        apply_btn = ttk.Button(param_group, text="应用设置", command=self.apply_settings)
        apply_btn.pack(pady=10)
    
    def create_control_tab(self):
        """创建控制标签页"""
        control_frame = ttk.Frame(self.notebook)
        self.notebook.add(control_frame, text="面部控制")
        
        # 创建滚动框架
        canvas = tk.Canvas(control_frame)
        scrollbar = ttk.Scrollbar(control_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 面部控制区域
        self.create_face_controls(scrollable_frame)
        
        # 鼠标滚轮绑定
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def create_audio_tab(self):
        """创建音频标签页"""
        audio_frame = ttk.Frame(self.notebook)
        self.notebook.add(audio_frame, text="音频分析")
        
        # 文件选择区域
        file_group = ttk.LabelFrame(audio_frame, text="音频文件", padding="10")
        file_group.pack(fill=tk.X, padx=10, pady=10)
        
        file_frame = ttk.Frame(file_group)
        file_frame.pack(fill=tk.X)
        
        ttk.Label(file_frame, text="WAV文件:").pack(side=tk.LEFT, padx=(0, 5))
        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_var, width=50)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(file_frame, text="浏览", command=self.browse_file).pack(side=tk.LEFT, padx=(0, 5))
        
        # 播放控制区域
        play_group = ttk.LabelFrame(audio_frame, text="播放控制", padding="10")
        play_group.pack(fill=tk.X, padx=10, pady=10)
        
        play_frame = ttk.Frame(play_group)
        play_frame.pack(fill=tk.X)
        
        self.play_btn = ttk.Button(play_frame, text="播放并控制", command=self.play_audio, width=15)
        self.play_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(play_frame, text="停止", command=self.stop_audio, width=10, state="disabled")
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # 播放状态
        self.play_status_label = ttk.Label(play_frame, text="未播放")
        self.play_status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 音频分析显示区域
        analysis_group = ttk.LabelFrame(audio_frame, text="分析信息", padding="10")
        analysis_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.analysis_text = tk.Text(analysis_group, height=10, state="disabled")
        analysis_scroll = ttk.Scrollbar(analysis_group, orient="vertical", command=self.analysis_text.yview)
        self.analysis_text.configure(yscrollcommand=analysis_scroll.set)
        
        self.analysis_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        analysis_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_log_tab(self):
        """创建日志标签页"""
        log_frame = ttk.Frame(self.notebook)
        self.notebook.add(log_frame, text="日志")
        
        # 日志显示区域
        log_group = ttk.LabelFrame(log_frame, text="系统日志", padding="10")
        log_group.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = tk.Text(log_group, state="disabled")
        log_scrollbar = ttk.Scrollbar(log_group, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 日志控制
        log_ctrl_frame = ttk.Frame(log_frame)
        log_ctrl_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(log_ctrl_frame, text="清空日志", command=self.clear_log).pack(side=tk.LEFT)
    
    def create_face_controls(self, parent):
        """创建面部控制滑块"""
        # 面部部位分组
        groups = {
            "眼部控制": [
                ("左眼球上下", "LEFT_EYE_V"),
                ("左眼球左右", "LEFT_EYE_H"),
                ("右眼球上下", "RIGHT_EYE_V"),
                ("右眼球左右", "RIGHT_EYE_H"),
                ("左上眼皮", "LEFT_UPPER_EYELID"),
                ("左下眼皮", "LEFT_LOWER_EYELID"),
                ("右上眼皮", "RIGHT_UPPER_EYELID"),
                ("右下眼皮", "RIGHT_LOWER_EYELID"),
            ],
            "眉毛和前额": [
                ("左眉毛", "LEFT_EYEBROW"),
                ("右眉毛", "RIGHT_EYEBROW"),
                ("左前额", "LEFT_FOREHEAD"),
                ("右前额", "RIGHT_FOREHEAD"),
            ],
            "嘴部和脸颊": [
                ("人中", "PHILTRUM"),
                ("下巴", "CHIN"),
                ("左脸颊", "LEFT_CHEEK"),
                ("右脸颊", "RIGHT_CHEEK"),
            ]
        }
        
        row = 0
        for group_name, parts in groups.items():
            group_frame = ttk.LabelFrame(parent, text=group_name, padding="10")
            group_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5, padx=5)
            group_frame.columnconfigure(1, weight=1)
            
            for i, (display_name, part_name) in enumerate(parts):
                self.create_slider_control(group_frame, display_name, part_name, i)
            
            row += 1
    
    def create_slider_control(self, parent, display_name, part_name, row):
        """创建单个滑块控制"""
        min_angle, max_angle = self.analyzer.get_angle_range(part_name)
        default_angle = (min_angle + max_angle) // 2
        
        # 标签
        label = ttk.Label(parent, text=display_name, width=12)
        label.grid(row=row, column=0, sticky=tk.W, padx=(0, 10), pady=2)
        
        # 滑块
        slider = ttk.Scale(parent, from_=min_angle, to=max_angle, orient=tk.HORIZONTAL, 
                          command=lambda val, name=part_name: self.on_slider_change(name, val))
        slider.set(default_angle)
        slider.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=2)
        
        # 数值标签
        value_label = ttk.Label(parent, text=str(default_angle), width=4)
        value_label.grid(row=row, column=2, sticky=tk.W, pady=2)
        
        # 重置按钮
        reset_btn = ttk.Button(parent, text="重置", width=6,
                              command=lambda name=part_name, s=slider, default=default_angle: self.reset_slider(name, s, default))
        reset_btn.grid(row=row, column=3, sticky=tk.W, padx=(5, 0), pady=2)
        
        # 保存引用
        self.sliders[part_name] = slider
        self.value_labels[part_name] = value_label
    
    def on_slider_change(self, part_name, value):
        """滑块值改变事件"""
        try:
            angle = int(float(value))
            self.value_labels[part_name].config(text=str(angle))
            
            if self.analyzer.is_connected:
                self.analyzer.set_face_part_angle(part_name, angle)
        except Exception as e:
            self.log_message(f"滑块控制错误: {str(e)}")
    
    def reset_slider(self, part_name, slider, default_value):
        """重置滑块到默认值"""
        slider.set(default_value)
        self.value_labels[part_name].config(text=str(default_value))
        if self.analyzer.is_connected:
            self.analyzer.set_face_part_angle(part_name, default_value)
    
    def refresh_ports(self):
        """刷新串口列表"""
        ports = self.analyzer.get_available_ports()
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.set(ports[0])
            self.log_message(f"发现 {len(ports)} 个串口")
        else:
            self.log_message("未发现可用串口")
    
    def toggle_connection(self):
        """切换连接状态"""
        if self.analyzer.is_connected:
            self.analyzer.disconnect()
        else:
            port = self.port_var.get()
            if not port:
                messagebox.showwarning("警告", "请选择串口")
                return
            
            self.log_message(f"正在连接到 {port}...")
            threading.Thread(target=self.connect_thread, args=(port,), daemon=True).start()
    
    def connect_thread(self, port):
        """连接线程"""
        self.analyzer.connect(port)
    
    def center_all(self):
        """所有舵机回到中位"""
        if self.analyzer.center_all_servos():
            for part_name, slider in self.sliders.items():
                min_angle, max_angle = self.analyzer.get_angle_range(part_name)
                default_angle = (min_angle + max_angle) // 2
                slider.set(default_angle)
                self.value_labels[part_name].config(text=str(default_angle))
            
            self.log_message("所有舵机已回到中位")
    
    def test_servos(self):
        """测试舵机"""
        if not self.analyzer.is_connected:
            messagebox.showwarning("警告", "请先连接设备")
            return
        
        self.log_message("开始测试舵机...")
        threading.Thread(target=self.analyzer.test_servo, daemon=True).start()
    
    def apply_settings(self):
        """应用设置"""
        self.analyzer.threshold_low = self.low_threshold_var.get()
        self.analyzer.threshold_high = self.high_threshold_var.get()
        self.analyzer.blink_interval = self.blink_interval_var.get()
        self.log_message("参数设置已应用")
    
    def browse_file(self):
        """浏览文件"""
        filename = filedialog.askopenfilename(
            title="选择WAV文件",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
        )
        if filename:
            self.file_var.set(filename)
    
    def play_audio(self):
        """播放音频"""
        if not self.file_var.get():
            messagebox.showwarning("警告", "请选择音频文件")
            return
        
        if not self.analyzer.is_connected:
            messagebox.showwarning("警告", "请先连接设备")
            return
        
        self.is_playing = True
        self.play_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.play_status_label.config(text="正在播放...")
        
        # 在线程中播放
        threading.Thread(target=self.play_thread, daemon=True).start()
    
    def play_thread(self):
        """播放线程"""
        try:
            result = self.analyzer.play_with_mouth_control(self.file_var.get())
            if result:
                self.log_message("音频播放完成")
            else:
                self.log_message("音频播放失败")
        except Exception as e:
            self.log_message(f"播放错误: {str(e)}")
        finally:
            self.root.after(0, self.play_finished)
    
    def stop_audio(self):
        """停止音频"""
        self.analyzer.is_playing = False
        self.play_finished()
    
    def play_finished(self):
        """播放完成"""
        self.is_playing = False
        self.play_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.play_status_label.config(text="未播放")
    
    def on_connection_change(self, connected, message):
        """连接状态改变回调"""
        def update_ui():
            if connected:
                self.status_label.config(text="已连接", foreground="green")
                self.connect_btn.config(text="断开")
                self.center_btn.config(state="normal")
                self.test_btn.config(state="normal")
            else:
                self.status_label.config(text="未连接", foreground="red")
                self.connect_btn.config(text="连接")
                self.center_btn.config(state="disabled")
                self.test_btn.config(state="disabled")
            
            self.log_message(message)
        
        self.root.after(0, update_ui)
    
    def on_response_received(self, response):
        """接收到Arduino响应"""
        if response.strip():
            self.log_message(f"Arduino: {response}")
    
    def log_message(self, message):
        """添加日志消息"""
        def add_log():
            self.log_text.config(state="normal")
            timestamp = time.strftime("%H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
            self.log_text.config(state="disabled")
        
        self.root.after(0, add_log)
    
    def clear_log(self):
        """清空日志"""
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
    
    def on_closing(self):
        """窗口关闭事件"""
        if self.analyzer.is_connected:
            self.analyzer.disconnect()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = FaceControlUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
