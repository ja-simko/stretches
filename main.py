from __future__ import annotations
import numpy as np 
import os
from shuffle_improved import shuffle_no_adjacent_repeated
import json as json
from sympy.solvers import solve
from sympy import Symbol
import time
from notion_client import Client
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Stretch(): 
    def __init__(self, name, category, curr_p, at_the_top, can_be_selected, requires_band, multiplier):
        self.name = name
        self.category = category
        self.curr_p = curr_p
        self.at_the_top = at_the_top
        self.can_be_selected = can_be_selected
        self.requires_band = requires_band
        self.multiplier = multiplier
        self.lower_bound = 0.01

    def __repr__(self):
        return self.name
        
    def normalize_probability_stretch(self, total_sum_of_category_p):
        if total_sum_of_category_p != 0:
            self.curr_p /= total_sum_of_category_p

class Category():
    instances: list[Category] = []
    final_stretches: list[Stretch] = []
    clashing_stretches: list[tuple[str, str]] = []
    quick_settings: list[list[int]] = []

    def __init__(self, name, amount_to_select, stretches, count_valid):
        self.name: str = name
        self.amount_to_select: int = amount_to_select 
        self.stretches: list[Stretch] = stretches
        self.count_valid: int = count_valid 
        Category.instances.append(self)

    def __repr__(self):
        return self.name

    @staticmethod
    def normalize_probabilities(probabilities):
        if sum(probabilities) > 0:
            return [p/sum(probabilities) for p in probabilities]
    
    @classmethod
    def is_sublist(cls, super_list):
        sub_lists = cls.clashing_stretches
        #check all possible pairs of conflicting stretches
        for sub_list in sub_lists:
            # Check if all items in sub_list are present in super_list
            if all(stretch in super_list for stretch in sub_list):
                return sub_list
        return None
    
    def get_sum_of_prob_in_category(self):
        return sum([stretch.curr_p for stretch in self.stretches])

    def choose_stretches_from_category(self):
        category_stretches = [stretch for stretch in self.stretches if stretch.can_be_selected == True]

        selected_stretches_in_category = np.random.choice(category_stretches, self.amount_to_select, p = Category.normalize_probabilities([stretch.curr_p for stretch in category_stretches]), replace=False).tolist()

        while True:
            conflicting_stretch_group = Category.is_sublist(Category.final_stretches + selected_stretches_in_category)
            if not conflicting_stretch_group:
                #no conflict
                break

            selected_stretches_in_category = self.resolve_conflict(conflicting_stretch_group, category_stretches, selected_stretches_in_category)

        Category.final_stretches.extend(selected_stretches_in_category) 
        return selected_stretches_in_category
    
    def resolve_conflict(self, conflicting_stretch_group, category_stretches, selected_stretches_in_category):
            #if the conflicted not in the same category, select stretch from current category
            if all(conflicting in category_stretches for conflicting in conflicting_stretch_group):
                stretch_to_remove = conflicting_stretch_group[np.random.randint(0,len(conflicting_stretch_group))]
            else:
                stretch_to_remove = next(stretch for stretch in conflicting_stretch_group if stretch.category == self)

            remaining_stretches = [stretch for stretch in category_stretches if stretch not in selected_stretches_in_category]

            if not remaining_stretches or (remaining_stretches[0].name == 'Superman' and len(remaining_stretches) == 1):
                Category.final_stretches = []
                raise Exception(f'Due to conflicting stretches, the amount ({self.amount_to_select}) of stretches in category {self} is too large. Consider lowering the number.')
            
            #pick a substitute stretch
            substitute_stretch = np.random.choice(remaining_stretches, p = Category.normalize_probabilities([stretch.curr_p for stretch in remaining_stretches]), replace=False)
            
            #remove one of the conflicted stretches from the list
            selected_stretches_in_category = [stretch for stretch in selected_stretches_in_category if stretch != stretch_to_remove]

            #append the substitute and check again if there's still a conflict
            selected_stretches_in_category.append(substitute_stretch)
            return selected_stretches_in_category
    
    def update_probabilities_after_selection(self, selected_stretches_in_category): #add multiplier
        all_can_be_selected_stretches = [stretch for stretch in self.stretches if stretch.can_be_selected == True]

        x, sum_of_prob_of_unselected, sum_of_multipliers = self.equation_solver(selected_stretches_in_category, all_can_be_selected_stretches)

        for stretch in all_can_be_selected_stretches:
            if len(selected_stretches_in_category) == self.count_valid: #if all non-zero p stretches in category selected
                stretch.curr_p = 1/self.count_valid #then uniform distribution summing to 100
                continue

            if stretch in selected_stretches_in_category:
                stretch.curr_p = stretch.lower_bound

            else: #stretch not selected
                #old p + ratio of probabilities*ratio of multipliers times x
                prob_upgrade = stretch.curr_p/sum_of_prob_of_unselected*stretch.multiplier/sum_of_multipliers*x
                stretch.curr_p += prob_upgrade
                stretch.curr_p = float(max(0.01, stretch.curr_p))

    def equation_solver(self, selected_stretches_in_category, all_can_be_selected_stretches):
        sum_of_prob_lower_bounds = sum([stretch.lower_bound for stretch in all_can_be_selected_stretches if stretch in selected_stretches_in_category])

        sum_of_prob_of_unselected = sum([stretch.curr_p for stretch in all_can_be_selected_stretches if stretch not in selected_stretches_in_category])

        sum_of_multipliers = sum([stretch.multiplier for stretch in all_can_be_selected_stretches if stretch not in selected_stretches_in_category])

        x = Symbol('x')

        reduction_in_p = 1 - sum_of_prob_of_unselected - sum_of_prob_lower_bounds

        if sum_of_prob_of_unselected:
            fraction_from_unselected = np.array([stretch.curr_p/sum_of_prob_of_unselected for stretch in self.stretches if stretch not in selected_stretches_in_category])

            fraction_of_multipliers = np.array([stretch.multiplier/sum_of_multipliers for stretch in self.stretches if stretch not in selected_stretches_in_category])

            equation = -reduction_in_p + x*(np.sum(fraction_from_unselected*fraction_of_multipliers))
                                                  
            x = solve(equation, x)[0]
        
        else:
            x = 0

        return x, sum_of_prob_of_unselected, sum_of_multipliers

