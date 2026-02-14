from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.listview import ListView
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.core.audio import SoundLoader
from kivy.properties import NumericProperty, StringProperty, BooleanProperty, ListProperty
from kivy.metrics import dp
import os
import time


class ModernButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = kwargs.get('bg_color', (0.4, 0.49, 0.92, 1))
        self.color = kwargs.get('text_color', (1, 1, 1, 1))
        self.font_size = kwargs.get('font_size', dp(16))
        self.bind(pos=self.update_canvas, size=self.update_canvas)
        self.update_canvas()
    
    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.background_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
    
    def on_press(self):
        self.background_color = tuple(max(0, c - 0.1) for c in self.background_color[:3]) + (1,)
        self.update_canvas()
    
    def on_release(self):
        self.background_color = self._original_bg if hasattr(self, '_original_bg') else (0.4, 0.49, 0.92, 1)
        self.update_canvas()


class AlbumArt(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(150), dp(150))
        self.bind(pos=self.draw, size=self.draw)
    
    def draw(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(0.06, 0.2, 0.38, 1)
            Ellipse(pos=self.pos, size=self.size)
            Color(0.09, 0.13, 0.24, 1)
            Ellipse(pos=(self.pos[0] + dp(15), self.pos[1] + dp(15)), 
                   size=(self.size[0] - dp(30), self.size[1] - dp(30)))
            Color(0.4, 0.49, 0.92, 1)
            Ellipse(pos=(self.pos[0] + dp(45), self.pos[1] + dp(45)), 
                   size=(self.size[0] - dp(90), self.size[1] - dp(90)))


class MP3PlayerLayout(BoxLayout):
    current_time = NumericProperty(0)
    total_time = NumericProperty(0)
    song_title = StringProperty("未选择歌曲")
    song_status = StringProperty("等待播放...")
    is_playing = BooleanProperty(False)
    is_paused = BooleanProperty(False)
    volume_value = NumericProperty(70)
    playlist = ListProperty([])
    current_index = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(20)
        self.spacing = dp(10)
        
        self.current_sound = None
        self.current_file = None
        self.update_event = None
        
        self.setup_ui()
    
    def setup_ui(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.1, 0.1, 0.18, 1)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_bg, size=self.update_bg)
        
        header = Label(
            text='[size=28][b]🎵 音乐播放器[/b][/size]',
            markup=True,
            color=(0.94, 0.58, 0.98, 1),
            size_hint_y=None,
            height=dp(60)
        )
        self.add_widget(header)
        
        art_container = BoxLayout(size_hint_y=None, height=dp(170))
        art_container.add_widget(Label(size_hint_x=0.5))
        self.album_art = AlbumArt()
        art_container.add_widget(self.album_art)
        art_container.add_widget(Label(size_hint_x=0.5))
        self.add_widget(art_container)
        
        info_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(60), spacing=dp(5))
        self.title_label = Label(
            text=self.song_title,
            font_size=dp(18),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(30)
        )
        info_box.add_widget(self.title_label)
        
        self.status_label = Label(
            text=self.song_status,
            font_size=dp(12),
            color=(0.63, 0.63, 0.63, 1),
            size_hint_y=None,
            height=dp(25)
        )
        info_box.add_widget(self.status_label)
        self.add_widget(info_box)
        
        progress_box = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        self.time_label = Label(text='0:00', font_size=dp(12), color=(0.63, 0.63, 0.63, 1), size_hint_x=0.15)
        progress_box.add_widget(self.time_label)
        
        self.progress_slider = Slider(min=0, max=100, value=0, size_hint_x=0.7)
        self.progress_slider.bind(on_touch_up=self.seek_song)
        progress_box.add_widget(self.progress_slider)
        
        self.total_label = Label(text='0:00', font_size=dp(12), color=(0.63, 0.63, 0.63, 1), size_hint_x=0.15)
        progress_box.add_widget(self.total_label)
        self.add_widget(progress_box)
        
        control_box = BoxLayout(size_hint_y=None, height=dp(80), spacing=dp(15))
        control_box.add_widget(Label(size_hint_x=0.2))
        
        self.prev_btn = ModernButton(text='⏮', font_size=dp(20), size_hint_x=0.2, bg_color=(0.06, 0.2, 0.38, 1))
        self.prev_btn.bind(on_press=self.prev_song)
        control_box.add_widget(self.prev_btn)
        
        self.play_btn = ModernButton(text='▶', font_size=dp(28), size_hint_x=0.3, bg_color=(0.4, 0.49, 0.92, 1))
        self.play_btn.bind(on_press=self.toggle_play)
        control_box.add_widget(self.play_btn)
        
        self.next_btn = ModernButton(text='⏭', font_size=dp(20), size_hint_x=0.2, bg_color=(0.06, 0.2, 0.38, 1))
        self.next_btn.bind(on_press=self.next_song)
        control_box.add_widget(self.next_btn)
        
        control_box.add_widget(Label(size_hint_x=0.2))
        self.add_widget(control_box)
        
        playlist_header = BoxLayout(size_hint_y=None, height=dp(40))
        playlist_header.add_widget(Label(
            text='播放列表',
            font_size=dp(16),
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_x=0.6,
            halign='left',
            valign='middle'
        ))
        
        add_btn = ModernButton(text='+ 添加', font_size=dp(14), size_hint_x=0.4, bg_color=(0.4, 0.49, 0.92, 1))
        add_btn.bind(on_press=self.show_file_chooser)
        playlist_header.add_widget(add_btn)
        self.add_widget(playlist_header)
        
        from kivy.uix.recycleview import RecycleView
        from kivy.uix.recycleboxlayout import RecycleBoxLayout
        
        class PlaylistView(RecycleView):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.viewclass = 'Label'
                self.layout_manager = RecycleBoxLayout(default_size=(None, dp(40)),
                                                       default_size_hint=(1, None),
                                                       orientation='vertical')
        
        self.playlist_widget = Label(
            text='[i]点击"添加"按钮选择音乐文件[/i]',
            markup=True,
            color=(0.5, 0.5, 0.5, 1),
            halign='center',
            valign='middle'
        )
        self.add_widget(self.playlist_widget)
        
        volume_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        volume_box.add_widget(Label(text='🔊', font_size=dp(20), size_hint_x=0.1))
        
        self.volume_slider = Slider(min=0, max=100, value=70, size_hint_x=0.8)
        self.volume_slider.bind(value=self.set_volume)
        volume_box.add_widget(self.volume_slider)
        
        self.volume_label = Label(text='70%', font_size=dp(14), color=(0.63, 0.63, 0.63, 1), size_hint_x=0.1)
        volume_box.add_widget(self.volume_label)
        self.add_widget(volume_box)
    
    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def format_time(self, seconds):
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f'{minutes}:{secs:02d}'
    
    def show_file_chooser(self, instance):
        from kivy.uix.modalview import ModalView
        from kivy.uix.filechooser import FileChooserListView
        
        content = BoxLayout(orientation='vertical', spacing=dp(10))
        
        try:
            filechooser = FileChooserListView(
                path='/sdcard/Music' if os.path.exists('/sdcard/Music') else os.path.expanduser('~'),
                filters=['*.mp3', '*.wav', '*.ogg', '*.flac'],
                multiselect=True
            )
        except:
            filechooser = FileChooserListView(
                path='.',
                multiselect=True
            )
        
        content.add_widget(filechooser)
        
        btn_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        cancel_btn = ModernButton(text='取消', bg_color=(0.5, 0.5, 0.5, 1))
        btn_box.add_widget(cancel_btn)
        
        select_btn = ModernButton(text='选择', bg_color=(0.4, 0.49, 0.92, 1))
        btn_box.add_widget(select_btn)
        content.add_widget(btn_box)
        
        popup = Popup(title='选择音乐文件', content=content, size_hint=(0.9, 0.9))
        
        cancel_btn.bind(on_press=popup.dismiss)
        select_btn.bind(on_press=lambda x: self.add_files(filechooser.selection, popup))
        
        popup.open()
    
    def add_files(self, files, popup):
        popup.dismiss()
        
        for file in files:
            if file not in self.playlist:
                self.playlist.append(file)
        
        if self.playlist:
            display_text = '\n'.join([os.path.basename(f) for f in self.playlist[:10]])
            if len(self.playlist) > 10:
                display_text += f'\n... 还有 {len(self.playlist) - 10} 首'
            self.playlist_widget.text = display_text
    
    def toggle_play(self, instance):
        if self.is_playing and not self.is_paused:
            self.pause_song()
        else:
            self.play_song()
    
    def play_song(self):
        if not self.playlist:
            self.status_label.text = '请先添加音乐文件！'
            return
        
        if self.is_paused:
            if self.current_sound:
                self.current_sound.play()
                self.is_paused = False
                self.is_playing = True
                self.status_label.text = '正在播放'
                self.play_btn.text = '⏸'
            return
        
        self.current_file = self.playlist[self.current_index]
        
        if self.current_sound:
            self.current_sound.stop()
            self.current_sound.unload()
        
        self.current_sound = SoundLoader.load(self.current_file)
        
        if self.current_sound:
            self.current_sound.play()
            self.is_playing = True
            self.is_paused = False
            
            filename = os.path.basename(self.current_file)
            if len(filename) > 25:
                filename = filename[:22] + '...'
            self.title_label.text = filename
            self.status_label.text = '正在播放'
            self.play_btn.text = '⏸'
            
            self.total_time = self.current_sound.length
            self.total_label.text = self.format_time(self.total_time)
            self.progress_slider.max = self.total_time
            
            if self.update_event:
                self.update_event.cancel()
            self.update_event = Clock.schedule_interval(self.update_progress, 0.1)
        else:
            self.status_label.text = '无法加载音频文件'
    
    def pause_song(self):
        if self.current_sound and self.is_playing:
            self.current_sound.stop()
            self.is_paused = True
            self.status_label.text = '已暂停'
            self.play_btn.text = '▶'
    
    def stop_song(self):
        if self.current_sound:
            self.current_sound.stop()
        self.is_playing = False
        self.is_paused = False
        self.status_label.text = '已停止'
        self.play_btn.text = '▶'
        if self.update_event:
            self.update_event.cancel()
    
    def prev_song(self, instance):
        if self.playlist:
            self.stop_song()
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.play_song()
    
    def next_song(self, instance):
        if self.playlist:
            self.stop_song()
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.play_song()
    
    def set_volume(self, instance, value):
        if self.current_sound:
            self.current_sound.volume = value / 100
        self.volume_label.text = f'{int(value)}%'
    
    def seek_song(self, instance, touch):
        if instance.collide_point(*touch.pos):
            if self.current_sound and self.total_time > 0:
                pos = instance.value
                self.current_sound.seek(pos)
    
    def update_progress(self, dt):
        if self.current_sound and self.is_playing and not self.is_paused:
            try:
                pos = self.current_sound.get_pos()
                if pos >= 0:
                    self.time_label.text = self.format_time(pos)
                    self.progress_slider.value = pos
                    
                    if pos >= self.total_time - 0.5:
                        self.next_song(None)
            except:
                pass


class MP3PlayerApp(App):
    def build(self):
        self.title = '🎵 音乐播放器'
        return MP3PlayerLayout()


if __name__ == '__main__':
    MP3PlayerApp().run()
