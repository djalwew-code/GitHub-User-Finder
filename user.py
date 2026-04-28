import tkinter as tk
from tkinter import ttk, messagebox
import requests
import json
import os
from datetime import datetime
from PIL import Image, ImageTk
import io
from urllib.request import urlopen

class GitHubUserFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub User Finder")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # API configuration
        self.api_url = "https://api.github.com"
        self.favorites_file = "favorites.json"
        self.favorites = self.load_favorites()
        
        # Create GUI elements
        self.create_widgets()
        
    def create_widgets(self):
        # Search frame
        search_frame = ttk.Frame(self.root, padding="10")
        search_frame.pack(fill=tk.X)
        
        ttk.Label(search_frame, text="Поиск пользователя GitHub:").pack(side=tk.LEFT, padx=5)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<Return>', lambda event: self.search_users())
        
        ttk.Button(search_frame, text="Поиск", command=self.search_users).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Избранное", command=self.show_favorites).pack(side=tk.LEFT, padx=5)
        
        # Main container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Results frame (left side)
        results_frame = ttk.LabelFrame(main_container, text="Результаты поиска", padding="10")
        main_container.add(results_frame, weight=1)
        
        # Scrollbar for results
        scrollbar = ttk.Scrollbar(results_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_listbox = tk.Listbox(results_frame, yscrollcommand=scrollbar.set, height=15)
        self.results_listbox.pack(fill=tk.BOTH, expand=True)
        self.results_listbox.bind('<Double-Button-1>', self.show_user_details)
        
        scrollbar.config(command=self.results_listbox.yview)
        
        # Add to favorites button
        ttk.Button(results_frame, text="Добавить в избранное", 
                  command=self.add_to_favorites).pack(pady=5)
        
        # User details frame (right side)
        details_frame = ttk.LabelFrame(main_container, text="Информация о пользователе", padding="10")
        main_container.add(details_frame, weight=1)
        
        # User info text widget with scrollbar
        self.details_text = tk.Text(details_frame, wrap=tk.WORD, width=40, height=20)
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к поиску")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Current search results
        self.current_results = []
        
    def search_users(self):
        """Search GitHub users by username"""
        query = self.search_var.get().strip()
        
        if not query:
            messagebox.showwarning("Предупреждение", "Поле поиска не может быть пустым!")
            return
            
        self.status_var.set(f"Поиск пользователей: {query}...")
        self.root.update()
        
        try:
            response = requests.get(f"{self.api_url}/search/users", 
                                  params={'q': query, 'per_page': 20},
                                  headers={'Accept': 'application/vnd.github.v3+json'})
            response.raise_for_status()
            
            data = response.json()
            users = data.get('items', [])
            
            # Clear previous results
            self.results_listbox.delete(0, tk.END)
            self.current_results = []
            
            if not users:
                self.status_var.set("Пользователи не найдены")
                return
                
            # Display users in listbox
            for user in users:
                self.results_listbox.insert(tk.END, user['login'])
                self.current_results.append(user)
                
            self.status_var.set(f"Найдено пользователей: {len(users)}")
            
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Ошибка", f"Ошибка при запросе к API: {str(e)}")
            self.status_var.set("Ошибка при поиске")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неизвестная ошибка: {str(e)}")
            self.status_var.set("Ошибка")
    
    def show_user_details(self, event=None):
        """Show detailed information about selected user"""
        selection = self.results_listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        if index >= len(self.current_results):
            return
            
        user = self.current_results[index]
        username = user['login']
        
        self.status_var.set(f"Загрузка информации о {username}...")
        self.root.update()
        
        try:
            response = requests.get(f"{self.api_url}/users/{username}",
                                  headers={'Accept': 'application/vnd.github.v3+json'})
            response.raise_for_status()
            
            user_data = response.json()
            
            # Display user details
            self.details_text.delete(1.0, tk.END)
            
            details = f"""Информация о пользователе:
            
Логин: {user_data.get('login', 'Н/Д')}
Имя: {user_data.get('name', 'Н/Д')}
Компания: {user_data.get('company', 'Н/Д')}
Блог: {user_data.get('blog', 'Н/Д')}
Местоположение: {user_data.get('location', 'Н/Д')}
Email: {user_data.get('email', 'Н/Д')}
Биография: {user_data.get('bio', 'Н/Д')}

Статистика:
Публичные репозитории: {user_data.get('public_repos', 0)}
Подписчики: {user_data.get('followers', 0)}
Подписки: {user_data.get('following', 0)}
Создан аккаунт: {user_data.get('created_at', 'Н/Д')}
Последнее обновление: {user_data.get('updated_at', 'Н/Д')}

URL профиля: {user_data.get('html_url', 'Н/Д')}
"""
            
            self.details_text.insert(1.0, details)
            self.status_var.set(f"Информация о {username} загружена")
            
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Ошибка", f"Ошибка при загрузке данных пользователя: {str(e)}")
            self.status_var.set("Ошибка при загрузке")
    
    def add_to_favorites(self):
        """Add selected user to favorites"""
        selection = self.results_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите пользователя для добавления в избранное")
            return
            
        index = selection[0]
        if index >= len(self.current_results):
            return
            
        user = self.current_results[index]
        username = user['login']
        
        # Check if already in favorites
        if username in self.favorites:
            messagebox.showinfo("Информация", f"Пользователь {username} уже в избранном")
            return
            
        # Add to favorites with timestamp
        self.favorites[username] = {
            'login': username,
            'avatar_url': user.get('avatar_url', ''),
            'html_url': user.get('html_url', ''),
            'added_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.save_favorites()
        messagebox.showinfo("Успех", f"Пользователь {username} добавлен в избранное")
        self.status_var.set(f"{username} добавлен в избранное")
    
    def show_favorites(self):
        """Display favorites in a new window"""
        if not self.favorites:
            messagebox.showinfo("Избранное", "Список избранного пуст")
            return
            
        # Create favorites window
        fav_window = tk.Toplevel(self.root)
        fav_window.title("Избранные пользователи")
        fav_window.geometry("400x500")
        
        # Favorites listbox
        frame = ttk.Frame(fav_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Избранные пользователи:", font=("Arial", 12, "bold")).pack(pady=5)
        
        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        fav_listbox = tk.Listbox(listbox_frame, yscrollcommand=scrollbar.set)
        fav_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=fav_listbox.yview)
        
        # Populate favorites
        for username in self.favorites:
            fav_listbox.insert(tk.END, username)
        
        # Buttons frame
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10)
        
        def remove_from_favorites():
            selection = fav_listbox.curselection()
            if not selection:
                messagebox.showwarning("Предупреждение", "Выберите пользователя для удаления")
                return
                
            username = fav_listbox.get(selection[0])
            if username in self.favorites:
                del self.favorites[username]
                self.save_favorites()
                fav_listbox.delete(selection[0])
                self.status_var.set(f"{username} удален из избранного")
                
                if not self.favorites:
                    fav_window.destroy()
                    
        def show_fav_user_details():
            selection = fav_listbox.curselection()
            if not selection:
                return
                
            username = fav_listbox.get(selection[0])
            # Set search and execute
            self.search_var.set(username)
            self.search_users()
            # After a short delay, select and show details
            self.root.after(1000, lambda: self.select_user_in_list(username))
            fav_window.destroy()
        
        ttk.Button(button_frame, text="Показать информацию", 
                  command=show_fav_user_details).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Удалить из избранного", 
                  command=remove_from_favorites).pack(side=tk.LEFT, padx=5)
    
    def select_user_in_list(self, username):
        """Find and select a user in the results listbox"""
        for i in range(self.results_listbox.size()):
            if self.results_listbox.get(i) == username:
                self.results_listbox.selection_clear(0, tk.END)
                self.results_listbox.selection_set(i)
                self.results_listbox.see(i)
                self.show_user_details()
                break
    
    def load_favorites(self):
        """Load favorites from JSON file"""
        if os.path.exists(self.favorites_file):
            try:
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading favorites: {e}")
                return {}
        return {}
    
    def save_favorites(self):
        """Save favorites to JSON file"""
        try:
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, indent=2, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить избранное: {str(e)}")

def main():
    root = tk.Tk()
    app = GitHubUserFinder(root)
    root.mainloop()

if __name__ == "__main__":
    main()