def load_and_read_input() -> list[Category]:
    input_file_path = BASE_DIR / "Stretches_input_json.json"

    with open(input_file_path,'r') as file:
        category_dict, Category.clashing_stretches, Category.quick_settings = json.load(file)

        for category_name, (amount, stretches_dict) in category_dict.items():

            category_instance = Category(category_name, amount_to_select=amount, stretches=[], count_valid=None)

            for stretch_name, value in stretches_dict.items():
                curr_p = value['probability'] if value['can_be_selected'] else 0

                stretch_instance = Stretch(
                                            stretch_name,
                                            category_instance, 
                                            curr_p = curr_p,
                                            at_the_top = value['placed_at_the_top'],
                                            can_be_selected = value['can_be_selected'],
                                            requires_band = value['requires_band'],
                                            multiplier = value['multiplier'])

                category_instance.stretches.append(stretch_instance)

            count_valid = len([stretch for stretch in category_instance.stretches if stretch.can_be_selected == True])
            category_instance.count_valid = count_valid
            category_instance.amount_to_select = min(amount, count_valid)


        stretch_name_to_stretch_instance = {stretch.name:stretch for category in Category.instances for stretch in category.stretches}

        for sub_list in Category.clashing_stretches:
            sub_list[0] = stretch_name_to_stretch_instance[sub_list[0]]
            sub_list[1] = stretch_name_to_stretch_instance[sub_list[1]]

    normalize_stretches_globally(Category.instances)
    return Category.instances

