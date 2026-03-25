import tkinter as tk
import tkinter as ttk
from tkinter import messagebox
from main import *
from tkinter import font
import time
import sys

import ctypes

# Make the app DPI-aware
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # Windows 8.1+
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()  # Windows 7 fallback
    except Exception:
        pass


sys.setrecursionlimit(10000)

class App:
    def __init__(self, root: tk.Tk):
        self.root: tk.Tk = root
        self.width = 1600
        self.height = 900
        
        self.root.geometry(f'{self.width}x{self.height}')
        self.root.state('zoomed')

        self.root.bind("<Configure>", self.resize_fontsize_generated_pages)

        self.menu_row = 0
        self.bars_row = 0
        self.total_count_of_stretches_to_select = 0

        self.previous_cat = None
        self.minimal_probability = 0.0001

        self.current_frame = None

        self.define_colors()

        self.load_categories_and_stretches_from_main()

        self.len_of_the_longest_stretch = int(max([len(stretch.name) for category in self.categories for stretch in category.stretches])*0.85)

        self.switch_to_main_page()
        
        #Shortcut Execute and Back; Category Switch
        self.root.bind("<Control-Return>", self.generate_stretches)
        self.root.bind("<BackSpace>", self.switch_to_main_page)
        self.root.bind("<Shift-Return>", self.switch_to_generated_stretches_page)

        for i in range(len(Category.quick_settings)):
            self.root.bind(f"<Key-{i+1}>", lambda event, index = i : self.reflect_changes_when_quick_settings_is_used(list(Category.quick_settings.values())[index]))

        self.long_pressed = False
        self.escape_is_pressed = False
        self.escape_duration_to_close = 1 #in seconds
        self.escape_bind()
    
    def define_colors(self):
        #Define Colors
        self.purplish = '#d7cae8'
        self.light_green = '#44f03c'
        self.dark_green = "#31912c"
        self.light_reddish = '#f0b45b'
        self.dark_reddish = '#a87e3e'
        self.orange = '#f5b507'
        self.grey = '#f0f0f0'
        self.bisque = '#ffe4c4'
        self.black = '#000000'
        self.white = '#ffffff'
        self.light_aquatic = '#e3e8e5'
        self.dark_aquatic = '#c8ccc9'
        self.yellowish_black = '#1f2211'
        self.silver = '#e0e0e0'
        self.yellow = '#f7f35c'
    
    def resize_fontsize_generated_pages(self, event):
        self.width = self.root.winfo_width()
        self.height = self.root.winfo_height()
        self.fontsize = self.width//120+12
        try:
            for label in self.stretches_labels:
                label.config(font=('Georgia',self.fontsize))
        except:
            pass

    def dim_window_when_holding_escape(self):
        delay = 0.25
        if self.escape_is_pressed == True:
            time_diff = time.time() - self.start_time
            if time_diff > delay:
                self.root.attributes('-alpha', 1 - (time_diff-delay)/(self.escape_duration_to_close-delay))
            self.root.after(20, self.dim_window_when_holding_escape)

    def escape_bind(self):
        self.start_time = None
        self.root.bind('<KeyPress-Escape>', self.on_press_escape)
        self.root.bind('<KeyRelease-Escape>', self.on_release_escape)

    def on_press_escape(self, event):
        if self.escape_is_pressed == False:
            self.escape_is_pressed = True
            self.start_time = time.time()
            self.dim_window_when_holding_escape()

    def on_release_escape(self, event):
        self.escape_is_pressed = False
        if self.start_time:
            time_diff = time.time() - self.start_time
            if time_diff > self.escape_duration_to_close: #a long escape press
                self.root.destroy()
            else:
                self.switch_to_main_page() # a short press
                self.root.attributes('-alpha', 1) #revert opacity to normal

    def load_categories_and_stretches_from_main(self):
        self.categories = load_and_read_input()
        self.categories: list[Category] = self.categories

    def create_top_bar(self):
        self.label = tk.Label(self.current_frame, text = 'Stretches', font = ('Georgia', 18), width = 60, bg = self.yellowish_black, fg=self.purplish, relief = "groove", borderwidth = 1)
        self.label.pack(padx = 0, pady = 10)

    def switch_to_main_page(self, event = None):
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = tk.Frame(self.root, width = 3000, height = 600)
        self.total_count_of_stretches_to_select = sum([category.amount_to_select for category in self.categories])

        self.create_top_bar()
        self.create_quick_settings_predefined_toolbar()
        self.create_categories_list_in_menu()

        #Generate Button
        self.big_button = tk.Button(self.current_frame, text = 'Generate Stretches', bg = self.orange, fg = self.black, width = 15, height = 1, relief='groove', font = ('Georgia', 13), command = self.generate_stretches)
        self.big_button.pack(pady = 10)

        #Total Label
        self.total_label = tk.Label(self.current_frame, text = f'Total: {self.total_count_of_stretches_to_select}', bg = self.purplish, fg = self.black, width = 15,height = 1, font = ('Georgia', 13))
        self.total_label.pack(pady = 0)

        self.last_selected_stretches_button = tk.Button(self.current_frame, text = 'Last stretches', bg = self.yellow, fg = self.black, width = 15, height = 1, relief='groove', font = ('Georgia', 13), command = self.switch_to_generated_stretches_page)
        self.last_selected_stretches_button.pack(pady = 10)


        self.current_frame.pack()

    def create_quick_settings_predefined_toolbar(self):
        self.menu = tk.Frame(self.current_frame)

        for i in range(len(Category.quick_settings)):
            self.menu.columnconfigure(i, weight = 1)

        relief = 'groove'

        i = 0
        for name, lst in Category.quick_settings.items():
            name = name.capitalize()
            button = tk.Button(self.menu, text = name, font = ('Georgia', 12), bg = self.purplish, relief = relief, borderwidth = 3, width=20, command = lambda lst = lst: self.reflect_changes_when_quick_settings_is_used(lst))
            button.grid(row = 0, column = i, sticky = tk.E + tk.W)
            i += 1

        self.menu.pack(fill = 'x')

    def reflect_changes_when_quick_settings_is_used(self, counts):
        for i, category in enumerate(self.categories):
            category.amount_to_select = min(counts[i] if len(counts) > i else 0, category.count_valid)
            self.entries[i].delete(0, tk.END) 
            self.entries[i].insert(0, category.amount_to_select)
        self.check_color_up_down_buttons()
        self.total_count_of_stretches_to_select = sum([int(entry.get()) for entry in self.entries])
        self.configure_label_stretches_total()

    def create_categories_list_in_menu(self):
        #Categories Frame
        self.frame = tk.Frame(self.current_frame)
        for i in range(6):
            self.frame.columnconfigure(i, weight = 0 if i <= 1 else 1)
        self.entries = []
        self.button_downs = []
        self.button_ups = []

        for i in range(len(self.categories)):
            category = self.categories[i]
            self.create_main_page_row(i, category)
        
        self.frame.pack()

    def create_main_page_row(self, row, category: Category):
        font_size_row = 14
        label = tk.Label(self.frame, text = category.name.capitalize(), font = ('Georgia', font_size_row), anchor = 'e', width = 19)
        label.grid(row = row, column = 0, padx = 5, pady = 10 if row == 0 else 0)

        entry = tk.Entry(self.frame, font = ('Georgia', 14), width = 4, justify = 'center', bg = self.grey)
        entry.insert(0, min(category.amount_to_select, category.count_valid))
        entry.grid(row = row, column = 1, sticky = 'nsew', pady = 10)

        self.entries.append(entry)
        relief = 'groove'
        self.button_down = tk.Button(self.frame,
                                     text = '−',
                                     font = ('Georgia', font_size_row),
                                     bg = self.dark_reddish if category.amount_to_select == 0 else self.light_reddish,
                                     width = 3,
                                     relief = relief,
                                     command = lambda row = row: self.subtract_one_from_stretches_count(row, True))
        self.button_down.grid(row = row, column = 2, padx = (10, 0), pady = (10) if row == 0 else 10)

        self.button_up = tk.Button(self.frame,
                                   text = '+',
                                   font = ('Georgia', font_size_row),
                                   bg = self.dark_green if category.amount_to_select == category.count_valid else self.light_green,
                                   width = 3,
                                   relief = relief,
                                   command = lambda row = row: self.add_one_to_stretches_count(row, True))
        self.button_up.grid(row = row, column = 3, padx = 0, pady = (10) if row == 0 else 10)

        self.list_stretches_button = tk.Button(self.frame,
                                               text = 'Info',
                                               font = ('Georgia', font_size_row),
                                               bg = self.purplish,
                                               width = 4,
                                               relief = relief,
                                               command = lambda cat = category: self.switch_to_info_individual_category_page(cat))
        self.list_stretches_button.grid(row = row, column = 4, padx = 10, pady = 10 if row == 0 else 10)

        self.textbox = tk.Text(self.frame, height = 2, font = ('Georgia', 11), width = 30, relief=relief)

        text = [stretch.name for stretch in sorted(category.stretches, key = lambda x: x.curr_p, reverse = 1)]
        text_to_insert = "\n".join(text)
        self.textbox.insert("1.0", text_to_insert)
        self.textbox.grid(row = row, column = 5, sticky = 'ew', pady = 5)

        if row == len(self.categories)-1:
            self.navigate_menu_rows()
            self.current_frame.bind('<Key-Up>', lambda event: self.navigate_menu_rows(up = True))
            self.current_frame.bind('<Key-Down>', lambda event: self.navigate_menu_rows(up = False))
            self.current_frame.focus_set()

        self.button_ups.append(self.button_up)
        self.button_downs.append(self.button_down)   
    
    def navigate_menu_rows(self, up = None, event = None):
        if up == True:
            self.menu_row = max(0, self.menu_row-1)
        elif up == False:
            self.menu_row = min(self.menu_row+1, len(self.categories)-1)

        index = self.menu_row
        self.bind_arrows_to_change_amount_of_stretches(index, from_menu = True)
        [self.entries[i].config(bg = self.bisque if self.menu_row == i else self.grey) for i in range(len(self.entries))]

        self.current_frame.bind('<KeyPress-space>', lambda event: self.switch_to_info_individual_category_page(self.categories[index]))

    def bind_arrows_to_change_amount_of_stretches(self, index, from_menu):
        self.current_frame.bind('<Key-Right>', lambda event: self.add_one_to_stretches_count(index, from_menu))
        self.current_frame.bind('<Key-Left>', lambda event: self.subtract_one_from_stretches_count(index, from_menu))

    def switch_to_generated_stretches_page(self, event = None):
        final_generated_stretches = self.generated_stretches

        self.stretches_labels = []

        if self.current_frame:
           self.current_frame.destroy()
            
        self.current_frame = tk.Frame(self.root, width = self.width, height = self.height)

        for i in range(len(final_generated_stretches)):
            self.stretch_name = tk.Label(self.current_frame, text = f"{' ' if (i+1) <= 9 else ''}{i+1}. {final_generated_stretches[i]}", font = ('Georgia', self.fontsize+8), width = 30, bg = self.light_aquatic if i%2 == 0 else self.dark_aquatic, anchor = 'w')
            self.stretch_name.pack(pady = (30, 0) if i == 0 else 0)
            self.stretches_labels.append(self.stretch_name)
        
        band_label = tk.Label(self.current_frame, text= 'Elastic Band', font = ('Georgia', 14), width = 20, bg = self.light_green if any(stretch.requires_band == True for stretch in final_generated_stretches) else self.dark_reddish)

        roller_label = tk.Label(self.current_frame, text= 'Roller', font = ('Georgia', 14), width = 20, bg = self.light_green if 'Roller' in [stretch.name for stretch in final_generated_stretches] else self.dark_reddish)

        band_label.pack(pady = (10, 5))
        roller_label.pack(pady = (5, 10))

        self.back_to_main_page_button()
        self.current_frame.pack()

    def back_to_main_page_button(self):
        self.to_main_page = tk.Button(self.current_frame, text = 'Go Back', font = ('Georgia', 14), width = 20, anchor = 'center', bg = self.purplish, command = self.switch_to_main_page)
        self.to_main_page.pack(pady = 20)

    def switch_to_info_individual_category_page(self, category: Category, event = None):
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = tk.Frame(self.root)

        if self.previous_cat and self.previous_cat != category:
            self.bars_row = 0
        self.previous_cat = category

        self.category_name_heading_info_page = tk.Label(self.current_frame, text = category.name.upper(), font = ('Georgia', 16), fg = self.purplish, bg = self.yellowish_black, width = 79)
        self.category_name_heading_info_page.pack(padx = 30)
    
        self.create_green_probability_bars(category)

        self.amount_stretches_label = tk.Label(self.current_frame, text = category.name.capitalize(), font = ('Georgia', 14), width = 16)
        self.amount_stretches_label.pack(padx = 5, pady = (0))

        self.amount_stretches_entry = tk.Entry(self.current_frame, font = ('Georgia', 14), width = 3, justify = 'center', bg = self.grey)
        self.amount_stretches_entry.insert(0, min(category.count_valid, category.amount_to_select))
        self.amount_stretches_entry.pack(padx = 5 , pady = (0))

        self.total_label = tk.Label(self.current_frame, font = ('Georgia', 14), text = f"Total: {self.total_count_of_stretches_to_select}")
        self.total_label.pack()

        self.back_to_main_page_button()
        self.current_frame.pack()
        
        if self.bars_row <= len(category.stretches):
            self.current_frame.bind('<Key-space>', lambda event, stretch = category.stretches[self.bars_row-1]: self.manipulate_checkbox(stretch))
        
        self.bind_arrows_for_category_info_page(category)

    def create_green_probability_bars(self, category):
        self.frame = tk.Frame(self.current_frame)

        for i in range(4):
            self.frame.columnconfigure(i , weight = 0 if i == 1 else 1)

        stretches_in_category = category.stretches
        max_value = max([stretch.curr_p for stretch in stretches_in_category])
        max_bar_length = 4000

        self.checkboxes_temp_removed = [bool for bool in range(len(category.stretches))]

        #Visual Labels and Buttons
        for row, stretch in enumerate(stretches_in_category):
            label = tk.Label(self.frame, text = stretch.name, bg = self.silver if row != self.bars_row-1 else self.bisque, font = ('Georgia', 14), width = self.len_of_the_longest_stretch, anchor = 'e')
            label.grid(row = row, column = 0, pady = 5)
            if max_value == 0:
                bar_length = 2
            else:
                bar_length = int(stretch.curr_p/max_value*max_bar_length)

            if bar_length >= 420:
                bar_length = bar_length//100
                bar = tk.Label(self.frame, text = f"{(round(stretch.curr_p, 2)):.2f}", font = ('Georgia', 14), bg = self.light_green, width = bar_length)
                bar.grid(row = row, column = 1, padx = 5, pady = 5, sticky = 'w')
            else:
                bar_length = bar_length//100
                right_text = tk.Label(self.frame, text = f"{" "*(bar_length+5)}{round(stretch.curr_p, 2):.2f}", font = ('Georgia', 14), width = max_bar_length//100, anchor='w')
                right_text.grid(row = row, column = 1, padx = 5, pady = 5)

                bar = tk.Label(self.frame, text = '', font = ('Georgia', 14), bg = self.light_green if stretch.curr_p != 0 else self.light_reddish, width = bar_length)
                bar.grid(row = row, column = 1, padx = 5, pady = 5, sticky = 'w')

            self.create_checkboxed_and_increase_buttons(stretch, row)
        print('')

        self.frame.pack()

    def create_checkboxed_and_increase_buttons(self, stretch, row):
        self.checkboxes_temp_removed[row] = tk.IntVar(self.frame, 1 if stretch.can_be_selected else 0)
        variable = self.checkboxes_temp_removed[row]

        checkbox = tk.Checkbutton(self.frame,
                                  text = 'Enabled' if variable.get() == 1 else 'Disabled',
                                  font = ('Georgia', 14),
                                  compound='center',
                                  bg = self.dark_reddish,
                                  variable = variable,
                                  indicatoron = False,
                                  selectcolor = self.dark_green,
                                  borderwidth = 0,
                                  onvalue = 1,
                                  offvalue = 0,
                                  width=8,
                                  command = lambda stretch = stretch: self.manipulate_checkbox(stretch))
        checkbox.grid(row = row, column = 2, padx = 0, pady = 5, sticky='we')

        increase_by_ten_button = tk.Button(self.frame, text = '+10%', font = ('Georgia', 14), width = 5, bg = self.yellow, relief = 'groove')
        increase_by_ten_button.bind('<Button-1>', lambda event, stretch = stretch: self.increase_prob_bar(stretch))
        increase_by_ten_button.bind('<Button-3>', lambda event, stretch = stretch: self.decrease_prob_bar(stretch))
        increase_by_ten_button.grid(row = row, column = 3, padx = (5,0), pady = 5, sticky = 'w')

    def bind_arrows_for_category_info_page(self, category):
        stretches_in_category = category.stretches
        self.current_frame.bind('<Key-Up>', lambda event, category = category: self.navigate_prob_bars_rows(category, up = True))
        self.current_frame.bind('<Key-Down>', lambda event, category = category: self.navigate_prob_bars_rows(category, up = False))

        if len(category.stretches) + 1> self.bars_row > 0:
            self.current_frame.bind(f'<Key-Left>', lambda event, stretch = stretches_in_category[self.bars_row-1]: self.decrease_prob_bar(stretch))
            self.current_frame.bind(f'<Key-Right>', lambda event, stretch = stretches_in_category[self.bars_row-1]: self.increase_prob_bar(stretch))
        elif self.bars_row == 0:
            self.bind_arrows_between_stretches_info_page(category) #if "zeroth" aka minus first row is selected for bar manipulation
            text = self.category_name_heading_info_page['text']

            current_font = font.Font(font = self.category_name_heading_info_page.cget('font'))
            current_font.config(underline = True)

            self.category_name_heading_info_page.config(fg = self.bisque, font = current_font, text = f"← {text} →")
        else:
            self.amount_stretches_entry.config(bg = self.bisque)
            category_index = self.categories.index(category)
            self.bind_arrows_to_change_amount_of_stretches(category_index, from_menu = False)

        self.current_frame.focus_set()

    def navigate_prob_bars_rows(self, category, up, event = None):
        if up == True:
            self.bars_row = (self.bars_row-1)%(len(category.stretches)+2)
        elif up == False:
            self.bars_row = (self.bars_row+1)%(len(category.stretches)+2)

        self.switch_to_info_individual_category_page(category)

    def bind_arrows_between_stretches_info_page(self, category):
        index = self.categories.index(category)

        self.current_frame.bind('<Key-Left>', lambda event: self.switch_to_info_individual_category_page(self.categories[index-1]))
        self.current_frame.bind('<Key-Right>', lambda event: self.switch_to_info_individual_category_page(self.categories[(index+1)%len(self.categories)]))
        self.current_frame.bind('<Key-space>', self.switch_to_main_page)
        self.current_frame.focus_set()

    def increase_prob_bar(self, current_stretch:Stretch):
        category: Category = current_stretch.category
        old_p_curr_str = current_stretch.curr_p

        increase = min(0.1, 1-current_stretch.curr_p)

        if increase != 0 and current_stretch.can_be_selected == True:
            for stretch in category.stretches:
                if stretch.can_be_selected == True:
                    if stretch == current_stretch:
                        stretch.curr_p += increase
                    else:  
                        stretch.curr_p = max(self.minimal_probability, stretch.curr_p - (stretch.curr_p/(1-old_p_curr_str))*increase)

        self.switch_to_info_individual_category_page(category)

    def decrease_prob_bar(self, current_stretch:Stretch):
        category:Category = current_stretch.category
        old_p_curr_str = current_stretch.curr_p

        if current_stretch.curr_p > 0.1:
            decrease = 0.1
        else:
            decrease = old_p_curr_str-self.minimal_probability

        if decrease != 0 and current_stretch.can_be_selected == True and category.count_valid >= 2:
            self.loop_helper_for_adjusting_probs(decrease, current_stretch, category, old_p_curr_str)

        self.switch_to_info_individual_category_page(category)

    def loop_helper_for_adjusting_probs(self, decrease, current_stretch, category, old_p_curr_str):
        for stretch in category.stretches:
            if stretch == current_stretch:
                stretch.curr_p = stretch.curr_p - decrease
            else:
                if old_p_curr_str != 1:  
                    stretch.curr_p = stretch.curr_p + (stretch.curr_p/(1-old_p_curr_str))*decrease
                elif stretch.can_be_selected == True: #if old was set to maximum and stretch is selectable
                    stretch.curr_p += 1/(category.count_valid-1)*decrease

    def manipulate_checkbox(self, stretch, event = None):
        category = stretch.category
        if stretch.can_be_selected: #ie. is checked to no longer be selected
            stretch.can_be_selected = False
            self.checkbox_stretch_disable_adjust_probabilities(stretch)
            category.count_valid -= 1
            category.amount_to_select = min(category.amount_to_select, category.count_valid)
        else:
            stretch.can_be_selected = True
            category.count_valid += 1
            stretch.curr_p = 0.01
            normalize_stretches_globally(self.categories)
        
        self.switch_to_info_individual_category_page(stretch.category)

    def checkbox_stretch_disable_adjust_probabilities(self, current_stretch):
        category:Category = current_stretch.category
        old_p_curr_str = current_stretch.curr_p

        if category.count_valid >= 2:
            self.loop_helper_for_adjusting_probs(old_p_curr_str, current_stretch, category, old_p_curr_str)
        else:
            current_stretch.curr_p = 0

    def add_one_to_stretches_count(self, index, from_menu, event = None):
        if from_menu:
            entry = self.entries[index]
        else:
            entry = self.amount_stretches_entry

        last_value = int(entry.get())        
        new_value = min(last_value + 1, self.categories[index].count_valid)

        entry.delete(0, tk.END)
        entry.insert(0, new_value)

        self.total_count_of_stretches_to_select += 1 if new_value == last_value + 1 else 0
        self.categories[index].amount_to_select = new_value

        if from_menu:
            self.check_color_up_down_buttons()

        self.configure_label_stretches_total()

    def subtract_one_from_stretches_count(self, index, from_menu, event = None):
        if from_menu:
            entry = self.entries[index]
        else:
            entry = self.amount_stretches_entry

        last_value = int(entry.get())        
        new_value = max(0, last_value-1)

        entry.delete(0, tk.END)
        entry.insert(0, new_value)

        self.total_count_of_stretches_to_select -= 1 if new_value == last_value - 1 else 0
        self.categories[index].amount_to_select = new_value

        if from_menu:
            self.check_color_up_down_buttons()

        self.configure_label_stretches_total()
    
    def check_color_up_down_buttons(self):
        for i, button in enumerate(self.button_downs):
            button.config(bg = self.light_reddish)
            if int(self.entries[i].get()) == 0:
                button.config(bg = self.dark_reddish)

        for i, button in enumerate(self.button_ups):
            button.config(bg = self.light_green)
            if int(self.entries[i].get()) == self.categories[i].count_valid:
                button.config(bg = self.dark_green)

    def configure_label_stretches_total(self):
        self.total_label.config(text = f'Total: {self.total_count_of_stretches_to_select}')

    def generate_stretches(self, event = None):
        try:
            self.generated_stretches = execute(self.categories)
            #write_to_notion(self.generated_stretches)
            self.switch_to_generated_stretches_page()
            self.load_categories_and_stretches_from_main()

        except Exception as e:
            self.root.unbind('<KeyPress-Escape>')
            self.root.unbind('<KeyRelease-Escape>')
            messagebox.showerror('Error', e) 
        self.escape_bind()

root = tk.Tk()
App(root)
root.mainloop()