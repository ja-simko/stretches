from __future__ import annotations
from collections import Counter
import numpy as np

def shuffle_no_adjacent_repeated(all_picked_ordered_stretches):
    stretches_placed_at_the_top, non_top_ordered_stretches, head_stretch = sort_placed_at_the_top_stretches_and_head(all_picked_ordered_stretches)

    #Main shuffle stretches
    selected_categories_amounts = Counter(stretch.category for stretch in non_top_ordered_stretches)

    remaining_stretches_prob = {stretch: (selected_categories_amounts[stretch.category])**(1.2) for stretch in non_top_ordered_stretches}    

    #Top list shuffled and last category
    shuffled_top_list = sorted(stretches_placed_at_the_top, key=lambda stretch: selected_categories_amounts[stretch.category],reverse=True)
    
    last_category =  shuffled_top_list[-1].category if shuffled_top_list else None

    #Main list and finalization
    main_shuffled_list = shuffle_main_without_repeating_categories(remaining_stretches_prob, last_category)
    print(head_stretch)
    return shuffled_top_list  + main_shuffled_list + ([head_stretch] if head_stretch else [])

def sort_placed_at_the_top_stretches_and_head(stretches):
    stretches_placed_at_the_top, non_top_stretches = [], []
    head_stretch = next((stretch for stretch in stretches if stretch.name in ['Head', 'Sternum square']), None)

    for stretch in stretches:
        if stretch == head_stretch:
            continue
        if stretch.at_the_top:
            stretches_placed_at_the_top.append(stretch)
        else:
            non_top_stretches.append(stretch)

    return stretches_placed_at_the_top, non_top_stretches, head_stretch

def shuffle_main_without_repeating_categories(stretches: dict['Stretch', float], last_category):
    main_shuffled_list = []
    #Picking probabilistically while avoiding repeating categories
    while stretches:
        filtered_stretches = {stretch:p for stretch, p in stretches.items() if stretch.category != last_category} or stretches 
    
        normalized_probabilities = normalize_probabilities(filtered_stretches.values())
        picked = np.random.choice(list(filtered_stretches.keys()), p = normalized_probabilities, replace=False)

        #Removing from stretches but adding to main list
        main_shuffled_list.append(picked)
        stretches.pop(picked)
        last_category = picked.category
    
    return main_shuffled_list

def normalize_probabilities(probabilities):
    total = sum(probabilities) 
    return [p/total for p in probabilities]    