def normalize_stretches_globally(categories:list[Category]):
    for category in categories:
        sum_probabilities = category.get_sum_of_prob_in_category()
        for stretch in category.stretches:
            stretch.normalize_probability_stretch(sum_probabilities)

def write_to_input_file(categories:list[Category]):
    input_file_path = BASE_DIR / "Stretches_input_json.json"

    with open(input_file_path,'w') as file:
        json_dict_categories = {category.name:
                    [
                        category.amount_to_select,

                    {
                        stretch.name:
                    {
                        'probability': round(100*stretch.curr_p), 
                        'placed_at_the_top': stretch.at_the_top, 
                        'can_be_selected': stretch.can_be_selected,
                        'requires_band': stretch.requires_band,
                        'multiplier': stretch.multiplier
                    }
                    for stretch in category.stretches}] for category in categories}
        
        json_clashing = [[str1.name,str2.name] for str1, str2 in Category.clashing_stretches]
        json.dump([json_dict_categories, json_clashing, Category.quick_settings], file, indent=2, separators=(',', ': '))

def write_to_notion(stretches):
    # Connect to Notion
    notion = Client(auth="[some numbers]")

    # Your Notion Database ID
    DATABASE_ID = "[some numbers]"

    # Format
    today = datetime.date.today().strftime("%B %d, %Y")
    iso_today = datetime.date.today().isoformat()  # YYYY-MM-DD

    stretch_text = "\n".join(f"-[] {s}" for s in stretches)

    # Create a new database entry
    notion.pages.create(
    parent={"database_id": DATABASE_ID},
    properties={
        "Name": {  # Title property
            "title": [{"text": {"content": "Stretches"}}]
        },
        "Date": {  # Date property
            "date": {"start": iso_today}
        },
        "Count": {  # Number property
            "number": len(stretches)
        }
    },
    children=[  # Each stretch as a bullet point inside the page
        {
            "object": "block",
            "type": "to_do",
            "to_do": {
            "rich_text": [{"text": {"content": s.name}}],
            "checked": False}
        }
        for s in stretches
        ]
    )

def get_final_shuffled_list():
    return shuffle_no_adjacent_repeated(Category.final_stretches)

def write_to_user(final_shuffled_stretches):
    output_path = BASE_DIR / "Stretches_todays.txt"

    with open(output_path,"w") as file:
        print('GGGG')
        for amount, stretch in enumerate(final_shuffled_stretches):
            file.write(f"{' ' if amount < 9 else ''}{(amount+1)}. {str(stretch)}\n")
        
    return final_shuffled_stretches

def execute(categories:list[Category]):
    selected_in_category_list = []
    try:
        for category in categories:
            selected_in_category_list.append(category.choose_stretches_from_category())
    except Exception as e:
        raise Exception(e)

    for i in range(len(selected_in_category_list)):
        categories[i].update_probabilities_after_selection(selected_in_category_list[i])

    write_to_input_file(categories)

    final_shuffled_list = get_final_shuffled_list()

    Category.final_stretches = []
    Category.instances = []
    return final_shuffled_list

def run_in_terminal():

    '''
    dict_stretches_counter = {}
    for i in range(100):
        categories = load_and_read_input()
        final_shuffled_list = execute(categories)

        for stretch in [s for s in final_shuffled_list if s.category.name == 'BACK']:
            if stretch.name in dict_stretches_counter:
                dict_stretches_counter[stretch.name] += 1
            else:
                dict_stretches_counter[stretch.name] = 1
        final_shuffled_list = []

    print(sorted(dict_stretches_counter.items()))
    '''

    categories = load_and_read_input()
    print([category.name for category in categories])
    final_shuffled_list = execute(categories)
    #write_to_notion(final_shuffled_list)
    write_to_user(final_shuffled_list)
    print(final_shuffled_list)
    print('Resounding Success')
    
if __name__ == '__main__':
    run_in_terminal()
