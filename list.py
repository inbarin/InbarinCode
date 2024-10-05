"""
Oh, hello there.
I see you don't trust random python scripts from the internet. smart move.
Feel free to look/poke around. If you find any bug, please report it.
"""

import importlib.util
import tkinter as tk
from tkinter import ttk, simpledialog, filedialog, messagebox
import json
import webbrowser
import os
try:
    import pyperclip
except ImportError:
    pyperclip = ""


CONFIG_FILE = "config.json"


def import_plugin(file_path):
    spec = importlib.util.spec_from_file_location("", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def warn_missing(package):
    messagebox.showinfo(f"This function requires '{package}' to be installed. sorry!")


def protect_package(package):
    if package in globals() and globals()[package]:
        return True
    warn_missing(package)
    return False


class InteractiveListApp(tk.Frame):
    def __init__(self, parent, notebook, tab_index, file_path=None):
        super().__init__(parent)
        self.notebook = notebook
        self.tab_index = tab_index

        self.tree = ttk.Treeview(self, show='tree')
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(fill=tk.X, side=tk.LEFT)

        self.add_item_button = self.create_button("Add Item", self.add_item)
        self.add_subitem_button = self.create_button("Add Subitem", self.add_subitem)
        self.edit_button = self.create_button("Edit Item", self.edit_item)
        self.remove_button = self.create_button("Remove Item", self.remove_item)
        self.cut_button = self.create_button("Cut", self.cut_item)
        self.copy_button = self.create_button("Copy", self.copy_item)
        self.paste_button = self.create_button("Paste", self.paste_item)
        self.up_button = self.create_button("Move Up", self.move_up)
        self.down_button = self.create_button("Move Down", self.move_down)
        self.expand_button = self.create_button("Expand All", self.expand_all)
        self.collapse_button = self.create_button("Collapse All", self.collapse_all)
        self.save_button = self.create_button("Save List", self.save_list)
        self.save_as_button = self.create_button("Save List As", self.save_list_as)
        self.load_button = self.create_button("Load List", self.load_list)
        self.open_link_button = self.create_button("Open Link", self.open_link)
        self.search_button = self.create_button("Find string", self.find_string)

        self.file_path = file_path

        self.bind_keys()

        if file_path:
            self.load_list_from_path(file_path)

    def add_plugin(self, module):
        module.apply_plugin_list(self)

    def create_button(self, text, command):
        button = tk.Button(self.button_frame, text=text, command=command)
        button.pack(side=tk.TOP, padx=5, pady=3)
        return button

    def bind_keys(self):
        self.tree.bind("<Return>", lambda event: self.add_subitem())
        self.tree.bind("<Tab>", lambda event: self.edit_item())
        self.tree.bind("<space>", lambda event: self.open_link())
        self.tree.bind("<Control-x>", lambda event: self.cut_item())
        self.tree.bind("<Control-c>", lambda event: self.copy_item())
        self.tree.bind("<Control-v>", lambda event: self.paste_item())
        self.tree.bind("<Control-s>", lambda event: self.save_list())

    def _add_item_to(self, item, item_text=None):
        if not item_text:
            item_text = simpledialog.askstring("Add Item", "Enter item text:")
        if item_text:
            self.tree.insert(item, 'end', text=item_text)
            self.tree.item(item, open=False)

    def add_item(self, item_text=None):
        self._add_item_to('', item_text)

    def add_subitem(self, item_text=None):
        self.wrap_function_with_item(self._add_item_to, item_text, can_use_root=True)

    def _edit_item(self, item):
        current_text = self.tree.item(item, 'text')
        new_text = simpledialog.askstring("Edit Item", "Edit item text:", initialvalue=current_text)
        if new_text:
            self.tree.item(item, text=new_text)

    def edit_item(self):
        self.wrap_function_with_item(self._edit_item)

    def remove_item(self):
        self.wrap_function_with_item(self.tree.delete)

    def _move_item(self, item, count):
        parent_item = self.tree.parent(item)
        index = self.tree.index(item)
        self.tree.move(item, parent_item, index + count)

    def move_up(self):
        self.wrap_function_with_item(self._move_item, -1)

    def move_down(self):
        self.wrap_function_with_item(self._move_item, 1)

    def _set_expand_state(self, item, state):
        self.tree.item(item, open=state)
        for child in self.tree.get_children(item):
            self._set_expand_state(child, state)

    def expand_all(self):
        self.wrap_function_with_item(self._set_expand_state, True)

    def collapse_all(self):
        self.wrap_function_with_item(self._set_expand_state, False)

    def _save_list(self):
        data = self.tree_to_dict('')
        with open(self.file_path, 'w') as file:
            json.dump(data, file, separators=(',', ':'))
        self.notebook.tab(self.tab_index, text=self.file_path.split("/")[-1])

    def save_list_as(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if file_path:
            self.file_path = file_path
            self._save_list()

    def save_list(self):
        if not self.file_path:
            self.save_list_as()
        else:
            self._save_list()

    def tree_to_dict(self, parent_id, filter_string=''):
        items = []
        for child_id in self.tree.get_children(parent_id):
            item = self.tree_to_dict_with_parent(child_id, filter_string)
            if item:
                items.append(item)
        return items

    def load_list(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if file_path:
            self.file_path = file_path
            self.load_list_from_path(self.file_path)
            self.notebook.tab(self.tab_index, text=self.file_path.split("/")[-1])

    def load_list_from_path(self, file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
            self.clear_list()
            self.dict_to_tree('', data)

    def dict_to_tree(self, parent_id, items):
        for item in items:
            text = item.get('t', item.get('text', ''))
            item_id = self.tree.insert(parent_id, 'end', text=text)
            subitems = item.get('s', item.get('subitems', []))
            self.dict_to_tree(item_id, subitems)

    def clear_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _open_link(self, item):
        text = self.tree.item(item, 'text')
        if text.startswith("http://") or text.startswith("https://"):
            webbrowser.open(text)
        else:
            messagebox.showinfo("This is not a link. if you are sure it is, please open it manually.")

    def open_link(self):
        self.wrap_function_with_item(self._open_link)

    def _copy_item(self, item):
        data = [self.tree_to_dict_with_parent(item)]
        pyperclip.copy(json.dumps(data))

    def _cut_item(self, item):
        self._copy_item(item)
        self.tree.delete(item)

    def copy_item(self):
        if not protect_package("pyperclip"):
            return
        self.wrap_function_with_item(self._copy_item)

    def cut_item(self):
        if not protect_package("pyperclip"):
            return
        self.wrap_function_with_item(self._cut_item)

    def paste_data(self, parent_id, items):
        for item in items:
            text = item.get('t', item.get('text', ''))
            item_id = self.tree.insert(parent_id, 'end', text=text)
            subitems = item.get('s', item.get('subitems', []))
            self.paste_data(item_id, subitems)

    def paste_item(self):
        if not protect_package("pyperclip"):
            return
        self.wrap_function_with_item(self.paste_data, json.loads(pyperclip.paste()), can_use_root=True)

    def tree_to_dict_with_parent(self, parent_id, filter_string=''):
        item = {'t': self.tree.item(parent_id, 'text')}
        children = self.tree_to_dict(parent_id, filter_string)
        if children:
            item['s'] = children
        if ('s' in item) or (filter_string in str(item['t'])):
            return item

    def _find_string(self, text):
        if not protect_package("pyperclip"):
            return
        pyperclip.copy(json.dumps(self.tree_to_dict('', text)))

    def find_string(self):
        if not protect_package("pyperclip"):
            return
        text = simpledialog.askstring("Find string", "Result will be placed in the clipboard")
        if text:
            self._find_string(text)

    def wrap_function_with_item(self, function, *args, can_use_root=False, **kwargs):
        selected_item = self.tree.focus()
        if selected_item or can_use_root:
            function(selected_item, *args, **kwargs)


class ListAppManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("List App Manager")
        self.geometry("1100x700")

        self.button_frame = tk.Frame(self)
        self.button_frame.pack(side=tk.TOP, fill=tk.X)

        self.add_list_app_button = self.create_button("Add List App", self.add_list_app)
        self.close_list_button = self.create_button("Close List", self.close_list)
        self.add_plugin_button = self.create_button("Add Plugin", self.add_plugin)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.load_config()

    def add_plugin(self):
        file_path = filedialog.askopenfilename(filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        if file_path:
            plugin = import_plugin(file_path)
            plugin.act_on_manager(self)
            for tab in self.notebook.tabs():
                app = self.notebook.nametowidget(tab)
                plugin.act_on_list(app)

    def create_button(self, text, command):
        button = tk.Button(self.button_frame, text=text, command=command)
        button.pack(side=tk.LEFT, padx=5, pady=3)
        return button

    def add_list_app(self, file_path=None):
        tab_index = len(self.notebook.tabs())
        tab_name = f"List App {tab_index + 1}" if not file_path else file_path.split("/")[-1]

        app = InteractiveListApp(self.notebook, self.notebook, tab_index, file_path)
        self.notebook.add(app, text=tab_name)

    def close_list(self):
        current_tab = self.notebook.select()
        if messagebox.askokcancel("Close", "Do you want to close this list?"):
            app = self.notebook.nametowidget(current_tab)
            if isinstance(app, InteractiveListApp):
                app.save_list()
            self.notebook.forget(current_tab)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as file:
                config = json.load(file)
            for file_path in config.get('file_paths', []):
                self.add_list_app(file_path)

    def save_config(self):
        config = {}
        file_paths = []
        for tab in self.notebook.tabs():
            app = self.notebook.nametowidget(tab)
            if isinstance(app, InteractiveListApp):
                file_paths.append(app.file_path)
            else:
                file_paths.append(self.notebook.tab(tab, 'text'))
        config['file_paths'] = file_paths
        with open(CONFIG_FILE, 'w') as file:
            json.dump(config, file)

    def save_all_data(self):
        for tab in self.notebook.tabs():
            app = self.notebook.nametowidget(tab)
            if isinstance(app, InteractiveListApp):
                app.save_list()

    def on_closing(self):
        self.save_all_data()
        self.save_config()
        self.destroy()


if __name__ == "__main__":
    manager = ListAppManager()
    manager.mainloop()
