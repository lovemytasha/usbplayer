\# U盘音乐播放器



插入U盘自动检测并播放音乐，支持双主题 UI、真频谱律动、系统托盘、开机自启。



\## 功能



\- U盘自动检测播放（支持先插后启动 / 先启动后插）

\- 多U盘时弹窗选择

\- 支持 MP3/WAV/FLAC/OGG/M4A/AAC/WMA/APE 等 20+ 格式

\- 4 种循环模式（顺序 / 列表循环 / 单曲循环 / 随机）

\- 可拖动进度条 + 当前/总时长显示

\- 内嵌频谱律动（真实频谱或模拟）

\- 双主题：战术 HUD 风格 / 系统风格

\- 多语言：简体中文 / English

\- 硬核启动动画（军事 HUD 风格）

\- 系统托盘（关闭窗口不退出）

\- 开机自启（弹窗确认）

\- 记忆上次设置（主题、语言、音量、窗口位置）



\## 截图



> 待补充



\## 依赖



\- Python 3.8+

\- VLC 播放器：https://www.videolan.org/vlc/



```bash

pip install -r requirements.txt

```



或手动安装：



```bash

pip install python-vlc psutil numpy soundcard pystray Pillow customtkinter

```



\## 运行



```bash

python u盘歌曲播放.py

```



跳过启动动画：



```bash

python u盘歌曲播放.py --no-boot

```



强制指定语言：



```bash

python u盘歌曲播放.py --lang=en\_US

```



\## 配置文件



程序会自动保存设置到：



```

\~/.usb\_music\_player/config.json

```



包含主题、语言、音量、播放模式、窗口位置等。删除该文件即可重置所有设置。



\## 打包



先确保已安装 VLC，然后：



```bash

pyi-makespec --onefile --windowed --icon=icon.ico --name="USBPlayer" u盘歌曲播放.py

```



编辑生成的 `USBPlayer.spec`，把 VLC 安装目录的 DLL 和 plugins 加入 `binaries`，然后：



```bash

pyinstaller USBPlayer.spec

```



成品在 `dist/USBPlayer.exe`，约 130 MB，已内置 VLC 解码器，用户无需额外安装。



\## 快捷键 / 操作



| 操作 | 方式 |

|------|------|

| 播放/暂停 | 主界面中央按钮 |

| 上一首 / 下一首 | 主界面两侧按钮 |

| 切换循环模式 | 🔁 按钮 |

| 调节音量 | 音量滑块 |

| 拖动进度 | 进度条 |

| 切换主题 | 右上角 ⇄ |

| 切换语言 | 右上角下拉框 |

| 关闭到托盘 | 点窗口 X |

| 退出程序 | 托盘右键 → 退出 |



\## 许可证



本项目基于 \[VLC media player](https://www.videolan.org/)（GPLv2）构建，整体以 \*\*GPLv2\*\* 发布。



VLC 版权归 VideoLAN 团队所有。



本项目源代码同样以 GPLv2 开源，你可以自由使用、修改、分发，但衍生作品也必须以 GPLv2 开源。

