#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TTS测试工具 - 诊断科大讯飞TTS问题
"""

import os
import sys
import logging
from tts_integration import TTSIntegration
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class TTSTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TTS测试工具")
        
        # 当前选择的音频文件
        self.current_file = None
        
        # 主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # 配置网格权重
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        
        # 日志文本框
        self.log_text = tk.Text(self.main_frame, wrap=tk.WRAP, height=10, state="disabled")
        self.log_text.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # 滚动条
        scrollbar = ttk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.log_text['yscrollcommand'] = scrollbar.set
        
        # 菜单
        self.setup_menu()
        
        # 控制面板
        self.setup_control_frame()
        
        # 状态栏
        self.status_bar = ttk.Label(self.main_frame, text="欢迎使用TTS测试工具", relief=tk.SUNKEN, anchor="w")
        self.status_bar.grid(row=2, column=0, sticky="ew")
        
        # 初始化面部控制分析对象
        from analysis_sound import AudioAnalyzer
        self.analyzer = AudioAnalyzer()
        
        # 连接Arduino
        self.connect_arduino()
    
    def setup_menu(self):
        """设置菜单"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        help_menu.add_command(label="关于", command=self.show_about)
    
    def show_about(self):
        """显示关于信息"""
        messagebox.showinfo("关于", "科大讯飞TTS测试工具\n版本 1.0\n作者: 您的名字")
    
    def setup_control_frame(self):
        """设置控制面板"""
        control_frame = ttk.LabelFrame(self.main_frame, text="控制面板", padding="10")
        control_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # 连接按钮
        self.connect_btn = ttk.Button(control_frame, text="连接Arduino", 
                                    command=self.connect_arduino)
        self.connect_btn.grid(row=0, column=0, columnspan=2, pady=5, sticky="ew")
        
        # 状态显示
        self.status_label = ttk.Label(control_frame, text="未连接", foreground="red")
        self.status_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # 音频控制区域
        audio_frame = ttk.LabelFrame(control_frame, text="音频控制", padding="5")
        audio_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky="ew")
        
        # 文件选择
        ttk.Button(audio_frame, text="选择音频文件", 
                  command=self.select_audio_file).grid(row=0, column=0, columnspan=2, pady=5, sticky="ew")
        
        self.file_label = ttk.Label(audio_frame, text="未选择文件", foreground="gray")
        self.file_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # 播放控制
        play_frame = ttk.Frame(audio_frame)
        play_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky="ew")
        
        self.play_btn = ttk.Button(play_frame, text="播放", command=self.play_audio)
        self.play_btn.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.stop_btn = ttk.Button(play_frame, text="停止", command=self.stop_audio)
        self.stop_btn.grid(row=0, column=1, padx=5, sticky="ew")
        
        play_frame.columnconfigure(0, weight=1)
        play_frame.columnconfigure(1, weight=1)
        
        # robot_head版本的增强面部控制区域
        face_frame = ttk.LabelFrame(control_frame, text="面部控制 (robot_head版)", padding="5")
        face_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")
        
        # 智能眨眼控制
        self.enable_blink_var = tk.BooleanVar(value=True)
        blink_check = ttk.Checkbutton(face_frame, text="启用智能眨眼 (说话间隙)", 
                                     variable=self.enable_blink_var)
        blink_check.grid(row=0, column=0, columnspan=2, pady=5, sticky="w")
        
        # 手动控制按钮
        manual_frame = ttk.Frame(face_frame)
        manual_frame.grid(row=1, column=0, columnspan=2, pady=5, sticky="ew")
        
        ttk.Button(manual_frame, text="手动眨眼", 
                  command=self.manual_blink).grid(row=0, column=0, padx=2, sticky="ew")
        
        ttk.Button(manual_frame, text="测试面部动画", 
                  command=self.test_face_animation).grid(row=0, column=1, padx=2, sticky="ew")
        
        ttk.Button(manual_frame, text="快速嘴部测试", 
                  command=self.test_fast_mouth).grid(row=0, column=2, padx=2, sticky="ew")
        
        manual_frame.columnconfigure(0, weight=1)
        manual_frame.columnconfigure(1, weight=1)
        manual_frame.columnconfigure(2, weight=1)
        
        # robot_head版本的预设表情控制
        expression_frame = ttk.LabelFrame(face_frame, text="预设表情", padding="3")
        expression_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky="ew")
        
        expressions = [
            ("微笑", "smile"),
            ("皱眉", "frown"), 
            ("眨眼", "blink"),
            ("中性", "neutral")
        ]
        
        for i, (text, expr) in enumerate(expressions):
            row = i // 2
            col = i % 2
            ttk.Button(expression_frame, text=text, 
                      command=lambda e=expr: self.apply_expression(e)).grid(
                          row=row, column=col, padx=2, pady=2, sticky="ew")
        
        expression_frame.columnconfigure(0, weight=1)
        expression_frame.columnconfigure(1, weight=1)
        
        # robot_head版本的敏感度控制
        sensitivity_frame = ttk.LabelFrame(control_frame, text="敏感度设置 (robot_head版)", padding="5")
        sensitivity_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")
        
        # 敏感度选择
        self.sensitivity_var = tk.StringVar(value="normal")
        sensitivity_options = [
            ("低", "low"),
            ("正常", "normal"),
            ("高", "high"), 
            ("超高", "ultra")
        ]
        
        for i, (text, value) in enumerate(sensitivity_options):
            ttk.Radiobutton(sensitivity_frame, text=text, variable=self.sensitivity_var,
                           value=value, command=self.update_sensitivity).grid(
                               row=0, column=i, padx=5, sticky="w")
        
        # 敏感度描述标签
        self.sensitivity_desc = ttk.Label(sensitivity_frame, text="正常敏感度 - 平衡的响应", 
                                         foreground="blue", font=("Arial", 8))
        self.sensitivity_desc.grid(row=1, column=0, columnspan=4, pady=5, sticky="w")
        
        # robot_head版本的高级测试功能
        advanced_frame = ttk.LabelFrame(control_frame, text="高级测试 (robot_head版)", padding="5")
        advanced_frame.grid(row=5, column=0, columnspan=2, pady=10, sticky="ew")
        
        ttk.Button(advanced_frame, text="动态嘴部测试", 
                  command=self.test_dynamic_mouth).grid(row=0, column=0, pady=5, sticky="ew")
        
        ttk.Button(advanced_frame, text="振幅映射测试", 
                  command=self.test_amplitude_mapping).grid(row=0, column=1, pady=5, sticky="ew")
        
        advanced_frame.columnconfigure(0, weight=1)
        advanced_frame.columnconfigure(1, weight=1)

    def manual_blink(self):
        """手动触发眨眼 - robot_head版本"""
        if not self.analyzer.is_connected:
            self.show_message("请先连接Arduino", "警告")
            return
        
        self.analyzer.trigger_blink()
        self.append_log("🔴 手动眨眼")

    def test_face_animation(self):
        """测试面部动画 - robot_head版本"""
        if not self.analyzer.is_connected:
            self.show_message("请先连接Arduino", "警告")
            return
        
        self.append_log("🎭 开始测试面部动画 (边说话边眨眼)...")
        self.analyzer.test_face_animation()

    def test_fast_mouth(self):
        """测试快速嘴部控制 - robot_head版本"""
        if not self.analyzer.is_connected:
            self.show_message("请先连接Arduino", "警告")
            return
        
        self.append_log("⚡ 开始测试快速嘴部控制...")
        self.analyzer.test_fast_mouth_control()

    def test_dynamic_mouth(self):
        """测试动态嘴部运动 - robot_head版本"""
        if not self.analyzer.is_connected:
            self.show_message("请先连接Arduino", "警告")
            return
        
        self.append_log("🌊 开始测试动态嘴部运动...")
        self.analyzer.test_dynamic_mouth_movement()

    def test_amplitude_mapping(self):
        """测试振幅映射 - robot_head版本"""
        self.append_log("📊 开始振幅映射测试...")
        if hasattr(self.analyzer, 'test_amplitude_mapping'):
            self.analyzer.test_amplitude_mapping()
        else:
            # 手动显示映射测试
            test_amplitudes = [0.0, 0.001, 0.003, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05, 0.1]
            self.append_log("=== 振幅到角度映射测试 ===")
            for amp in test_amplitudes:
                if hasattr(self.analyzer, 'amplitude_to_angle'):
                    angle = self.analyzer.amplitude_to_angle(amp)
                    self.append_log(f"振幅: {amp:.4f} -> 角度: {angle}°")
            self.append_log("=== 测试完成 ===")

    def update_sensitivity(self):
        """更新敏感度设置 - robot_head版本"""
        if hasattr(self.analyzer, 'set_mouth_sensitivity'):
            sensitivity = self.sensitivity_var.get()
            self.analyzer.set_mouth_sensitivity(sensitivity)
            
            # 更新描述标签
            desc = self.analyzer.current_sensitivity.get('description', '未知设置')
            self.sensitivity_desc.config(text=desc)
            
            self.append_log(f"⚙️ 敏感度设置: {sensitivity} - {desc}")

    def play_audio(self):
        """播放音频 - robot_head版本的增强播放"""
        if not self.current_file:
            self.show_message("请先选择音频文件", "警告")
            return
        
        if not self.analyzer.is_connected:
            self.show_message("请先连接Arduino", "警告")
            return
        
        try:
            self.append_log(f"🎵 开始播放: {os.path.basename(self.current_file)}")
            
            # 获取robot_head版本的面部控制设置
            enable_blink = self.enable_blink_var.get()
            
            # 使用robot_head版本的完整面部控制播放方法
            self.current_playback = self.analyzer.play_audio_with_face_control(
                self.current_file, 
                enable_blink=enable_blink
            )
            
            if self.current_playback:
                self.play_btn.configure(state="disabled")
                self.stop_btn.configure(state="normal")
                self.append_log(f"🎭 面部控制: {'完整模式(嘴部+智能眨眼)' if enable_blink else '仅嘴部模式'}")
                
                # 监控播放状态
                self.monitor_playback()
            else:
                self.append_log("❌ 播放启动失败")
                
        except Exception as e:
            self.show_message(f"播放失败: {str(e)}", "错误")
            self.append_log(f"❌ 播放异常: {e}")

    def monitor_playback(self):
        """监控播放状态"""
        if self.current_playback:
            # 检查音频线程是否还在运行
            if self.current_playback["audio_thread"].is_alive():
                # 继续监控
                self.root.after(1000, self.monitor_playback)
            else:
                # 播放完成
                self.current_playback = None
                self.play_btn.configure(state="normal")
                self.stop_btn.configure(state="disabled")
                self.append_log("✅ 播放完成")

    def connect_arduino(self):
        """连接Arduino"""
        try:
            if self.analyzer.connect_arduino():
                self.status_label.configure(text="已连接", foreground="green")
                self.append_log("✅ Arduino连接成功")
            else:
                self.status_label.configure(text="未连接", foreground="red")
                self.append_log("❌ Arduino连接失败")
        except Exception as e:
            self.status_label.configure(text="未连接", foreground="red")
            self.append_log(f"❌ 连接错误: {e}")

    def select_audio_file(self):
        """选择音频文件"""
        file_path = filedialog.askopenfilename(
            filetypes=[("WAV文件", "*.wav"), ("所有文件", "*.*")],
            title="选择音频文件"
        )
        
        if file_path:
            self.current_file = file_path
            self.file_label.configure(text=os.path.basename(file_path), foreground="black")
            self.append_log(f"📂 选择音频文件: {file_path}")
        else:
            self.append_log("❌ 未选择音频文件")

    def stop_audio(self):
        """停止音频播放"""
        if self.current_playback:
            self.current_playback["stop"]()
            self.current_playback = None
            self.play_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self.append_log("⏹️ 停止播放")

    def append_log(self, message):
        """追加日志信息到文本框"""
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.configure(state="disabled")
        self.log_text.yview(tk.END)

    def show_message(self, message, title="信息"):
        """显示消息框"""
        messagebox.showinfo(title, message)

# 测试代码
if __name__ == "__main__":
    root = tk.Tk()
    app = TTSTestApp(root)
    root.mainloop()